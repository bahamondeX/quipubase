set -euo pipefail

# CONFIGURACIÓN
BUCKET_NAME="quipubase-store"  # Reemplaza por el nombre de tu bucket
LOCAL_DIR="./data"

# Determinar la ruta del archivo de clave de cuenta de servicio basada en el OS
SERVICE_ACCOUNT_KEY_PATH=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  SERVICE_ACCOUNT_KEY_PATH="./service_account.json" # Path DENTRO del contenedor para Linux
elif [[ "$OSTYPE" == "darwin"* ]]; then
  # Ruta común para la clave de cuenta de servicio en macOS si no está en un contenedor.
  # ASEGÚRATE DE QUE ESTA RUTA ES CORRECTA PARA TU ARCHIVO service_account.json
  # Podría ser en el directorio de tu proyecto, o en ~/.config/gcloud/
  SERVICE_ACCOUNT_KEY_PATH="./service_account.json" # Asumiendo que está en el mismo directorio que el script o tu proyecto.
  # O si la tienes en la ubicación predeterminada de gcloud:
  # SERVICE_ACCOUNT_KEY_PATH="${HOME}/.config/gcloud/application_default_credentials.json"
  # O si tienes un archivo .json específico que descargaste:
  # SERVICE_ACCOUNT_KEY_PATH="/ruta/a/tu/archivo/service_account.json"
else
  echo "[ERROR] Sistema operativo no soportado."
  exit 1
fi

# CREAR DIRECTORIO LOCAL SI NO EXISTE
mkdir -p "$LOCAL_DIR"

# VERIFICAR SI YA ESTÁ MONTADO
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  if mountpoint -q "$LOCAL_DIR"; then
    echo "[INFO] $LOCAL_DIR ya está montado."
    exit 0
  fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
  # En macOS, verifica si el directorio está listado como un punto de montaje por gcsfuse
  # gcsfuse no crea un punto de montaje "tradicional" que 'mount' muestre de la misma manera.
  # La forma más robusta es verificar si el proceso gcsfuse está activo para ese punto de montaje.
  # Sin embargo, una forma más sencilla para el script es simplemente intentar montarlo y manejar el error
  # si ya está en uso, o verificar si el directorio no está vacío (si esperas que se pueble).
  # Para este script, simplificaremos y confiaremos en que gcsfuse manejará el "ya montado" o lo volverá a montar.
  # Si necesitas una verificación estricta, tendrías que parsear la salida de 'ps aux | grep gcsfuse'.
  # Por ahora, eliminaremos la verificación de 'mount' para evitar falsos negativos en macOS.
  # (Se asume que gcsfuse dará un error si ya está montado, o que el script se ejecuta en un entorno donde no debería haber conflictos)
  echo "[INFO] La verificación de 'mountpoint' se omite en macOS debido a la complejidad de gcsfuse."
else
  echo "[ERROR] No se puede verificar el punto de montaje en este sistema operativo."
  exit 1
fi

# MONTAR EL BUCKET EN ./data
echo "[INFO] Montando bucket gs://${BUCKET_NAME} en ${LOCAL_DIR}..."
# Asegúrate de que SERVICE_ACCOUNT_KEY_PATH apunta a tu clave JSON
# Si la clave está configurada a través de GOOGLE_APPLICATION_CREDENTIALS, podrías omitir --key-file
gcsfuse --implicit-dirs --key-file "$SERVICE_ACCOUNT_KEY_PATH" "$BUCKET_NAME" "$LOCAL_DIR"

echo "[SUCCESS] Bucket montado exitosamente."