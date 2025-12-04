import streamlit as st
import glob
import os
import json
import time
import re
# Importamos la lógica interna
import config
from modules import video_manager, data_manager, ai_agent

def render_sidebar():
    """Dibuja toda la barra lateral"""
    with st.sidebar:
        st.title("🗄️ Mis Partidos")
        
        # Métricas
        with st.expander("📊 Métricas de Consumo", expanded=True):
            col1, col2 = st.columns(2)
            col1.metric("Input", f"{st.session_state.tokens_total['input']}", delta_color="off")
            col2.metric("Output", f"{st.session_state.tokens_total['output']}", delta_color="off")
            st.metric("Total Tokens", f"{st.session_state.tokens_total['total']}")
            
            if st.button("🔄 Resetear"):
                st.session_state.tokens_total = {"input": 0, "output": 0, "total": 0}
                st.rerun()

        st.divider()

        # Nuevo Análisis
        with st.expander("🆕 Añadir Nuevo Partido", expanded=False):
            url_input = st.text_input("URL de YouTube")
            if st.button("🚀 Analizar", type="primary"):
                if url_input:
                    vid_id = video_manager.extraer_id_youtube(url_input)
                    with st.status("Analizando...", expanded=True) as status:
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

        # Historial
        st.markdown("### 💬 Conversaciones")
        archivos = data_manager.listar_archivos_analisis()
        
        for ruta in archivos:
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    datos_archivo = json.load(f)
                vid_id = os.path.basename(ruta).replace(".json", "")
                titulo = datos_archivo.get('partido', 'Desconocido')
                
                if st.button(f"⚽ {titulo}", key=vid_id, use_container_width=True):
                    st.session_state['datos_partido'] = datos_archivo
                    st.session_state['video_id'] = vid_id
                    st.session_state['mensajes'] = data_manager.cargar_chat_de_disco(vid_id)
                    
                    # Auto-recovery
                    ruta_mp4 = video_manager.obtener_ruta_video(vid_id)
                    if not os.path.exists(ruta_mp4):
                        url = datos_archivo.get("url_origen")
                        if url:
                            with st.spinner("📥 Recuperando video..."):
                                video_manager.descargar_video(url, vid_id)
                    st.rerun()
            except: pass

        # Limpieza
        st.divider()
        if st.button("🗑️ Liberar Espacio", type="secondary"):
            for folder in [config.CARPETA_VIDEOS, config.CARPETA_RECORTES]:
                for f in glob.glob(os.path.join(folder, "*.mp4")):
                    try: os.remove(f)
                    except: pass
            st.success("Listo.")
            time.sleep(1)
            st.rerun()

def render_chat_area():
    """Dibuja el área principal del chat"""
    st.title("⚽ IA Video Analyst Pro")

    if 'datos_partido' in st.session_state:
        datos = st.session_state['datos_partido']
        vid_id = st.session_state.get('video_id', 'unknown')
        
        st.header(f"🏟️ {datos.get('partido', 'Partido')}")
        
        if "mensajes" not in st.session_state:
            st.session_state.mensajes = []

        # Mostrar mensajes
        for idx, msg in enumerate(st.session_state.mensajes):
            with st.chat_message(msg["role"]):
                if "video_path" not in msg:
                    st.write(msg["content"])
                else:
                    st.write(msg["content"])
                    if os.path.exists(msg["video_path"]):
                        st.video(msg["video_path"])
                        with open(msg["video_path"], "rb") as file:
                            st.download_button("⬇️", file, os.path.basename(msg["video_path"]), "video/mp4", key=f"dl_{idx}")
                        
                        if st.button("🧠 Táctica", key=f"tac_{idx}"):
                            with st.spinner("Analizando..."):
                                ana = ai_agent.analizar_tactica(msg["video_path"])
                                st.session_state.mensajes.append({"role": "assistant", "content": f"🔍 {ana}"})
                                data_manager.guardar_chat_en_disco(vid_id, st.session_state.mensajes)
                                st.rerun()
                
                if "usage" in msg:
                    u = msg["usage"]
                    st.caption(f"🪙 {u.get('total_tokens', 0)} tokens")

        # Input Usuario
        if prompt := st.chat_input("Escribe aquí..."):
            st.session_state.mensajes.append({"role": "user", "content": prompt})
            data_manager.guardar_chat_en_disco(vid_id, st.session_state.mensajes)
            with st.chat_message("user"): st.write(prompt)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.write("🤖...")
                
                ctx = json.dumps(st.session_state['datos_partido'], ensure_ascii=False)
                sys_prompt = f"""
                Eres experto deportivo. JSON: {ctx}
                SI PIDEN VIDEO: Responde JSON {{ "accion": "cortar", "tiempo_video": "MM:SS", "duracion": 15, "descripcion": "titulo" }}
                SI NO: Texto.
                """
                
                msgs = [{"role": "system", "content": sys_prompt}] + \
                       [{"role": m["role"], "content": m["content"]} for m in st.session_state.mensajes[-6:] if "video_path" not in m]

                content = ai_agent.obtener_respuesta_chat(msgs)
                
                # Procesar
                matches = re.findall(r'\{.*?\}', content, re.DOTALL)
                videos = []
                txt = content
                
                if matches:
                    txt = ""
                    for m in matches:
                        try:
                            cmd = json.loads(m)
                            if cmd.get('accion') == 'cortar':
                                placeholder.write(f"✂️ {cmd['descripcion']}...")
                                
                                # Auto-recovery
                                p_vid = video_manager.obtener_ruta_video(vid_id)
                                if not os.path.exists(p_vid):
                                    url = st.session_state['datos_partido'].get("url_origen")
                                    if url: video_manager.descargar_video(url, vid_id)

                                r = video_manager.cortar_video_ffmpeg(vid_id, cmd['tiempo_video'], cmd['descripcion'])
                                if r: videos.append((r, f"Clip: **{cmd['descripcion']}**"))
                        except: txt = content

                if videos:
                    placeholder.empty()
                    for r, d in videos:
                        st.write(d)
                        st.video(r)
                        with open(r, "rb") as f: st.download_button("⬇️", f, os.path.basename(r), "video/mp4", key=f"dln_{r}")
                        st.session_state.mensajes.append({"role": "assistant", "content": d, "video_path": r})
                else:
                    placeholder.write(txt)
                    st.session_state.mensajes.append({"role": "assistant", "content": txt})
                
                data_manager.guardar_chat_en_disco(vid_id, st.session_state.mensajes)
                if videos: st.rerun()

    else:
        st.info("👈 Selecciona un partido.")