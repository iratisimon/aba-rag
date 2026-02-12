import umap
import numpy as np
from tqdm import tqdm
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from loguru import logger
import os
import chromadb
import utils
from dotenv import load_dotenv

# Configuración básica (si se ejecuta directo)
load_dotenv()

def visualizar_umap(collections, n_components=3, color_por="categoria"):
    """
    Proyecta y visualiza embeddings desde una colección ChromaDB con UMAP.

    Args:
        collections: lista de colecciones de ChromaDB cargada
        n_components: dimensiones UMAP (2D o 3D)
        color_por: metadato usado para colorear puntos (ej: "categoria")
    """
    logger.info(f"Aplicando UMAP para visualización (coloreado por '{color_por}')...")

    # Obtener embeddings y metadatos
    # OJO: Sacar TODOS puede ser lento si hay millones. Para demo está bien.
    logger.info("Obteniendo embeddings y metadatos...")
    collection_pdfs = collections[0]
    collection_imagenes = collections[1]
    try:
        results_pdfs = collection_pdfs.get(include=["embeddings", "metadatas"])
        embeddings_pdfs = results_pdfs["embeddings"]
        metadatas_pdfs = results_pdfs["metadatas"]

        results_imagenes = collection_imagenes.get(include=["embeddings", "metadatas"])
        embeddings_imagenes = results_imagenes["embeddings"]
        metadatas_imagenes = results_imagenes["metadatas"]

        logger.info(f"Obtenidos {len(embeddings_pdfs)} embeddings y {len(metadatas_pdfs)} metadatos.")
        logger.info(f"Obtenidos {len(embeddings_imagenes)} embeddings y {len(metadatas_imagenes)} metadatos.")
        if len(embeddings_pdfs) == 0 or len(embeddings_imagenes) == 0:
            logger.error(f"Error al obtener datos de las colecciones: {collection_pdfs}, {collection_imagenes}")
            return


    except Exception as e:
        logger.error(f"Error al obtener embeddings y metadatos: {e}")
        return

    # 1. Crear el reductor UMAP
    umap_model = umap.UMAP(
         n_components=3,      # Reducir a 3D para visualizar
         n_neighbors=15,      # Cuántos vecinos considerar (más = más global)
         min_dist=0.1,        # Separación mínima entre puntos (más = más disperso)
         metric='cosine',     # Métrica (cosine es ideal para embeddings de texto)
         random_state=42      # Para reproducibilidad
    )

    logger.info(f"Entrenando UMAP con {len(embeddings_pdfs)} y {len(embeddings_imagenes)} vectores...")
    
    # Proyectar
    # Convertir embeddings a numpy array (UMAP espera arrays) - matriz Numpy 2D
    embedding_matrix_pdfs = np.array(embeddings_pdfs)
    embedding_matrix_imagenes = np.array(embeddings_imagenes)
    if len(embedding_matrix_pdfs) < 5 or len(embedding_matrix_imagenes) < 5:
         logger.warning("Muy pocos datos para UMAP (necesitamos al menos 5-10 chunks).")
         return

    proyected_3d_pdfs = umap_model.fit_transform(embedding_matrix_pdfs)
    proyected_3d_imagenes = umap_model.fit_transform(embedding_matrix_imagenes)

    # 3. Preparar Etiquetas
    labels_pdfs = []
    for m in metadatas_pdfs:
        val = m.get("categoria") or m.get("category") or "N/A"
        if color_por == 'source':
            labels_pdfs.append(os.path.basename(str(val)))
        else:
            labels_pdfs.append(val)

    labels_imagenes = []
    for m in metadatas_imagenes:
        val = m.get("categoria") or m.get("category") or "N/A"
        if color_por == 'source':
            labels_imagenes.append(os.path.basename(str(val)))
        else:
            labels_imagenes.append(val)

    # Definir etiquetas únicas para iteración sin romper el masking
    unique_labels_pdfs = list(dict.fromkeys(labels_pdfs))
    unique_labels_imagenes = list(dict.fromkeys(labels_imagenes))

    # 4. Crear Subplots con tipos de escena diferentes
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "xy"}, {"type": "scene"}],
               [{"type": "xy"}, {"type": "scene"}]], # xy = 2D, scene = 3D
        subplot_titles=("Proyección UMAP 2D", "Proyección UMAP 3D")
    )

    # Colores: Plotly Express genera colores auto, aquí lo haremos manual para que coincidan
    all_unique_labels = sorted(list(set(labels_pdfs) | set(labels_imagenes)))
    colors = px.colors.qualitative.Plotly
    color_map = {label: colors[i % len(colors)] for i, label in enumerate(all_unique_labels)}
    
    labels_in_legend = set()

    for label in unique_labels_pdfs:
        mask = [l == label for l in labels_pdfs]
        
        # Añadir a Scatter 2D (Columna 1)
        show_this_legend = label not in labels_in_legend
        if show_this_legend:
            labels_in_legend.add(label)

        fig.add_trace(
            go.Scatter(
                x=proyected_3d_pdfs[mask, 0], y=proyected_3d_pdfs[mask, 1],
                mode='markers', name=label, marker=dict(color=color_map.get(label, "grey"), size=6),
                legendgroup=label, showlegend=show_this_legend
            ), row=1, col=1
        )

        # Añadir a Scatter 3D (Columna 2)
        fig.add_trace(
            go.Scatter3d(
                x=proyected_3d_pdfs[mask, 0], y=proyected_3d_pdfs[mask, 1], z=proyected_3d_pdfs[mask, 2],
                mode='markers', name=label, marker=dict(color=color_map.get(label, "grey"), size=4),
                legendgroup=label, showlegend=False
            ), row=1, col=2
        )

    for label in unique_labels_imagenes:
        mask = [l == label for l in labels_imagenes]
        
        # Añadir a Scatter 2D (Columna 1)
        show_this_legend = label not in labels_in_legend
        if show_this_legend:
            labels_in_legend.add(label)

        fig.add_trace(
            go.Scatter(
                x=proyected_3d_imagenes[mask, 0], y=proyected_3d_imagenes[mask, 1],
                mode='markers', name=label, marker=dict(color=color_map.get(label, "grey"), size=6),
                legendgroup=label, showlegend=show_this_legend
            ), row=2, col=1
        )

        # Añadir a Scatter 3D (Columna 2)
        fig.add_trace(
            go.Scatter3d(
                x=proyected_3d_imagenes[mask, 0], y=proyected_3d_imagenes[mask, 1], z=proyected_3d_imagenes[mask, 2],
                mode='markers', name=label, marker=dict(color=color_map.get(label, "grey"), size=4),
                legendgroup=label, showlegend=False
            ), row=2, col=2
        )

    fig.update_layout(height=600, title_text=f"Análisis Espacial de Embeddings por {color_por}")
    fig.show()

    try:
        #guardar el html en el directorio base del proyecto
        ruta_archivo = os.path.abspath(__file__)
        ruta_proyecto = os.path.dirname(os.path.dirname(os.path.dirname(ruta_archivo)))
        output_dir = os.path.join(ruta_proyecto, "visualizaciones_umap")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Carpeta creada: {output_dir}")

        output_path = os.path.join(output_dir, f"umap_ABA_{n_components}d_{color_por}.html")
        fig.write_html(
            output_path,
            full_html=True
        )
        logger.info(f"Visualización guardada en: {output_path}")
    except Exception as e:
        logger.error(f"Error al guardar la visualización: {e}")

def main():
    DB_DIR = os.getenv("DB_PATH")
    COLLECTION_NAME_PDFS = os.getenv("COLLECTION_NAME_PDFS")
    COLLECTION_NAME_IMAGENES = os.getenv("COLLECTION_NAME_IMAGENES")
    
    if not os.path.exists(DB_DIR):
        print(f"No existe la base de datos en {DB_DIR}.")
        return

    print("Conectando a ChromaDB...")
    client_db = chromadb.PersistentClient(path=DB_DIR)
    collection_pdfs = client_db.get_collection(name=COLLECTION_NAME_PDFS)
    collection_imagenes = client_db.get_collection(name=COLLECTION_NAME_IMAGENES)
    
    count_pdfs = collection_pdfs.count()
    count_imagenes = collection_imagenes.count()
    print(f"Colección cargada con {count_pdfs} chunks de PDFs y {count_imagenes} chunks de imágenes.")
    
    if count_pdfs == 0 and count_imagenes == 0:
        return
    
    visualizar_umap([collection_pdfs, collection_imagenes], color_por="categoria")

if __name__ == "__main__":
    main()
