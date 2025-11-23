# Advanced Migration Patterns

Detailed examples and patterns for database migrations in the fsapi framework.

## Complex Schema Migrations

### Multiple Related Tables

```sql
-- UP
-- Create parent table first
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create child tables with foreign keys
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Add indexes
CREATE INDEX idx_departments_company_id ON departments(company_id);
CREATE INDEX idx_employees_department_id ON employees(department_id);
CREATE INDEX idx_employees_email ON employees(email);

-- DOWN
-- Drop in reverse order (child tables first)
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
```

### Composite Keys and Constraints

```sql
-- UP
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    granted_by INTEGER REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

-- Add check constraint
ALTER TABLE user_roles ADD CONSTRAINT chk_no_self_grant
    CHECK (user_id != granted_by);

-- DOWN
DROP TABLE IF EXISTS user_roles CASCADE;
```

### Triggers and Functions

```sql
-- UP
-- Create function
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER tr_users_update_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_timestamp();

-- DOWN
DROP TRIGGER IF EXISTS tr_users_update_timestamp ON users;
DROP FUNCTION IF EXISTS update_modified_timestamp();
```

## Data Transformation Migrations

### Backfilling Data

```sql
-- UP
BEGIN;

-- Add new column
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Backfill data from existing columns
UPDATE users SET full_name = CONCAT(first_name, ' ', last_name);

-- Make it NOT NULL after backfill
ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;

COMMIT;

-- DOWN
BEGIN;

ALTER TABLE users DROP COLUMN IF EXISTS full_name;

COMMIT;
```

### Data Type Changes

```sql
-- UP
BEGIN;

-- Add new column with new type
ALTER TABLE products ADD COLUMN price_new DECIMAL(10, 2);

-- Copy and transform data
UPDATE products SET price_new = price::DECIMAL(10, 2);

-- Drop old column and rename new one
ALTER TABLE products DROP COLUMN price;
ALTER TABLE products RENAME COLUMN price_new TO price;

-- Add NOT NULL constraint
ALTER TABLE products ALTER COLUMN price SET NOT NULL;

COMMIT;

-- DOWN
BEGIN;

-- Reverse the process
ALTER TABLE products ADD COLUMN price_old INTEGER;
UPDATE products SET price_old = price::INTEGER;
ALTER TABLE products DROP COLUMN price;
ALTER TABLE products RENAME COLUMN price_old TO price;
ALTER TABLE products ALTER COLUMN price SET NOT NULL;

COMMIT;
```

### Splitting Tables

```sql
-- UP
BEGIN;

-- Create new table for extracted data
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    avatar_url VARCHAR(500),
    website VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Migrate existing data
INSERT INTO user_profiles (user_id, bio, avatar_url, website)
SELECT id, bio, avatar_url, website FROM users;

-- Remove old columns
ALTER TABLE users DROP COLUMN bio;
ALTER TABLE users DROP COLUMN avatar_url;
ALTER TABLE users DROP COLUMN website;

COMMIT;

-- DOWN
BEGIN;

-- Add columns back to users
ALTER TABLE users ADD COLUMN bio TEXT;
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
ALTER TABLE users ADD COLUMN website VARCHAR(500);

-- Migrate data back
UPDATE users u
SET
    bio = up.bio,
    avatar_url = up.avatar_url,
    website = up.website
FROM user_profiles up
WHERE u.id = up.user_id;

-- Drop the profiles table
DROP TABLE IF EXISTS user_profiles CASCADE;

COMMIT;
```

## Conditional Seeders

### Environment-Aware Seeds

```sql
-- UP
BEGIN;

-- Always seed admin user
INSERT INTO users (email, name, role) VALUES
    ('admin@example.com', 'Admin', 'admin');

-- Conditionally seed test data (check if in development)
DO $$
BEGIN
    IF current_database() = 'avelumina_dev' THEN
        INSERT INTO users (email, name, role) VALUES
            ('test1@example.com', 'Test User 1', 'user'),
            ('test2@example.com', 'Test User 2', 'user'),
            ('test3@example.com', 'Test User 3', 'user');
    END IF;
END $$;

COMMIT;

-- DOWN
BEGIN;

DELETE FROM users WHERE email IN (
    'admin@example.com',
    'test1@example.com',
    'test2@example.com',
    'test3@example.com'
);

COMMIT;
```

### Idempotent Seeds (Don't Insert Duplicates)

