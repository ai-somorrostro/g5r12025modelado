import os
import re
import yt_dlp
import subprocess
import cv2
import base64
import streamlit as st
import config

# Asegúrate que la carpeta existe
if not os.path.exists(config.CARPETA_VIDEOS):
    os.makedirs(config.CARPETA_VIDEOS)

def extraer_id_youtube(url):
    """Extrae el ID de un vídeo de YouTube"""
    patron = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(patron, url)
    return match.group(1) if match else "desconocido"

def obtener_ruta_video(video_id):
    """Devuelve la ruta esperada del video"""
    return os.path.join(config.CARPETA_VIDEOS, f"{video_id}.mp4")

def descargar_video(url, video_id):
    """
    Descarga usando la estrategia 'bestvideo+bestaudio' y fusiona a MP4.
    Usa cliente Android para evitar bloqueo SABR.
    """
    ruta_destino = obtener_ruta_video(video_id)
    
    # 1. Chequeo rápido si ya existe
    if os.path.exists(ruta_destino) and os.path.getsize(ruta_destino) > 0:
        return ruta_destino

    print(f"📱 Iniciando descarga INTELIGENTE para: {video_id}")

    # 2. Configuración flexible
    ydl_opts = {
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]', # Limitamos a 720p para no saturar
        'outtmpl': os.path.join(config.CARPETA_VIDEOS, f"{video_id}.%(ext)s"),
        'merge_output_format': 'mp4',
        
        # Estrategia anti-bloqueo
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        },

        'nocheckcertificate': True,
        'ignoreerrors': True,
        'quiet': False,
        'no_warnings': False,
        
        # 'cookiefile': config.COOKIES_FILE, # Descomenta si tienes cookies.txt actualizado
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # 3. Verificación post-descarga
        if os.path.exists(ruta_destino):
            return ruta_destino
        
        # Búsqueda de emergencia (por si quedó con otro nombre/extensión)
        archivos = os.listdir(config.CARPETA_VIDEOS)
        for archivo in archivos:
            if archivo.startswith(video_id):
                return os.path.join(config.CARPETA_VIDEOS, archivo)

        return None

    except Exception as e:
        st.error(f"Error en descarga: {e}")
        return None

def encode_video_to_base64(video_path):
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode('utf-8')

def capturar_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
    ret, frame = cap.read()
    cap.release()
    if ret:
        temp_path = os.path.join(config.BASE_DIR, "frame_temp.jpg")
        cv2.imwrite(temp_path, frame)
        with open(temp_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return None

def cortar_video_ffmpeg(video_id, tiempo_inicio, descripcion, duracion=15):
    nombre_clean = re.sub(r'[^\w\s-]', '', descripcion).strip().replace(' ', '_')
    tiempo_clean = tiempo_inicio.replace(':', 'm') + 's'
    nombre_salida = os.path.join(config.CARPETA_RECORTES, f"{video_id}_clip_{tiempo_clean}_{nombre_clean}.mp4")
    
    # Buscamos el video fuente de forma inteligente
    ruta_origen = obtener_ruta_video(video_id)
    if not os.path.exists(ruta_origen):
         # Si no está el .mp4 exacto, buscamos cualquier archivo que empiece por el ID
         for f in os.listdir(config.CARPETA_VIDEOS):
            if f.startswith(video_id):
                ruta_origen = os.path.join(config.CARPETA_VIDEOS, f)
                break
    
    if not os.path.exists(ruta_origen):
        return None 

    # Cortamos
    comando = ["ffmpeg", "-ss", tiempo_inicio, "-i", ruta_origen, "-t", str(duracion), "-c", "copy", "-y", "-loglevel", "error", nombre_salida]
    try:
        subprocess.run(comando, check=True)
        return nombre_salida
    except Exception:
        # Fallback: Si 'copy' falla, recodificamos rápido (útil si el origen es mkv y salida mp4)
        comando = ["ffmpeg", "-ss", tiempo_inicio, "-i", ruta_origen, "-t", str(duracion), "-c:v", "libx264", "-c:a", "aac", "-y", "-loglevel", "error", nombre_salida]
        try:
            subprocess.run(comando, check=True)
            return nombre_salida
        except Exception as e:
            st.error(f"Error cortando video: {e}")
            return None

def optimizar_video_para_ia(ruta_original):
    if not os.path.exists(ruta_original):
        return None
        
    nombre_base = os.path.splitext(ruta_original)[0]
    ruta_optimizada = f"{nombre_base}_ia_low.mp4"
    
    if os.path.exists(ruta_optimizada) and os.path.getsize(ruta_optimizada) > 0:
        return ruta_optimizada

    comando = [
        "ffmpeg", "-i", ruta_original,
        "-vf", "fps=1,scale=-2:360",
        "-c:v", "libx264", "-crf", "32", "-preset", "ultrafast",
        "-an",
        "-y", "-loglevel", "error",
        ruta_optimizada
    ]
    try:
        subprocess.run(comando, check=True)
        return ruta_optimizada
    except Exception:
        return ruta_original
