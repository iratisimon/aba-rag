"""
Este script contiene las funciones relacionadas con la base de datos.
Utiliza ChromaDB como base de datos.
"""

import chromadb
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from PIL import Image
import torch
from sentence_transformers import SentenceTransformer, util
#from utilidades import utils
import utils
import os
from loguru import logger
import json
#from utilidades.funciones_preprocesado import leer_pdf
from funciones_preprocesado import leer_pdf
import traceback
import uuid

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
COLLECTION_NAME_PDFS = os.getenv("COLLECTION_NAME_PDFS")
COLLECTION_NAME_IMAGENES = os.getenv("COLLECTION_NAME_IMAGENES")
MODELO_EMBEDDINGS = os.getenv("MODELO_EMBEDDINGS")
MODELO_CLIP = os.getenv("MODELO_CLIP")
PDFS_DIR = utils.project_root() /"data"/"documentos"/"pdfs"

def obtener_coleccion(tipo="pdfs"):
    """
    Obtiene una colección de la base de datos (sin resetear).
    
    Args:
        tipo (str): Tipo de colección. Puede ser "pdfs" o "imagenes".
    
    Returns:
        chromadb.Collection: La colección solicitada.
    """
    client = chromadb.PersistentClient(path=DB_PATH)
    
    if tipo.lower() == "pdfs":
        return client.get_collection(COLLECTION_NAME_PDFS)
    elif tipo.lower() == "imagenes":
        return client.get_collection(COLLECTION_NAME_IMAGENES)
    else:
        raise ValueError(f"Tipo de colección no válido: {tipo}. Use 'pdfs' o 'imagenes'")

def cargar_modelos():
    """Carga todos los modelos de IA necesarios."""
    logger.info("Cargando modelos de IA...")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"   Dispositivo detectado: {device.upper()}")

    # 1. Modelo de Embeddings (Texto)
    logger.info("Cargando Embeddings de Texto...")
    model_emb = SentenceTransformer(MODELO_EMBEDDINGS)

    # 2. Modelo de Visión (CLIP desde SentenceTransformers)
    logger.info("Cargando CLIP (Visión)...")
    model_clip = SentenceTransformer(MODELO_CLIP)
    model_clip.to(device)
    
    
    return model_emb, model_clip, device

def crear_db(reset=False):
    """
    Crea la base de datos de Chroma con dos colecciones (PDFs e imágenes).
    
    Args:
        reset (bool): Si es True, borra las colecciones existentes.
    
    Returns:
        dict: Diccionario con ambas colecciones {'pdfs': collection, 'imagenes': collection}
    """
    client = chromadb.PersistentClient(path=DB_PATH)
    
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME_PDFS)
            logger.info(f"Reset activado. Borrando colección '{COLLECTION_NAME_PDFS}'.")
        except:
            logger.warning(f"No se encontraba la colección '{COLLECTION_NAME_PDFS}'.")
        
        try:
            client.delete_collection(COLLECTION_NAME_IMAGENES)
            logger.info(f"Reset activado. Borrando colección '{COLLECTION_NAME_IMAGENES}'.")
        except:
            logger.warning(f"No se encontraba la colección '{COLLECTION_NAME_IMAGENES}'.")
        
        collection_pdfs = client.create_collection(COLLECTION_NAME_PDFS)
        collection_imagenes = client.create_collection(COLLECTION_NAME_IMAGENES)
    else:
        collection_pdfs = client.get_or_create_collection(COLLECTION_NAME_PDFS)
        collection_imagenes = client.get_or_create_collection(COLLECTION_NAME_IMAGENES)
    
    logger.info(f"Base de datos lista con colecciones: '{COLLECTION_NAME_PDFS}' e '{COLLECTION_NAME_IMAGENES}'")
    
    return {"pdfs": collection_pdfs, "imagenes": collection_imagenes}

