from api.api import ejecutar_api
from loguru import logger
import multiprocessing
import subprocess
import sys
import time
from pathlib import Path

def main():
    logger.info("Iniciando aplicación RAG...")
    proceso_api = multiprocessing.Process(target=ejecutar_api, daemon=False)
    proceso_api.start()
    logger.info("Esperando a que la API inicie servicios (15s)...")
    time.sleep(15)
    try:
        logger.info("Lanzando interfaz de Streamlit...")
        interfaz_path = Path(__file__).parent / "ui" / "interfaz.py"
        cmd = [sys.executable, "-m", "streamlit", "run", str(interfaz_path)]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        logger.info("Interrupción de usuario detectada.")
    except Exception as e:
        logger.error(f"Error en el lanzador: {e}")
    finally:
        logger.info("Cerrando procesos...")
        if proceso_api.is_alive():
            proceso_api.terminate()
            proceso_api.join()
        logger.info("Aplicación finalizada.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()