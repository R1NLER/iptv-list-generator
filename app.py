import os
from pathlib import Path

from playwright.sync_api import sync_playwright

# URL remota desde la que se descarga la lista M3U. Obligatoria.
URL = os.environ["URL"]
# Texto a buscar para reemplazar. Opcional (por defecto 127.0.0.1:6878).
SEARCH_TEXT = os.getenv("SEARCH_TEXT", "127.0.0.1:6878")
# Texto que sustituirá el valor de SEARCH_TEXT dentro de la lista. Obligatoria.
REPLACE_TEXT = os.environ["REPLACE_TEXT"]
# Ruta donde se guarda la lista final, servida por Nginx en /htdocs.
OUTPUT = Path("/htdocs/lista.m3u")

# Tiempo máximo (ms) de espera a que el Service Worker de IPFS resuelva el
# contenido. La fuente configurada (inbrowser.link) no sirve el archivo por
# HTTP simple: solo lo resuelve un navegador ejecutando su JavaScript, así
# que usamos un Chromium headless real en vez de una petición HTTP directa.
TIMEOUT_MS = 60_000


def _es_lista_valida(contenido: str) -> bool:
    return contenido.lstrip()[:20].upper().startswith("#EXTM3U")


def obtener_contenido_m3u(url: str) -> str:
    """Abre la URL en un Chromium headless (para que el Service Worker de
    IPFS se ejecute igual que en un navegador real) y devuelve el
    contenido de la lista m3u, ya sea capturando una descarga de archivo
    o leyendo el texto resultante en la página."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        contexto = browser.new_context(accept_downloads=True)
        pagina = contexto.new_page()

        contenido = None

        try:
            with pagina.expect_download(timeout=TIMEOUT_MS) as info_descarga:
                pagina.goto(url, timeout=TIMEOUT_MS, wait_until="commit")
            descarga = info_descarga.value
            ruta_temp = "/tmp/lista_descargada.m3u"
            descarga.save_as(ruta_temp)
            contenido = Path(ruta_temp).read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Sin descarga automática ({e}); probando leer la página...")

        if contenido is None or not _es_lista_valida(contenido):
            try:
                if pagina.url != url:
                    pagina.goto(url, timeout=TIMEOUT_MS, wait_until="networkidle")
                else:
                    pagina.wait_for_load_state("networkidle", timeout=TIMEOUT_MS)
                pagina.wait_for_function(
                    "document.body && document.body.innerText && "
                    "document.body.innerText.trim().toUpperCase().startsWith('#EXTM3U')",
                    timeout=TIMEOUT_MS,
                )
                contenido = pagina.inner_text("body")
            except Exception as e:
                print(f"Tampoco se pudo leer el contenido de la página: {e}")

        browser.close()

        if contenido is None or not _es_lista_valida(contenido):
            raise RuntimeError("No se obtuvo una lista m3u válida.")

        return contenido


def main():
    print(f"Descargando lista desde: {URL}")
    try:
        contenido = obtener_contenido_m3u(URL)
    except Exception as e:
        print(f"Error descargando lista: {e}")
        return 1

    data = contenido.replace(SEARCH_TEXT, REPLACE_TEXT)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(data, encoding="utf-8")
    print(f"Lista actualizada en {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())