"""FastAPI server for plugent."""

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from plugent.core import (
    ReactAgent,
    ConversationMemory,
    BusinessDetector,
    SkillBuilder,
    AgentConfig,
    CompanyConfig,
)
from plugent.db import SQLConnector, SchemaParser, to_prompt_string
from plugent.knowledge import VectorStore, KnowledgeBuilder
from plugent.llm import get_llm, test_connection


# Global state
_app_state: dict[str, Any] = {}


def get_limiter():
    return Limiter(key_func=get_remote_address)


limiter = get_limiter()
security = HTTPBearer(auto_error=False)


async def verify_token(request: Request):
    """Optional Bearer token verification."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return None
    # Add your token validation logic here
    expected = os.getenv("PLUGENT_API_KEY", "")
    if expected and token != expected:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token


def get_state() -> dict:
    return _app_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Initialize on startup
    config = {
        "provider": os.getenv("LITELLM_MODEL", "openai"),
        "api_key": os.getenv("LITELLM_API_KEY", ""),
    }
    if config["api_key"]:
        config["provider"] = "openai"

    try:
        llm = get_llm(config)
        _app_state["llm"] = llm
        _app_state["connected"] = True
    except Exception as e:
        _app_state["llm"] = None
        _app_state["connected"] = False

    # Initialize components
    _app_state["memory"] = ConversationMemory(
        redis_url=os.getenv("REDIS_URL")
    )
    _app_state["skills"] = []
    _app_state["schema"] = None

    # Try to connect to database
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            conn = SQLConnector()
            conn.connect(db_url)
            _app_state["db"] = conn

            # Parse schema
            parser = SchemaParser()
            schema = parser.parse(conn)
            _app_state["schema"] = schema

            # Build knowledge if LLM available
            if _app_state.get("llm"):
                store = VectorStore(persist_dir=os.getenv("CHROMA_DIR", "./chroma_data"))
                store.set_llm(_app_state["llm"])
                _app_state["knowledge"] = store

                builder = KnowledgeBuilder(store)
                builder.from_database(conn, "db_knowledge")
        except Exception as e:
            _app_state["db_error"] = str(e)
    else:
        _app_state["db"] = None

    yield

    # Cleanup
    if _app_state.get("db"):
        _app_state["db"].close()


# Create app
app = FastAPI(
    title="plugent",
    description="Plugin-based LLM agent framework",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return {"error": "Rate limit exceeded"}


# Request models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ReloadRequest(BaseModel):
    db_url: str | None = None
    llm_config: dict | None = None


# Routes
@app.get("/health")
async def health_check(credentials = Depends(verify_token)):
    """Health check endpoint."""
    state = get_state()

    # Check LLM
    llm_status = "disconnected"
    if state.get("llm"):
        if test_connection(state["llm"]):
            llm_status = "connected"

    # Check DB
    db_status = "not_configured"
    if state.get("db"):
        db_status = "connected"
    elif state.get("db_error"):
        db_status = f"error: {state['db_error']}"

    # Count skills
    skills_count = len(state.get("skills", []))

    return {
        "status": "ok" if state.get("connected") else "degraded",
        "db": db_status,
        "llm": llm_status,
        "skills_count": skills_count,
    }


@app.post("/chat")
@limiter.limit("60/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    credentials = Depends(verify_token),
):
    """Chat endpoint."""
    state = get_state()
    llm = state.get("llm")
    if not llm:
        raise HTTPException(status_code=503, detail="LLM not configured")

    memory = state.get("memory", ConversationMemory())

    # Get history
    history = memory.get_recent(body.session_id, n=10)

    # Build agent if needed
    skills = state.get("skills", [])
    knowledge = state.get("knowledge")
    company_config = {
        "name": os.getenv("COMPANY_NAME", "plugent"),
        "description": os.getenv("COMPANY_DESC", ""),
        "domain": os.getenv("COMPANY_DOMAIN", ""),
    }

    agent = ReactAgent(
        llm=llm,
        skills=skills,
        knowledge=knowledge,
        company_config=company_config,
    )

    # Add user message to memory
    memory.add(body.session_id, "user", body.message)

    # Think
    reply = agent.think(body.message, history)

    # Add assistant response to memory
    memory.add(body.session_id, "assistant", reply)

    # Get sources from knowledge if available
    sources = []
    if knowledge:
        try:
            results = knowledge.search(body.message, "db_knowledge", n=3)
            sources = [r["text"][:200] for r in results]
        except Exception:
            pass

    return {
        "reply": reply,
        "session_id": body.session_id,
        "sources": sources,
        "confidence": 0.8,
    }


@app.get("/skills")
async def list_skills(credentials = Depends(verify_token)):
    """List active skills."""
    state = get_state()
    skills = state.get("skills", [])

    return [
        {
            "name": s.name,
            "description": s.description,
            "parameters": s.parameters,
        }
        for s in skills
    ]


@app.get("/schema")
async def get_schema(credentials = Depends(verify_token)):
    """Get discovered DB schema summary."""
    state = get_state()
    schema = state.get("schema")

    if not schema:
        return {"error": "No schema loaded", "tables": []}

    return {
        "business_type": schema.business_type,
        "tables": [
            {
                "name": t.name,
                "columns": len(t.columns),
                "row_count": schema.row_counts.get(t.name, "?"),
            }
            for t in schema.tables
        ],
        "relationships": len(schema.relationships),
        "row_counts": schema.row_counts,
    }


@app.delete("/chat/{session_id}")
async def clear_chat(session_id: str, credentials = Depends(verify_token)):
    """Clear conversation history."""
    state = get_state()
    memory = state.get("memory")
    if memory:
        memory.clear(session_id)

    return {"status": "cleared", "session_id": session_id}


@app.post("/reload")
async def reload(
    body: ReloadRequest | None = None,
    credentials = Depends(verify_token),
):
    """Reload schema and rebuild skills."""
    state = get_state()

    # Update DB if provided
    db_url = body.db_url if body and body.db_url else os.getenv("DATABASE_URL")
    if db_url:
        try:
            conn = SQLConnector()
            conn.connect(db_url)
            state["db"] = conn

            parser = SchemaParser()
            schema = parser.parse(conn)
            state["schema"] = schema

            # Rebuild knowledge
            if state.get("llm"):
                store = VectorStore(persist_dir=os.getenv("CHROMA_DIR", "./chroma_data"))
                store.set_llm(state["llm"])
                state["knowledge"] = store

                builder = KnowledgeBuilder(store)
                builder.from_database(conn, "db_knowledge")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Reload failed: {e}")

    # Rebuild skills
    schema = state.get("schema")
    if schema and state.get("llm") and state.get("db"):
        try:
            detector = BusinessDetector()
            business = detector.detect(schema, state["llm"])

            builder = SkillBuilder()
            skills = builder.build(schema, business, state["db"], state["llm"])
            state["skills"] = skills
        except Exception as e:
            return {"status": "partial", "error": str(e)}

    return {"status": "reloaded", "skills_count": len(state.get("skills", []))}


@app.get("/widget.js")
async def get_widget():
    """Serve the chat widget JavaScript."""
    widget_path = os.path.join(
        os.path.dirname(__file__),
        "widget",
        "widget.js",
    )
    try:
        with open(widget_path, "r") as f:
            content = f.read()
        return Response(content=content, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Widget not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "plugent.server.app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )