#!/bin/sh
# Volcar el entorno del contenedor a un archivo que el cron job pueda cargar,
# ya que cron no hereda las variables definidas por env_file/docker-compose.
printenv | sed "s/^\(.*\)=\(.*\)$/export \1='\2'/" > /app/env.sh

# Margen para que el daemon de IPFS termine de arrancar/bootstrapear antes de
# la primera descarga (si no, falla con "connection refused" en frío).
sleep 10

echo "➡️ Ejecutando primera descarga..."
cd /app && python app.py
echo "➡️ Iniciando cron..."
cron
echo "➡️ Iniciando servidor de gestión manual (/manual)..."
cd /app && uvicorn manual_app:app --host 127.0.0.1 --port 5000 &
echo "➡️ Iniciando nginx..."
nginx -g "daemon off;"
