import os
from dotenv import load_dotenv

# Cargar variables
load_dotenv()

# --- CLAVES ---
API_KEY = os.getenv("API_KEY_OPENROUTER")

# --- URLS Y MODELOS ---
URL_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODELO_VISION = "google/gemini-3-pro-preview"
MODELO_CHAT = "google/gemini-3-pro-preview"

# --- RUTAS DE DIRECTORIOS ---
# Usamos rutas absolutas para evitar problemas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARPETA_VIDEOS = os.path.join(BASE_DIR, "videos_originales")
CARPETA_RECORTES = os.path.join(BASE_DIR, "recortes_generados")
CARPETA_DB = os.path.join(BASE_DIR, "db_partidos")
CARPETA_CHATS = os.path.join(BASE_DIR, "db_chats")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")

# --- INICIALIZACIÓN ---
def crear_carpetas():
    for folder in [CARPETA_VIDEOS, CARPETA_RECORTES, CARPETA_DB, CARPETA_CHATS]:
        os.makedirs(folder, exist_ok=True)

# Ejecutar al importar
crear_carpetas()