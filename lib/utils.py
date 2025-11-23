import os
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv


def _init_env():
    """Initialize environment by loading .env from project root."""
    root_dir = Path(__file__).parent.parent
    env_file = root_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    return root_dir


# Auto-load .env when module is imported
_root_dir = _init_env()


def root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to project root (parent of lib/ directory)
    """
    return _root_dir


def env(key: str, default=None):
    """
    Get environment variable by key.

    Args:
        key: Environment variable name
        default: Default value if not found (default: None)

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


# Configure logger with timestamp
_logger = logging.getLogger("uvicorn.error")
_handler = logging.StreamHandler()
_formatter = logging.Formatter(
    fmt="%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
_handler.setFormatter(_formatter)

# Only add handler if not already present
if not _logger.handlers:
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)

# Export as lgr for easy import
lgr = _logger


# Cache the template environment
_template_env = None


def tpl() -> Environment:
    """
    Get Jinja2 template environment configured for views/ folder.

    Returns:
        Jinja2 Environment instance
    """
    global _template_env

    if _template_env is None:
        # Get the project root directory (parent of lib/)
        root_dir = Path(__file__).parent.parent
        views_dir = root_dir / "views"

        # Create views directory if it doesn't exist
        views_dir.mkdir(exist_ok=True)

        # Configure Jinja2 environment
        _template_env = Environment(
            loader=FileSystemLoader(str(views_dir)),
            autoescape=True,  # Auto-escape HTML for security
            trim_blocks=True,
            lstrip_blocks=True,
        )

    return _template_env
