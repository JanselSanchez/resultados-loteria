import requests
from bs4 import BeautifulSoup

def main():
    url = "https://loteriasdominicanas.com/pagina/ultimos-resultados"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, verify=False)
    except requests.exceptions.SSLError as e:
        print("❌ Error SSL:", e)
        return


    soup = BeautifulSoup(response.text, "html.parser")
    bloques = soup.select("div.card")

    if not bloques:
        print("⚠️ La página se cargó, pero no se encontraron resultados.")
        return

    for bloque in bloques:
        nombre_loteria_tag = bloque.select_one("h6")
        nombre_sorteo_tag = bloque.select_one(".text-warning")
        fecha_tag = bloque.select_one(".table-inner-text")
        numeros_tags = bloque.select("span.badge.bg-primary.rounded-pill")

        if not nombre_loteria_tag or not nombre_sorteo_tag or not numeros_tags:
            continue

        nombre_loteria = nombre_loteria_tag.get_text(strip=True)
        nombre_sorteo = nombre_sorteo_tag.get_text(strip=True)
        numeros = [n.get_text(strip=True) for n in numeros_tags]
        fecha = fecha_tag.get_text(strip=True) if fecha_tag else "Fecha no encontrada"
        hora = ''  # No se muestra hora en la web, puedes dejarlo vacío o estimar

        print("🎰 Lotería:", nombre_loteria)
        print("📛 Sorteo :", nombre_sorteo)
        print("🔢 Números:", ", ".join(numeros))
        print("📅 Fecha  :", fecha)
        print("🕒 Hora   :", hora if hora else "No especificada")
        print("-" * 40)

if __name__ == "__main__":
    
    main()
