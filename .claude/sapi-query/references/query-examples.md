

# Advanced Query Examples

Detailed SQL query patterns for use with `sapi.py query` command.

## Full-Text Search

### Basic Full-Text Search

```bash
# Simple search
uv run sapi.py query "
SELECT * FROM articles
WHERE to_tsvector('english', title || ' ' || content) @@ to_tsquery('english', 'postgresql')
"

# With ranking
uv run sapi.py query "
SELECT
    title,
    ts_rank(to_tsvector('english', title || ' ' || content), query) as rank
FROM articles, to_tsquery('english', 'postgresql & database') query
WHERE to_tsvector('english', title || ' ' || content) @@ query
ORDER BY rank DESC
"
```

### Pre-computed Search Vectors

```bash
# Using tsvector column with GIN index
uv run sapi.py query "
SELECT title, content
FROM articles
WHERE search_vector @@ to_tsquery('english', 'fastapi & asyncpg')
ORDER BY ts_rank(search_vector, to_tsquery('english', 'fastapi & asyncpg')) DESC
LIMIT 10
"

# Phrase search
uv run sapi.py query "
SELECT title
FROM articles
WHERE search_vector @@ phraseto_tsquery('english', 'machine learning')
"

# Prefix search
uv run sapi.py query "
SELECT title
FROM articles
WHERE search_vector @@ to_tsquery('english', 'postgre:*')
"
```

## Array Operations

### Querying Arrays

```bash
# Check if array contains value
uv run sapi.py query "
SELECT * FROM products
WHERE 'electronics' = ANY(tags)
"

# Check if array contains all values
uv run sapi.py query "
SELECT * FROM products
WHERE tags @> ARRAY['electronics', 'laptop']
"

# Array overlap
uv run sapi.py query "
SELECT * FROM products
WHERE tags && ARRAY['sale', 'clearance']
"

# Array length
uv run sapi.py query "
SELECT name, array_length(tags, 1) as tag_count
FROM products
"
```

### Modifying Arrays

```bash
# Append to array
uv run sapi.py query "
UPDATE products
SET tags = array_append(tags, 'featured')
WHERE id = 1
"

# Remove from array
uv run sapi.py query "
UPDATE products
SET tags = array_remove(tags, 'discontinued')
WHERE id = 1
"

# Concatenate arrays
uv run sapi.py query "
UPDATE products
SET tags = tags || ARRAY['new', 'trending']
WHERE id = 1
"
```

### Unnesting Arrays

```bash
# Expand array into rows
uv run sapi.py query "
SELECT id, unnest(tags) as tag
FROM products
"

# Count occurrences of array elements
uv run sapi.py query "
SELECT tag, COUNT(*) as count
FROM (
    SELECT unnest(tags) as tag FROM products
) t
GROUP BY tag
ORDER BY count DESC
"
```

## Date and Time Operations

### Date Filtering

```bash
# Specific date
uv run sapi.py query "
SELECT * FROM orders
WHERE DATE(created_at) = '2025-11-23'
"

# Date range
uv run sapi.py query "
SELECT * FROM orders
WHERE created_at BETWEEN '2025-11-01' AND '2025-11-30'
"

# Relative dates
uv run sapi.py query "
SELECT * FROM orders
WHERE created_at > NOW() - INTERVAL '7 days'
"

# Today's records
uv run sapi.py query "
SELECT * FROM orders
WHERE DATE(created_at) = CURRENT_DATE
"
```

### Date Aggregations

```bash
# Group by date
uv run sapi.py query "
SELECT DATE(created_at) as date, COUNT(*) as orders
FROM orders
GROUP BY DATE(created_at)
ORDER BY date DESC
"

# Group by month
uv run sapi.py query "
SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as orders,
    SUM(total) as revenue
FROM orders
GROUP BY month
ORDER BY month DESC
"

# Group by hour of day
uv run sapi.py query "
SELECT
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as count
FROM orders
GROUP BY hour
ORDER BY hour
"
```

### Date Formatting

```bash
# Custom format
uv run sapi.py query "
SELECT
    id,
    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') as formatted_date
FROM orders
"

# Different formats
uv run sapi.py query "
SELECT
    TO_CHAR(NOW(), 'Day, DD Month YYYY') as full_date,
    TO_CHAR(NOW(), 'HH12:MI AM') as time_12hr,
    TO_CHAR(NOW(), 'YYYY-MM-DD') as iso_date
"
```

## Complex Aggregations

### Conditional Aggregations

```bash
# COUNT with conditions
uv run sapi.py query "
SELECT
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_orders,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_orders,
    COUNT(*) FILTER (WHERE total > 100) as large_orders
FROM orders
"

# SUM with conditions
uv run sapi.py query "
SELECT
    SUM(total) as total_revenue,
    SUM(total) FILTER (WHERE status = 'completed') as completed_revenue,
    SUM(total) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as last_30_days
FROM orders
"
```

### Multiple Aggregations

```bash
uv run sapi.py query "
SELECT
    category,
    COUNT(*) as product_count,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(price) as avg_price,
    STDDEV(price) as price_stddev,
    SUM(stock) as total_stock
FROM products
GROUP BY category
ORDER BY product_count DESC
"
```

### ROLLUP and CUBE

```bash
# Subtotals with ROLLUP
uv run sapi.py query "
SELECT
    category,
    brand,
    SUM(stock) as total_stock
FROM products
GROUP BY ROLLUP(category, brand)
ORDER BY category, brand
"

# All combinations with CUBE
uv run sapi.py query "
SELECT
    category,
    brand,
    COUNT(*) as count
FROM products
GROUP BY CUBE(category, brand)
"
```

## Advanced JOINs

### LATERAL JOIN

```bash
# Get top 3 products per category
uv run sapi.py query "
SELECT c.name as category, p.name as product, p.price
FROM categories c
CROSS JOIN LATERAL (
    SELECT name, price
    FROM products
    WHERE category_id = c.id
    ORDER BY price DESC
    LIMIT 3
) p
ORDER BY c.name, p.price DESC
"
```

### Self JOIN

```bash
# Find users with same email domain
uv run sapi.py query "
SELECT
    u1.email as user1,
    u2.email as user2
FROM users u1
INNER JOIN users u2
    ON SPLIT_PART(u1.email, '@', 2) = SPLIT_PART(u2.email, '@', 2)
    AND u1.id < u2.id
"
```

### Recursive CTE

```bash
# Organizational hierarchy
uv run sapi.py query "
WITH RECURSIVE org_chart AS (
    -- Base case: top-level managers
    SELECT id, name, manager_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- Recursive case: employees reporting to someone
    SELECT e.id, e.name, e.manager_id, oc.level + 1
    FROM employees e
    INNER JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT * FROM org_chart ORDER BY level, name
"
```

## Statistical Queries

### Percentiles

```bash
# Calculate percentiles
uv run sapi.py query "
SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price) as p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price) as median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price) as p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY price) as p95
FROM products
"
```

### Mode (Most Frequent Value)

```bash
uv run sapi.py query "
SELECT MODE() WITHIN GROUP (ORDER BY category) as most_common_category
FROM products
"
```

### Correlation

```bash
# Calculate correlation between two columns
uv run sapi.py query "
SELECT CORR(price, stock) as price_stock_correlation
FROM products
"
```

## Query Optimization Techniques

### EXPLAIN Query

```bash
# See query execution plan
uv run sapi.py query "
EXPLAIN ANALYZE
SELECT u.name, COUNT(p.id)
FROM users u
LEFT JOIN posts p ON p.user_id = u.id
GROUP BY u.id, u.name
"
```

### Using Indexes

```bash
# Check if index is being used
uv run sapi.py query "
EXPLAIN
SELECT * FROM users WHERE email = 'test@example.com'
"

# Index usage statistics
uv run sapi.py query "
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC
"
```

