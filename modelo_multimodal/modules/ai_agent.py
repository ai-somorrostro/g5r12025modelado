import requests
import json
import re
import os
import streamlit as st
import config
from modules import video_manager, data_manager

def actualizar_tokens(usage):
    """Suma los tokens al contador global en la sesión"""
    if usage and 'tokens_total' in st.session_state:
        st.session_state.tokens_total["input"] += usage.get("prompt_tokens", 0)
        st.session_state.tokens_total["output"] += usage.get("completion_tokens", 0)
        st.session_state.tokens_total["total"] += usage.get("total_tokens", 0)

def analizar_tactica(video_path):
    base64_img = video_manager.capturar_frame(video_path)
    if not base64_img: return "Error al capturar imagen."
    
    prompt = "Analiza tácticamente esta imagen. Posicionamiento, faltas, contexto. Sé breve."
    
    try:
        payload = {
            "model": config.MODELO_VISION,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}]}]
        }
        resp = requests.post(config.URL_ENDPOINT, headers={"Authorization": f"Bearer {config.API_KEY}"}, json=payload)
        resp_json = resp.json()
        
        if 'usage' in resp_json:
            actualizar_tokens(resp_json['usage'])
            
        return resp_json['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

def analizar_video_con_ia(video_id, url_origen):
    # 1. Intentar cargar de disco
    datos = data_manager.cargar_analisis(video_id)
    if datos:
        if "url_origen" not in datos:
            datos["url_origen"] = url_origen
            data_manager.guardar_analisis(video_id, datos)
        return datos

    # 2. Si no existe, llamar a la API
    try:
        ruta_video = video_manager.obtener_ruta_video(video_id)
        # Comprobar que el video existe
        if not os.path.exists(ruta_video):
            return None

        base64_video = video_manager.encode_video_to_base64(ruta_video)
        data_url = f"data:video/mp4;base64,{base64_video}"
        
        prompt_text = """
        Analiza este video de fútbol. Identifica eventos clave.
        Responde SOLO JSON:
        { "partido": "Equipo A vs Equipo B", "eventos": [ { "tiempo_video": "MM:SS", "tiempo_partido": "MM:SS", "descripcion": "string" } ] }
        """
        
        payload = {
            "model": config.MODELO_VISION,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt_text}, {"type": "video_url", "video_url": {"url": data_url}}]}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"} 
        }

        response = requests.post(config.URL_ENDPOINT, headers={"Authorization": f"Bearer {config.API_KEY}"}, json=payload)
        response_json = response.json()
        
        if 'usage' in response_json:
            actualizar_tokens(response_json['usage'])

        if 'error' in response_json:
            print(f"Error API: {response_json['error']}")
            return None

        content = response_json['choices'][0]['message']['content']
        clean = re.sub(r'```json\s*|\s*```', '', content).strip()
        match_json = re.search(r'(\{.*\})', clean, re.DOTALL)
        if match_json: clean = match_json.group(1)
        
        datos = json.loads(clean)
        datos["url_origen"] = url_origen 
        
        data_manager.guardar_analisis(video_id, datos)
        return datos

    except Exception as e:
        print(f"Error IA: {e}")
        return None

# --- ESTA ES LA FUNCIÓN QUE FALTABA ---
def obtener_respuesta_chat(mensajes_historial):
    """Envía el historial al chat y devuelve la respuesta cruda"""
    try:
        resp = requests.post(config.URL_ENDPOINT, headers={"Authorization": f"Bearer {config.API_KEY}"}, 
                             json={"model": config.MODELO_CHAT, "messages": mensajes_historial})
        resp_json = resp.json()
        
        if 'usage' in resp_json:
            actualizar_tokens(resp_json['usage'])
            
        return resp_json['choices'][0]['message']['content']
    except Exception as e:
        return f"Error API: {e}"