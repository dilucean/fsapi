# Advanced CLI Command Patterns

Detailed patterns for building robust CLI commands in sapi.py.

## Interactive CLI Prompts

### Simple Input

```python
def get_user_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default"""
    if default:
        response = input(f"{prompt} [{default}]: ")
        return response if response else default
    return input(f"{prompt}: ")

async def cmd_create_user():
    """Interactive user creation"""
    email = get_user_input("Email")
    name = get_user_input("Name")
    role = get_user_input("Role", default="user")

    # Validate
    if not email or "@" not in email:
        print("Error: Invalid email")
        sys.exit(1)

    # Create user
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO users (email, name, role) VALUES ($1, $2, $3)",
            email, name, role
        )
        print(f"Created user: {email}")
    finally:
        await conn.close()
```

### Multiple Choice

```python
def choose_option(prompt: str, options: list) -> str:
    """Present multiple choice to user"""
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")

    while True:
        try:
            choice = int(input("Enter choice (number): "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            print(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print("Please enter a valid number")

async def cmd_select_environment():
    """Select environment interactively"""
    env = choose_option(
        "Select environment:",
        ["development", "staging", "production"]
    )

    print(f"Selected: {env}")
    # Proceed with environment-specific operation
```

### Password Input

```python
import getpass

async def cmd_create_admin():
    """Create admin with password"""
    email = input("Admin email: ")

    # Get password securely (won't echo to terminal)
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Error: Passwords don't match")
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)

    # Hash and store password
    # ... password hashing logic ...
```

## Command Chaining

### Sequential Operations

```python
async def cmd_deploy():
    """Deploy with multiple steps"""
    steps = [
        ("Running migrations", cmd_migrate),
        ("Seeding data", cmd_seed_data),
        ("Restarting service", cmd_restart_service),
    ]

    for description, func in steps:
        print(f"\n{description}...")
        try:
            await func()
            print(f"✓ {description} completed")
        except Exception as e:
            print(f"✗ {description} failed: {e}")
            sys.exit(1)

    print("\n✓ Deployment completed successfully")
```

### Conditional Chaining

```python
async def cmd_smart_deploy():
    """Deploy with conditional steps"""
    # Check for pending migrations
    pending = await check_pending_migrations()

    if pending:
        print(f"Found {len(pending)} pending migrations")
        response = input("Run migrations? (y/n): ")

        if response.lower() == 'y':
            await cmd_migrate()
        else:
            print("Skipping migrations")

    # Check for schema changes
    if await has_schema_changes():
        print("Schema changes detected, restarting services...")
        await cmd_restart_services()
    else:
        print("No schema changes, skipping restart")
```

## Background Task Execution

### Async Background Task

```python
import asyncio

async def background_task():
    """Long-running background task"""
    for i in range(10):
        print(f"Background task progress: {i+1}/10")
        await asyncio.sleep(1)
    print("Background task completed")

async def cmd_run_with_background():
    """Run command with background task"""
    # Start background task
    task = asyncio.create_task(background_task())

    # Do main work
    print("Doing main work...")
    await asyncio.sleep(3)
    print("Main work done")

    # Wait for background task
    await task
    print("All tasks completed")
```

### Process-Based Background Task

```python
import subprocess

async def cmd_start_worker():
    """Start worker process in background"""
    worker_script = root() / "workers" / "process_queue.py"

    # Start process in background
    process = subprocess.Popen(
        ["python", str(worker_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True  # Detach from parent
    )

    print(f"Started worker process (PID: {process.pid})")

    # Save PID for later management
    pid_file = root() / "worker.pid"
    pid_file.write_text(str(process.pid))
```

## Configuration File Handling

### JSON Configuration

