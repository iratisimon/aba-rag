from pathlib import Path 
import re
from loguru import logger
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List

def generar_embeddings(model, textos: List[str]) -> List[List[float]]:
    """Genera embeddings usando el modelo SentenceTransformer dado."""
    return model.encode(textos, normalize_embeddings=True).tolist()

def project_root() -> Path:
    return Path(__file__).resolve().parents[2]

def limpiar_texto(texto: str) -> str:
    """
    Limpieza SUAVE para texto extraído de PDF, pensada para embeddings.
    Objetivo: quitar ruido de extracción SIN perder información técnica.

    Limpieza suave para PDFs (quitar ruido sin destruir semántica, los embeddings (Qwen) entienden tildes, mayúsculas y contexto)
    No queremos destruir esa información. Solo queremos quitar el "ruido de PDF" (guiones partidos, espacios raros).
    """
    if not texto:
        return ""

    #Convertir todos los retornos de carro (\r) en saltos de línea (\n) y los tabs (\t) en espacios.
    t = texto.replace("\r", "\n").replace("\t", " ")

    # Unir palabras cortadas por guion al final de línea:
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)

    # Convertir saltos de línea “sueltos” en espacios (sin cargarse párrafos)
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)

    # Sustituir caracteres como el espacio no separable (\u00A0) por espacios normales.
    t = t.replace("\u00A0", " ")

    #Compactar espacios
    t = re.sub(r"[ ]{2,}", " ", t).strip()

    return t

def hacer_chunking(texto: str, chunk_size=200, overlap=50) -> list:
    """
    Usa LangChain para dividir el texto en chunks.

    args:
        texto: str
        chunk_size: int
        overlap: int
    returns:
        list de chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,      # Tamaño objetivo
        chunk_overlap=overlap,      # Solapamiento para contexto
        length_function=len,        # Cómo medimos (por caracteres)
        separators=["\n\n", "\n", " ", ""] # Prioridad de corte : Párrafos > Líneas > Frases 
    )

    # 2. Ejecutar el corte
    chunks = text_splitter.split_text(texto)
    
    return chunks

def chunk_padre_hijo(texto: str) -> list:
    """
    Crea Pares [Hijo, Texto_Padre]. Lógica "Small-to-Big".
    
    1. Primero cortamos el texto en bloques GRANDES (Padres). Estos tienen el sentido completo.
    2. Luego, cada bloque grande lo volvemos a picar en trozos PEQUEÑOS (Hijos).
    
    ¿Por qué?
    - Los HIJOS son vectores: Muy específicos, fáciles de encontrar por similitud.
    - Los PADRES son contexto: Lo que realmente necesita leer el LLM.
    
    Al final, guardamos el HIJO en la base de datos, pero le metemos una nota 
    en su mochila (metadatos) que contiene el texto del PADRE entero.
    """
    chunks_procesados = []

    chunks_padre = hacer_chunking(texto, chunk_size=2000, overlap=200)
    
    logger.info(f"Generados {len(chunks_padre)} Chunks padre.")
    
    total_hijos = 0

    for i, texto_padre in enumerate(chunks_padre):
        chunks_hijo = hacer_chunking(texto_padre, chunk_size=400, overlap=50)
        total_hijos += len(chunks_hijo)

        for texto_hijo in chunks_hijo:
            chunks_procesados.append({
                "texto_vectorizable": texto_hijo,     
                "texto_completo_padre": texto_padre,  
                "padre_id": i
            })

    logger.info(f"Generados {total_hijos} Chunks hijo.")

    return chunks_procesados