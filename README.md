# ABA (Asistente Bizkaia Autonomos) - RAG Multimodal

Este proyecto implementa un sistema avanzado de Generacion Aumentada por Recuperacion (RAG) Multimodal disenado para asistir a autonomos de Bizkaia. Utiliza una arquitectura basada en grafos para gestionar el flujo de conversacion, recuperacion de documentos (PDFs) e imagenes, y validacion de respuestas.

## Caracteristicas Principales

- **RAG Multimodal**: Recuperacion inteligente tanto de fragmentos de texto como de imagenes relevantes (graficos, tablas, logos) extraidos de documentos tecnicos.
- **Flujo Basado en Grafos**: Implementado con **LangGraph** para una logica de decision robusta (enrutamiento de consultas, evaluacion de calidad, reintento de busqueda sin filtros).
- **Interfaz**: Frontend desarrollado con **Streamlit**, optimizado para una experiencia de usuario fluida y visualmente atractiva con estados de carga claros.
- **Backend**: API construida con **FastAPI** que gestiona el procesamiento, la busqueda vectorial y la orquestacion de modelos.
- **Busqueda Hibrida y HyDE**: Mejora la recuperacion mediante la generacion de respuestas hipoteticas (HyDE) y re-ranking de resultados con Cross-Encoders.
- **Logica de Reintento**: Si el sistema no encuentra informacion relevante en la categoria seleccionada, realiza un segundo intento de busqueda global sin filtros.
- **Evaluacion Integrada**: Metricas de generacion (Fidelidad, Relevancia) y alculo automatico de metricas de retrieval (Hit Rate, MRR).

---

## Estructura del Proyecto

```text
aba_rag/
├── chromadb/                           # Base de datos vectorial (ChromaDB)
├── data/                               # Documentos originales y metadatos procesados
│   ├── documentos/                     # PDFs originales e imagenes extraidas
│   ├── metadata_pdf.json               # Metadatos extraidos de PDFs (clave: category)
│   └── metadata_imagenes.json          # Metadatos de imagenes procesadas (clave: categoria)
├── src/                                # Codigo fuente
│   ├── api/                            # Backend FastAPI y logica del Grafo (LangGraph)
│   │   └── api.py                      # Definicion de nodos, bordes y endpoints de la API
│   ├── ui/                             # Frontend Streamlit
│   │   └── interfaz.py                 # Componentes visuales y logica de cliente
│   └── utilidades/                     # Funciones modulares de soporte
│       ├── funciones_db.py             # Gestion de ChromaDB (insercion, carga)
│       ├── funciones_preprocesado.py   # OCR, extraccion de texto e imagenes
│       ├── funciones_evaluacion.py     # Logica de metricas RAG
│       ├── funciones_umap.py           # Visualizacion de embeddings con UMAP
│       ├── prompts.py                  # Plantillas de sistema para el LLM
│       └── utils.py                    # Utilidades generales del proyecto
├── visualizaciones_umap/               # Carpeta para visualizaciones UMAP generadas
│   └── umap_ABA_3d_categoria.html      # Proyeccion de embeddings en 3D por categoria
├── run.py                              # Script principal para arrancar API + UI simultaneamente
├── requirements.txt                    # Dependencias del proyecto
└── .env.template                       # Configuracion de claves API y rutas
```

---

## Esquema de Ejecucion (LangGraph Flow)

El siguiente diagrama muestra cono fluye una consulta a traves del sistema, incluyendo la logica de reintento automatico:

```mermaid
graph TD
    A[Pregunta Usuario] --> B{Router}
    B -- Saludo --> C[Respuesta Directa]
    B -- Pregunta --> D[Generacion HyDE]
    D --> E[Buscador Multimodal con Filtros]
    E --> F[Reranker]
    F --> G{Evaluador Relevancia}
    G -- No Relevante y primer intento --> H[Buscador SIN Filtros]
    H --> F
    G -- No Relevante y reintento fallido --> I[Mensaje de Fallo]
    G -- Relevante --> J[Generador de Respuesta]
    J --> K[Evaluador Calidad/Fidelidad]
    K --> L[Respuesta Final]
```

---

## Como Empezar

### 1. Requisitos Previos
- Python 3.10 o superior.

### 2. Instalacion
Clona el repositorio e instala las dependencias:
```bash
git clone https://github.com/iratisimon/aba-rag.git
cd aba-rag
pip install -r requirements.txt
```

### 3. Configuracion de Entorno
Crea un archivo .env y configuralo usando como base el archivo .env.template.
Es necesario configurar la API key de el proveedor de LLM compatible con OpenAI (ej: Groq).

### 4. Preparacion de Datos
Para procesar los PDFs y crear la base de datos vectorial:
```bash
python src/utilidades/funciones_db.py
```

### 5. Ejecucion
El proyecto incluye un script unificado que arranca la API de FastAPI y la interfaz de Streamlit automaticamente:
```bash
python run.py
```

---

## Tecnologias Utilizadas

- **Modelos**: LLM compatible con OpenAI (GPT, Llama), CLIP (Multimodal), Sentence Transformers (BGE), Cross-Encoders (Re-ranking).
- **Orquestacion**: LangGraph para la gestion de estados y flujos complejos.
- **Base de Datos**: ChromaDB para almacenamiento vectorial distribuido por colecciones (PDFs/Imagenes).
- **Backend**: FastAPI para la exposicion de servicios y procesamiento asincrono.
- **Frontend**: Streamlit para la interfaz de usuario con componentes personalizados.
- **Procesamiento de Docs**: PyMuPDF para extraccion, UMAP para analisis de clusters.

---

## Visualizacion de ejemplo
<div align="center">
  <i>Pagina de inicio:</i>
  <br><br>
  <img src="https://github.com/user-attachments/assets/0b090202-e39d-4362-984e-7d0171de80ba" alt="interfaz_1">
</div>

<br>

<div align="center">
  <i>Flujo de ejecucion:</i>
  <br><br>
  <img src="https://github.com/user-attachments/assets/333ce817-daed-4c9a-ab6e-39e7d9d42e4e" alt="interfaz_2">
</div>

<br>

<div align="center">
  <i>Apartado de flujo de acciones/evaluacion:</i>
  <br><br>
  <img src="https://github.com/user-attachments/assets/00dbce57-1cd9-4ef2-82e4-94c8eb18926e" alt="interfaz_3">
</div>