```python
import json

async def cmd_init_config():
    """Initialize configuration file"""
    config_path = root() / "config.json"

    if config_path.exists():
        response = input("Config file exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted")
            return

    default_config = {
        "database": {
            "host": env("DB_HOST"),
            "port": int(env("DB_PORT")),
            "name": env("DB_NAME")
        },
        "app": {
            "environment": "development",
            "debug": True
        }
    }

    with config_path.open("w") as f:
        json.dump(default_config, f, indent=2)

    print(f"Created config file: {config_path}")

async def cmd_read_config():
    """Read configuration"""
    config_path = root() / "config.json"

    if not config_path.exists():
        print("Config file not found. Run 'init-config' first.")
        sys.exit(1)

    with config_path.open("r") as f:
        config = json.load(f)

    return config
```

### YAML Configuration

```python
import yaml

async def cmd_load_yaml_config():
    """Load YAML configuration"""
    config_path = root() / "config.yaml"

    try:
        with config_path.open("r") as f:
            config = yaml.safe_load(f)

        print(f"Loaded configuration:")
        print(yaml.dump(config, default_flow_style=False))

        return config

    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)
```

## Bulk Operations

### Batch Processing

```python
async def cmd_batch_update():
    """Process records in batches"""
    BATCH_SIZE = 100

    conn = await get_connection()
    try:
        # Get total count
        total = await conn.fetchval("SELECT COUNT(*) FROM users WHERE active = false")
        print(f"Processing {total} inactive users...")

        # Process in batches
        offset = 0
        processed = 0

        while offset < total:
            users = await conn.fetch(
                "SELECT id, email FROM users WHERE active = false "
                "ORDER BY id LIMIT $1 OFFSET $2",
                BATCH_SIZE, offset
            )

            for user in users:
                # Process each user
                await process_user(conn, user)
                processed += 1

                # Progress indicator
                percent = (processed / total) * 100
                print(f"Progress: {processed}/{total} ({percent:.1f}%)", end="\r")

            offset += BATCH_SIZE

        print(f"\n✓ Processed {processed} users")

    finally:
        await conn.close()
```

### Parallel Processing

```python
async def process_item(conn, item):
    """Process single item"""
    await conn.execute(
        "UPDATE items SET processed = true WHERE id = $1",
        item['id']
    )

async def cmd_parallel_process():
    """Process items in parallel"""
    conn = await get_connection()
    try:
        items = await conn.fetch("SELECT id FROM items WHERE processed = false")

        print(f"Processing {len(items)} items in parallel...")

        # Create tasks
        tasks = [process_item(conn, item) for item in items]

        # Run up to 10 at a time
        for i in range(0, len(tasks), 10):
            batch = tasks[i:i+10]
            await asyncio.gather(*batch)
            print(f"Processed batch {i//10 + 1}")

        print(f"✓ All {len(items)} items processed")

    finally:
        await conn.close()
```

## Data Import/Export

### CSV Import

```python
import csv

async def cmd_import_csv(filename: str):
    """Import CSV file to database"""
    file_path = root() / "imports" / filename

    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    conn = await get_connection()
    try:
        with file_path.open("r") as f:
            reader = csv.DictReader(f)

            imported = 0
            for row in reader:
                try:
                    await conn.execute(
                        "INSERT INTO users (email, name) VALUES ($1, $2)",
                        row['email'], row['name']
                    )
                    imported += 1
                except Exception as e:
                    print(f"Error importing row {imported + 1}: {e}")

            print(f"✓ Imported {imported} records")

    finally:
        await conn.close()
```

### JSON Export

```python
import json

async def cmd_export_json(table: str, filename: str):
    """Export table to JSON file"""
    conn = await get_connection()
    try:
        # Get all records
        records = await conn.fetch(f"SELECT * FROM {table}")

        # Convert to list of dicts
        data = [dict(record) for record in records]

        # Write to file
        output_path = root() / "exports" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            json.dump(data, f, indent=2, default=str)  # default=str for dates

        print(f"✓ Exported {len(data)} records to {filename}")

    finally:
        await conn.close()
```

## Database Backup/Restore

### Backup with pg_dump

