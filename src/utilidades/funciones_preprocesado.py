"""En este script aparecen la sfunciones relacionadas con el preprocesado de los datos 
que se van a recoger en la base de datos"""
import os
from loguru import logger
import utils
import glob
import fitz  
from openai import OpenAI

# Lista de categorías
CATEGORIAS_VALIDAS = [
    "Laboral",      
    "Fiscal", 
    "Ayudas_y_Subvenciones"                
]
# Modelo
MODELO_CLASIFICADOR = os.getenv("MODELO_FAST", "llama3.2")

# Configuración de Rutas usando utils
DATA_DIR = utils.project_root() / "data" / "documentos" / "pdfs"
logger.info(f"Ruta de datos: {DATA_DIR}")

# Configuración LLM para clasificación automática
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")

def leer_pdf(ruta_pdf: str) -> str:
    """
    Lee todo el texto de un archivo PDF.
    
    Args:
        ruta_pdf: Ruta absoluta o relativa al archivo PDF.
        
    Returns:
        String con todo el texto del PDF concatenado.
    """
    
    if not os.path.exists(ruta_pdf):
        logger.error(f" No encuentro el archivo: {ruta_pdf}")
        return ""

    logger.info(f" Leyendo PDF: {os.path.basename(ruta_pdf)}...")
    #doc es un objeto iterable- La len(doc) es el numero de paginas. Itera por cada pagina
    doc = fitz.open(ruta_pdf)
    texto_completo = ""
    
    for pagina in doc:
        texto_completo += pagina.get_text() + "\n"  # pagina.get_text() extrae el texto de la pagina + \n salto de linea
        
    logger.info(f"    Leídas {len(doc)} páginas ({len(texto_completo)} caracteres).")
    return texto_completo

def clasificar_documento(nombre_archivo: str, texto_inicio: str, client_llm) -> str:
    """
    Clasifica un documento usando LLM.
    """
    system_prompt = f"""Eres un sistema de clasificación documental para una aplicación RAG legal-administrativa
dirigida a personas autónomas en Bizkaia.
Categorías válidas: {', '.join(CATEGORIAS_VALIDAS)}

REGLAS:
- Responde SOLO con el nombre exacto de la categoría.
- Usa EXCLUSIVAMENTE una de las categorías permitidas.
- NO inventes nuevas categorías.
- NO devuelvas explicaciones ni texto adicional.
- Si el documento contiene varios temas, elige el tema principal.
- Si ninguna categoría encaja claramente, usa "otros".
- NO expliques tu razonamiento."""

    user_prompt = f"""Clasifica este documento:

ARCHIVO: {nombre_archivo}
TEXTO:
"{texto_inicio[:1000]}"

CATEGORIA:"""

    try:
        resp = client_llm.chat.completions.create(
            model=MODELO_CLASIFICADOR,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        categoria_raw = resp.choices[0].message.content.strip()
        
        for cat in CATEGORIAS_VALIDAS:
            if cat.lower() in categoria_raw.lower():
                return cat
        
        logger.warning(f"  LLM respondió '{categoria_raw}' (no válida) → Usando 'otros'")
        return "General"
        
    except Exception as e:
        logger.warning(f"Fallo al clasificar {nombre_archivo}: {e}")
        return "General"

def main():
    logger.info("Iniciando pre-procesado")
    
    patron_ruta = os.path.join(DATA_DIR, "*.pdf")
    #Lista de rutas a todos los PDFs
    archivos = glob.glob(patron_ruta)
    # Setup Cliente LLM (para clasificación automática)
    client_llm = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

    if not archivos:
        logger.error("No se encontraron archivos PDF en la carpeta.")
        return
    
    for archivo in archivos:
        nombre_archivo = os.path.basename(archivo)
        logger.info(f"Procesando: {nombre_archivo}...")
        
        texto = leer_pdf(archivo)
        
        # Caso B: LLM clasifica automáticamente
        categoria = clasificar_documento(nombre_archivo, texto, client_llm)
        subcategoria = "General"
        logger.info(f"[LLM] Categoría: {categoria}")
        
        # --- ESTRATEGIA PADRE-HIJO ---
        items_jerarquicos = crear_chunks_jerarquicos(texto)
        
        # Preparar batch para Chroma
        textos_hijos = [item["texto_vectorizable"] for item in items_jerarquicos]
        metadatas = []
        ids = []
        
        for idx, item in enumerate(items_jerarquicos):
            metadatas.append({
                "source": nombre_archivo,
                "category": categoria,
                "subcategory": subcategoria, 
                "type": "child",
                "parent_id": item["padre_id"],
                "contexto_expandido": item["texto_completo_padre"]
            })
            ids.append(f"{nombre_archivo}_child_{idx}")
            
        # Generar Embeddings (Solo de los HIJOS)
        embeddings = utils.generar_embeddings(model, textos_hijos)
        
        # Guardar en DB
        collection.add(
            documents=textos_hijos,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        total_chunks += len(ids)
        logger.info(f"  -> Insertados {len(ids)} chunks hijos (con sus padres ocultos).")

    logger.info("\n" + "="*50)
    logger.info(f" FINALIZADO. Total indexado: {total_chunks} vectores.")
    logger.info(f"Colección especial: {COLLECTION_NAME}")
    logger.info("="*50)

if __name__ == "__main__":
    main()
