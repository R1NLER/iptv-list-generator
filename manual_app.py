import json
import os
import uuid
from pathlib import Path
from html import escape

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

# Host:puerto usado para construir la URL de stream, mismo valor que usa
# app.py para sustituir SEARCH_TEXT en la lista principal.
REPLACE_TEXT = os.environ["REPLACE_TEXT"]

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
DATA_FILE = DATA_DIR / "channels.json"
OUTPUT = Path("/htdocs/emergency.m3u")

app = FastAPI()


def _cargar_canales() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _guardar_canales(canales: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(canales, ensure_ascii=False, indent=2), encoding="utf-8")


def _regenerar_m3u(canales: list[dict]) -> None:
    """Genera emergency.m3u: solo canales, sin grupos."""
    lineas = ["#EXTM3U"]
    for canal in canales:
        lineas.append(f"#EXTINF:-1,{canal['name']}")
        lineas.append(f"http://{REPLACE_TEXT}/ace/getstream?id={canal['hash']}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def _render_pagina(canales: list[dict]) -> str:
    filas = ""
    for canal in canales:
        filas += f"""
        <tr>
          <form method="post" action="/manual/edit/{canal['id']}">
            <td><input name="name" value="{escape(canal['name'])}" required></td>
            <td><input name="hash" value="{escape(canal['hash'])}" required></td>
            <td class="acciones">
              <button type="submit" class="btn btn-guardar">Guardar</button>
              <button type="submit" class="btn btn-eliminar" formaction="/manual/delete/{canal['id']}"
                      formnovalidate onclick="return confirm('¿Eliminar este canal?')">Eliminar</button>
            </td>
          </form>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lista de emergencia</title>
  <style>
    :root {{
      --bg: #0f1420;
      --panel: #1a2233;
      --panel-2: #212b40;
      --border: #2c3752;
      --text: #e6e9f0;
      --muted: #92a0b8;
      --accent: #4f8cff;
      --accent-2: #3b6fd6;
      --danger: #e05263;
      --danger-2: #c23f4e;
      --radius: 10px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "Segoe UI", Roboto, system-ui, sans-serif;
      background: linear-gradient(180deg, var(--bg), #0b0f18 60%);
      color: var(--text);
      max-width: 860px;
      margin: 0 auto;
      padding: 2.5rem 1.25rem 4rem;
    }}
    header {{ margin-bottom: 2rem; }}
    h1 {{ font-size: 1.6rem; margin: 0 0 .25rem; }}
    h1 .badge {{
      display: inline-block; font-size: .7rem; font-weight: 600;
      color: var(--accent); background: rgba(79,140,255,.12);
      border: 1px solid rgba(79,140,255,.35); border-radius: 999px;
      padding: .15rem .6rem; margin-left: .5rem; vertical-align: middle;
    }}
    header p {{ color: var(--muted); margin: 0; font-size: .9rem; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.75rem;
      box-shadow: 0 4px 18px rgba(0,0,0,.25);
    }}
    .panel h2 {{
      font-size: 1rem; text-transform: uppercase; letter-spacing: .04em;
      color: var(--muted); margin: 0 0 1rem;
    }}
    .fila-add {{ display: grid; grid-template-columns: 1fr 1fr auto; gap: .75rem; align-items: end; }}
    label {{ display: block; font-size: .78rem; color: var(--muted); margin-bottom: .3rem; }}
    input {{
      width: 100%; padding: .55rem .7rem; border-radius: 8px;
      border: 1px solid var(--border); background: var(--panel-2);
      color: var(--text); font-size: .9rem;
    }}
    input:focus {{ outline: none; border-color: var(--accent); }}
    .btn {{
      cursor: pointer; border: none; border-radius: 8px; padding: .55rem 1rem;
      font-size: .85rem; font-weight: 600; transition: filter .15s ease; white-space: nowrap;
    }}
    .btn:hover {{ filter: brightness(1.12); }}
    .btn-add, .btn-guardar {{ background: var(--accent); color: #fff; }}
    .btn-add:hover, .btn-guardar:hover {{ background: var(--accent-2); }}
    .btn-eliminar {{ background: transparent; color: var(--danger); border: 1px solid var(--danger); }}
    .btn-eliminar:hover {{ background: var(--danger); color: #fff; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
      text-align: left; font-size: .75rem; text-transform: uppercase;
      color: var(--muted); font-weight: 600; padding: .5rem .4rem;
      border-bottom: 1px solid var(--border);
    }}
    td {{ padding: .5rem .4rem; border-bottom: 1px solid var(--border); }}
    tr:last-child td {{ border-bottom: none; }}
    td.acciones {{ display: flex; gap: .5rem; white-space: nowrap; }}
    form {{ display: contents; }}
    .vacio {{ color: var(--muted); font-style: italic; padding: 1rem .4rem; }}
  </style>
</head>
<body>
  <header>
    <h1>Lista de emergencia <span class="badge">emergency.m3u</span></h1>
    <p>Gestiona los canales que se generan en /emergency.m3u</p>
  </header>

  <section class="panel">
    <h2>Añadir canal</h2>
    <form method="post" action="/manual/add" class="fila-add">
      <div>
        <label>Nombre del canal</label>
        <input name="name" placeholder="Ej. DAZN 1 FHD" required>
      </div>
      <div>
        <label>Hash</label>
        <input name="hash" placeholder="Ej. 691739972eb3468cf16b25e84dafdeaa40dead6d" required>
      </div>
      <button type="submit" class="btn btn-add">Añadir</button>
    </form>
  </section>

  <section class="panel">
    <h2>Canales ({len(canales)})</h2>
    <table>
      <tr><th>Nombre</th><th>Hash</th><th></th></tr>
      {filas or '<tr><td colspan="3" class="vacio">Sin canales todavía.</td></tr>'}
    </table>
  </section>
</body>
</html>"""


@app.get("/manual", response_class=HTMLResponse)
def ver_manual():
    return _render_pagina(_cargar_canales())


@app.post("/manual/add")
def anadir_canal(name: str = Form(...), hash: str = Form(...)):
    canales = _cargar_canales()
    canales.append({"id": uuid.uuid4().hex, "name": name, "hash": hash})
    _guardar_canales(canales)
    _regenerar_m3u(canales)
    return RedirectResponse("/manual", status_code=303)


@app.post("/manual/edit/{item_id}")
def editar_canal(item_id: str, name: str = Form(...), hash: str = Form(...)):
    canales = _cargar_canales()
    for canal in canales:
        if canal["id"] == item_id:
            canal["name"] = name
            canal["hash"] = hash
            break
    _guardar_canales(canales)
    _regenerar_m3u(canales)
    return RedirectResponse("/manual", status_code=303)


@app.post("/manual/delete/{item_id}")
def eliminar_canal(item_id: str):
    canales = [c for c in _cargar_canales() if c["id"] != item_id]
    _guardar_canales(canales)
    _regenerar_m3u(canales)
    return RedirectResponse("/manual", status_code=303)
