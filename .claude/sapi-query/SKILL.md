---
name: sapi-query
description: Execute SQL queries using the sapi.py query command in the fsapi framework. Use when running SELECT queries, INSERT/UPDATE/DELETE operations, aggregations, JOINs, CTEs, or any ad-hoc database queries through the CLI. Includes patterns for filtering, ordering, pagination, JSON operations, and query optimization.
---

# SAPI Query Command

SQL query patterns and examples for the fsapi framework's `sapi.py query` command.

## Quick Start

### Basic Query Syntax

```bash
uv run sapi.py query '<sql>'
```

### Example

```bash
uv run sapi.py query "SELECT * FROM users LIMIT 5"
```

## SELECT Queries

### Basic SELECT

```bash
# All columns
uv run sapi.py query "SELECT * FROM products"

# Specific columns
uv run sapi.py query "SELECT name, price FROM products"

# With aliases
uv run sapi.py query "SELECT name AS product_name, price AS cost FROM products"
```

### WHERE Clauses

```bash
# Equality
uv run sapi.py query "SELECT * FROM users WHERE email = 'admin@example.com'"

# Comparison operators
uv run sapi.py query "SELECT * FROM products WHERE price > 100"
uv run sapi.py query "SELECT * FROM products WHERE stock <= 10"

# Multiple conditions
uv run sapi.py query "SELECT * FROM products WHERE price > 50 AND stock > 0"
uv run sapi.py query "SELECT * FROM users WHERE role = 'admin' OR role = 'moderator'"

# Pattern matching
uv run sapi.py query "SELECT * FROM users WHERE email LIKE '%@example.com'"
uv run sapi.py query "SELECT * FROM products WHERE name ILIKE '%laptop%'"

# IN clause
uv run sapi.py query "SELECT * FROM products WHERE category IN ('Electronics', 'Books')"

# NULL checks
uv run sapi.py query "SELECT * FROM users WHERE phone IS NULL"
uv run sapi.py query "SELECT * FROM users WHERE phone IS NOT NULL"
```

### Ordering

```bash
# Single column
uv run sapi.py query "SELECT * FROM products ORDER BY price ASC"
uv run sapi.py query "SELECT * FROM products ORDER BY created_at DESC"

# Multiple columns
uv run sapi.py query "SELECT * FROM products ORDER BY category ASC, price DESC"

# NULL handling
uv run sapi.py query "SELECT * FROM products ORDER BY discount NULLS LAST"
```

### Limiting and Pagination

```bash
# LIMIT
uv run sapi.py query "SELECT * FROM users LIMIT 10"

# OFFSET (pagination)
uv run sapi.py query "SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 0"   # Page 1
uv run sapi.py query "SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 10"  # Page 2
uv run sapi.py query "SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 20"  # Page 3
```

## Aggregation Queries

### Basic Aggregations

```bash
# COUNT
uv run sapi.py query "SELECT COUNT(*) FROM users"
uv run sapi.py query "SELECT COUNT(DISTINCT email) FROM users"

# SUM
uv run sapi.py query "SELECT SUM(price) AS total_value FROM products"

# AVG
uv run sapi.py query "SELECT AVG(price) AS average_price FROM products"

# MIN/MAX
uv run sapi.py query "SELECT MIN(price), MAX(price) FROM products"
```

### GROUP BY

```bash
# Single column
uv run sapi.py query "SELECT category, COUNT(*) FROM products GROUP BY category"

# Multiple columns
uv run sapi.py query "SELECT category, brand, COUNT(*) FROM products GROUP BY category, brand"

# With aggregations
uv run sapi.py query "SELECT category, COUNT(*) as count, AVG(price) as avg_price FROM products GROUP BY category"

# With HAVING
uv run sapi.py query "SELECT category, COUNT(*) FROM products GROUP BY category HAVING COUNT(*) > 5"
```

## JOIN Queries

### INNER JOIN

```bash
uv run sapi.py query "
SELECT u.name, p.title
FROM users u
INNER JOIN posts p ON p.user_id = u.id
"
```

### LEFT JOIN

```bash
uv run sapi.py query "
SELECT u.name, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON p.user_id = u.id
GROUP BY u.id, u.name
"
```

### Multiple JOINs

```bash
uv run sapi.py query "
SELECT u.name, p.title, c.content
FROM users u
INNER JOIN posts p ON p.user_id = u.id
LEFT JOIN comments c ON c.post_id = p.id
WHERE u.role = 'admin'
"
```

## INSERT Queries

### Single Row

```bash
uv run sapi.py query "INSERT INTO users (email, name) VALUES ('new@example.com', 'New User')"
```

### Multiple Rows

