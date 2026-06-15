import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

class Settings:
    # Root directory of the backend folder
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Path where cloned repositories will be stored
    CLONED_REPOS_DIR = os.path.join(BASE_DIR, "cloned_repos")

# Instantiate settings
settings = Settings()

# 1. Load environment variables using python-dotenv
# config.py is at: backend/app/core/config.py (parents[2] is backend/)
BASE_DIR = Path(__file__).resolve().parents[2]
if not (BASE_DIR / ".env").exists():
    # Fallback to parents[1] if layout changes
    BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. Safe startup print
print("Gemini API key loaded:", "Yes" if GEMINI_API_KEY else "No")

# 3. Ensure google-generativeai is configured
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
