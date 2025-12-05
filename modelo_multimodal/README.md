# IA Video Analyst Pro

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/AI-Gemini%203%20Pro-4285F4?style=flat&logo=google&logoColor=white)
![FFmpeg](https://img.shields.io/badge/Tool-FFmpeg-007808?style=flat&logo=ffmpeg&logoColor=white)
![Status](https://img.shields.io/badge/Status-Stable-success)

**IA Video Analyst Pro** es un **Agente Multimodal RAG** (Retrieval-Augmented Generation) avanzado, diseñado para el análisis deportivo automatizado.

El sistema ingesta videos de partidos (YouTube), los analiza visualmente fotograma a fotograma utilizando **Google Gemini 3 Pro**, y permite al usuario interactuar mediante un chat inteligente. Lo que diferencia a este proyecto es su capacidad de **"Tool Use" (Uso de Herramientas)**: el asistente no solo responde texto, sino que **ejecuta comandos de edición de video** para recortar y entregar *highlights* (goles, tarjetas, jugadas) automáticamente bajo demanda.

---

## Características Principales

- **Visión Artificial Generativa:** Análisis completo del video detectando eventos con doble timestamp (tiempo de juego vs. tiempo de reproducción).
- **Agente Editor de Video:** Si pides *"Quiero ver el gol"*, la IA detecta la intención, localiza el momento exacto y usa **FFmpeg** para cortar y entregarte el clip al instante.
- **Análisis Táctico:** Función para extraer fotogramas específicos y realizar un análisis estratégico de posicionamiento de jugadores.
- **Persistencia y Memoria:** Base de datos local (JSON) que guarda el historial de conversaciones y análisis para no re-procesar videos antiguos.
- **Ingesta Robusta:** Sistema avanzado de descarga (`yt-dlp`) con gestión de cookies para evadir bloqueos anti-bot de YouTube.
- **Métricas de Consumo:** Monitorización en tiempo real del uso de Tokens (Input/Output) de la API.

---

## Requisitos Previos

Antes de instalar, asegúrate de tener en tu sistema:

1.  **Python 3.10** o superior.
2.  **FFmpeg** (Esencial para el recorte de videos).
    *   **Ubuntu/Linux:** `sudo apt install ffmpeg`
    *   **Windows:** `winget install ffmpeg` o añadir al PATH manualmente.
    *   **Mac:** `brew install ffmpeg`

---

## Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone git@github.com:ai-somorrostro/g5r12025modelado.git
    cd modelo_multimodal
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    # Linux / Mac
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

---

## Configuración (CRÍTICO)

Para que el proyecto funcione, necesitas crear **dos archivos de seguridad** en la raíz del proyecto. Estos archivos **NO** se incluyen en el repositorio por seguridad.

### 1. Variables de Entorno (`.env`)
Crea un archivo llamado `.env` en la raíz y añade tu clave de OpenRouter:

```env
API_KEY_OPENROUTER="sk-or-v1-TuClaveSuperSecretaAqui..."
```

### 2. Autenticación de YouTube (`cookies.txt`)
YouTube bloquea las descargas automatizadas. Para solucionarlo, debes exportar tu sesión:

1.  Instala la extensión **"Get cookies.txt LOCALLY"** en tu navegador (Chrome/Firefox).
2.  Ve a [YouTube.com](https://www.youtube.com) y asegúrate de haber iniciado sesión.
3.  Abre la extensión y pulsa **"Export"**.
4.  Renombra el archivo descargado a `cookies.txt` y colócalo en la raíz del proyecto.

---

## Uso

Una vez configurado, ejecuta la aplicación:

```bash
streamlit run main.py
```
1. Pega una URL de YouTube en la barra lateral.
2. Pulsa "Analizar".
3. Espera a que la IA procese el video.
4. ¡Empieza a chatear!
    - Ejemplo: "¿Quién marcó el segundo gol?"
    - Ejemplo: "Quiero ver la tarjeta roja del minuto 80".

## Estructura del Proyecto

El código sigue una arquitectura modular profesional:

```text
├── main.py                # Punto de entrada (Orquestador de la UI)
├── config.py              # Configuración global y rutas
├── modules/               # Lógica de negocio
│   ├── ai_agent.py        # Comunicación con OpenRouter/Gemini
│   ├── video_manager.py   # Descarga, FFmpeg, OpenCV
│   ├── data_manager.py    # Persistencia JSON (DB)
│   └── interface.py       # Componentes visuales de Streamlit
├── db_partidos/           # (Generado) Almacena los análisis JSON
├── db_chats/              # (Generado) Historial de conversaciones
├── videos_originales/     # (Generado) Archivos MP4 descargados
└── recortes_generados/    # (Generado) Clips cortados por la IA
```

## Solución de Problemas (Troubleshooting)

*   **Error 401 / "Sign in to confirm you are not a bot":**
    *   Tus cookies han caducado. Genera un nuevo `cookies.txt` y reemplaza el antiguo.
*   **Error 500 (Internal Server Error):**
    *   El video es demasiado largo para la API. Intenta con resúmenes más cortos (<10 min) o espera un momento, ya que la API de Gemini Preview puede estar saturada.
*   **El video no se corta:**
    *   Asegúrate de que tienes **FFmpeg** instalado en tu sistema operativo y accesible desde la terminal.

---

## Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo `LICENSE` para más detalles.

---

**Nota:** Este software es una herramienta educativa y de portafolio. El usuario es responsable de cumplir con los Términos de Servicio de YouTube y las leyes de derechos de autor aplicables en su país respecto a la descarga y uso de contenido de terceros.