#!/bin/sh

echo "➡️ Ejecutando primera descarga..."
cd /app && python app.py

echo "➡️ Iniciando cron..."
crond

echo "➡️ Iniciando nginx..."
nginx -g "daemon off;"