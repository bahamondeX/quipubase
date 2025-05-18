FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
# Copy the application files
COPY . .

# Install runtime Python dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    libgflags-dev \
    liblz4-dev \
    libzstd-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt


EXPOSE 5431

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5454","--reload"]