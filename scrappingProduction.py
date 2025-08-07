import requests
from bs4 import BeautifulSoup
import json
import certifi
import os
from datetime import datetime

URL = 'https://tusnumerosrd.com/'
ARCHIVO_JSON = "resultados.json"

def obtener_html(url):
    try:
        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[{datetime.now()}] Error al descargar página: {e}")
        return None


def scrapear_resultados(html):
    soup = BeautifulSoup(html, 'html.parser')
    resultados = []
    for fila in soup.find_all('tr'):
        nombre_tag = fila.find('h6')
        if not nombre_tag:
            continue
        nombre = nombre_tag.text.strip()

        numeros = [div.text.strip() for div in fila.find_all('div', class_='badge-dot')]

        fecha_tag = fila.find('span', class_='table-inner-text')
        fecha = fecha_tag.text.strip() if fecha_tag else None

        tds = fila.find_all('td')
        hora = None
        if tds:
            for td in tds:
                if td.text and ':' in td.text:
                    hora = td.text.strip()
                    break

        if not (nombre and numeros and fecha and hora):
            # Salta resultados incompletos
            continue

        resultados.append({
            'loteria': nombre,
            'numeros': numeros,
            'fecha': fecha,
            'hora': hora
        })
    return resultados

def cargar_historico(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def guardar_historico(path, resultados):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

def clave_resultado(res):
    return (res['loteria'], res['fecha'], res['hora'])

def main():
    html = obtener_html(URL)
    if html is None:
        print("No se pudo scrapear.")
        return

    nuevos = scrapear_resultados(html)
    historico = cargar_historico(ARCHIVO_JSON)

    # Convertimos a set para buscar duplicados fácil
    claves_existentes = set(clave_resultado(r) for r in historico)
    nuevos_unicos = [r for r in nuevos if clave_resultado(r) not in claves_existentes]

    if nuevos_unicos:
        historico.extend(nuevos_unicos)
        guardar_historico(ARCHIVO_JSON, historico)
        print(f"✅ Agregados {len(nuevos_unicos)} resultados nuevos al histórico.")
    else:
        print("Sin resultados nuevos.")

    # Muestra los últimos 5 resultados como ejemplo
    print("Últimos 5 resultados:")
    for r in historico[-5:]:
        print(r)

if __name__ == "__main__":
    main()
