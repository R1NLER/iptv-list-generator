import os
import urllib.request
from pathlib import Path

# La url definida en el .env
URL = os.environ["URL"]
# Se busca el texto SEARCH_TEXT si es definido en el .env, si no se usa un valor por defecto (127.0.0.1:6878) suele ser el valor usado para listas de IPTV que usan Acestream
SEARCH_TEXT = os.getenv("SEARCH_TEXT", "127.0.0.1:6878")
# Se reemplaza por el definido en el .env para ajustarlo a las necesidades de usuario.
REPLACE_TEXT = os.environ["REPLACE_TEXT"]
# Ruta dentro del contenedor donde se guarda la lista creada, se publicará por NGINX en el puerto 80 del contenedor.
OUTPUT = Path("/htdocs/lista.m3u")


def main():
    """ 
        Función principal que descarga la lista, reemplaza el texto y guarda el resultado en un archivo.
            - Descarga la lista desde la URL definida usando urllib.request con un User-Agent personalizado.
            - Reemplaza el texto SEARCH_TEXT por REPLACE_TEXT en el contenido descargado.
            - Guarda el resultado en OUTPUT, creando los directorios necesarios si no existen.
            - Imprime un mensaje de éxito o error según corresponda.

    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    req = urllib.request.Request(URL, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Error descargando lista: {e}")
        return 1

    data = content.replace(SEARCH_TEXT, REPLACE_TEXT)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(data, encoding="utf-8")

    print(f"Lista actualizada en {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())