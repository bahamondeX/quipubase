
set -euo pipefail

# CONFIGURACIÓN
BUCKET_NAME="quipubase-store"  # Reemplaza por el nombre de tu bucket
LOCAL_DIR="/app/data"
SERVICE_ACCOUNT_KEY_PATH="/app/service_account.json" # Path INSIDE THE CONTAINER

# CREAR DIRECTORIO LOCAL SI NO EXISTE
mkdir -p "$LOCAL_DIR"

# VERIFICAR SI YA ESTÁ MONTADO
if mountpoint -q "$LOCAL_DIR"; then
  echo "[INFO] $LOCAL_DIR ya está montado."
  exit 0
fi

# MONTAR EL BUCKET EN ~/.data
echo "[INFO] Montando bucket gs://${BUCKET_NAME} en ${LOCAL_DIR}..."
# You would need to add --key-file here if you weren't using GOOGLE_APPLICATION_CREDENTIALS
gcsfuse --implicit-dirs --key-file "$SERVICE_ACCOUNT_KEY_PATH" "$BUCKET_NAME" "$LOCAL_DIR"

echo "[SUCCESS] Bucket montado exitosamente."