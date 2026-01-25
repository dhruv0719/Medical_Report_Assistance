# Use Python 3.11 slim image
FROM python:3.11-slim

# Copy uv from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copy requirements
COPY requirements.txt .

# 3. Install dependencies using uv
RUN uv pip install --system torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system -r requirements.txt

# 4. Copy application code
COPY . .

# 5. Run command
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT