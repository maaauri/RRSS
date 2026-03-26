"""Configuración centralizada del proyecto RRSS."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- Rutas ---
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent
RUTA_DATOS = RAIZ_PROYECTO / "data"
RUTA_DB = Path(os.getenv("DB_PATH", str(RUTA_DATOS / "rrss.db")))

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODELO = os.getenv("OPENAI_MODELO", "gpt-4o")

# --- Meta Graph API (Instagram y Facebook) ---
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_APP_ID = os.getenv("META_APP_ID", "")
META_APP_SECRET = os.getenv("META_APP_SECRET", "")
META_API_VERSION = "v21.0"
META_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"

# --- TikTok API ---
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_BASE_URL = "https://open.tiktokapis.com/v2"

# --- General ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Instaloader (login opcional para evitar 403) ---
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

# Asegurar que exista el directorio de datos
RUTA_DATOS.mkdir(parents=True, exist_ok=True)
