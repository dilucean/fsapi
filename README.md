# fsapi

Personal opiniated framework to work *flawlessly* with Claude Code

*you are absolutely right!*

## Stack

- Python 3.12+
- uv, ruff
- FastAPI
- asyncpg
- Jinja2, encourage to just use HTML5, CSS, and vanilla JS
- pytest, playwright -> encourage to just write e2e testing instead of unit test
- PostgreSQL

## Quick Start

### Installation

1. Clone the repo
2. Run `uv sync`
3. Run `cp .env.example .env`
4. Run `uv run main.py`
5. Check CLAUDE.md on tuning for project specific

## Project Structure

```
fsapi/
├── main.py              # FastAPI app, lifespan, router registration
├── sapi.py              # CLI tool for migrations, DB queries, and many other in the future
├── lib/
│   ├── pg.py            # Database pool, transactions, connection
│   └── utils.py         # Environment, logger, templates
├── routers/             # API route handlers
│   └── home.py          # Example routes (/, /health)
├── models/              # Pydantic models for validation
├── views/               # Jinja2 HTML templates (flat structure)
│   └── home.html        # Example template
├── migrations/          # SQL migration files
└── tests/
    └── e2e/             # Playwright end-to-end tests
```

## Development Commands

```bash
# Run development server with auto-reload
uv run main.py

# Run tests
uv run pytest
uv run pytest --headed  # E2E tests with visible browser

# Code quality
uv run ruff check       # Lint code
uv run ruff format      # Format code

# Database migrations
uv run sapi.py migrate:make <name>   # Create new migration
uv run sapi.py migrate               # Run pending migrations
uv run sapi.py migrate:rollback      # Rollback last migration
uv run sapi.py migrate:fresh         # Drop all tables and rerun

# Database queries
uv run sapi.py query 'SELECT * FROM users LIMIT 10'
```
