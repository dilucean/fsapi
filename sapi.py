#!/usr/bin/env python3
"""
sapi.py - CLI tool for fsapi framework database migrations
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
import asyncpg

from lib.utils import env, root
from lib.pg import connect


MIGRATIONS_DIR = root() / "migrations"
MIGRATION_TABLE = "migrations"


async def ensure_migrations_table(conn: asyncpg.Connection):
    """Create migrations tracking table if it doesn't exist"""
    await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP NOT NULL DEFAULT NOW(),
            duration_ms INTEGER NOT NULL
        )
    """)


def get_migration_files() -> list[Path]:
    """Get all migration files sorted by name (chronological order)"""
    if not MIGRATIONS_DIR.exists():
        MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return files


async def get_applied_migrations(conn: asyncpg.Connection) -> set[str]:
    """Get set of already applied migration names"""
    await ensure_migrations_table(conn)
    rows = await conn.fetch(f"SELECT name FROM {MIGRATION_TABLE} ORDER BY id")
    return {row["name"] for row in rows}


def parse_migration_file(file_path: Path) -> tuple[str, str]:
    """Parse migration file into UP and DOWN sections"""
    content = file_path.read_text()

    # Split on -- DOWN marker
    if "-- DOWN" in content:
        parts = content.split("-- DOWN", 1)
        up_sql = parts[0].replace("-- UP", "").strip()
        down_sql = parts[1].strip()
    else:
        # No DOWN section
        up_sql = content.replace("-- UP", "").strip()
        down_sql = ""

    return up_sql, down_sql


async def cmd_migrate_make(name: str):
    """Create a new migration file"""
    if not name:
        print("Error: Migration name is required")
        print("Usage: uv run sapi.py migrate:make <name>")
        sys.exit(1)

    # Generate timestamp: YYYY_MM_DD_HH_mm
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    filename = f"{timestamp}_{name}.sql"
    filepath = MIGRATIONS_DIR / filename

    # Ensure migrations directory exists
    MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Create template
    template = """-- UP
-- Write your UP migration here


-- DOWN
-- Write your DOWN migration here (for rollback)

