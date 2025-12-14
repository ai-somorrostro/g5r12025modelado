import streamlit as st
import config
from modules import interface  # Importamos la UI que acabamos de crear
from modules import video_rag # <--- NUEVO

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="IA Video Analyst Pro", page_icon="⚽", layout="wide")

if not config.API_KEY:
    st.error("❌ Falta la API KEY en el archivo .env")
    st.stop()

# Inicializar sesión
if 'tokens_total' not in st.session_state:
    st.session_state.tokens_total = {"input": 0, "output": 0, "total": 0}

# --- EJECUCIÓN ---
def main():
    # 1. Pintar Barra Lateral
    interface.render_sidebar()
    
    # 2. Pintar Chat Central
    interface.render_chat_area()

if __name__ == "__main__":
    main()

# Inicializar Elastic
try:
    video_rag.inicializar_indice()
except Exception as e:
    st.warning(f"⚠️ No se pudo conectar con Elasticsearch. El RAG no funcionará. Error: {e}")