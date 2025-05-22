#!/usr/bin/env bash
set -euo pipefail

# Define models to download
MODELS=(
    "nomic-ai/nomic-embed-text-v1.5"
    "sentence-transformers/all-mpnet-base-v2"
    "sentence-transformers/all-MiniLM-L6-v2"
)

# Base cache directory
BASE_CACHE_DIR=".cache/huggingface/hub"

# Download each model
for MODEL_ID in "${MODELS[@]}"; do
    # Convert model ID to cache directory format
    CACHE_DIR="$BASE_CACHE_DIR/models--$(echo "$MODEL_ID" | tr '/' '-')"
    
    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$CACHE_DIR")"
    
    # Download the model
    echo "Descargando modelo $MODEL_ID a $CACHE_DIR..."
    huggingface-cli download "$MODEL_ID" --local-dir "$CACHE_DIR" --local-dir-use-symlinks False
    
    echo "✅ Modelo $MODEL_ID descargado en: $CACHE_DIR"
    echo ""
done

echo "🎉 Todos los modelos descargados exitosamente"