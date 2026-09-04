FROM python:3.12-slim

# Nota: se cambia de Alpine a Debian slim porque Playwright (necesario para
# resolver la URL actual, que requiere JavaScript) no es compatible con
# musl/Alpine — su Chromium empaquetado necesita glibc.

# Instalacion de Nginx y cron (equivalente Debian de crond en Alpine)
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx \
        cron \
    && rm -rf /var/lib/apt/lists/*

# Crear directorios necesarios para Nginx
RUN mkdir -p /app /htdocs /run/nginx

# Instalar Playwright y su navegador Chromium (con dependencias de sistema)
RUN pip install --no-cache-dir playwright \
    && python3 -m playwright install --with-deps chromium

# Cargar configuración de inicio del contenedor y configuración de Nginx, Crond, y la aplicación Flask
COPY app.py /app/app.py
COPY nginx.conf /etc/nginx/nginx.conf
COPY crontab /app/crontab
COPY start.sh /start.sh

# Registrar el crontab para el usuario root (equivalente a copiarlo en
# /etc/crontabs/root en Alpine, pero a la manera de Debian)
RUN crontab /app/crontab

# Eliminar posibles CRLF que Windows pueda haber introducido y dar permisos
# Esto evita errores "no such file or directory" por shebang con \r
RUN sed -i 's/\r$//' /start.sh || true \
    && chmod +x /start.sh

# Exponer el puerto 80 para Nginx
EXPOSE 80
CMD ["/start.sh"]