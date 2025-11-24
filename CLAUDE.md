# CLAUDE.md

Developer guide for Claude Code (claude.ai/code) working with fsapi framework.

## Framework Map

```
fsapi/
├── main.py              # App setup, static files, router registration
├── sapi.py              # CLI: migrations, DB queries
├── lib/
│   ├── pg.py            # Pool (min=10, max=20), transaction(), get_pool()
│   └── utils.py         # env(), lgr (logger), tpl() (Jinja2), root()
├── routers/             # APIRouter instances (export as `r`)
│   └── *.py             # Route handlers, import and register in main.py
├── models/              # Pydantic models for validation
├── views/               # Jinja2 templates (flat structure with prefixes)
│   └── *.html           # Use prefixes: user_*, product_*, admin_*
├── static/              # CSS, JS, images (served at /static/*)
├── migrations/          # SQL files: YYYY_MM_DD_HH_MM_<name>.sql
└── tests/e2e/           # Playwright tests
```

## Core Patterns

### Router (routers/example.py)
```python
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from lib.utils import tpl, lgr
from lib.pg import get_pool, transaction

r = APIRouter()

@r.get("/items", response_class=HTMLResponse)
async def list_items():
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM items ORDER BY created_at DESC")
        items = [dict(row) for row in rows]
    return tpl().get_template("item_list.html").render(items=items)

@r.post("/items")
async def create_item(name: str = Form(...)):
    async with transaction() as conn:
        await conn.execute("INSERT INTO items (name) VALUES ($1)", name)
    lgr.info(f"Created item: {name}")
    return RedirectResponse(url="/items", status_code=303)
```

### Database (lib/pg.py)
```python
from lib.pg import transaction, get_pool

# Transactions (write operations)
async with transaction() as conn:
    id = await conn.fetchval("INSERT INTO users (name) VALUES ($1) RETURNING id", name)
    await conn.execute("INSERT INTO profiles (user_id) VALUES ($1)", id)

# Pool access (read-only)
pool = get_pool()
async with pool.acquire() as conn:
    rows = await conn.fetch("SELECT * FROM users WHERE status = $1", "active")
    users = [dict(r) for r in rows]

# Query methods: fetchval() = single value, fetchrow() = one row, fetch() = multiple rows
# Always use parameterized queries: $1, $2, $3 (never f-strings or % formatting)
```

### Dynamic Filters
```python
# Default: Just filter in Python
async def search_items(conn, name=None, status=None):
    rows = await conn.fetch("SELECT * FROM items ORDER BY created_at DESC")
    items = [dict(r) for r in rows]

    if name:
        items = [i for i in items if name.lower() in i["name"].lower()]
    if status:
        items = [i for i in items if i["status"] == status]

    return items

# Only move filtering to SQL if you measure actual performance problems
```

### Templates (views/)
```python
from lib.utils import tpl

template = tpl().get_template("product_list.html")
return template.render(products=products, user=current_user)
```

Template with static files:
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="/static/js/app.js"></script>
</head>
<body>
    <h1>{{ title }}</h1>
    {% for item in items %}
        <p>{{ item.name }}</p>
    {% endfor %}
</body>
</html>
```

### Models (models/)
```python
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    price: float = Field(gt=0)

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

    class Config:
        from_attributes = True  # For asyncpg.Record conversion
```

### Logging
```python
from lib.utils import lgr

lgr.info("User logged in")
lgr.error(f"Database error: {e}")
# Output: 15:30:45.123 | INFO | User logged in
```

## CLI Commands

```bash
# Development
uv run main.py              # Start dev server (auto-reload)
uv run pytest               # Run tests
uv run pytest --headed      # E2E tests with browser
uv run ruff check           # Lint
uv run ruff format          # Format

# Migrations
uv run sapi.py migrate:make <name>    # Create migration file
uv run sapi.py migrate                # Run pending migrations
uv run sapi.py migrate:rollback       # Rollback last migration
uv run sapi.py migrate:fresh          # Drop all tables, rerun all

# Database
uv run sapi.py query 'SELECT * FROM users LIMIT 10'
```

## Migration Files (migrations/)

Format: `YYYY_MM_DD_HH_MM_<name>.sql`

```sql
-- UP
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_items_name ON items(name);

-- DOWN
DROP TABLE IF EXISTS items;
```

## Testing Strategy

- **E2E First:** Write Playwright test for key user workflow
- **Unit Tests:** Only for complex logic (branching, calculations, edge cases)
- **Skip Unit Tests:** Simple CRUD, getters/setters, basic glue code

```python
# tests/e2e/test_items.py
from playwright.sync_api import Page, expect

def test_create_item(page: Page):
    page.goto("/items/new")
    page.fill("input[name='name']", "Test Item")
    page.click("button[type='submit']")
    expect(page).to_have_url("/items")
    expect(page.locator("table")).to_contain_text("Test Item")
```

## Rules

### DO
- Use parameterized queries ($1, $2) - prevents SQL injection
- Use `transaction()` for writes, `get_pool()` for reads
- Flat template structure with prefixes (user_*, product_*)
- Lint and format before completing tasks
- Import logger as: `from lib.utils import lgr`

### DO NOT
- DO NOT add emojis to code or commits
- DO NOT obsess over DRY - copy-paste is fine for clarity
- DO NOT run `uv run main.py` - developer already has it running with auto-reload
- DO NOT use string interpolation in SQL queries
- DO NOT create nested template directories

## Environment Variables

Check .env or .env.example
