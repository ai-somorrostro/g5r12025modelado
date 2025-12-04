import os
import yt_dlp
import re
import subprocess
import cv2
import base64
import streamlit as st # Necesario para tus st.error originales
import config

def extraer_id_youtube(url):
    patron = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(patron, url)
    return match.group(1) if match else "desconocido"

def obtener_ruta_video(video_id):
    return os.path.join(config.CARPETA_VIDEOS, f"{video_id}.mp4")

def descargar_video(url, video_id):
    ruta_destino = obtener_ruta_video(video_id)
    if os.path.exists(ruta_destino) and os.path.getsize(ruta_destino) > 0:
        return True
    if not os.path.exists(config.COOKIES_FILE):
        st.error(f"⚠️ ERROR: Falta '{config.COOKIES_FILE}'.")
        return False
    
    ydl_opts = {
        'format': 'worst[ext=mp4]/mp4',
        'outtmpl': ruta_destino,
        'quiet': True, 'overwrites': True, 'nocheckcertificate': True, 'ignoreerrors': True, 'no_warnings': True,
        'cookiefile': config.COOKIES_FILE,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return os.path.exists(ruta_destino) and os.path.getsize(ruta_destino) > 0
    except Exception as e:
        st.error(f"Error descarga: {e}")
        return False

def encode_video_to_base64(video_path):
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode('utf-8')

def capturar_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
    ret, frame = cap.read()
    cap.release()
    if ret:
        # Usamos una ruta temporal fija en la raíz
        temp_path = os.path.join(config.BASE_DIR, "frame_temp.jpg")
        cv2.imwrite(temp_path, frame)
        with open(temp_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return None

def cortar_video_ffmpeg(video_id, tiempo_inicio, descripcion, duracion=15):
    nombre_clean = re.sub(r'[^\w\s-]', '', descripcion).strip().replace(' ', '_')
    tiempo_clean = tiempo_inicio.replace(':', 'm') + 's'
    nombre_salida = os.path.join(config.CARPETA_RECORTES, f"{video_id}_clip_{tiempo_clean}_{nombre_clean}.mp4")
    
    ruta_origen = obtener_ruta_video(video_id)
    if not os.path.exists(ruta_origen):
        return None 

    comando = ["ffmpeg", "-ss", tiempo_inicio, "-i", ruta_origen, "-t", str(duracion), "-c", "copy", "-y", "-loglevel", "error", nombre_salida]
    try:
        subprocess.run(comando, check=True)
        return nombre_salida
    except Exception as e:
        st.error(f"Error FFmpeg: {e}")
        return None