import requests
import json
import re
import streamlit as st # Necesario para st.session_state y st.error
import config
from modules import video_manager # Necesitamos funciones de video aquí

def actualizar_tokens(usage):
    """Suma los tokens al contador global"""
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
        
        # Guardar tokens
        if 'usage' in resp_json:
            actualizar_tokens(resp_json['usage'])
            
        return resp_json['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

def analizar_video_con_ia(video_id, url_origen):
    ruta_json = os.path.join(config.CARPETA_DB, f"{video_id}.json")
    ruta_video = video_manager.obtener_ruta_video(video_id)
    
    if os.path.exists(ruta_json):
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            if "url_origen" not in datos:
                datos["url_origen"] = url_origen
                with open(ruta_json, "w", encoding="utf-8") as f2:
                    json.dump(datos, f2, ensure_ascii=False, indent=2)
            return datos

    try:
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

        # Guardar tokens de la visión (esto consume mucho)
        if 'usage' in response_json:
            actualizar_tokens(response_json['usage'])

        if 'error' in response_json:
            st.error(f"❌ Error de la API: {response_json['error']}")
            return None

        content = response_json['choices'][0]['message']['content']
        clean = re.sub(r'```json\s*|\s*```', '', content).strip()
        match_json = re.search(r'(\{.*\})', clean, re.DOTALL)
        if match_json: clean = match_json.group(1)
        
        try:
            datos = json.loads(clean)
            datos["url_origen"] = url_origen 
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            return datos
        except json.JSONDecodeError:
            st.error("Error al leer el JSON de la IA.")
            return None

    except Exception as e:
        st.error(f"Error conexión: {e}")
        return None