"""

    filepath.write_text(template)
    print(f"Created migration: {filename}")


async def cmd_migrate():
    """Run all pending migrations"""
    conn = await connect(
        host=env("DB_HOST"),
        port=int(env("DB_PORT")),
        user=env("DB_USER"),
        password=env("DB_PASS"),
        database=env("DB_NAME"),
    )
    try:
        await ensure_migrations_table(conn)

        # Get all migrations and check which are applied
        all_files = get_migration_files()
        applied = await get_applied_migrations(conn)

        pending = [f for f in all_files if f.name not in applied]

        if not pending:
            print("No pending migrations")
            return

        print(f"Running {len(pending)} migration(s)...")

        for file_path in pending:
            start_time = datetime.now()
            up_sql, _ = parse_migration_file(file_path)

            if not up_sql:
                print(f"  Skipping {file_path.name} (empty UP section)")
                continue

            print(f"  Migrating: {file_path.name}")

            try:
                # Execute UP migration
                await conn.execute(up_sql)

                # Record migration
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                await conn.execute(
                    f"INSERT INTO {MIGRATION_TABLE} (name, duration_ms) VALUES ($1, $2)",
                    file_path.name,
                    duration_ms,
                )

                print(f"     Completed in {duration_ms}ms")
            except Exception as e:
                print(f"     Failed: {e}")
                raise

        print("All migrations completed successfully")
    finally:
        await conn.close()


async def cmd_migrate_pending():
    """Show pending migrations"""
    conn = await connect(
        host=env("DB_HOST"),
        port=int(env("DB_PORT")),
        user=env("DB_USER"),
        password=env("DB_PASS"),
        database=env("DB_NAME"),
    )
    try:
        await ensure_migrations_table(conn)

        all_files = get_migration_files()
        applied = await get_applied_migrations(conn)

        pending = [f for f in all_files if f.name not in applied]

        if not pending:
            print("No pending migrations")
        else:
            print(f"Pending migrations ({len(pending)}):")
            for file_path in pending:
                print(f"  - {file_path.name}")
    finally:
        await conn.close()


async def cmd_migrate_rollback():
    """Rollback the last applied migration"""
    conn = await connect(
        host=env("DB_HOST"),
        port=int(env("DB_PORT")),
        user=env("DB_USER"),
        password=env("DB_PASS"),
        database=env("DB_NAME"),
    )
    try:
        await ensure_migrations_table(conn)

        # Get last applied migration
        row = await conn.fetchrow(
            f"SELECT name FROM {MIGRATION_TABLE} ORDER BY id DESC LIMIT 1"
        )

        if not row:
            print("No migrations to rollback")
            return

        migration_name = row["name"]
        file_path = MIGRATIONS_DIR / migration_name

        if not file_path.exists():
            print(f"Error: Migration file not found: {migration_name}")
            sys.exit(1)

        _, down_sql = parse_migration_file(file_path)

        if not down_sql:
            print(f"Error: No DOWN section in {migration_name}")
            sys.exit(1)

        print(f"Rolling back: {migration_name}")

        try:
            # Execute DOWN migration
            await conn.execute(down_sql)

            # Remove from tracking table
            await conn.execute(
                f"DELETE FROM {MIGRATION_TABLE} WHERE name = $1", migration_name
            )

            print("   Rolled back successfully")
        except Exception as e:
            print(f"   Rollback failed: {e}")
            raise
    finally:
        await conn.close()


async def cmd_migrate_fresh():
    """Drop all tables and rerun all migrations"""
    conn = await connect(
        host=env("DB_HOST"),
        port=int(env("DB_PORT")),
        user=env("DB_USER"),
        password=env("DB_PASS"),
        database=env("DB_NAME"),
    )
    try:
        print("WARNING: This will drop all tables in the database!")
        print("Database:", env("DB_NAME"))

        # Confirm action
        response = input("Are you sure? Type 'yes' to continue: ")
        if response.lower() != "yes":
            print("Aborted")
            return

        print("\nDropping all tables...")

        # Drop all tables in public schema
        await conn.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)

        print("All tables dropped")

        # Recreate migrations table and run all migrations
        await ensure_migrations_table(conn)
        await conn.close()

        # Run all migrations
        await cmd_migrate()
    except Exception as e:
        print(f"Error: {e}")
        await conn.close()
        raise


async def cmd_query(sql: str):
    """Execute a SQL query and display results"""
    if not sql:
        print("Error: SQL query is required")
        print("Usage: uv run sapi.py query '<sql>'")
        sys.exit(1)

    conn = await connect(
        host=env("DB_HOST"),
        port=int(env("DB_PORT")),
        user=env("DB_USER"),
        password=env("DB_PASS"),
        database=env("DB_NAME"),
    )
    try:
        # Determine if this is a SELECT query or modification query
        sql_upper = sql.strip().upper()
        is_select = sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")

        start_time = datetime.now()

        if is_select:
            # Fetch results for SELECT queries
            rows = await conn.fetch(sql)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if not rows:
                print("No rows returned")
                print(f"Query executed in {duration_ms}ms")
            else:
                # Print column headers
                columns = list(rows[0].keys())
                header = " | ".join(columns)
                separator = "-" * len(header)

                print(header)
                print(separator)

                # Print rows
                for row in rows:
                    values = [str(row[col]) for col in columns]
                    print(" | ".join(values))

                print(f"\n{len(rows)} row(s) returned in {duration_ms}ms")
        else:
            # Execute modification queries (INSERT, UPDATE, DELETE, etc.)
            result = await conn.execute(sql)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            print(f"Query executed: {result}")
            print(f"Completed in {duration_ms}ms")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await conn.close()


def print_usage():
    """Print usage information"""
    print("""
fsapi CLI

Usage:
  uv run sapi.py migrate:make <name>  - Create new migration file
  uv run sapi.py migrate              - Run pending migrations
  uv run sapi.py migrate:pending      - Show pending migrations
  uv run sapi.py migrate:rollback     - Rollback last migration
  uv run sapi.py migrate:fresh        - Drop all tables and rerun migrations
  uv run sapi.py query '<sql>'        - Execute SQL query and display results
""")


async def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "migrate:make":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        await cmd_migrate_make(name)
    elif command == "migrate":
        await cmd_migrate()
    elif command == "migrate:pending":
        await cmd_migrate_pending()
    elif command == "migrate:rollback":
        await cmd_migrate_rollback()
    elif command == "migrate:fresh":
        await cmd_migrate_fresh()
    elif command == "query":
        sql = sys.argv[2] if len(sys.argv) > 2 else ""
        await cmd_query(sql)
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
