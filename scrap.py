import requests
from bs4 import BeautifulSoup
import json
import certifi

url = 'https://loteriasdominicanas.com/pagina/ultimos-resultados'  # Usa https para mayor compatibilidad

# Para pruebas rápidas: ignora la verificación del certificado
response = requests.get(url, verify=False)

soup = BeautifulSoup(response.text, 'html.parser')
resultados = []
ARCHIVO_JSON = "resultados.json"

for fila in soup.find_all('tr'):
    nombre_tag = fila.find('h6')
    if not nombre_tag:
        continue
    nombre = nombre_tag.text.strip()

    numeros = [div.text.strip() for div in fila.find_all('div', class_='badge-dot')]
    
    fecha_tag = fila.find('span', class_='table-inner-text')
    fecha = fecha_tag.text.strip() if fecha_tag else None

    # La hora suele estar en el último <td> (puede cambiar)
    tds = fila.find_all('td')
    hora = None
    if tds:
        for td in tds:
            if td.text and ':' in td.text:
                hora = td.text.strip()
                break

    resultados.append({
        'loteria': nombre,
        'numeros': numeros,
        'fecha': fecha,
        'hora': hora
    })

for resultado in resultados:
    print(resultado)
