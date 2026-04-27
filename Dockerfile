FROM python:3.12-alpine

# Instalacion de Nginx y dependencias necesarias
RUN apk add --no-cache nginx
# Crear directorios necesarios para Nginx
RUN mkdir -p /app /htdocs /run/nginx
# Cargar configuración de inicio del contenedor y configuración de Nginx, Crond, y la aplicación Flask
COPY app.py /app/app.py
COPY nginx.conf /etc/nginx/nginx.conf
COPY crontab /etc/crontabs/root
COPY start.sh /start.sh
# Dar permisos de ejecución al script de inicio
RUN chmod +x /start.sh
# Exponer el puerto 80 para Nginx
EXPOSE 80

CMD ["/start.sh"]