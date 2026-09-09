#!/bin/sh
# Volcar el entorno del contenedor a un archivo que el cron job pueda cargar,
# ya que cron no hereda las variables definidas por env_file/docker-compose.
printenv | sed "s/^\(.*\)=\(.*\)$/export \1='\2'/" > /app/env.sh

echo "➡️ Ejecutando primera descarga..."
cd /app && python app.py
echo "➡️ Iniciando cron..."
cron
echo "➡️ Iniciando nginx..."
nginx -g "daemon off;"
