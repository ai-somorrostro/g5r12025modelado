import streamlit as st
import requests
import json
import os
import re
import glob
import time
# IMPORTAMOS NUESTROS MÓDULOS
import config
from modules import video_manager, data_manager, ai_agent

# ==========================================
#               CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="IA Video Analyst Pro", page_icon="⚽", layout="wide")

if not config.API_KEY:
    st.error("❌ No se encontró la API KEY. Revisa tu archivo .env")
    st.stop()

# Inicializar contador de tokens en sesión si no existe
if 'tokens_total' not in st.session_state:
    st.session_state.tokens_total = {"input": 0, "output": 0, "total": 0}

# ==========================================
#           INTERFAZ GRÁFICA
# ==========================================

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🗄️ Mis Partidos")
    
    # SECCIÓN DE MÉTRICAS
    with st.expander("📊 Métricas de Consumo", expanded=True):
        col1, col2 = st.columns(2)
        col1.metric("Input", f"{st.session_state.tokens_total['input']}", delta_color="off")
        col2.metric("Output", f"{st.session_state.tokens_total['output']}", delta_color="off")
        st.metric("Total Tokens", f"{st.session_state.tokens_total['total']}")
        
        if st.button("🔄 Resetear Contador"):
            st.session_state.tokens_total = {"input": 0, "output": 0, "total": 0}
            st.rerun()

    st.divider()

    with st.expander("🆕 Añadir Nuevo Partido", expanded=False):
        url_input = st.text_input("URL de YouTube")
        if st.button("🚀 Analizar", type="primary"):
            if url_input:
                vid_id = video_manager.extraer_id_youtube(url_input)
                with st.status("Analizando partido...", expanded=True) as status:
                    if video_manager.descargar_video(url_input, vid_id):
                        status.write("✅ Video descargado.")
                        datos = ai_agent.analizar_video_con_ia(vid_id, url_input)
                        if datos:
                            status.update(label="¡Listo!", state="complete")
                            st.session_state['datos_partido'] = datos
                            st.session_state['video_id'] = vid_id
                            st.session_state['mensajes'] = [] 
                            st.rerun()
            else:
                st.warning("Pega una URL.")

    st.markdown("### 💬 Conversaciones")
    archivos_historial = glob.glob(os.path.join(config.CARPETA_DB, "*.json"))
    archivos_historial.sort(key=os.path.getmtime, reverse=True)

    for ruta in archivos_historial:
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                datos_archivo = json.load(f)
            vid_id_guardado = os.path.basename(ruta).replace(".json", "")
            titulo_partido = datos_archivo.get('partido', 'Partido Desconocido')
            if st.button(f"⚽ {titulo_partido}", key=vid_id_guardado, use_container_width=True):
                st.session_state['datos_partido'] = datos_archivo
                st.session_state['video_id'] = vid_id_guardado
                st.session_state['mensajes'] = data_manager.cargar_chat_de_disco(vid_id_guardado)
                ruta_mp4 = video_manager.obtener_ruta_video(vid_id_guardado)
                if not os.path.exists(ruta_mp4):
                    url_guardada = datos_archivo.get("url_origen")
                    if url_guardada:
                        with st.spinner(f"📥 Descargando video original..."):
                            video_manager.descargar_video(url_guardada, vid_id_guardado)
                st.rerun()
        except Exception as e:
            st.error(f"Error leyendo archivo: {e}")

    st.divider()
    if st.button("🗑️ Borrar Videos (Liberar Espacio)", type="secondary", key="btn_limpieza", use_container_width=True):
        files_v = glob.glob(os.path.join(config.CARPETA_VIDEOS, "*.mp4"))
        files_c = glob.glob(os.path.join(config.CARPETA_RECORTES, "*.mp4"))
        for f in files_v + files_c:
            try: os.remove(f)
            except: pass
        st.success(f"Espacio liberado.")
        time.sleep(1.5)
        st.rerun()

# --- PANTALLA PRINCIPAL ---
st.title("⚽ IA Video Analyst Pro")

