# plugent

AI agent for PostgreSQL — ask questions about your database.

## Installation

```bash
pip install plugent
```

## Quick Start

```python
from plugent import Plugent

# Initialize
plugent = Plugent(
    groq_api_key="your_groq_api_key",
    postgres_url="postgresql://user:password@localhost:5432/yourdb",
    vector_store_path="./my_vector_store",
    schedule_interval=60,
)

# Start - connects to DB, builds vector store, starts background sync
plugent.start()

# Ask questions about your data
answer = plugent.ask("What are the users in the database?")
print(answer)

# Stop the scheduler when done
plugent.stop()
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `groq_api_key` | str | required | Groq API key for LLM responses |
| `postgres_url` | str | required | PostgreSQL connection URL |
| `vector_store_path` | str | "./plugent_store" | Path for saving/loading vector store |
| `schedule_interval` | int | 60 | Seconds between DB change checks |

## How It Works

1. **start()** connects to PostgreSQL, reads all rows, embeds them using sentence-transformers, builds FAISS index, saves to disk, starts background scheduler
2. **ask()** embeds your question, searches vector store for relevant context, sends to Groq LLM with context, returns answer
3. **Background scheduler** checks for DB changes every N seconds, updates vector store for new/changed/deleted rows

## Development

Run tests:
```bash
pytest tests/
```