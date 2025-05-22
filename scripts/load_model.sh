#!/usr/bin/env bash
set -euo pipefail

# Definir variables
MODEL_ID="nomic-ai/nomic-embed-text-v1.5"
CACHE_DIR=".cache/huggingface/hub/models--nomic-ai--nomic-embed-text-v1.5"

# Crear directorio de destino si no existe
mkdir -p "$(dirname "$CACHE_DIR")"

# Descargar el modelo usando huggingface-cli
echo "Descargando modelo $MODEL_ID a $CACHE_DIR..."
huggingface-cli download "$MODEL_ID" --local-dir "$CACHE_DIR" --local-dir-use-symlinks False

echo "✅ Modelo descargado en: $CACHE_DIR"