if 'datos_partido' in st.session_state:
    datos = st.session_state['datos_partido']
    vid_id_actual = st.session_state.get('video_id', 'unknown')
    
    st.header(f"🏟️ {datos.get('partido', 'Partido')}")
    st.caption(f"ID Video: {vid_id_actual}")
    
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    for idx, msg in enumerate(st.session_state.mensajes):
        with st.chat_message(msg["role"]):
            if "video_path" not in msg:
                st.write(msg["content"])
            else:
                st.write(msg["content"])
                if os.path.exists(msg["video_path"]):
                    st.video(msg["video_path"])
                    if st.button("🧠 Analizar Táctica", key=f"btn_tac_{idx}"):
                        with st.spinner("Analizando..."):
                            analisis = ai_agent.analizar_tactica(msg["video_path"])
                            st.info(analisis)
                            st.session_state.mensajes.append({"role": "assistant", "content": f"🔍 **Táctica:** {analisis}"})
                            data_manager.guardar_chat_en_disco(vid_id_actual, st.session_state.mensajes)
                            st.rerun()
                else:
                    st.warning("⚠️ Clip no disponible.")
            
            if "usage" in msg:
                u = msg["usage"]
                st.caption(f"🪙 Tokens: {u['total_tokens']} (In: {u['prompt_tokens']} / Out: {u['completion_tokens']})")

    if prompt := st.chat_input("Pide un clip..."):
        st.session_state.mensajes.append({"role": "user", "content": prompt})
        data_manager.guardar_chat_en_disco(vid_id_actual, st.session_state.mensajes)
        
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.write("🤖 Pensando...")
            
            contexto_str = json.dumps(st.session_state['datos_partido'], ensure_ascii=False)
            
            system_prompt = f"""
            Eres un analista deportivo experto. Tienes los datos del partido en este JSON: 
            {contexto_str}

            SIGUE ESTAS REGLAS AL PIE DE LA LETRA:

            1. SI EL USUARIO PIDE INFORMACIÓN (Texto):
               - Preguntas como: "¿Cómo quedó?", "¿Quién marcó?", "¿Hubo tarjetas?", "Resumen", "¿Cuál fue el resultado?".
               - RESPONDE SOLO CON TEXTO. Explica el resultado o el dato usando el JSON.
               - PROHIBIDO generar JSON de corte en este caso.

            2. SI EL USUARIO PIDE VISUALIZAR (Video):
               - Solo si usa verbos explícitos como: "Quiero ver", "Enséñame", "Muestra", "Sácame un clip".
               - ENTONCES responde SOLO con el JSON: {{ "accion": "cortar", "tiempo_video": "MM:SS", "duracion": 15, "descripcion": "titulo_breve" }}
            """
            
            try:
                msgs_api = [{"role": "system", "content": system_prompt}] + \
                           [{"role": m["role"], "content": m["content"]} for m in st.session_state.mensajes[-6:] if "video_path" not in m]

                resp = requests.post(config.URL_ENDPOINT, headers={"Authorization": f"Bearer {config.API_KEY}"}, 
                                     json={"model": config.MODELO_CHAT, "messages": msgs_api})
                
                resp_json = resp.json()
                
                usage_info = {}
                if 'usage' in resp_json:
                    ai_agent.actualizar_tokens(resp_json['usage'])
                    usage_info = resp_json['usage']

                content = resp.json()['choices'][0]['message']['content']
                matches = re.findall(r'\{.*?\}', content, re.DOTALL)
                
                videos_generados = []
                texto_normal = content
                
                if matches:
                    texto_normal = "" 
                    for match in matches:
                        try:
                            cmd = json.loads(match)
                            if isinstance(cmd, dict) and cmd.get('accion') == 'cortar':
                                message_placeholder.write(f"✂️ Procesando: {cmd.get('descripcion')}...")
                                ruta_origen = video_manager.obtener_ruta_video(vid_id_actual)
                                if not os.path.exists(ruta_origen):
                                    url = st.session_state['datos_partido'].get("url_origen")
                                    if url: video_manager.descargar_video(url, vid_id_actual)

                                ruta = video_manager.cortar_video_ffmpeg(vid_id_actual, cmd['tiempo_video'], cmd['descripcion'])
                                if ruta:
                                    videos_generados.append((ruta, f"Aquí tienes: **{cmd['descripcion']}**"))
                        except:
                            texto_normal = content

                if videos_generados:
                    message_placeholder.empty()
                    for ruta, desc in videos_generados:
                        st.write(desc)
                        st.video(ruta)
                        st.session_state.mensajes.append({
                            "role": "assistant", 
                            "content": desc, 
                            "video_path": ruta,
                            "usage": usage_info
                        })
                else:
                    message_placeholder.write(texto_normal)
                    st.session_state.mensajes.append({
                        "role": "assistant", 
                        "content": texto_normal,
                        "usage": usage_info
                    })
                    st.caption(f"🪙 Tokens: {usage_info.get('total_tokens', 0)}")
                
                data_manager.guardar_chat_en_disco(vid_id_actual, st.session_state.mensajes)
                if videos_generados: st.rerun()

            except Exception as e:
                st.error(e)

else:
    st.info("👈 Selecciona un partido.")