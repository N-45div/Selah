import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current directory and backend/ directory
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = Path(__file__).resolve().parent.parent

load_dotenv(backend_dir / ".env", override=True)
load_dotenv(root_dir / ".env", override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEYS = os.getenv("GEMINI_API_KEYS", "")  # Comma-separated pool
PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Ensure ADK has access to the valid key
if GEMINI_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

DATA_DIR = root_dir / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATIC_DIR = root_dir / "frontend" / "static"
TEMPLATES_DIR = root_dir / "frontend" / "templates"
