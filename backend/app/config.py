import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current directory and backend/ directory
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = Path(__file__).resolve().parent.parent

load_dotenv(backend_dir / ".env")
load_dotenv(root_dir / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Ensure ADK has access to GOOGLE_API_KEY
if GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY

DATA_DIR = root_dir / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATIC_DIR = root_dir / "frontend" / "static"
TEMPLATES_DIR = root_dir / "frontend" / "templates"