def insertar_texto(texto, nombre_pdf, modelo_embeddings, collection):
    """
    Inserta un texto en la base de datos con metadatos del PDF.
    
    Args:
        texto (str): El texto a insertar.
        nombre_pdf (str): El nombre del PDF.
        modelo_embeddings (SentenceTransformer): El modelo de embeddings.
        collection (chromadb.Collection): La colección de la base de datos.
        metadatos_json (dict): Metadatos del JSON de metadata_pdf.json
    """
    if not texto:
        return
    
    texto = utils.limpiar_texto(texto)
    chunks = utils.chunk_padre_hijo(texto)
    
    if not chunks:
        logger.warning(f"No se generaron chunks para {nombre_pdf}")
        return
    
    categoria = "sin_categoria"  # valor por defecto
    try:
        with open("data/metadata_pdf.json", "r", encoding="utf-8") as f:
            metadatos_json = json.load(f)
            for doc in metadatos_json:
                if doc.get("archivo") == nombre_pdf:
                    categoria = doc.get("categoria", "sin_categoria")
                    break
    except FileNotFoundError:
        logger.warning("No se encontró data/metadata_pdf.json, se usará categoria por defecto")
    except json.JSONDecodeError:
        logger.error("Error al parsear metadata_pdf.json, se usará categoria por defecto")

    textos_hijos = [item["texto_vectorizable"] for item in chunks]
    metadatas = []
    ids = []

    # Preparar metadatos para cada chunk (combinando JSON + chunk info)
    for idx, item in enumerate(chunks):
        metadatas.append({
            "source": nombre_pdf,
            "category": categoria,
            "type": "child",
            "parent_id": item["padre_id"],
            "contexto_expandido": item["texto_completo_padre"]
        })
        ids.append(f"{nombre_pdf}_child_{idx}")
            
    # Generar Embeddings (Solo de los HIJOS)
    embeddings = utils.generar_embeddings(modelo_embeddings, textos_hijos)
        
    # Guardar en DB
    try:
        logger.info(f"  Insertando {len(ids)} chunks en ChromaDB...")
        collection.add(
            documents=textos_hijos,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Insertados {len(ids)} chunks de {nombre_pdf}")
    except Exception as e:
        logger.error(f"Error al insertar en ChromaDB: {str(e)}")
        logger.error(traceback.format_exc())

def insertar_imagen(model_clip, model_emb, device, collection):
    try:
        with open("data/metadata_imagenes.json", "r", encoding="utf-8") as f:
            metadata_imagenes = json.load(f)
    except FileNotFoundError:
        logger.warning("No se encontró data/metadata_imagenes.json")

    logger.info(f"Procesando {len(metadata_imagenes)} imágenes desde metadatos")

    for meta in metadata_imagenes:
        try:
            ruta = Path(meta["ruta_imagen"])

            if not ruta.exists():
                logger.warning(f"Imagen no encontrada: {ruta}")
                continue

            image = Image.open(ruta).convert("RGB")

            inputs = model_clip.processor(
                images=image,
                return_tensors="pt"
            ).to(device)

            # Generar feature CLIP
            with torch.no_grad():
                features = model_clip.model.get_image_features(**inputs)
                vector_clip = features[0].cpu().numpy().tolist()

            # Generar embedding final usando tu función
            embedding = utils.generar_embeddings(model_emb, [vector_clip])[0]

            collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[embedding],
                documents=[meta["nombre_archivo"]],
                metadatas=[{
                    "pdf_origen": meta["pdf_origen"],
                    "categoria": meta.get("categoria", "sin_categoria"),
                    "pagina": meta.get("pagina"),
                    "nombre_archivo": meta["nombre_archivo"],
                    "tipo": "imagen"
                }]
            )

        except Exception as e:
            logger.error(
                f"Error procesando imagen {meta.get('nombre_archivo')}: {e}"
            )

def main():
    print("\n RAG MULTIMODAL - CREANDO LA BASE DE DATOS \n")

    #Preguntar si borramos BD --> para ir haciendo pruebas
    resp = input("¿Borrar base de datos y empezar de cero? (s/n): ").lower()
    reset_db = (resp == 's')
    
    # Cargar modelos y crear db
    model_emb, model_clip, device = cargar_modelos()
    collections = crear_db(reset_db)
    
    # Procesar pdfs
    pdfs = list(PDFS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"Error: No hay PDFs en {PDFS_DIR}")
        return
    
    for pdf in pdfs:
        nombrePDF = pdf.name
        logger.info(f"Procesando: {nombrePDF}...")
        try:
            # Usar función de preprocesado
            texto_completo = leer_pdf(str(pdf))
            # Insertar texto
            insertar_texto(texto_completo, nombrePDF, model_emb, collections["pdfs"])
        except Exception as e:
            logger.error(f"Error procesando {nombrePDF}: {e}")
            continue

    
    # Procesar imágenes
    logger.info("\nProcesando imágenes...")
    insertar_imagen(
        model_clip=model_clip,
        device=device,
        model_emb=model_emb,
        collection=collections["imagenes"]
    )
    logger.info("\n PROCESAMIENTO TERMINADO")
    logger.info(f"Base de datos guardada en: {DB_PATH}")


if __name__ == "__main__":
    main()