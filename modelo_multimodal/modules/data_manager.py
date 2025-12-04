import json
import os
import config

def guardar_chat_en_disco(video_id, mensajes):
    archivo = os.path.join(config.CARPETA_CHATS, f"chat_{video_id}.json")
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(mensajes, f, ensure_ascii=False, indent=2)

def cargar_chat_de_disco(video_id):
    archivo = os.path.join(config.CARPETA_CHATS, f"chat_{video_id}.json")
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return []