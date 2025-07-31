from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime

def scrapear_loterias_dominicanas():
    resultados = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://loteriasdominicanas.com/pagina/ultimos-resultados", timeout=60000)
            page.wait_for_timeout(10000)

            soup = BeautifulSoup(page.content(), 'html.parser')
            juegos = soup.select("div.game-info.p-2")

            for juego in juegos:
                fecha_tag = juego.select_one(".session-date")
                nombre_tag = juego.select_one(".game-title span")
                numeros_tag = juego.find_next("div", class_="game-scores")

                # Mejorado: busca img en todo el bloque y soporta data-src
                img_tag = juego.find("img")
                img_url = ""
                if img_tag:
                    img_url = img_tag.get("src", "") or img_tag.get("data-src", "")
                    if img_url and img_url.startswith('/'):
                        img_url = "https://loteriasdominicanas.com" + img_url

                if not (fecha_tag and nombre_tag and numeros_tag):
                    continue

                fecha = fecha_tag.get_text(strip=True)
                nombre = nombre_tag.get_text(strip=True)
                numeros = [n.get_text(strip=True) for n in numeros_tag.select("span.score")]

                resultados.append({
                    'fuente': 'loteriasdominicanas.com',
                    'loteria': nombre,
                    'img': img_url,
                    'numeros': numeros,
                    'fecha': fecha,
                    'hora_scrapeo': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

            browser.close()
    except Exception as e:
        print(f"❌ Error al scrapear loteriasdominicanas.com: {e}")
    return resultados

def scrapear_tusnumerosrd():
    resultados = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.tusnumerosrd.com/resultados.php", timeout=60000)
            page.wait_for_timeout(7000)

            soup = BeautifulSoup(page.content(), 'html.parser')
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
                    fecha = fila.select("span.table-inner-text")
                    fecha_texto = fecha[-1].get_text(strip=True) if fecha else "Fecha no encontrada"
                    hora_tag = fila.select("td.text-center")
                    hora = hora_tag[-1].get_text(strip=True) if hora_tag else "Hora no encontrada"

                    if nombre and numeros:
                        resultados.append({
                            'fuente': 'tusnumerosrd.com',
                            'loteria': nombre,
                            'img': img_url,
                            'numeros': numeros,
                            'fecha': fecha_texto,
                            'hora': hora,
                            'hora_scrapeo': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                except Exception as e:
                    print(f"Error fila tusnumerosrd: {e}")
                    continue

            browser.close()
    except Exception as e:
        print(f"❌ Error al scrapear tusnumerosrd.com: {e}")
    return resultados

def main():
    resultados = []

    print("🔍 Buscando en loteriasdominicanas.com...")
    resultados_ld = scrapear_loterias_dominicanas()
    if resultados_ld:
        print(f"✅ {len(resultados_ld)} resultados encontrados en loteriasdominicanas.com")
        resultados.extend(resultados_ld)

    print("🔍 Buscando en tusnumerosrd.com...")
    resultados_tn = scrapear_tusnumerosrd()
    if resultados_tn:
        print(f"✅ {len(resultados_tn)} resultados encontrados en tusnumerosrd.com")
        resultados.extend(resultados_tn)

    if resultados:
        with open("resultados_combinados.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=4, ensure_ascii=False)
        print(f"📦 Se guardaron {len(resultados)} resultados en 'resultados_combinados.json'")
    else:
        print("⚠️ No se pudo extraer ningún resultado de ninguna fuente.")

if __name__ == "__main__":
    main()
