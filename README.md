# 🔌 Plugent

> **Your database. Your AI. Zero configuration.**
>
> Plugent automatically reads your website's database, understands your business, builds its own skills, and deploys a fully functional AI customer support agent — all with just a few lines of code.

[![PyPI version](https://img.shields.io/pypi/v/plugent.svg)](https://pypi.org/project/plugent/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/plugent.svg)](https://pypi.org/project/plugent/)

---

## 📌 What is Plugent?

Most AI chatbot solutions require days of manual setup — writing intents, training data, configuring flows. **Plugent is different.**

You give it:
- An **LLM API key** (or a local model file)
- Your **database credentials**
- Basic **company information**

It gives you:
- A fully working **AI agent** that knows your products, orders, FAQs, customers
- A **chat widget** you can embed in any website with one line of HTML
- An **HTTP API** for custom integrations

```python
from plugent import SiteAgent

agent = SiteAgent(
    llm={"provider": "groq", "api_key": "gsk_..."},
    db_url="postgresql://user:pass@localhost/myshop",
    company={"name": "MyShop BD", "language": "Bengali"}
)

agent.serve(port=8000)
# ✅ Your AI agent is live!
```

---

## ✨ Features

- 🔍 **Auto Schema Discovery** — Reads your DB tables, columns, and relationships automatically
- 🧠 **Auto Skill Building** — Generates tools like `search_products`, `check_order`, `get_faq` from your schema
- 🔌 **Universal LLM Support** — Works with OpenAI, Anthropic, Gemini, Groq, Mistral, Cohere, HuggingFace, Ollama, LM Studio, and more
- 🆓 **Free LLM Support** — Works with Groq (free tier), Gemini Free, HuggingFace Inference, Together AI free models
- 🏠 **Local Model Support** — Run 100% offline with Ollama or GGUF models (no data leaves your server)
- 🗄️ **Multi-Database Support** — PostgreSQL, MySQL, SQLite, MongoDB, and more
- 🏢 **Agent Personality Setup** — Set company name, language, tone, rules, and custom instructions
- 🌐 **Embeddable Widget** — One-line HTML embed for any website
- 🔒 **Privacy First** — Use local models to keep all data on your machine
- 📦 **Zero Dependencies Hell** — Simple pip install, minimal setup
- 🔄 **Hot Reload** — Update your DB and the agent learns automatically

---

## 🆓 Supported LLM Providers

### Free / Free Tier Available

| Provider | Model | Free Limit | Notes |
|---|---|---|---|
| **Groq** | `llama-3.3-70b`, `mixtral-8x7b` | 14,400 req/day | Fastest free option ⚡ |
| **Google Gemini** | `gemini-1.5-flash`, `gemini-2.0-flash` | 1,500 req/day | Generous free tier |
| **HuggingFace** | Many open models | Free (slow) | Good for testing |
| **Together AI** | `llama-3`, `mistral` etc | $1 free credit | Good quality |
| **OpenRouter** | Various models | Some free | Aggregator |
| **Cohere** | `command-r` | Free trial | Good for RAG |

### Paid (Best Quality)

| Provider | Model | Notes |
|---|---|---|
| **OpenAI** | `gpt-4o`, `gpt-4o-mini` | Best overall quality |
| **Anthropic** | `claude-sonnet-4-5`, `claude-haiku` | Best reasoning |
| **Google** | `gemini-1.5-pro` | Great multimodal |
| **Mistral AI** | `mistral-large` | Good & affordable |

### Local / Offline (100% Private)

| Method | Models | Notes |
|---|---|---|
| **Ollama** | `llama3`, `mistral`, `phi3`, `gemma` | Easiest local setup |
| **LM Studio** | Any GGUF model | GUI-based |
| **GGUF Direct** | Any `.gguf` file | Via llama-cpp-python |
| **HuggingFace Local** | Transformers models | Full control |

---

## 🗄️ Supported Databases

| Database | URL Format | Status |
|---|---|---|
| PostgreSQL | `postgresql://user:pass@host/db` | ✅ Full support |
| MySQL / MariaDB | `mysql://user:pass@host/db` | ✅ Full support |
| SQLite | `sqlite:///./mydb.sqlite3` | ✅ Full support |
| MongoDB | `mongodb://user:pass@host/db` | ✅ Full support |
| Microsoft SQL Server | `mssql://user:pass@host/db` | ✅ Full support |
| Oracle | `oracle://user:pass@host/db` | 🔄 Coming soon |

---

## 📦 Installation

```bash
pip install plugent
```

### With optional extras

```bash
# For local models via Ollama (recommended)
pip install plugent[ollama]

# For local GGUF models
pip install plugent[gguf]

# For MongoDB support
pip install plugent[mongo]

# Install everything
pip install plugent[all]
```

---

## 🚀 Quick Start

### Option 1 — Free (Groq API)

```python
from plugent import SiteAgent

agent = SiteAgent(
    llm={
        "provider": "groq",
        "api_key": "gsk_your_groq_api_key",   # Free at console.groq.com
        "model": "llama-3.3-70b-versatile"
    },
    db_url="postgresql://user:pass@localhost/myshop_db",
    company={
        "name": "MyShop BD",
        "language": "Bengali",
        "fallback_language": "English"
    }
)

agent.serve(port=8000)
```

### Option 2 — Free (Google Gemini)

```python
from plugent import SiteAgent

agent = SiteAgent(
    llm={
        "provider": "gemini",
        "api_key": "AIza...",         # Free at aistudio.google.com
        "model": "gemini-2.0-flash"
    },
    db_url="mysql://root:pass@localhost/shop",
    company={"name": "My Store"}
)

agent.serve(port=8000)
```

### Option 3 — Local / Offline (Ollama)

```python
from plugent import SiteAgent

# First: install Ollama from ollama.com and run: ollama pull llama3

agent = SiteAgent(
    llm={
        "provider": "ollama",
        "model": "llama3",             # No API key needed!
        "base_url": "http://localhost:11434"
    },
    db_url="sqlite:///./mywebsite.sqlite3",
    company={"name": "Local Shop"}
)

agent.serve(port=8000)
```

### Option 4 — Local GGUF Model File

```python
from plugent import SiteAgent

agent = SiteAgent(
    llm={
        "provider": "gguf",
        "model_path": "./models/llama-3-8b-instruct.Q4_K_M.gguf",
        "n_ctx": 4096,
        "n_gpu_layers": 35        # 0 for CPU only
    },
    db_url="postgresql://user:pass@localhost/mydb"
)

agent.serve(port=8000)
```

---

## ⚙️ Full Configuration

```python
from plugent import SiteAgent

agent = SiteAgent(

    # ── LLM Configuration ─────────────────────────────────────
    llm={
        "provider": "groq",           # openai | anthropic | gemini | groq |
                                      # mistral | cohere | together | huggingface |
                                      # ollama | gguf | lmstudio
        "api_key": "gsk_...",
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.3,           # Lower = more consistent answers
        "max_tokens": 1024,
    },

    # ── Database Configuration ────────────────────────────────
    db_url="postgresql://user:pass@localhost/myshop",
    db_options={
        "read_only": True,            # Agent can only SELECT (recommended)
        "max_rows_per_query": 50,     # Limit data fetched per query
        "exclude_tables": [           # Tables the agent should NOT access
            "users",
            "payments",
            "admin_logs"
        ],
        "include_tables": None,       # If set, ONLY these tables are used
        "sample_rows": 3,             # Sample rows per table for context
    },

    # ── Company / Agent Identity ──────────────────────────────
    company={
        "name": "MyShop BD",
        "tagline": "Bangladesh's best online shop",
        "website": "https://myshop.com.bd",
        "language": "Bengali",              # Primary response language
        "fallback_language": "English",     # If user writes in English
        "support_email": "help@myshop.com.bd",
        "support_phone": "01700-000000",
        "business_hours": "Sat–Thu, 9AM–6PM (BST)",
        "location": "Dhaka, Bangladesh",
    },

    # ── Agent Personality & Rules ─────────────────────────────
    agent={
        "name": "Mia",                    # Agent's name
        "persona": "friendly",            # friendly | professional | formal
        "greeting": "আসসালামু আলাইকুম! আমি Mia, আপনাকে কীভাবে সাহায্য করতে পারি?",
        "fallback_message": "দুঃখিত, এই বিষয়ে আমি নিশ্চিত নই। আমাদের সাপোর্ট টিমে যোগাযোগ করুন।",
        "max_conversation_turns": 20,
        "instructions": """
            - সবসময় বাংলায় উত্তর দাও, যদি না user ইংরেজিতে লেখে
            - order status জানতে order ID চাও
            - product price সবসময় ৳ (BDT) তে দেখাও
            - কখনো competitor-এর নাম নিও না
            - payment বা personal information কখনো জিজ্ঞেস করো না
        """,
        "blocked_topics": [               # এই বিষয়গুলো এড়িয়ে চলবে
            "politics",
            "religion",
            "competitor pricing"
        ]
    },

    # ── Knowledge Base (Extra Info) ───────────────────────────
    knowledge={
        "faq_file": "./data/faq.txt",          # Plain text FAQ
        "policy_file": "./data/policies.md",    # Return/shipping policies
        "custom_docs": ["./docs/guide.pdf"],    # Any extra documents
    },

    # ── Server Configuration ──────────────────────────────────
    server={
        "host": "0.0.0.0",
        "port": 8000,
        "cors_origins": ["*"],          # Restrict to your domain in production
        "rate_limit": 30,               # Requests per minute per IP
        "auth_token": None,             # Optional: Bearer token for API security
    },

    # ── Cache & Performance ───────────────────────────────────
    cache={
        "enabled": True,
        "ttl_seconds": 300,             # Cache responses for 5 minutes
        "backend": "memory",            # memory | redis
        "redis_url": None,              # redis://localhost:6379 (optional)
    },

    # ── Logging ───────────────────────────────────────────────
    logging={
        "level": "INFO",                # DEBUG | INFO | WARNING | ERROR
        "save_conversations": True,     # Save chat logs to file
        "log_file": "./logs/agent.log",
    }
)

agent.serve()
```

---

## 📁 Project File Structure

```
plugent/
│
├── 📄 README.md
├── 📄 pyproject.toml
├── 📄 setup.py
├── 📄 LICENSE
├── 📄 .env.example
│
├── plugent/                          # Main package
│   ├── __init__.py                    # Public API: SiteAgent, Config
│   ├── agent.py                       # SiteAgent main class
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── schema_reader.py           # DB schema discovery
│   │   ├── skill_builder.py           # Auto tool/skill generation
│   │   ├── knowledge_builder.py       # Vector embedding of DB data
│   │   ├── react_agent.py             # ReAct reasoning loop
│   │   └── memory.py                  # Conversation history manager
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py                    # BaseLLM interface
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   ├── groq_provider.py
│   │   ├── mistral_provider.py
│   │   ├── cohere_provider.py
│   │   ├── together_provider.py
│   │   ├── huggingface_provider.py
│   │   ├── ollama_provider.py
│   │   ├── gguf_provider.py           # llama-cpp-python
│   │   ├── lmstudio_provider.py
│   │   └── router.py                  # Auto-selects provider from config
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                    # BaseDBConnector interface
│   │   ├── sql_connector.py           # SQLAlchemy (PG, MySQL, SQLite, MSSQL)
│   │   ├── mongo_connector.py         # MongoDB connector
│   │   └── schema_parser.py           # Table → structured schema dict
│   │
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── base_skill.py              # BaseSkill class
│   │   ├── generated/                 # Auto-generated skills go here
│   │   └── builtin/
│   │       ├── search_products.py
│   │       ├── check_order.py
│   │       ├── get_categories.py
│   │       ├── check_stock.py
│   │       └── get_contact_info.py
│   │
│   ├── server/
│   │   ├── __init__.py
│   │   ├── app.py                     # FastAPI application
│   │   ├── routes.py                  # /chat, /health, /widget.js endpoints
│   │   ├── middleware.py              # CORS, rate limiting, auth
│   │   └── widget/
│   │       ├── widget.js              # Embeddable chat widget (vanilla JS)
│   │       └── widget.css
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── vector_store.py            # ChromaDB wrapper
│   │   ├── embedder.py                # Text → vector embedding
│   │   └── document_loader.py        # Load txt, pdf, md files
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── cache.py
│       └── config_validator.py
│
├── examples/
│   ├── ecommerce_groq.py              # Groq free tier example
│   ├── ecommerce_gemini.py            # Gemini free tier example
│   ├── ecommerce_ollama.py            # Local model example
│   ├── ecommerce_openai.py            # OpenAI example
│   ├── restaurant_bot.py              # Restaurant use case
│   ├── hospital_bot.py                # Hospital/clinic use case
│   └── sample_db/
│       └── demo_shop.sqlite3          # Sample ecommerce DB for testing
│
├── tests/
│   ├── test_schema_reader.py
│   ├── test_skill_builder.py
│   ├── test_llm_providers.py
│   ├── test_agent.py
│   └── test_server.py
│
└── docs/
    ├── getting_started.md
    ├── configuration.md
    ├── llm_providers.md
    ├── database_setup.md
    ├── embedding_widget.md
    ├── custom_skills.md
    └── deployment.md
```

---

## 🌐 Embedding on Your Website

After running `agent.serve(port=8000)`, add this **one line** to any HTML page:

```html
<!-- Floating chat bubble (bottom-right corner) -->
<script src="http://your-server:8000/widget.js"></script>
```

### Custom Widget Options

```html
<script
  src="http://your-server:8000/widget.js"
  data-position="bottom-right"
  data-theme="dark"
  data-primary-color="#E63946"
  data-title="MyShop সাপোর্ট"
  data-greeting="আপনাকে স্বাগতম! কীভাবে সাহায্য করব?"
  data-agent-avatar="/path/to/avatar.png"
  data-open-delay="3000"
></script>
```

### React / Next.js Integration

```jsx
import { AgentWidget } from 'plugent/react'

export default function Layout({ children }) {
  return (
    <>
      {children}
      <AgentWidget
        serverUrl="http://your-server:8000"
        theme="light"
        primaryColor="#2563EB"
      />
    </>
  )
}
```

---

## 🔌 REST API

Once the server is running, you can use the HTTP API directly:

### Chat Endpoint

```http
POST http://localhost:8000/chat
Content-Type: application/json

{
  "message": "আমার order BD-1234 এর status কী?",
  "session_id": "user_abc123"
}
```

**Response:**
```json
{
  "reply": "আপনার অর্ডার BD-1234 বর্তমানে 'শিপমেন্টে' আছে। আনুমানিক ডেলিভারি তারিখ: ১৫ মে ২০২৬।",
  "session_id": "user_abc123",
  "sources": ["orders table"],
  "confidence": 0.94
}
```

### Other Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server & DB health check |
| `GET` | `/skills` | List all auto-generated skills |
| `GET` | `/schema` | View discovered DB schema |
| `POST` | `/chat` | Send a chat message |
| `GET` | `/chat/{session_id}/history` | Get conversation history |
| `DELETE` | `/chat/{session_id}` | Clear conversation |
| `POST` | `/reload` | Reload schema & rebuild skills |
| `GET` | `/widget.js` | Embeddable JS widget |

---

## 🛠️ Custom Skills

You can add your own skills beyond what Plugent auto-generates:

```python
from plugent import SiteAgent, skill

@skill(
    name="check_delivery_area",
    description="Check if we deliver to a specific area or district"
)
def check_delivery_area(district: str) -> str:
    delivery_zones = ["Dhaka", "Chittagong", "Sylhet", "Rajshahi"]
    if district in delivery_zones:
        return f"হ্যাঁ, আমরা {district}-এ ডেলিভারি করি। চার্জ ৳60।"
    return f"দুঃখিত, আমরা এখনো {district}-এ ডেলিভারি করি না।"


agent = SiteAgent(
    llm={...},
    db_url="...",
    custom_skills=[check_delivery_area]
)
```

---

## 🔄 How Auto Skill Building Works

```
1. SCHEMA DISCOVERY
   DB → Tables & Columns → "products, orders, categories, reviews..."

2. INTENT ANALYSIS (via LLM)
   Schema → "This is an ecommerce store with orders and products"

3. SKILL GENERATION
   LLM auto-generates Python tool functions:
   ✅ search_products(query, category, max_price)
   ✅ get_product_details(product_id)
   ✅ check_order_status(order_id)
   ✅ list_categories()
   ✅ check_stock(product_id)
   ✅ get_top_rated_products(limit)

4. KNOWLEDGE EMBEDDING
   Sample data → Vector embeddings → ChromaDB
   (For semantic search: "সস্তা ফোন আছে?" → finds budget phones)

5. AGENT ASSEMBLY
   LLM + Skills + Knowledge + Memory → Ready-to-use Agent
```

---

## 📋 Environment Variables (.env)

```env
# LLM Provider
PLUGENT_LLM_PROVIDER=groq
PLUGENT_LLM_API_KEY=gsk_your_key_here
PLUGENT_LLM_MODEL=llama-3.3-70b-versatile

# Database
PLUGENT_DB_URL=postgresql://user:pass@localhost/myshop

# Company
PLUGENT_COMPANY_NAME=MyShop BD
PLUGENT_AGENT_LANGUAGE=Bengali

# Server
PLUGENT_PORT=8000
PLUGENT_RATE_LIMIT=30

# Optional
PLUGENT_REDIS_URL=redis://localhost:6379
PLUGENT_LOG_LEVEL=INFO
```

Load from `.env` file:

```python
from plugent import SiteAgent
from dotenv import load_dotenv

load_dotenv()

agent = SiteAgent.from_env()  # Reads all config from environment
agent.serve()
```

---

## 🏭 Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install plugent

COPY agent.py .
CMD ["python", "agent.py"]
```

```yaml
# docker-compose.yml
services:
  agent:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

### Run with Gunicorn (Production)

```bash
plugent serve --workers 4 --host 0.0.0.0 --port 8000
```

### Nginx Reverse Proxy

```nginx
location /ai-agent/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Host $host;
}
```

---

## 🔒 Security Best Practices

- Never expose your DB credentials in client-side code
- Use `read_only: True` in `db_options` so the agent cannot modify data
- Use `exclude_tables` to hide sensitive tables (users, payments)
- Set `cors_origins` to your domain only in production
- Use `auth_token` if your `/chat` endpoint is public-facing
- For maximum privacy, use a **local model** (Ollama/GGUF) — no data sent to third parties

---

## 🤝 Contributing

```bash
git clone https://github.com/yourusername/plugent
cd plugent
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -e ".[dev]"
pytest tests/
```

Pull requests are welcome! Please open an issue first for major changes.

---

## 📊 Roadmap

- [x] Core schema reader & skill builder
- [x] Multi-LLM provider support
- [x] Embeddable JS widget
- [x] REST API server
- [ ] WhatsApp integration (via Twilio)
- [ ] Telegram bot support
- [ ] Voice support (speech-to-text)
- [ ] Dashboard UI for monitoring conversations
- [ ] WordPress plugin
- [ ] Shopify app
- [ ] Multi-agent support (handoff to human)
- [ ] Fine-tuning from conversation history

---

## 📄 License

MIT License — free for personal and commercial use.

---

## 💬 Support

- 📧 Email: support@plugent.dev
- 💬 Discord: discord.gg/plugent
- 🐛 Issues: github.com/yourusername/plugent/issues
- 📖 Docs: docs.plugent.dev

---

<p align="center">Built with ❤️ for developers who want AI without the complexity.</p>
