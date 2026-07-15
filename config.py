import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ===== LLM =====
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.3

# ===== Google Shopping API (RapidAPI) =====
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = "real-time-product-search.p.rapidapi.com"
PRODUCT_SEARCH_URL = "https://real-time-product-search.p.rapidapi.com/search"

# ===== Database =====
DATABASE_URL = "sqlite:///database/fashion.db"

# ===== Defaults =====
DEFAULT_BUDGET = 500_000
DEFAULT_COUNTRY = "id"
MAX_PRODUCTS_PER_SEARCH = 5
