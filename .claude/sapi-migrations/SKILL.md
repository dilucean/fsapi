---
name: sapi-migrations
description: Generate database migration files for the fsapi framework using sapi.py CLI. Use when creating schema migrations, seeders, understanding migration file structure, implementing UP/DOWN sections, handling rollbacks, or working with the migrate commands (migrate:make, migrate, migrate:pending, migrate:rollback, migrate:fresh).
---

# SAPI Migrations

Database migration patterns and best practices for the fsapi framework's sapi.py CLI tool.

## Quick Start

### Creating a New Migration

```bash
uv run sapi.py migrate:make <name>
```

Creates a timestamped migration file: `YYYY_MM_DD_HH_mm_<name>.sql`

### Migration File Structure

```sql
-- UP
-- Schema changes or data insertions go here


-- DOWN
-- Rollback logic goes here
```

## Schema Migrations

Schema migrations create or modify database structure (tables, indexes, constraints).

### Creating a Table

```sql
-- UP
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- DOWN
DROP TABLE IF EXISTS users CASCADE;
```

### Altering a Table

```sql
-- UP
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;

-- DOWN
ALTER TABLE users DROP COLUMN IF EXISTS phone;
ALTER TABLE users DROP COLUMN IF EXISTS is_active;
```

### Adding Indexes

```sql
-- UP
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_created_at ON products(created_at);

-- DOWN
DROP INDEX IF EXISTS idx_products_name;
DROP INDEX IF EXISTS idx_products_created_at;
```

## Seeder Migrations

Seeder migrations insert initial or test data. **Always wrap in transactions** for safety.

### Basic Seeder Pattern

```sql
-- UP
BEGIN;

INSERT INTO users (email, name) VALUES
    ('admin@example.com', 'Admin User'),
    ('user@example.com', 'Regular User');

COMMIT;

-- DOWN
BEGIN;

DELETE FROM users WHERE email IN ('admin@example.com', 'user@example.com');

COMMIT;
```

### Seeder with Related Data

```sql
-- UP
BEGIN;

-- Insert categories first
INSERT INTO categories (id, name) VALUES
    (1, 'Electronics'),
    (2, 'Books');

-- Then products with foreign keys
INSERT INTO products (name, category_id, price) VALUES
    ('Laptop', 1, 1299.99),
    ('Python Book', 2, 49.99);

COMMIT;

-- DOWN
BEGIN;

DELETE FROM products WHERE category_id IN (1, 2);
DELETE FROM categories WHERE id IN (1, 2);

COMMIT;
```

## Migration Commands

### Run Pending Migrations

```bash
uv run sapi.py migrate
```

Executes all pending migrations in chronological order.

### Check Pending Migrations

```bash
uv run sapi.py migrate:pending
```

Shows which migrations haven't been applied yet.

### Rollback Last Migration

```bash
uv run sapi.py migrate:rollback
```

Executes the DOWN section of the last applied migration.

### Fresh Migration

```bash
uv run sapi.py migrate:fresh
```

Drops all tables and re-runs all migrations from scratch (requires confirmation).

## Best Practices

### Naming Conventions

- Use descriptive names: `create_users_table`, `add_email_to_users`, `seed_initial_categories`
- Schema migrations: `create_*`, `add_*`, `alter_*`, `drop_*`
- Seeders: `seed_*`, `populate_*`

### UP Section Guidelines

- Keep migrations focused (one logical change per file)
- Use `IF NOT EXISTS` for CREATE operations when appropriate
- Schema migrations: no transactions (some DDL can't run in transactions)
- Seeders: always use `BEGIN;` and `COMMIT;`

### DOWN Section Guidelines

- Mirror the UP section in reverse
- Use `IF EXISTS` for DROP operations
- Always provide a rollback path
- Test rollbacks work before committing migration

### Transaction Safety

**Schema migrations (no transaction):**
```sql
-- UP
CREATE TABLE products (...);
ALTER TABLE products ADD COLUMN ...;
```

**Seeders (use transaction):**
```sql
-- UP
BEGIN;
INSERT INTO products (...) VALUES (...);
COMMIT;
```

## Common Patterns

### Foreign Keys

```sql
-- UP
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- DOWN
DROP TABLE IF EXISTS orders CASCADE;
```

### JSONB Columns

```sql
-- UP
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    preferences JSONB NOT NULL DEFAULT '{}',
    metadata JSONB
);

-- DOWN
DROP TABLE IF EXISTS settings CASCADE;
```

### Enum Types

```sql
-- UP
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'completed', 'cancelled');

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    status order_status NOT NULL DEFAULT 'pending'
);

-- DOWN
DROP TABLE IF EXISTS orders CASCADE;
DROP TYPE IF EXISTS order_status;
```

## Migration Tracking

The system automatically tracks migrations in the `migrations` table:

```sql
CREATE TABLE migrations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
    duration_ms INTEGER NOT NULL
);
```

Query migration history:
```bash
uv run sapi.py query "SELECT * FROM migrations ORDER BY id"
```

## Advanced Patterns

See reference file for detailed examples:
- Complex schema migrations (multiple tables, constraints, triggers)
- Data transformation migrations
- Conditional seeders
- Migration dependencies and ordering
