import chromadb
import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).resolve().parents[2]))

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
COLLECTION_NAME_IMAGENES = os.getenv("COLLECTION_NAME_IMAGENES")

def check_images():
    print(f"--- Diagnóstico de Base de Datos de Imágenes ---")
    print(f"Ruta DB: {DB_PATH}")
    print(f"Colección Objetivo: {COLLECTION_NAME_IMAGENES}")
    
    if not os.path.exists(DB_PATH):
        print("❌ Error: La ruta de la base de datos no existe.")
        return

    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        try:
            collection = client.get_collection(COLLECTION_NAME_IMAGENES)
            count = collection.count()
            print(f"✅ Colección encontrada.")
            print(f"📊 Total de imágenes en la colección: {count}")
            
            if count > 0:
                print("\nMostrando primeros 3 elementos:")
                preview = collection.get(limit=3)
                for i in range(len(preview['ids'])):
                    print(f"  [{i+1}] ID: {preview['ids'][i]}")
                    if preview['metadatas']:
                        print(f"      Metadata: {preview['metadatas'][i]}")
            else:
                print("⚠️ La colección está vacía. Necesitas ejecutar el script de ingestión para añadir imágenes.")
                
        except Exception as e:
            print(f"❌ La colección '{COLLECTION_NAME_IMAGENES}' no existe o no se pudo leer.")
            print(f"Detalle: {e}")
            
    except Exception as e:
        print(f"❌ Error conectando a ChromaDB: {e}")

if __name__ == "__main__":
    check_images()
