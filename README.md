# IPTV Generador de listas

Servicio ligero para descargar una lista M3U remota, reemplazar un texto dentro del contenido y publicarla por HTTP.

El proyecto usa:

- Python para descargar y transformar la lista.
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
- Dockerfile: Imagen base con Python, cron y nginx.
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

## Uso rápido

1. Levantar el servicio:

```bash
docker compose up -d --build
```

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

- Usa cabeceras HTTP de navegador para mejorar compatibilidad con fuentes remotas.
- Tiene timeout de 30 segundos en la descarga.
- Si hay error, lo muestra en consola y termina con código de error.
- Siempre escribe el resultado en /htdocs/lista.m3u cuando la descarga funciona.

## Detalle de app.py

Resumen de lógica de app.py:

1. Lee variables de entorno obligatorias: URL y REPLACE_TEXT.
2. Lee SEARCH_TEXT (si no existe, usa 127.0.0.1:6878).
3. Hace una petición HTTP GET a URL con headers tipo navegador.
4. Decodifica la respuesta como UTF-8 (con reemplazo de caracteres inválidos).
5. Aplica un reemplazo global: SEARCH_TEXT -> REPLACE_TEXT.
6. Guarda el resultado final en /htdocs/lista.m3u.

Puntos clave para que funcione bien:

- URL debe responder correctamente y con contenido de texto.
- El texto definido en SEARCH_TEXT debe existir en la respuesta para que se vea el cambio.
- REPLACE_TEXT no puede estar vacío.

## Formato de entrada esperado (JSON y no JSON)

Actualmente, app.py no parsea JSON. El script espera que la respuesta en URL sea texto plano (por ejemplo, una lista M3U).

Eso significa que:

- No consume campos JSON.
- No requiere claves como name, url, channels, etc.
- Solo aplica reemplazo sobre el cuerpo textual completo recibido.

Si tu endpoint devuelve JSON, primero debes transformarlo a texto M3U antes de pasarlo a este script.

Ejemplo de salida textual esperada por app.py:

```m3u
#EXTM3U
#EXTINF:-1 tvg-id="canal1" tvg-name="Canal 1",Canal 1
http://127.0.0.1:6878/stream/canal1
```

En ese ejemplo, si SEARCH_TEXT=127.0.0.1:6878 y REPLACE_TEXT=mi-dominio.com:9000, la URL final quedará reemplazada automáticamente.
