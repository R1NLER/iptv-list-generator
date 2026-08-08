#!/bin/sh
echo "➡️ Ejecutando primera descarga..."
cd /app && python app.py
echo "➡️ Iniciando cron..."
cron
echo "➡️ Iniciando nginx..."
nginx -g "daemon off;"