from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import re

# --- FCM V1 DEPENDENCIAS ---
import requests
from google.oauth2 import service_account
import google.auth.transport.requests

# === CONFIGURA AQUÍ TU JSON ===
SERVICE_ACCOUNT_FILE = "bancard-a52ba-579846c6a728.json"
PROJECT_ID = "bancard-a52ba"

MESES = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06',
    'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

def normaliza_fecha(fecha):
    match = re.match(r"(\d{2})-(\d{2})-(\d{4})", fecha)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    match = re.match(r"(\d{2})\s+([a-zA-Z]+)", fecha)
    if match:
        hoy = datetime.now()
        dia = match.group(1)
        mes = MESES.get(match.group(2).lower(), "01")
        return f"{hoy.year}-{mes}-{dia}"
    return fecha

def scrapear_loterias_dominicanas():
    resultados = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto("https://loteriasdominicanas.com/pagina/ultimos-resultados", timeout=60000)
            page.wait_for_selector("div.game-info.p-2", timeout=20000)
            html = page.content()
            with open("debug_loterias.html", "w", encoding="utf-8") as f:
                f.write(html)
            soup = BeautifulSoup(html, 'html.parser')
            juegos = soup.select("div.game-info.p-2")
            for juego in juegos:
                try:
                    fecha_tag = juego.select_one(".session-date")
                    nombre_tag = juego.select_one(".game-title span")
                    numeros_tag = juego.find_next_sibling("div", class_="game-scores")
                    logo_div = juego.select_one("div.game-logo")
                    img_url = ""
                    if logo_div:
                        img_tag = logo_div.find("img")
                        if img_tag:
                            img_url = img_tag.get("src", "") or img_tag.get("data-src", "")
                    if img_url.startswith("/"):
                        img_url = "https://loteriasdominicanas.com" + img_url
                    if not (fecha_tag and nombre_tag and numeros_tag):
                        print("[LoteriasDom] ⛔ Falta dato, se omite.")
                        continue
                    fecha = fecha_tag.get_text(strip=True)
                    fecha_normalizada = normaliza_fecha(fecha)
                    nombre = nombre_tag.get_text(strip=True)
                    numeros = [n.get_text(strip=True) for n in numeros_tag.select("span.score")]
                    print(f"[LoteriasDom] Fecha: {fecha_normalizada} | Lotería: {nombre} | Números: {numeros}")
                    resultados.append({
                        'fuente': 'loteriasdominicanas.com',
                        'loteria': nombre,
                        'img': img_url,
                        'numeros': numeros,
                        'fecha_original': fecha,
                        'fecha': fecha_normalizada,
                        'hora_scrapeo': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Exception as e:
                    print(f"[LoteriasDom] Error juego: {e}")
                    continue
            browser.close()
    except Exception as e:
        print(f"❌ Error al scrapear loteriasdominicanas.com: {e}")
    return resultados

def scrapear_tusnumerosrd():
    resultados = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto("https://www.tusnumerosrd.com/resultados.php", timeout=60000)
            page.wait_for_timeout(9000)
            html = page.content()
            with open("debug_tusnumerosrd.html", "w", encoding="utf-8") as f:
                f.write(html)
            soup = BeautifulSoup(html, 'html.parser')
            filas = soup.select("tr")
            for fila in filas:
                try:
                    nombre_tag = fila.select_one("h6.mb-0")
                    if not nombre_tag:
                        continue
                    nombre = nombre_tag.get_text(strip=True)
                    img_tag = fila.select_one("img")
                    img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""
                    if img_url and img_url.startswith('/'):
                        img_url = "https://www.tusnumerosrd.com" + img_url
                    numeros = [n.get_text(strip=True) for n in fila.select("div.badge.badge-primary.badge-dot")]
                    fecha_tag = fila.select_one("span.table-inner-text")
                    fecha = fecha_tag.get_text(strip=True) if fecha_tag else "Fecha no encontrada"
                    fecha_normalizada = normaliza_fecha(fecha)
                    celdas = fila.find_all("td", class_="text-center")
                    hora = celdas[-1].get_text(strip=True) if celdas else "Hora no encontrada"
                    print(f"[TusNumerosRD] Fecha: {fecha_normalizada} | Lotería: {nombre} | Números: {numeros}")
                    if nombre and numeros:
                        resultados.append({
                            'fuente': 'tusnumerosrd.com',
                            'loteria': nombre,
                            'img': img_url,
                            'numeros': numeros,
                            'fecha_original': fecha,
                            'fecha': fecha_normalizada,
                            'hora': hora,
                            'hora_scrapeo': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                except Exception as e:
                    print(f"[TusNumerosRD] Error fila: {e}")
                    continue
            browser.close()
    except Exception as e:
        print(f"❌ Error al scrapear tusnumerosrd.com: {e}")
    return resultados

def cargar_historico(path="resultados_combinados.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def evitar_duplicados(resultados_viejos, nuevos):
    existentes = set(
        (r['loteria'], tuple(r['numeros']), r['fecha']) for r in resultados_viejos
    )
    no_duplicados = []
    for r in nuevos:
        clave = (r['loteria'], tuple(r['numeros']), r['fecha'])
        if clave not in existentes:
            no_duplicados.append(r)
    return resultados_viejos + no_duplicados

# ========== FUNCION FCM V1 ==========
def enviar_fcm_v1(title, body, topic="resultados_loteria"):
    SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    access_token = credentials.token

    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
    message = {
        "message": {
            "topic": topic,
            "notification": {
                "title": title,
                "body": body
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }

    response = requests.post(url, headers=headers, data=json.dumps(message))
    if response.status_code == 200:
        print("✅ Notificación enviada exitosamente por FCM v1.")
    else:
        print(f"❌ Error enviando notificación FCM v1: {response.status_code} - {response.text}")

# ========== MAIN ==========

def main():
    print("🔍 Buscando en loteriasdominicanas.com...")
    resultados_ld = scrapear_loterias_dominicanas()
    print(f"✅ {len(resultados_ld)} resultados encontrados en loteriasdominicanas.com")

    print("🔍 Buscando en tusnumerosrd.com...")
    resultados_tn = scrapear_tusnumerosrd()
    print(f"✅ {len(resultados_tn)} resultados encontrados en tusnumerosrd.com")

    nuevos_resultados = resultados_ld + resultados_tn

    if nuevos_resultados:
        historico = cargar_historico()
        resultados_actualizados = evitar_duplicados(historico, nuevos_resultados)
        nuevos_agregados = len(resultados_actualizados) - len(historico)
        with open("resultados_combinados.json", "w", encoding="utf-8") as f:
            json.dump(resultados_actualizados, f, indent=4, ensure_ascii=False)
        print(f"📦 Se guardaron {len(resultados_actualizados)} resultados en 'resultados_combinados.json'")
        print(f"➕ Nuevos resultados agregados: {nuevos_agregados}")

        # Envia FCM solo si hubo resultados nuevos
        if nuevos_agregados > 0:
            enviar_fcm_v1(
                "¡Nuevos Resultados de Lotería!",
                f"Se agregaron {nuevos_agregados} nuevos resultados. Abre tu app para verlos."
            )
    else:
        print("⚠️ No se pudo extraer ningún resultado de ninguna fuente.")

if __name__ == "__main__":
    main()
