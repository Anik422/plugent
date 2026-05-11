# Plugent

**AI Agent for PostgreSQL** — Ask natural language questions about your database and get intelligent answers powered by LLMs.

Plugent bridges the gap between natural language and SQL by using embeddings, vector search, and large language models (LLMs) to provide intuitive database interactions without writing SQL queries.

## Features

- 🤖 **Natural Language Queries** — Ask your database questions in plain English
- 🔄 **Automatic Vector Store Synchronization** — Background scheduler keeps embeddings in sync with database changes
- ⚡ **Fast Semantic Search** — Uses FAISS for efficient vector similarity search across your data
- 📊 **Context-Aware Responses** — Provides relevant database context to the LLM for accurate answers
- 🔌 **PostgreSQL Integration** — Works seamlessly with PostgreSQL databases
- 🚀 **Production-Ready** — Async-safe scheduler with configurable sync intervals

## Installation

Install Plugent from PyPI:

```bash
pip install plugent
```

### Prerequisites

- Python 3.9 or higher
- PostgreSQL database
- Groq API key (get one free at [groq.com](https://console.groq.com))

## Quick Start

```python
from plugent import Plugent

# Initialize with your database and API credentials
plugent = Plugent(
    groq_api_key="your_groq_api_key",
    postgres_url="postgresql://user:password@localhost:5432/yourdb",
    vector_store_path="./my_vector_store",
    schedule_interval=60,
)

# Start the agent (connects to DB, builds vector store, starts background sync)
plugent.start()

# Ask natural language questions about your data
answer = plugent.ask("What are the most recent users in the database?")
print(answer)

# Stop the scheduler when done
plugent.stop()
```

## Configuration

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `groq_api_key` | str | required | API key for Groq LLM service |
| `postgres_url` | str | required | PostgreSQL connection string (format: `postgresql://user:password@host:port/database`) |
| `vector_store_path` | str | `"./plugent_store"` | Directory path for saving/loading the FAISS vector store |
| `schedule_interval` | int | `60` | Seconds between database synchronization checks |

## How It Works

### Architecture Overview

Plugent operates through three main components:

1. **Database Reader** — Connects to PostgreSQL and reads table schemas and data
2. **Embedder** — Converts database rows and user queries into vector embeddings using sentence-transformers
3. **Vector Store** — Maintains a FAISS index for fast semantic search and retrieval

### Workflow

1. **Initialization (`start()`)** 
   - Connects to your PostgreSQL database
   - Reads all tables and rows
   - Generates embeddings for each row using sentence-transformers
   - Builds a FAISS vector index
   - Saves the vector store to disk for reuse
   - Starts a background scheduler for continuous updates

2. **Query Processing (`ask()`)**
   - Embeds your natural language question
   - Searches the FAISS vector store for semantically relevant database rows
   - Retrieves the most relevant context
   - Sends the query + context to the Groq LLM
   - Returns the AI-generated answer

3. **Background Synchronization**
   - Periodically checks PostgreSQL for new, modified, or deleted rows
   - Updates the vector store with changes
   - Keeps embeddings fresh and in sync with your database

## Development

### Running Tests

Run the test suite with pytest:

```bash
pytest tests/
```

Run specific tests:

```bash
pytest tests/test_core.py -v
```

### Project Structure

```
plugent/
├── core.py           # Main Plugent class
├── db_reader.py      # PostgreSQL connector
├── embedder.py       # Embedding generation
├── responder.py      # LLM response handler
├── retriever.py      # Vector search retriever
├── scheduler.py      # Background task scheduler
└── vector_store.py   # FAISS vector store management
```

## Requirements

- **sentence-transformers** — For generating embeddings
- **FAISS** — For vector similarity search
- **psycopg2** — PostgreSQL adapter
- **SQLAlchemy** — SQL toolkit and ORM
- **APScheduler** — Background task scheduler
- **Groq** — LLM API client

## License

MIT License — see [LICENSE](LICENSE) for details

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bug reports and feature requests.

## Support

For issues, questions, or feedback, please open an issue on [GitHub](https://github.com/aniksaha/plugent).

---

**Note:** Ensure your PostgreSQL connection string is secure and never commit API keys to version control. Use environment variables for sensitive credentials.