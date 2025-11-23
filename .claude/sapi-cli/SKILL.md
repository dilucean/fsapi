---
name: sapi-cli
description: Build and extend the sapi.py CLI tool for the fsapi framework. Use when adding new commands, implementing command handlers, parsing arguments, managing async execution, handling database connections, or implementing error handling patterns for CLI operations.
---

# SAPI CLI Development

Patterns and best practices for extending the sapi.py CLI tool in the fsapi framework.

## CLI Architecture

The sapi.py CLI tool follows a simple command-based architecture:

```python
#!/usr/bin/env python3
import asyncio
import sys
from lib.utils import env
from lib.pg import connect

async def cmd_example():
    """Command handler function"""
    # Command implementation
    pass

async def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "example":
        await cmd_example()
    # ... other commands

if __name__ == "__main__":
    asyncio.run(main())
```

## Adding New Commands

### Basic Command Structure

```python
async def cmd_your_command(arg1: str, arg2: str = ""):
    """
    Brief description of what this command does

    Args:
        arg1: Description of first argument
        arg2: Description of optional second argument
    """
    # Validate arguments
    if not arg1:
        print("Error: arg1 is required")
        print("Usage: uv run sapi.py your-command <arg1> [arg2]")
        sys.exit(1)

    # Implementation
    print(f"Executing command with {arg1}")
```

### Registering Commands

Add to the `main()` function:

```python
async def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    # ... existing commands ...

    elif command == "your-command":
        arg1 = sys.argv[2] if len(sys.argv) > 2 else ""
        arg2 = sys.argv[3] if len(sys.argv) > 3 else ""
        await cmd_your_command(arg1, arg2)

    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)
```

### Updating Help Text

```python
def print_usage():
    """Print usage information"""
    print("""
fsapi CLI

Usage:
  uv run sapi.py migrate:make <name>  - Create new migration file
  uv run sapi.py migrate              - Run pending migrations
  uv run sapi.py query '<sql>'        - Execute SQL query
  uv run sapi.py your-command <arg>   - Your command description
""")
```

## Database Connection Patterns

### Direct Connection

For CLI commands, use direct connections instead of the pool:

```python
async def cmd_database_operation():
    """Command that needs database access"""
    conn = await connect(
        host=env("DB_HOST"),
        port=int(env("DB_PORT")),
        user=env("DB_USER"),
        password=env("DB_PASS"),
        database=env("DB_NAME"),
    )
    try:
        # Use connection
        result = await conn.fetch("SELECT * FROM users")

        # Process result
        for row in result:
            print(row['email'])

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await conn.close()
```

### Reusable Connection Helper

Create a helper function for consistent connection handling:

```python
async def get_connection():
    """Get database connection with environment config"""
    return await connect(
        host=env("DB_HOST"),
        port=int(env("DB_PORT")),
        user=env("DB_USER"),
        password=env("DB_PASS"),
        database=env("DB_NAME"),
    )

async def cmd_example():
    """Example using helper"""
    conn = await get_connection()
    try:
        # Use connection
        pass
    finally:
        await conn.close()
```

## Argument Parsing

### Simple Arguments

```python
async def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if command == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        type_ = sys.argv[3] if len(sys.argv) > 3 else "default"
        await cmd_create(name, type_)
```

### Named Arguments (Flags)

```python
def parse_flags(args):
    """Parse --flag=value style arguments"""
    flags = {}
    positional = []

    for arg in args:
        if arg.startswith("--"):
            if "=" in arg:
                key, value = arg[2:].split("=", 1)
                flags[key] = value
            else:
                flags[arg[2:]] = True
        else:
            positional.append(arg)

    return positional, flags

async def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]
    positional, flags = parse_flags(args)

    if command == "deploy":
        await cmd_deploy(positional, flags)
```

### Using argparse (Advanced)

```python
import argparse

def create_parser():
    """Create argument parser for CLI"""
    parser = argparse.ArgumentParser(
        description="fsapi CLI tool",
        prog="sapi.py"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # migrate:make command
    migrate_make = subparsers.add_parser("migrate:make", help="Create migration")
    migrate_make.add_argument("name", help="Migration name")

    # query command
    query_cmd = subparsers.add_parser("query", help="Execute SQL query")
    query_cmd.add_argument("sql", help="SQL query to execute")

    return parser

async def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "migrate:make":
        await cmd_migrate_make(args.name)
    elif args.command == "query":
        await cmd_query(args.sql)
```

## Error Handling

### Basic Error Handling

```python
async def cmd_risky_operation():
    """Command with error handling"""
    try:
        # Operation that might fail
        result = await perform_operation()
        print(f"Success: {result}")

    except asyncpg.PostgresError as e:
        print(f"Database error: {e}")
        sys.exit(1)

    except ValueError as e:
        print(f"Invalid input: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
```

### Graceful Cleanup

