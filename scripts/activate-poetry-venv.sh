# Este script es cargado por el terminal para activar el entorno virtual de Poetry.
# Está diseñado para sesiones de shell interactivas dentro del devcontainer.

# Asegúrate de que el directorio del proyecto sea el actual si no lo es (aunque WORKDIR ya lo hace)
# cd /app # Descomentar si tienes problemas con la activación del venv

# Verifica si Poetry está instalado y en PATH
if command -v poetry &> /dev/null; then
    # Intenta activar el entorno virtual directamente si existe
    if [ -d "/app/.venv" ] && [ -f "/app/.venv/bin/activate" ]; then
        . "/app/.venv/bin/activate"
        echo "Entorno virtual de Poetry activado."
    else
        echo "Entorno virtual de Poetry no encontrado en /app/.venv. Ejecuta 'poetry install' si es necesario."
    fi
else
    echo "Poetry no encontrado. Asegúrate de que esté instalado y en tu PATH."
fi
