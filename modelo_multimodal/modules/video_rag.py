import os
import cv2
import ssl
import numpy as np
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ElasticsearchWarning
from PIL import Image
from deep_translator import GoogleTranslator
import config
import warnings

# Silenciar warnings
warnings.simplefilter('ignore', category=ElasticsearchWarning)

# CONFIGURACIÓN DE DENSIDAD
# 3 = Analizar 3 fotos cada segundo (Muy preciso)
FOTOS_POR_SEGUNDO = 3 

# 1. CONEXIÓN
try:
    contexto_ssl = ssl.create_default_context()
    contexto_ssl.check_hostname = False
    contexto_ssl.verify_mode = ssl.CERT_NONE

    es_client = Elasticsearch(
        config.ELASTIC_HOSTS,
        api_key=(config.ELASTIC_ID, config.ELASTIC_KEY),
        ssl_context=contexto_ssl,
        verify_certs=False,
        ssl_show_warn=False
    )
except Exception as e:
    print(f"⚠️ Error conexión Elastic: {e}")
    es_client = None

INDEX_NAME = "video_clips_vector"

# 2. MODELO
print("⏳ Cargando CLIP Large (ViT-L-14)...")
model = SentenceTransformer('clip-ViT-L-14')

# 3. FUNCIONES

def inicializar_indice():
    if es_client and not es_client.indices.exists(index=INDEX_NAME):
        mappings = {
            "properties": {
                "descripcion": {"type": "text"},
                "ruta_video": {"type": "keyword"},
                "timestamp": {"type": "keyword"},
                "video_id": {"type": "keyword"},
                "segundo_exacto": {"type": "integer"},
                "vector_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
        es_client.indices.create(index=INDEX_NAME, mappings=mappings)

def obtener_frames_alta_densidad(ruta_video):
    """
    Extrae FOTOS_POR_SEGUNDO frames de forma equidistante.
    """
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened(): return []
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0: return []
    
    duracion_segundos = total_frames / fps
    total_fotos = int(duracion_segundos * FOTOS_POR_SEGUNDO)
    
    # Puntos de corte exactos
    puntos = np.linspace(0, total_frames - 5, total_fotos, dtype=int)
    
    frames = []
    for p in puntos:
        cap.set(cv2.CAP_PROP_POS_FRAMES, p)
        ret, frame = cap.read()
        if ret:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frames.append(img)
    cap.release()
    return frames

def indexar_clip(ruta_clip, descripcion, timestamp, video_id):
    if not es_client: return
    
    imagenes = obtener_frames_alta_densidad(ruta_clip)
    if not imagenes: return

    print(f"📸 Indexando {len(imagenes)} vectores para: {descripcion}")

    for i, img in enumerate(imagenes):
        try:
            vector = model.encode(img)
            
            # --- CÁLCULO DEL SEGUNDO REAL ---
            # Si es la foto 9 y vamos a 3fps -> Es el segundo 3
            segundo_real = int(i / FOTOS_POR_SEGUNDO)
            # --------------------------------
            
            doc = {
                "descripcion": descripcion,
                "ruta_video": ruta_clip,
                "timestamp": timestamp,
                "video_id": video_id,
                "segundo_exacto": segundo_real, # Guardamos el segundo real, no el índice
                "vector_embedding": vector.tolist()
            }
            es_client.index(index=INDEX_NAME, document=doc)
        except: pass

def buscar_por_texto(query_texto, top_k=50):
    if not es_client: return []
    
    try:
        query_ingles = GoogleTranslator(source='auto', target='en').translate(query_texto)
    except:
        query_ingles = query_texto

    vector_busqueda = model.encode(query_ingles)
    
    try:
        response = es_client.search(
            index=INDEX_NAME,
            knn={
                "field": "vector_embedding",
                "query_vector": vector_busqueda.tolist(),
                "k": top_k,
                "num_candidates": 200
            }
        )
        
        resultados_unicos = []
        videos_vistos = set()

        for hit in response['hits']['hits']:
            ruta = hit['_source']['ruta_video']
            score = hit['_score']
            sec = hit['_source'].get('segundo_exacto', 0)
            
            if ruta not in videos_vistos:
                videos_vistos.add(ruta)
                resultados_unicos.append({
                    "score": score,
                    "descripcion": hit['_source']['descripcion'],
                    "ruta_video": ruta,
                    "timestamp": hit['_source']['timestamp'],
                    "segundo_detectado": sec
                })
        
        return resultados_unicos[:5]

    except Exception as e:
        print(f"Error búsqueda: {e}")
        return []