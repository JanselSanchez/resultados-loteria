from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

def scrapear_loterias_dominicanas():
    resultados = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Cambia a True si ya todo funciona
            page = browser.new_page()
            page.goto("https://loteriasdominicanas.com/pagina/ultimos-resultados", timeout=60000)
            page.wait_for_selector("div.game-info.p-2", timeout=20000)
            
            # Guarda el HTML para debug si hay errores visuales
            with open("debug_loterias.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            juegos = soup.select("div.game-info.p-2")

            for juego in juegos:
                fecha_tag = juego.select_one(".session-date")
                nombre_tag = juego.select_one(".game-title span")
                numeros_tag = juego.find_next("div", class_="game-scores")

                # SOLO el logo real de la lotería
                logo_div = juego.select_one("div.game-logo")
                img_url = ""
                if logo_div:
                    img_tag = logo_div.find("img")
                    if img_tag:
                        img_url = img_tag.get("src", "") or img_tag.get("data-src", "")
                else:
                    # Fallback para imágenes reales pero ignora estadísticas
                    for img_tag in juego.find_all("img"):
                        img_src = img_tag.get("src", "") or img_tag.get("data-src", "")
                        if "ex_stats" not in img_src and img_src.strip() != "":
                            img_url = img_src
                            break

                if img_url.startswith("/"):
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
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto("https://www.tusnumerosrd.com/resultados.php", timeout=60000)
            page.wait_for_timeout(7000)

            with open("debug_tusnumerosrd.html", "w", encoding="utf-8") as f:
                f.write(page.content())

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
        # Unimos evitando duplicados por loteria, numeros y fecha
        resultados_actualizados = evitar_duplicados(historico, nuevos_resultados)
        with open("resultados_combinados.json", "w", encoding="utf-8") as f:
            json.dump(resultados_actualizados, f, indent=4, ensure_ascii=False)
        print(f"📦 Se guardaron {len(resultados_actualizados)} resultados en 'resultados_combinados.json'")
    else:
        print("⚠️ No se pudo extraer ningún resultado de ninguna fuente.")

if __name__ == "__main__":
    main()
