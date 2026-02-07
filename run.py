import subprocess
import time
import sys
import os
import urllib.request
import urllib.error
from pathlib import Path
from loguru import logger

# Ejecutar siempre desde la raíz del proyecto (donde está run.py)
PROJECT_ROOT = Path(__file__).resolve().parent
if os.getcwd() != str(PROJECT_ROOT):
    os.chdir(PROJECT_ROOT)
    logger.info(f"Cambiado al directorio del proyecto: {PROJECT_ROOT}")

API_URL = "http://127.0.0.1:8000"
HEALTH_URL = f"{API_URL}/health"
POLL_INTERVAL = 2
MAX_WAIT = 300  # 5 minutos máximo

def wait_for_api():
    """Espera a que la API responda en /health antes de continuar."""
    logger.info("Esperando a que la API esté lista (modelos cargados)...")
    start = time.monotonic()
    while (time.monotonic() - start) < MAX_WAIT:
        try:
            req = urllib.request.Request(HEALTH_URL)
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status == 200:
                    logger.info("API lista.")
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(POLL_INTERVAL)
    logger.error("Timeout: la API no respondió a tiempo.")
    return False

def start():
    # 1. Arrancar FastAPI en segundo plano
    logger.info("Iniciando API de Bizkaia (FastAPI)...")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "src.api.api:app", 
        "--host", "127.0.0.1", "--port", "8000"
    ])

    # 2. Esperar a que la API (y los modelos) esté lista
    if not wait_for_api():
        api_process.terminate()
        sys.exit(1)

    # 3. Arrancar Streamlit
    logger.info("Iniciando Interfaz (Streamlit)...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "src/ui/interfaz.py"])
    except KeyboardInterrupt:
        logger.info("Cerrando servicios...")
    finally:
        api_process.terminate()
        logger.info("Procesos finalizados.")

if __name__ == "__main__":
    start()