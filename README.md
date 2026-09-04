# IPTV Generador de listas

Servicio ligero para descargar una lista M3U remota, reemplazar un texto dentro del contenido y publicarla por HTTP para ser consumida por reproductores.

El proyecto usa:

- Python + Playwright (Chromium headless) para descargar y transformar la lista.
- Cron para ejecutar la actualización cada 5 minutos.
- Nginx para servir el archivo final.
- Docker Compose para orquestar todo en un solo contenedor.

## Flujo de funcionamiento

1. Al iniciar el contenedor, se ejecuta una descarga inicial de la lista.
2. El script guarda el resultado en /htdocs/lista.m3u.
3. Cron vuelve a ejecutar el proceso cada 5 minutos.
4. Nginx expone el directorio /htdocs por el puerto 80 del contenedor.
5. Docker Compose publica ese puerto en el host como 8000.

## Estructura del proyecto

- app.py: Descarga la lista, reemplaza texto y genera el archivo final.
- crontab: Programación de actualización periódica (cada 5 minutos).
- Dockerfile: Imagen base con Python, cron, nginx y Playwright/Chromium.
- docker-compose.yml: Servicio y publicación del puerto.
- nginx.conf: Configuración del servidor HTTP para servir /htdocs.
- start.sh: Arranque de descarga inicial, cron y nginx.

## Variables de entorno

Este proyecto requiere un archivo .env en la raíz.

Variables disponibles:

- URL: URL remota desde la que se descarga la lista M3U. Obligatoria.
- REPLACE_TEXT: Texto que sustituirá el valor de SEARCH_TEXT dentro de la lista. Obligatoria.
- SEARCH_TEXT: Texto a buscar para reemplazar. Opcional.
  - Valor por defecto: 127.0.0.1:6878

Ejemplo de .env:

```env
URL=https://tu-fuente/lista.m3u
REPLACE_TEXT=tu-dominio-o-ip:puerto
SEARCH_TEXT=127.0.0.1:6878
```

Nota sobre IPFS:

- A partir de esta versión se incluye un servicio `ipfs` en `docker-compose.yml` que arranca un gateway local y se publica en el host en el puerto `8081`.
- Opciones para `URL` en el archivo `.env`:
  - Para que `lista-m3u` use el gateway interno del servicio en la red Compose, usa:
    `URL=http://ipfs:8080/ipns/<hash>/ruta/a/lista.m3u`
  - Para apuntar al gateway expuesto en el host (útil desde tu navegador o si el gateway corre fuera de Compose), usa:
    `URL=http://host.docker.internal:8081/ipns/<hash>/ruta/a/lista.m3u` (Windows / Docker Desktop)
  - También puedes usar la IP o hostname del nodo que sirve el gateway:
    `URL=http://192.168.x.y:8081/ipns/<hash>/ruta/a/lista.m3u`

Cambios operativos importantes:

- Si usas la dirección interna `http://ipfs:8080/...`, la resolución se hace dentro de la red de Compose y no depende del host.
- Si apuntas al gateway del host (`:8081`), asegúrate de que el contenedor `lista-m3u` pueda resolver `host.docker.internal` (Docker Desktop en Windows lo hace por defecto).
- Tras cambiar `URL` en `.env` debes reiniciar o forzar la actualización del servicio `lista-m3u` para que cargue la nueva variable (p. ej. `docker compose restart lista-m3u` o ejecutar `python /app/app.py` dentro del contenedor).


## Uso rápido

1. Levantar el servicio:

```bash
docker compose up -d --build
```