### Materialized CTEs

```bash
# Force CTE materialization for optimization
uv run sapi.py query "
WITH filtered_products AS MATERIALIZED (
    SELECT * FROM products WHERE price > 100
)
SELECT category, COUNT(*)
FROM filtered_products
GROUP BY category
"
```

## Data Validation Queries

### Find Duplicates

```bash
# Duplicate emails
uv run sapi.py query "
SELECT email, COUNT(*) as count
FROM users
GROUP BY email
HAVING COUNT(*) > 1
"

# Duplicate combinations
uv run sapi.py query "
SELECT first_name, last_name, COUNT(*)
FROM users
GROUP BY first_name, last_name
HAVING COUNT(*) > 1
"
```

### Find Orphaned Records

```bash
# Orders without users
uv run sapi.py query "
SELECT o.*
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
WHERE u.id IS NULL
"
```

### Data Quality Checks

```bash
# Null value checks
uv run sapi.py query "
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE email IS NULL) as null_emails,
    COUNT(*) FILTER (WHERE name IS NULL) as null_names
FROM users
"

# Invalid data patterns
uv run sapi.py query "
SELECT * FROM users
WHERE email NOT LIKE '%@%.%'
OR LENGTH(name) < 2
"
```

## Pivot and Unpivot

### Pivot with CROSSTAB

```bash
# Monthly sales by category (requires tablefunc extension)
uv run sapi.py query "
SELECT
    category,
    SUM(CASE WHEN EXTRACT(MONTH FROM created_at) = 1 THEN total ELSE 0 END) as jan,
    SUM(CASE WHEN EXTRACT(MONTH FROM created_at) = 2 THEN total ELSE 0 END) as feb,
    SUM(CASE WHEN EXTRACT(MONTH FROM created_at) = 3 THEN total ELSE 0 END) as mar
FROM orders
GROUP BY category
"
```

### Unpivot

```bash
# Convert columns to rows
uv run sapi.py query "
SELECT id, 'q1' as quarter, q1_sales as sales FROM quarterly_sales
UNION ALL
SELECT id, 'q2' as quarter, q2_sales as sales FROM quarterly_sales
UNION ALL
SELECT id, 'q3' as quarter, q3_sales as sales FROM quarterly_sales
UNION ALL
SELECT id, 'q4' as quarter, q4_sales as sales FROM quarterly_sales
"
```

## String Operations

### Pattern Matching

```bash
# SIMILAR TO (SQL regex)
uv run sapi.py query "
SELECT * FROM products
WHERE name SIMILAR TO '%(laptop|notebook)%'
"

# Regular expressions
uv run sapi.py query "
SELECT * FROM users
WHERE email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
"
```

### String Manipulation

```bash
# Concatenation
uv run sapi.py query "
SELECT first_name || ' ' || last_name as full_name
FROM users
"

# String functions
uv run sapi.py query "
SELECT
    UPPER(name) as uppercase,
    LOWER(name) as lowercase,
    INITCAP(name) as title_case,
    LENGTH(name) as length,
    SUBSTRING(name, 1, 10) as truncated
FROM products
"

# Replace and trim
uv run sapi.py query "
SELECT
    REPLACE(description, 'old', 'new') as replaced,
    TRIM(BOTH ' ' FROM name) as trimmed,
    REGEXP_REPLACE(name, '[^a-zA-Z0-9]', '', 'g') as alphanumeric_only
FROM products
"
```

## Transactions with Query Command

While the query command doesn't wrap queries in transactions automatically, you can use explicit transactions:

```bash
# Begin transaction
uv run sapi.py query "BEGIN"

# Make changes
uv run sapi.py query "UPDATE users SET balance = balance - 100 WHERE id = 1"
uv run sapi.py query "UPDATE users SET balance = balance + 100 WHERE id = 2"

# Commit or rollback
uv run sapi.py query "COMMIT"
# or
uv run sapi.py query "ROLLBACK"
```

For complex multi-query transactions, use a migration file instead.
