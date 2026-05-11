"""
Quick Start - Minimal 5-line example
Uses SQLite + environment variables
"""

import os
import sys

# Add plugent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === 5 LINE QUICK START ===
# Setup: pip install plugent && cp .env.example .env
# Edit .env with your API keys, then run this!

from plugent.db import SQLConnector
from plugent.llm import get_llm
from plugent.core import ReactAgent

# 1. Create database (auto-creates SQLite)
db = SQLConnector(); db.connect("sqlite:///myapp.db")

# 2. Get LLM from env vars (OPENAI_API_KEY, etc.)
llm = get_llm({"provider": "openai", "api_key": os.getenv("OPENAI_API_KEY")})

# 3. Create agent with company config
agent = ReactAgent(llm, company_config={"name": "My Company", "domain": "general"})

# 4. Chat!
print(agent.think("Hello! What can you do?", []))

# 5. Done! 🚀


# === Extended Example with More Features ===
def extended_example():
    """Full example with more options."""
    from plugent.knowledge import VectorStore, KnowledgeBuilder
    from plugent.core import ConversationMemory
    from plugent import skill

    # --- Database ---
    db = SQLConnector()
    db.connect("sqlite:///myapp.db")
    tables = db.get_tables()
    print(f"Tables: {tables}")

    # --- LLM ---
    llm = get_llm({
        "provider": "openai",  # or "anthropic", "gemini", "groq", "ollama"
        "api_key": "sk-...",
        "model": "gpt-4o-mini",
    })

    # --- Custom Skills ---
    @skill(name="hello", description="Say hello")
    def hello(name: str = "Friend") -> str:
        return f"Hello, {name}! 👋"

    # --- Knowledge Base ---
    store = VectorStore(persist_dir="./chroma_data")
    store.set_llm(llm)
    builder = KnowledgeBuilder(store)
    builder.from_database(db, "kb")

    # --- Agent ---
    agent = ReactAgent(
        llm=llm,
        knowledge=store,
        custom_skills=[hello],
        company_config={
            "name": "My Company",
            "description": "Your business description",
            "domain": "ecommerce",  # or restaurant, hospital, etc.
        },
    )

    # --- Memory ---
    memory = ConversationMemory()
    memory.add("session1", "user", "Hi!")
    memory.add("session1", "assistant", "Hello!")

    # --- Chat Loop ---
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        history = memory.get_recent("session1", n=6)
        response = agent.think(user_input, history)
        print(f"Bot: {response}\n")
        memory.add("session1", "user", user_input)
        memory.add("session1", "assistant", response)


# Run extended example
# extended_example()


if __name__ == "__main__":
    print("Quick start complete!")
    print("\n--- Configuration via .env ---")
    print("""
# .env file options:
DATABASE_URL=sqlite:///myapp.db  # or postgresql://... or mysql://...
LITELLM_MODEL=openai
LITELLM_API_KEY=sk-...
COMPANY_NAME=My Company
COMPANY_DOMAIN=general
REDIS_URL=redis://localhost:6379  # optional
CHROMA_DIR=./chroma_data          # optional
""")