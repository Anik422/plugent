# Plugent

Plugent is a plugin-based LLM agent framework that connects to your application data, builds useful agent skills, and exposes a simple API for chat, health checks, and schema discovery.

[![PyPI version](https://img.shields.io/pypi/v/plugent.svg)](https://pypi.org/project/plugent/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/plugent.svg)](https://pypi.org/project/plugent/)

## Overview

Plugent is designed for developer-facing AI assistants that need access to a database and a small set of custom tools. The package provides:

- A lightweight `SiteAgent` class for running prompts through an LLM-backed agent
- A `skill` decorator for registering custom functions as skills
- A FastAPI server with `/health`, `/chat`, `/skills`, and `/schema` endpoints
- A Typer-based CLI for setup and debugging

## Installation

Install the base package:

```bash
pip install plugent
```

Install optional extras when needed:

```bash
pip install plugent[mongo]
pip install plugent[gguf]
pip install plugent[test]
pip install plugent[all]
```

## Quick Start

```python
from plugent import SiteAgent

agent = SiteAgent(
    model="gpt-4o-mini",
    db_url="postgresql://user:pass@localhost/mydb",
    company_name="MyShop"
)

reply = agent.run("What products are available?")
print(reply)
```

## Custom Skills

Use the `skill` decorator to mark a function as a reusable agent skill.

```python
from plugent import SiteAgent, skill

@skill
def check_delivery_area(district: str) -> str:
    delivery_zones = ["Dhaka", "Chattogram", "Sylhet", "Rajshahi"]
    if district in delivery_zones:
        return f"Yes, we deliver to {district}."
    return f"Sorry, we do not deliver to {district} yet."


agent = SiteAgent(
    model="gpt-4o-mini",
    db_url="postgresql://user:pass@localhost/mydb",
    custom_skills=[check_delivery_area],
)
```

## CLI

The package includes a CLI named `plugent`.

```bash
plugent init
plugent serve --db-url postgresql://user:pass@localhost/mydb --provider openai
plugent test-db --db-url postgresql://user:pass@localhost/mydb
plugent test-llm --provider openai --api-key your_key
plugent skills --db-url postgresql://user:pass@localhost/mydb
```

## HTTP API

When the server is running, these endpoints are available:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check for the server, LLM, and database |
| `POST` | `/chat` | Send a chat message to the agent |
| `GET` | `/skills` | List active skills |
| `GET` | `/schema` | Return the discovered database schema |

Example request:

```http
POST /chat
Content-Type: application/json

{
  "message": "What is the order status for BD-1234?",
  "session_id": "user_123"
}
```

Example response:

```json
{
  "reply": "Your order BD-1234 is currently being processed.",
  "session_id": "user_123",
  "sources": ["orders table"],
  "confidence": 0.8
}
```

## Environment Variables

The server uses these environment variables:

```env
DATABASE_URL=postgresql://user:pass@localhost/mydb
LITELLM_MODEL=openai
LITELLM_API_KEY=your_api_key
COMPANY_NAME=MyShop
COMPANY_DOMAIN=retail
REDIS_URL=redis://localhost:6379
PLUGENT_API_KEY=optional_auth_token
CHROMA_DIR=./chroma_data
```

## Example Projects

The `examples/` folder contains ready-to-run samples such as:

- `examples/ecommerce_groq.py`
- `examples/ecommerce_ollama.py`
- `examples/quick_start.py`
- `examples/restaurant_bot.py`

## Project Structure

```text
plugent/
├── plugent/
│   ├── agent.py
│   ├── cli.py
│   ├── decorators.py
│   ├── core/
│   ├── db/
│   ├── knowledge/
│   ├── llm/
│   ├── server/
│   └── skills/
├── examples/
├── tests/
├── pyproject.toml
├── setup.py
└── README.md
```

## Development

```bash
git clone https://github.com/yourusername/plugent.git
cd plugent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest tests/
```

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2026 plugent Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