```bash
uv run sapi.py query "
INSERT INTO products (name, price, stock) VALUES
    ('Product A', 99.99, 10),
    ('Product B', 149.99, 5),
    ('Product C', 29.99, 20)
"
```

### With RETURNING

```bash
uv run sapi.py query "
INSERT INTO users (email, name)
VALUES ('test@example.com', 'Test User')
RETURNING id, email
"
```

## UPDATE Queries

### Basic UPDATE

```bash
uv run sapi.py query "UPDATE users SET name = 'Updated Name' WHERE id = 1"
```

### Multiple Columns

```bash
uv run sapi.py query "
UPDATE products
SET price = 99.99, stock = stock + 10
WHERE id = 5
"
```

### Conditional UPDATE

```bash
uv run sapi.py query "
UPDATE products
SET stock = stock - 1
WHERE id = 3 AND stock > 0
"
```

### UPDATE with RETURNING

```bash
uv run sapi.py query "
UPDATE users
SET last_login = NOW()
WHERE email = 'admin@example.com'
RETURNING id, email, last_login
"
```

## DELETE Queries

### Basic DELETE

```bash
uv run sapi.py query "DELETE FROM users WHERE email = 'test@example.com'"
```

### Conditional DELETE

```bash
uv run sapi.py query "DELETE FROM products WHERE stock = 0 AND discontinued = true"
```

### DELETE with RETURNING

```bash
uv run sapi.py query "DELETE FROM users WHERE id = 10 RETURNING email, name"
```

## JSON/JSONB Queries

### Querying JSON Data

```bash
# Extract JSON field
uv run sapi.py query "SELECT id, metadata->>'name' as name FROM products"

# JSON array element
uv run sapi.py query "SELECT id, tags->0 as first_tag FROM products"

# Nested JSON
uv run sapi.py query "SELECT id, data->'user'->>'email' as email FROM events"

# Check JSON key exists
uv run sapi.py query "SELECT * FROM products WHERE metadata ? 'featured'"

# JSON contains
uv run sapi.py query "SELECT * FROM products WHERE tags @> '[\"electronics\"]'"
```

### Updating JSON

```bash
# Update JSON field
uv run sapi.py query "
UPDATE products
SET metadata = jsonb_set(metadata, '{featured}', 'true')
WHERE id = 1
"

# Append to JSON array
uv run sapi.py query "
UPDATE products
SET tags = tags || '[\"new\"]'::jsonb
WHERE id = 1
"
```

## Common Table Expressions (CTEs)

### Basic CTE

```bash
uv run sapi.py query "
WITH expensive_products AS (
    SELECT * FROM products WHERE price > 100
)
SELECT category, COUNT(*) FROM expensive_products GROUP BY category
"
```

### Multiple CTEs

```bash
uv run sapi.py query "
WITH
    active_users AS (SELECT * FROM users WHERE is_active = true),
    recent_posts AS (SELECT * FROM posts WHERE created_at > NOW() - INTERVAL '7 days')
SELECT u.name, COUNT(p.id) as posts
FROM active_users u
LEFT JOIN recent_posts p ON p.user_id = u.id
GROUP BY u.id, u.name
"
```

## Subqueries

### IN Subquery

```bash
uv run sapi.py query "
SELECT * FROM products
WHERE category_id IN (
    SELECT id FROM categories WHERE featured = true
)
"
```

### Scalar Subquery

```bash
uv run sapi.py query "
SELECT
    name,
    price,
    (SELECT AVG(price) FROM products) as avg_price
FROM products
"
```

## Window Functions

### ROW_NUMBER

```bash
uv run sapi.py query "
SELECT
    name,
    price,
    ROW_NUMBER() OVER (ORDER BY price DESC) as rank
FROM products
"
```

### PARTITION BY

```bash
uv run sapi.py query "
SELECT
    category,
    name,
    price,
    RANK() OVER (PARTITION BY category ORDER BY price DESC) as category_rank
FROM products
"
```

## Utility Queries

### Table Information

```bash
# List all tables
uv run sapi.py query "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"

# Table columns
uv run sapi.py query "
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'users'
"

# Table indexes
uv run sapi.py query "SELECT indexname FROM pg_indexes WHERE tablename = 'users'"

# Table size
uv run sapi.py query "
SELECT pg_size_pretty(pg_total_relation_size('users')) as size
"
```

### Database Statistics

```bash
# Row count
uv run sapi.py query "SELECT COUNT(*) FROM users"

# Table stats
uv run sapi.py query "
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
"
```

## Advanced Patterns

See reference file for detailed examples:
- Full-text search queries
- Array operations
- Date/time manipulations
- Complex aggregations
- Query optimization techniques
