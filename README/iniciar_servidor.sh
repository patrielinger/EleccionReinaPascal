#!/bin/bash

# Script para iniciar el servidor de Elecciones Reina

cd "$(dirname "$0")"

echo "================================"
echo "Iniciando Servidor de Elecciones"
echo "================================"
echo ""

# Verificar si Python 3 está disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    exit 1
fi

echo "✓ Python 3 encontrado"
echo ""

# Iniciar el servidor
python3 server.py
