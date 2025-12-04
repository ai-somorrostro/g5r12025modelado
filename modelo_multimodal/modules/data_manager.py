import json
import os
import glob
import config

def guardar_chat(video_id, mensajes):
    archivo = os.path.join(config.CARPETA_CHATS, f"chat_{video_id}.json")
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(mensajes, f, ensure_ascii=False, indent=2)

def cargar_chat(video_id):
    archivo = os.path.join(config.CARPETA_CHATS, f"chat_{video_id}.json")
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_analisis(video_id, datos):
    archivo = os.path.join(config.CARPETA_DB, f"{video_id}.json")
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def cargar_analisis(video_id):
    archivo = os.path.join(config.CARPETA_DB, f"{video_id}.json")
    if os.path.exists(archivo):
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# --- AQUÍ ESTABA EL ERROR DE NOMBRE ---
def listar_archivos_analisis():
    # Devuelve la lista de archivos ordenada por fecha
    archivos = glob.glob(os.path.join(config.CARPETA_DB, "*.json"))
    archivos.sort(key=os.path.getmtime, reverse=True)
    return archivos