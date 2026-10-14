import os

from dotenv import load_dotenv # type: ignore

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
FAQ_DIR = os.path.join(BASE_DIR, "faq")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

WRAPPER_URL = "https://model-wrapper.vernost.ai/aws-bedrock/invoke-llm-stream"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WRAPPER_API_KEY = os.environ.get("WRAPPER_API_KEY", "")
DATABASE_URL = os.environ["DATABASE_URL"]
WRAPPER_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
AGENT_TEMPERATURE = 0.2
AGENT_MAX_TOKENS = 500
MAX_TOOL_STEPS = 4

REDIS_HOST = "localhost"
REDIS_PORT = 6379
SESSION_TTL_SECONDS = 1800
MAX_MEMORY_TURNS = 10

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
FAQ_TOP_K = 3

FASTAPI_PORT = 8010
GENERIC_ERROR = "Sorry, something went wrong. Please try again."