"""CLI for plugent using Typer."""

import os
import sys
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="plugent - Plugin-based LLM agent framework")
console = Console()


@app.command()
def serve(
    db_url: Optional[str] = typer.Option(None, "--db-url", help="Database URL"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="LLM API key"),
    provider: str = typer.Option("openai", "--provider", help="LLM provider"),
    port: int = typer.Option(8000, "--port", help="Server port"),
    host: str = typer.Option("0.0.0.0", "--host", help="Server host"),
):
    """Start the plugent server."""
    # Set environment variables
    if db_url:
        os.environ["DATABASE_URL"] = db_url
    if api_key:
        os.environ["LITELLM_API_KEY"] = api_key
    os.environ["LITELLM_MODEL"] = provider

    console.print(f"[green]Starting plugent server on {host}:{port}...[/green]")

    import uvicorn
    from plugent.server.app import app

    uvicorn.run(app, host=host, port=port)


@app.command()
def init():
    """Interactive setup wizard."""
    console.print("[bold blue]plugent Setup Wizard[/bold blue]\n")

    # Collect config
    config = {}

    # Database
    db_type = typer.prompt(
        "Database type? (sqlite/postgresql/mysql)",
        default="sqlite"
    )

    if db_type == "sqlite":
        config["DATABASE_URL"] = typer.prompt(
            "DB file path",
            default="./plugent.db"
        )
        config["DATABASE_URL"] = f"sqlite:///{config['DATABASE_URL']}"
    else:
        host = typer.prompt("DB host", default="localhost")
        user = typer.prompt("DB user")
        password = typer.prompt("DB password", hide_input=True)
        db_name = typer.prompt("Database name")
        port = typer.prompt("DB port", default="5432" if db_type == "postgresql" else "3306")
        config["DATABASE_URL"] = f"{db_type}://{user}:{password}@{host}:{port}/{db_name}"

    # LLM
    config["LITELLM_MODEL"] = typer.prompt(
        "LLM provider? (openai/anthropic/gemini/groq/ollama)",
        default="openai"
    )

    if config["LITELLM_MODEL"] not in ["ollama", "lmstudio"]:
        config["LITELLM_API_KEY"] = typer.prompt(
            "API key",
            hide_input=True
        )

    if config["LITELLM_MODEL"] == "ollama":
        config["OLLAMA_BASE_URL"] = typer.prompt(
            "Ollama URL",
            default="http://localhost:11434"
        )

    # Company info
    config["COMPANY_NAME"] = typer.prompt("Company name", default="My Company")
    config["COMPANY_DOMAIN"] = typer.prompt("Business domain", default="general")

    # Optional Redis
    use_redis = typer.confirm("Use Redis for session storage?", default=False)
    if use_redis:
        config["REDIS_URL"] = typer.prompt("Redis URL", default="redis://localhost:6379")

    # API key
    config["PLUGENT_API_KEY"] = typer.prompt(
        "API key for authentication (optional)",
        default=""
    )

    # Write .env file
    env_content = "\n".join(f"{k}={v}" for k, v in config.items() if v)
    with open(".env", "w") as f:
        f.write(env_content)

    console.print("\n[green]✓[/green] Created .env file")
    console.print("\nRun [bold]plugent serve[/bold] to start the server.")


@app.command()
def test_db(
    db_url: str = typer.Option(..., "--db-url", help="Database URL"),
):
    """Test database connection and show discovered tables."""
    from plugent.db import SQLConnector

    console.print(f"[dim]Connecting to {db_url}...[/dim]")

    try:
        conn = SQLConnector()
        conn.connect(db_url)

        tables = conn.get_tables()
        console.print(f"\n[green]✓[/green] Connected successfully!")
        console.print(f"\n[bold]Discovered {len(tables)} tables:[/bold]\n")

        for table in tables:
            columns = conn.get_columns(table)
            sample = conn.get_sample_rows(table, n=2)
            console.print(f"  • {table} ({len(columns)} columns, {len(sample)} sample rows)")

            # Show FKs
            fks = conn.get_foreign_keys()
            if table in fks:
                for fk in fks[table]:
                    console.print(f"    ↳ FK: {fk['constrained_columns']} → {fk['referred_table']}")

        conn.close()

    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        raise typer.Exit(1)


@app.command()
def test_llm(
    provider: str = typer.Option(..., "--provider", help="LLM provider"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name"),
):
    """Test LLM connection."""
    from plugent.llm import get_llm

    config = {"provider": provider}
    if api_key:
        config["api_key"] = api_key
    if model:
        config["model"] = model

    console.print(f"[dim]Testing {provider}...[/dim]")

    try:
        llm = get_llm(config)

        # Send test message
        messages = [{"role": "user", "content": "Say 'OK' if you can hear me."}]
        response = llm.chat(messages)

        if response:
            console.print(f"\n[green]✓[/green] Connected successfully!")
            console.print(f"\n[bold]Response:[/bold]\n{response[:200]}")
        else:
            console.print("[yellow]⚠[/yellow] No response received")

    except Exception as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        raise typer.Exit(1)


@app.command()
def skills(
    db_url: str = typer.Option(..., "--db-url", help="Database URL"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key"),
    provider: str = typer.Option("openai", "--provider", help="LLM provider"),
):
    """Show skills that would be generated for a database."""
    from plugent.db import SQLConnector, SchemaParser
    from plugent.llm import get_llm
    from plugent.core import BusinessDetector

    console.print("[dim]Analyzing database...[/dim]\n")

    try:
        # Connect to DB
        conn = SQLConnector()
        conn.connect(db_url)

        # Parse schema
        parser = SchemaParser()
        schema = parser.parse(conn)

        console.print(f"[green]✓[/green] Found {len(schema.tables)} tables")

        # Get LLM
        config = {"provider": provider}
        if api_key:
            config["api_key"] = api_key

        llm = get_llm(config)

        # Detect business
        detector = BusinessDetector()
        business = detector.detect(schema, llm)

        # Display results
        console.print(f"\n[bold]Business Type:[/bold] {business.business_type}")
        console.print(f"[bold]Confidence:[/bold] {business.confidence:.2f}\n")

        console.print("[bold]Key Entities:[/bold]")
        for entity in business.key_entities:
            console.print(f"  • {entity.get('table')}: {entity.get('description', '')}")

        console.print("\n[bold]Suggested Skills:[/bold]")
        for skill in business.suggested_skills:
            console.print(f"  • {skill}")

        conn.close()

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()