```python
async def cmd_with_cleanup():
    """Command with proper resource cleanup"""
    conn = None
    temp_file = None

    try:
        conn = await get_connection()
        temp_file = open("/tmp/data.txt", "w")

        # Do work
        result = await conn.fetch("SELECT * FROM users")
        temp_file.write(str(result))

        print("Operation completed successfully")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    finally:
        # Cleanup resources
        if conn:
            await conn.close()
        if temp_file:
            temp_file.close()
            os.remove("/tmp/data.txt")
```

## User Confirmation

### Simple Confirmation

```python
async def cmd_dangerous_operation():
    """Command requiring confirmation"""
    print("WARNING: This will delete all data!")
    response = input("Are you sure? Type 'yes' to continue: ")

    if response.lower() != 'yes':
        print("Aborted")
        return

    # Proceed with operation
    print("Executing dangerous operation...")
```

### Detailed Confirmation

```python
async def cmd_migrate_fresh():
    """Drop all tables and rerun migrations"""
    print("WARNING: This will drop all tables in the database!")
    print(f"Database: {env('DB_NAME')}")
    print(f"Host: {env('DB_HOST')}")
    print()

    response = input("Type the database name to confirm: ")

    if response != env('DB_NAME'):
        print("Database name doesn't match. Aborted.")
        return

    # Proceed
    print("Proceeding with fresh migration...")
```

## Output Formatting

### Table Output

```python
def print_table(rows, columns):
    """Print rows as formatted table"""
    if not rows:
        print("No rows returned")
        return

    # Print header
    header = " | ".join(columns)
    separator = "-" * len(header)

    print(header)
    print(separator)

    # Print rows
    for row in rows:
        values = [str(row[col]) for col in columns]
        print(" | ".join(values))

    print(f"\n{len(rows)} row(s) returned")
```

### Progress Indicators

```python
async def cmd_batch_operation():
    """Command with progress indicator"""
    items = await get_items()
    total = len(items)

    print(f"Processing {total} items...")

    for i, item in enumerate(items, 1):
        await process_item(item)

        # Print progress
        percent = (i / total) * 100
        print(f"  Progress: {i}/{total} ({percent:.1f}%)", end="\r")

    print("\nCompleted!")
```

### Color Output (Optional)

```python
class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")
```

## Performance Timing

### Basic Timing

```python
from datetime import datetime

async def cmd_timed_operation():
    """Command with execution timing"""
    start_time = datetime.now()

    # Perform operation
    result = await long_running_operation()

    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    print(f"Completed in {duration_ms}ms")
```

### Multiple Operations

```python
async def cmd_multi_step():
    """Command with step timing"""
    total_start = datetime.now()

    # Step 1
    step_start = datetime.now()
    await step_one()
    step1_ms = int((datetime.now() - step_start).total_seconds() * 1000)
    print(f"  Step 1: {step1_ms}ms")

    # Step 2
    step_start = datetime.now()
    await step_two()
    step2_ms = int((datetime.now() - step_start).total_seconds() * 1000)
    print(f"  Step 2: {step2_ms}ms")

    total_ms = int((datetime.now() - total_start).total_seconds() * 1000)
    print(f"\nTotal: {total_ms}ms")
```

## File Operations

### Reading Files

```python
from pathlib import Path
from lib.utils import root

async def cmd_import_data(filename: str):
    """Import data from file"""
    file_path = root() / "data" / filename

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    try:
        content = file_path.read_text()
        # Process content
        lines = content.strip().split("\n")
        print(f"Read {len(lines)} lines from {filename}")

    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
```

### Writing Files

```python
async def cmd_export_data(filename: str):
    """Export data to file"""
    file_path = root() / "exports" / filename

    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Get data
        conn = await get_connection()
        data = await conn.fetch("SELECT * FROM users")
        await conn.close()

        # Write to file
        with file_path.open("w") as f:
            for row in data:
                f.write(f"{row['email']},{row['name']}\n")

        print(f"Exported {len(data)} records to {filename}")

    except Exception as e:
        print(f"Error exporting data: {e}")
        sys.exit(1)
```

## Command Categories

### Grouping Related Commands

```python
# Migration commands
async def cmd_migrate(): pass
async def cmd_migrate_make(): pass
async def cmd_migrate_rollback(): pass
async def cmd_migrate_fresh(): pass

# Query commands
async def cmd_query(): pass
async def cmd_query_explain(): pass

# Data commands
async def cmd_import(): pass
async def cmd_export(): pass
async def cmd_backup(): pass

# Admin commands
async def cmd_users_list(): pass
async def cmd_users_create(): pass
async def cmd_users_delete(): pass
```

### Namespaced Commands

```python
async def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    # Handle namespace:action pattern
    if ":" in command:
        namespace, action = command.split(":", 1)

        if namespace == "migrate":
            if action == "make":
                await cmd_migrate_make(sys.argv[2:])
            elif action == "rollback":
                await cmd_migrate_rollback()
            # ... other migrate commands

        elif namespace == "users":
            if action == "list":
                await cmd_users_list()
            elif action == "create":
                await cmd_users_create(sys.argv[2:])
            # ... other user commands
```

## Advanced Patterns

See reference file for:
- Interactive CLI prompts
- Command chaining and pipelines
- Background task execution
- Configuration file handling
- Plugin system architecture
