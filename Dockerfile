FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY . .

# Instalar dependencias del sistema y gcsfuse desde el repositorio oficial
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    libpq-dev \
    git \
    gcc \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    libgflags-dev \
    liblz4-dev \
    libzstd-dev \
    fuse \
 && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt gcsfuse-bullseye main" | tee /etc/apt/sources.list.d/gcsfuse.list \
 && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
 && apt-get update && apt-get install -y gcsfuse \
 && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 5454

ENTRYPOINT ["entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5454", "--reload"]