```sql
-- UP
BEGIN;

-- Insert only if not exists
INSERT INTO categories (name, slug)
SELECT 'Electronics', 'electronics'
WHERE NOT EXISTS (
    SELECT 1 FROM categories WHERE slug = 'electronics'
);

INSERT INTO categories (name, slug)
SELECT 'Books', 'books'
WHERE NOT EXISTS (
    SELECT 1 FROM categories WHERE slug = 'books'
);

COMMIT;

-- DOWN
BEGIN;

DELETE FROM categories WHERE slug IN ('electronics', 'books');

COMMIT;
```

## Migration Dependencies and Ordering

### File Naming Strategy

Migrations run in alphabetical order based on filename. Use timestamps to control execution order:

```
2025_11_23_14_00_create_users_table.sql        # First
2025_11_23_14_01_create_posts_table.sql        # Second (depends on users)
2025_11_23_14_02_create_comments_table.sql     # Third (depends on posts)
2025_11_23_15_00_seed_users.sql                # After all tables
2025_11_23_15_01_seed_posts.sql                # After users seeded
```

### Handling Dependencies

If you need to ensure a specific order, use timestamp increments:

```bash
# Schema migrations
uv run sapi.py migrate:make create_categories      # 2025_11_23_10_00_create_categories.sql
uv run sapi.py migrate:make create_products        # 2025_11_23_10_01_create_products.sql

# Wait a minute, then create seeders
uv run sapi.py migrate:make seed_categories        # 2025_11_23_10_02_seed_categories.sql
uv run sapi.py migrate:make seed_products          # 2025_11_23_10_03_seed_products.sql
```

## Rollback Strategies

### Safe Rollback with Data Preservation

```sql
-- UP
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- DOWN
-- Don't drop column, just mark as deprecated in a comment
-- ALTER TABLE users DROP COLUMN phone;
--
-- Instead, in production, you might want to:
-- 1. Stop using the column in application code
-- 2. Keep the column for data recovery
-- 3. Create a future migration to actually drop it
```

### Point-in-Time Rollback

To rollback multiple migrations:

```bash
# Rollback one at a time
uv run sapi.py migrate:rollback
uv run sapi.py migrate:rollback
uv run sapi.py migrate:rollback
```

Or check migration history and manually run DOWN sections:

```bash
uv run sapi.py query "SELECT name FROM migrations ORDER BY id DESC LIMIT 5"
```

## Full-Text Search Migrations

### Adding Full-Text Search

```sql
-- UP
-- Add tsvector column
ALTER TABLE articles ADD COLUMN search_vector tsvector;

-- Create index
CREATE INDEX idx_articles_search_vector ON articles USING GIN(search_vector);

-- Create trigger to auto-update search vector
CREATE OR REPLACE FUNCTION articles_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_articles_search_vector_update
    BEFORE INSERT OR UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION articles_search_vector_update();

-- Backfill existing rows
UPDATE articles SET search_vector =
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(content, '')), 'B');

-- DOWN
DROP TRIGGER IF EXISTS tr_articles_search_vector_update ON articles;
DROP FUNCTION IF EXISTS articles_search_vector_update();
DROP INDEX IF EXISTS idx_articles_search_vector;
ALTER TABLE articles DROP COLUMN IF EXISTS search_vector;
```

## Performance Considerations

### Creating Indexes Concurrently

For large tables in production, create indexes without locking:

```sql
-- UP
-- Note: Cannot be run in a transaction block
CREATE INDEX CONCURRENTLY idx_large_table_column ON large_table(column_name);

-- DOWN
DROP INDEX CONCURRENTLY IF EXISTS idx_large_table_column;
```

### Partitioned Tables

```sql
-- UP
-- Create parent partitioned table
CREATE TABLE events (
    id SERIAL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE events_2025_q1 PARTITION OF events
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE events_2025_q2 PARTITION OF events
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

-- Create indexes on partitions
CREATE INDEX idx_events_2025_q1_created_at ON events_2025_q1(created_at);
CREATE INDEX idx_events_2025_q2_created_at ON events_2025_q2(created_at);

-- DOWN
DROP TABLE IF EXISTS events CASCADE;
```

## Testing Migrations

### Verify Migration Applied

```bash
# Check if table exists
uv run sapi.py query "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'users')"

# Check column exists
uv run sapi.py query "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'"

# Check index exists
uv run sapi.py query "SELECT indexname FROM pg_indexes WHERE tablename = 'users'"
```

### Test Rollback Before Committing

```bash
# Apply migration
uv run sapi.py migrate

# Test the change works
uv run sapi.py query "SELECT * FROM new_table LIMIT 1"

# Test rollback
uv run sapi.py migrate:rollback

# Verify rollback worked
uv run sapi.py query "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = 'new_table')"

# Re-apply for production
uv run sapi.py migrate
```
