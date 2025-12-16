import streamlit as st
import glob
import os
import json
import time
import re
from modules import video_rag
import config
from modules import video_manager, data_manager, ai_agent

def render_sidebar():
    """Dibuja toda la barra lateral"""
    with st.sidebar:
        st.title("🗄️ Mis Partidos")
        
        # Métricas
        with st.expander("📊 Métricas de Consumo", expanded=True):
            col1, col2 = st.columns(2)
            if 'tokens_total' in st.session_state:
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

        st.divider()
        
        # --- INDEXADOR MASIVO ---
        if 'datos_partido' in st.session_state:
            st.markdown("### ⚡ Acciones Rápidas")
            datos = st.session_state['datos_partido']
            vid_id = st.session_state.get('video_id')
            
            if st.button("🧠 Generar e Indexar TODOS los clips", help="Corta y guarda en Elasticsearch todos los eventos detectados"):
                
                progreso = st.progress(0)
                total = len(datos['eventos'])

                # Esto obliga a crear el índice con configuración vectorial ANTES de meter datos
                try: video_rag.inicializar_indice()
                except: pass
                
                ruta_mp4 = video_manager.obtener_ruta_video(vid_id)
                if not os.path.exists(ruta_mp4):
                    video_manager.descargar_video(datos.get("url_origen"), vid_id)

                for i, evento in enumerate(datos['eventos']):
                    ruta_clip = video_manager.cortar_video_ffmpeg(
                        vid_id, 
                        evento['tiempo_video'], 
                        evento['descripcion']
                    )
                    
                    if ruta_clip:
                        try:
                            video_rag.indexar_clip(
                                ruta_clip=ruta_clip,
                                descripcion=evento['descripcion'],
                                timestamp=evento['tiempo_video'],
                                video_id=vid_id
                            )
                        except: pass
                    
                    progreso.progress((i + 1) / total)
                
                st.success(f"¡{total} eventos indexados en tus máquinas virtuales!")
                time.sleep(2)
                st.rerun()
                
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
                    
                    ruta_mp4 = video_manager.obtener_ruta_video(vid_id)
                    if not os.path.exists(ruta_mp4):
                        url = datos_archivo.get("url_origen")
                        if url:
                            with st.spinner("📥 Recuperando video..."):
                                video_manager.descargar_video(url, vid_id)
                    st.rerun()
            except: pass

        # Buscador RAG
        st.divider()
        st.markdown("### 🧠 Buscador Semántico (RAG)")
        st.caption("Busca jugadas en tu base de datos global (Elasticsearch)")
        
        query_rag = st.text_input("Ej: 'Gol de cabeza', 'Tarjeta roja'...")
        
        if query_rag:
            with st.spinner("Buscando en las 3 máquinas virtuales..."):
                video_rag.inicializar_indice()
                resultados = video_rag.buscar_por_texto(query_rag)
                
                if resultados:
                    for res in resultados:
                        # Recuperamos el segundo exacto que detectó el RAG
                        segundo = res.get('segundo_detectado', 0)
                        
                        # Mostramos título y detalles técnicos debajo
                        st.markdown(f"**{res['descripcion']}**")
                        st.caption(f"🎯 Detectado visualmente en el segundo: **{segundo}s** (Similitud: {res['score']:.4f})")
                        
                        if os.path.exists(res['ruta_video']):
                            # 'start_time' hace que el video empiece justo donde ocurrió la acción
                            st.video(res['ruta_video'], start_time=int(segundo))
                        else:
                            st.warning("El video original ya no existe en disco.")
                else:
                    st.info("No se encontraron coincidencias visuales.")
        
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
                            st.download_button("⬇️ Descargar", file, os.path.basename(msg["video_path"]), "video/mp4", key=f"dl_{idx}")
                        
                        if st.button("🧠 Análisis táctico", key=f"tac_{idx}"):
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
                placeholder.write("🤖 Pensando...")
                
                ctx = json.dumps(st.session_state['datos_partido'], ensure_ascii=False)
                
                sys_prompt = f"""
                CONTEXTO (DATOS DEL PARTIDO):
                {ctx}

                ROL: Eres un comentarista deportivo de primer nivel y analista táctico experto.
                TONO: Dinámico, preciso y profesional. No suenes como un robot, suena como un experto en fútbol.

                INSTRUCCIONES DE FORMATO:
                - Usa **Negritas** para resaltar: Nombres de jugadores, Minutos clave y Resultados.
                - Usa Emojis para categorizar eventos: ⚽ (Goles), 🟥/🟨 (Tarjetas), 🧤 (Paradas), ⚔️ (Faltas/Duelos).
                - Si el usuario saluda, sé breve y ofrece ayuda sobre el partido cargado.

                LÓGICA DE RESPUESTA (SIGUE ESTO ESTRICTAMENTE):

                1. SI EL USUARIO PIDE INFORMACIÓN (Texto):
                   - Analiza el JSON y construye una respuesta narrativa.
                   - No digas "según el JSON". Di "En el partido...".
                   - Si hay varios eventos, usa una lista con viñetas (-).
                   - CIERRE OBLIGATORIO: Termina SIEMPRE sugiriendo ver una jugada clave. 
                     (Ej: "Fue un momento decisivo. ¿Te gustaría ver el video de ese gol?").
                   - PROHIBIDO generar JSON en este modo.

                2. SI EL USUARIO PIDE VISUALIZAR (Intención de Video):
                   - Palabras clave: "Ver", "Enséñame", "Muestra", "Clip", "Video", "Sí quiero".
                   - ACCIÓN: Genera SOLO el JSON técnico de corte: 
                     {{ "accion": "cortar", "tiempo_video": "MM:SS", "duracion": 15, "descripcion": "titulo_corto_y_atractivo" }}
                """
                
                try:
                    msgs = [{"role": "system", "content": sys_prompt}] + \
                           [{"role": m["role"], "content": m["content"]} for m in st.session_state.mensajes[-6:] if "video_path" not in m]

                    content = ai_agent.obtener_respuesta_chat(msgs)
                    
                    # --- PARSEO ROBUSTO DE LA RESPUESTA ---
                    # 1. Limpieza de Markdown
                    content_clean = re.sub(r'```json\s*', '', content).replace('```', '')
                    
                    # 2. Búsqueda de JSON
                    matches = re.findall(r'\{.*?\}', content_clean, re.DOTALL)
                    videos = []
                    txt = content # Por defecto es texto
                    
                    if matches:
                        for m in matches:
                            try:
                                # Intento de corrección de comillas simples (error común de LLMs)
                                if "'" in m and '"' not in m:
                                    m = m.replace("'", '"')
                                
                                cmd = json.loads(m)
                                if isinstance(cmd, dict) and cmd.get('accion') == 'cortar':
                                    # Si encontramos un comando válido, limpiamos el texto
                                    txt = ""
                                    placeholder.write(f"✂️ Procesando: {cmd.get('descripcion')}...")
                                    
                                    # Auto-recovery
                                    ruta_origen = video_manager.obtener_ruta_video(vid_id)
                                    if not os.path.exists(ruta_origen):
                                        url = datos.get("url_origen")
                                        if url: 
                                            st.toast("Descargando video...", icon="📥")
                                            video_manager.descargar_video(url, vid_id)
                                        else:
                                            st.error("❌ Error: Falta el video original y no hay URL para bajarlo.")

                                    # Corte
                                    r = video_manager.cortar_video_ffmpeg(vid_id, cmd['tiempo_video'], cmd['descripcion'])
                                    
                                    if r:
                                        # Indexar RAG
                                        try:
                                            video_rag.indexar_clip(r, cmd['descripcion'], cmd['tiempo_video'], vid_id)
                                        except Exception as e:
                                            print(f"Error indexando: {e}")
                                        
                                        videos.append((r, f"Clip: **{cmd['descripcion']}**"))
                                    else:
                                        st.error(f"❌ Error al generar el video: {cmd['descripcion']}")
                            except Exception as e:
                                # Si falla el JSON, no rompemos, simplemente se mostrará como texto
                                print(f"Intento de JSON fallido: {e}")

                    # Mostrar Resultados
                    if videos:
                        placeholder.empty()
                        for r, d in videos:
                            st.write(d)
                            st.video(r)
                            with open(r, "rb") as f: st.download_button("⬇️ Descargar", f, os.path.basename(r), "video/mp4", key=f"dl_n_{r}")
                            st.session_state.mensajes.append({"role": "assistant", "content": d, "video_path": r})
                    else:
                        # Solo mostramos texto si no está vacío
                        if txt.strip():
                            placeholder.write(txt)
                            st.session_state.mensajes.append({"role": "assistant", "content": txt})
                    
                    data_manager.guardar_chat_en_disco(vid_id, st.session_state.mensajes)
                    if videos: st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("👈 Selecciona un partido.")