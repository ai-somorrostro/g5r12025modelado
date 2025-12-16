import time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from modules import video_rag

# ==========================================
# 1. CONFIGURACIÓN DEL TEST (GROUND TRUTH)
# ==========================================
TEST_CASES = [
    {"query": "Gol",               "expected": "Gol",     "categoria": "Acción"},
    {"query": "Tarjeta amarilla",  "expected": "Tarjeta", "categoria": "Objeto"},
    {"query": "Tarjeta roja",      "expected": "Roja",    "categoria": "Objeto"},
    {"query": "Árbitro",           "expected": "Tarjeta", "categoria": "Visual"}, 
    {"query": "Jugadores celebrando", "expected": "Gol",  "categoria": "Semántica"},
    {"query": "Soccer goal",       "expected": "Gol",     "categoria": "Idioma"},
]

def ejecutar_benchmark_real():
    print("🚀 INICIANDO BENCHMARK REAL (Minimalist Design)...")
    
    # Asegurar conexión
    video_rag.inicializar_indice()
    
    resultados = []
    top_k_evaluado = 5

    for test in TEST_CASES:
        print(f"🔎 Buscando: '{test['query']}'...", end=" ")
        
        start_time = time.time()
        res_busqueda = video_rag.buscar_por_texto(test["query"], top_k=top_k_evaluado)
        end_time = time.time()
        
        latencia_ms = (end_time - start_time) * 1000
        
        aciertos = 0
        if res_busqueda:
            for item in res_busqueda:
                if test["expected"].lower() in item["descripcion"].lower():
                    aciertos += 1
            precision = (aciertos / len(res_busqueda)) * 100
        else:
            precision = 0
            
        print(f"-> {latencia_ms:.0f}ms | Precisión: {precision}%")

        resultados.append({
            "Query": test["query"],
            "Latencia (ms)": latencia_ms,
            "Precisión (%)": precision
        })

    df = pd.DataFrame(resultados)
    df.to_csv("resultados_benchmark_real.csv", index=False)
    
    print("\n✅ Datos recopilados. Generando gráficos minimalistas...")
    generar_graficos_minimalistas(df)

def generar_graficos_minimalistas(df):
    # ESTILO MINIMALISTA GLOBAL
    sns.set_theme(style="white") # Fondo blanco puro
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['text.color'] = '#333333'
    plt.rcParams['axes.labelcolor'] = '#333333'
    plt.rcParams['xtick.color'] = '#333333'
    plt.rcParams['ytick.color'] = '#333333'
    
    # --- GRÁFICO 1: PRECISIÓN (Barra Simple Azul Acero) ---
    plt.figure(figsize=(10, 6))
    
    ax = sns.barplot(
        data=df,
        x="Query",
        y="Precisión (%)",
        color="#4A90E2", # Un solo color elegante (Azul)
        edgecolor=None   # Sin bordes negros
    )
    
    # Limpieza visual extrema
    sns.despine(left=True, bottom=True) # Quitar bordes del gráfico
    ax.yaxis.grid(True, color='#EEEEEE') # Rejilla muy suave solo horizontal
    ax.xaxis.grid(False)
    
    plt.title("Precisión de Recuperación Semántica", fontsize=16, pad=20, loc='left')
    plt.ylabel("Precisión (%)", fontsize=11)
    plt.xlabel("") # Quitamos la etiqueta X porque ya se leen las categorías
    plt.ylim(0, 110)
    
    # Etiquetas de valor simples encima de las barras
    for i, v in enumerate(df["Precisión (%)"]):
        ax.text(i, v + 2, f"{v:.0f}%", ha='center', fontsize=10, color='#4A90E2', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig("grafico_precision_minimal.png", dpi=300)
    print("📊 Gráfico 1 guardado: grafico_precision_minimal.png")

    # --- GRÁFICO 2: LATENCIA (Barra Simple Gris Oscuro) ---
    plt.figure(figsize=(10, 6))
    
    ax = sns.barplot(
        data=df,
        x="Query",
        y="Latencia (ms)",
        color="#5D6D7E", # Gris azulado profesional
        edgecolor=None
    )
    
    sns.despine(left=True, bottom=True)
    ax.yaxis.grid(True, color='#EEEEEE')
    ax.xaxis.grid(False)
    
    # Línea media sutil
    media = df["Latencia (ms)"].mean()
    plt.axhline(y=media, color='#E74C3C', linestyle=':', linewidth=1, label=f'Media: {media:.0f} ms')
    plt.legend(frameon=False) # Leyenda sin caja
    
    plt.title("Latencia de Respuesta (Elasticsearch Cluster)", fontsize=16, pad=20, loc='left')
    plt.ylabel("Milisegundos (ms)", fontsize=11)
    plt.xlabel("")
    
    plt.tight_layout()
    plt.savefig("grafico_latencia_minimal.png", dpi=300)
    print("📊 Gráfico 2 guardado: grafico_latencia_minimal.png")

if __name__ == "__main__":
    ejecutar_benchmark_real()