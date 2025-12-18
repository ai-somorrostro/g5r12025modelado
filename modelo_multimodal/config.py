import os
from dotenv import load_dotenv
import ssl
from elasticsearch import Elasticsearch

# --- Cargar variables de entorno ---
load_dotenv()

# --- CLAVES API ---
API_KEY = os.getenv("API_KEY_OPENROUTER")

# --- URLS y modelos ---
URL_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODELO_VISION = "google/gemini-3-pro-preview"
MODELO_CHAT = "google/gemini-3-pro-preview"

# --- RUTAS DE DIRECTORIOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CARPETA_VIDEOS = os.path.join(BASE_DIR, "videos_originales")
CARPETA_RECORTES = os.path.join(BASE_DIR, "recortes_generados")
CARPETA_DB = os.path.join(BASE_DIR, "db_partidos")
CARPETA_CHATS = os.path.join(BASE_DIR, "db_chats")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")

# --- CREAR CARPETAS SI NO EXISTEN ---
def crear_carpetas():
    for folder in [CARPETA_VIDEOS, CARPETA_RECORTES, CARPETA_DB, CARPETA_CHATS]:
        os.makedirs(folder, exist_ok=True)

crear_carpetas()

# --- CONFIGURACIÓN ELASTICSEARCH ---
ELASTIC_HOSTS = ["https://localhost:9200"]  # Cambia a http si no usas SSL

# Contexto SSL para desarrollo (ignora certificados auto-firmados)
contexto_ssl = ssl.create_default_context()
contexto_ssl.check_hostname = False
contexto_ssl.verify_mode = ssl.CERT_NONE

es_client = Elasticsearch(
    ELASTIC_HOSTS,
    basic_auth=("elastic", "svXSauT7aDbvRQuM4YJ"),  # Usuario/contraseña de tu ES
    ssl_context=contexto_ssl,
    verify_certs=False,
    ssl_show_warn=False
)

# --- NOMBRE DEL ÍNDICE ---
INDEX_NAME = "video_clips_vector"