> El `--build` es importante tras actualizar el proyecto: la imagen cambió de base (ver [Notas de la versión actual](#notas-de-la-versión-actual)) e incluye la instalación de Chromium, por lo que la primera construcción tarda más y pesa más que antes.

2. Ver logs:

```bash
docker compose logs -f
```

3. Abrir la lista generada, cambia localhost por la dirección de tu host:

- http://localhost:8080/lista.m3u

También puedes abrir el índice de archivos:

- http://localhost:8080/

4. Detener el servicio:

```bash
docker compose down
```

## Comportamiento del script

El script principal:

- Abre la URL configurada en un navegador Chromium headless (Playwright), en vez de hacer una petición HTTP simple.
- Esto es necesario porque la fuente actual sirve el contenido a través de un gateway IPFS que requiere ejecutar JavaScript en el cliente (Service Worker) para resolver el archivo real; una petición HTTP tradicional solo devuelve una página de carga, no la lista.
- Captura el contenido de dos formas, según cómo responda el gateway: interceptando una descarga de archivo automática, o leyendo el texto ya resuelto en la página.
- Tiene un margen de hasta 60 segundos de espera (más que una descarga HTTP normal, porque el contenido se resuelve vía red P2P/Service Worker, no por una respuesta HTTP directa).
- Valida que el contenido obtenido sea realmente una lista m3u (debe empezar por `#EXTM3U`) antes de darlo por válido.
- Si hay error, lo muestra en consola y termina con código de error.
- Siempre escribe el resultado en /htdocs/lista.m3u cuando la descarga funciona.

## Detalle de app.py

Resumen de lógica de app.py:

1. Lee variables de entorno obligatorias: URL y REPLACE_TEXT.
2. Lee SEARCH_TEXT (si no existe, usa 127.0.0.1:6878).
3. Abre la URL con Chromium headless (Playwright) y espera a que se resuelva el contenido real, capturando una descarga de archivo o leyendo el texto de la página.
4. Comprueba que el contenido obtenido sea una lista m3u válida (empieza por `#EXTM3U`).
5. Aplica un reemplazo global: SEARCH_TEXT -> REPLACE_TEXT.
6. Guarda el resultado final en /htdocs/lista.m3u.

Puntos clave para que funcione bien:

- URL debe apuntar a una página o archivo desde el que Chromium pueda obtener la lista (directamente en crudo o mediante un gateway que la resuelva vía JS).
- El texto definido en SEARCH_TEXT debe existir en la respuesta para que se vea el cambio.
- REPLACE_TEXT no puede estar vacío.

## Formato de entrada esperado (JSON y no JSON)

Actualmente, app.py no parsea JSON. El script espera que el contenido final resuelto en el navegador sea texto plano (por ejemplo, una lista M3U).

Eso significa que:

- No consume campos JSON.
- No requiere claves como name, url, channels, etc.
- Solo aplica reemplazo sobre el cuerpo textual completo obtenido.

Si tu endpoint devuelve JSON, primero debes transformarlo a texto M3U antes de pasarlo a este script.

Ejemplo de salida textual esperada por app.py:

```m3u
#EXTM3U
#EXTINF:-1 tvg-id="canal1" tvg-name="Canal 1",Canal 1
http://127.0.0.1:6878/stream/canal1
```

En ese ejemplo, si SEARCH_TEXT=127.0.0.1:6878 y REPLACE_TEXT=mi-dominio.com:9000, la URL final quedará reemplazada automáticamente.

Ejemplo de salida generado por app.py:

```m3u
#EXTM3U
#EXTINF:-1 tvg-id="canal1" tvg-name="Canal 1",Canal 1
http://192.168.1.5:8000/stream/canal1
```

## Notas de la versión actual

A partir de esta versión, el proyecto usa **Playwright con Chromium headless** en vez de una petición HTTP simple (`urllib`), porque la fuente configurada por defecto (un gateway IPFS/IPNS) dejó de servir el archivo en crudo por HTTP y ahora requiere ejecutar JavaScript en el cliente para resolver el contenido.

Esto trae dos cambios relevantes a nivel de infraestructura:

- **Imagen base**: se cambió de `python:3.12-alpine` a `python:3.12-slim` (Debian), porque Playwright/Chromium no es compatible con Alpine (musl).
- **Demonio de cron**: `crond` (Alpine/busybox) pasa a ser `cron` (Debian); el crontab se registra con el comando `crontab` en vez de copiarse directamente a una ruta fija.
- **Tamaño de la imagen y tiempos de build/arranque**: al incluir un navegador completo, la imagen es notablemente más pesada y la primera descarga tarda más que con el método HTTP simple anterior.

Si en el futuro la fuente configurada vuelve a servir el archivo m3u directamente por HTTP (sin necesitar JavaScript), este script seguiría funcionando igual sin cambios: Playwright captura tanto una descarga de archivo directa como el contenido resuelto vía JS, así que es compatible con ambos escenarios — simplemente sería más lento que una petición HTTP pura para ese caso. El código que usaba `urllib` (versión anterior) sigue disponible en el historial de commits de este repositorio por si se quisiera volver a un método más ligero en caso de que la fuente cambie de comportamiento.