```python
import subprocess
from datetime import datetime

async def cmd_backup():
    """Create database backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = root() / "backups" / f"backup_{timestamp}.sql"

    # Ensure backup directory exists
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Creating backup...")

    try:
        # Run pg_dump
        result = subprocess.run([
            "pg_dump",
            "-h", env("DB_HOST"),
            "-p", env("DB_PORT"),
            "-U", env("DB_USER"),
            "-d", env("DB_NAME"),
            "-f", str(backup_file)
        ], env={
            **os.environ,
            "PGPASSWORD": env("DB_PASS")
        }, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)

        file_size = backup_file.stat().st_size / 1024 / 1024  # MB
        print(f"✓ Backup created: {backup_file} ({file_size:.2f} MB)")

    except Exception as e:
        print(f"Error creating backup: {e}")
        sys.exit(1)
```

### Restore from Backup

```python
async def cmd_restore(backup_file: str):
    """Restore database from backup"""
    file_path = root() / "backups" / backup_file

    if not file_path.exists():
        print(f"Backup file not found: {file_path}")
        sys.exit(1)

    print("WARNING: This will overwrite the current database!")
    response = input(f"Restore from {backup_file}? Type 'yes' to confirm: ")

    if response.lower() != 'yes':
        print("Aborted")
        return

    print("Restoring database...")

    try:
        result = subprocess.run([
            "psql",
            "-h", env("DB_HOST"),
            "-p", env("DB_PORT"),
            "-U", env("DB_USER"),
            "-d", env("DB_NAME"),
            "-f", str(file_path)
        ], env={
            **os.environ,
            "PGPASSWORD": env("DB_PASS")
        }, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)

        print(f"✓ Database restored from {backup_file}")

    except Exception as e:
        print(f"Error restoring: {e}")
        sys.exit(1)
```

## Health Checks

### Database Health Check

```python
async def cmd_health_check():
    """Check database health"""
    print("Running health checks...")

    try:
        conn = await get_connection()

        # Check connection
        await conn.fetchval("SELECT 1")
        print("✓ Database connection")

        # Check tables exist
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        print(f"✓ Found {len(tables)} tables")

        # Check migrations
        migration_count = await conn.fetchval(
            "SELECT COUNT(*) FROM migrations"
        )
        print(f"✓ {migration_count} migrations applied")

        # Check active connections
        active_conn = await conn.fetchval(
            "SELECT count(*) FROM pg_stat_activity "
            "WHERE datname = $1",
            env("DB_NAME")
        )
        print(f"✓ {active_conn} active connections")

        await conn.close()

        print("\n✓ All health checks passed")

    except Exception as e:
        print(f"\n✗ Health check failed: {e}")
        sys.exit(1)
```

## Command Aliases

### Creating Shortcuts

```python
COMMAND_ALIASES = {
    "m:m": "migrate:make",
    "m:r": "migrate:rollback",
    "m:f": "migrate:fresh",
    "q": "query",
}

async def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    # Resolve alias
    command = COMMAND_ALIASES.get(command, command)

    if command == "migrate:make":
        await cmd_migrate_make(sys.argv[2:])
    # ... rest of commands
```

## Dry Run Mode

### Implementing Dry Run

```python
async def cmd_destructive_operation(dry_run: bool = False):
    """Operation with dry-run support"""
    if dry_run:
        print("[DRY RUN] No changes will be made\n")

    conn = await get_connection()
    try:
        # Simulate deletion
        to_delete = await conn.fetch(
            "SELECT id, email FROM users WHERE inactive = true"
        )

        print(f"Will delete {len(to_delete)} users:")
        for user in to_delete[:5]:  # Show first 5
            print(f"  - {user['email']}")

        if len(to_delete) > 5:
            print(f"  ... and {len(to_delete) - 5} more")

        if not dry_run:
            result = await conn.execute(
                "DELETE FROM users WHERE inactive = true"
            )
            print(f"\n✓ Deleted {len(to_delete)} users")
        else:
            print("\n[DRY RUN] No changes made")

    finally:
        await conn.close()

# Usage
async def main():
    # ...
    if command == "cleanup":
        dry_run = "--dry-run" in sys.argv
        await cmd_destructive_operation(dry_run=dry_run)
```

These patterns provide a foundation for building robust, user-friendly CLI commands in the fsapi framework.
