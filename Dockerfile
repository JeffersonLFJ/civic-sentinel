FROM python:3.11-slim

# Install system dependencies
# tesseract-ocr: for OCR capabilities
# libgl1-mesa-glx: required by some opencv/image libs if used
# git: for potential git installs or debug
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for cache optimization
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create data directories and set permissions
RUN mkdir -p data/chromadb data/sqlite data/uploads_temp data/processed data/models && \
    chmod -R 777 data

# Expose API port
EXPOSE 8000

# Entrypoint script
# We don't strictly need to copy if we are volume mounting, but good for prod build
COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh
RUN chmod +x /app/scripts/entrypoint.sh

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
