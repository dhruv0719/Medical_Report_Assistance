# Use Python 3.11 slim image
FROM python:3.11-slim

# Copy uv from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 1. Install system dependencies & clean up immediately
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copy requirements
COPY requirements.txt .

# 3. Install dependencies using uv
# --no-cache prevents uv from storing the downloaded wheels (saving space)
RUN uv pip install --system --no-cache torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system --no-cache -r requirements.txt

# 4. Copy application code
COPY . .

# 5. Run command
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT