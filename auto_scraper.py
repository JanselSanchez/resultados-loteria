import subprocess
import time
from datetime import datetime
import os
import sys

# CONFIGURA AQUÍ
REPO_PATH = r"C:\Users\jansel.sanchez\resultados-loteria"
SCRAPER_FILE = "scraper_playwright.py"  # Nombre de tu script

# PRIMERO PRUEBA "python", LUEGO "py", SI NO FUNCIONA, USA RUTA COMPLETA A python.exe
SCRAPER_COMMAND = ["python", SCRAPER_FILE]
# Ejemplo si tienes que especificar el path:
# SCRAPER_COMMAND = [r"C:\Users\jansel.sanchez\AppData\Local\Programs\Python\Python313\python.exe", SCRAPER_FILE]

BRANCH = "main"  # O "master" o tu rama

def check_setup():
    if not os.path.exists(REPO_PATH):
        print(f"❌ ERROR: La ruta {REPO_PATH} no existe.")
        sys.exit(1)
    if not os.path.isdir(REPO_PATH):
        print(f"❌ ERROR: {REPO_PATH} no es un directorio.")
        sys.exit(1)
    script_path = os.path.join(REPO_PATH, SCRAPER_FILE)
    if not os.path.isfile(script_path):
        print(f"❌ ERROR: {script_path} no existe.")
        sys.exit(1)

def run_scraper():
    print(f"[{datetime.now()}] Ejecutando scraper...")
    result = subprocess.run(SCRAPER_COMMAND, cwd=REPO_PATH)
    if result.returncode != 0:
        print(f"❌ Error ejecutando {SCRAPER_FILE}. Código: {result.returncode}")

def git_push():
    print(f"[{datetime.now()}] Haciendo push a git...")
    subprocess.run(["git", "add", "."], cwd=REPO_PATH)
    commit_msg = f"Auto update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_PATH)
    subprocess.run(["git", "push", "origin", BRANCH], cwd=REPO_PATH)

def cambios_para_subir():
    res = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_PATH, capture_output=True, text=True)
    return len(res.stdout.strip()) > 0

if __name__ == "__main__":
    print("Automatizador corriendo cada 40 minutos. Ctrl+C para salir.")
    check_setup()
    while True:
        run_scraper()
        if cambios_para_subir():
            git_push()
        else:
            print(f"[{datetime.now()}] No hay cambios para subir.")
        print("Esperando 40 minutos...\n")
        time.sleep(40 * 60)
