# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# 1. Install system dependencies
# We need poppler-utils for pdf2image and tesseract-ocr for OCR
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Install uv (Faster pip replacement)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 3. Copy requirements first to cache dependencies
COPY requirements.txt .

# 4. Install dependencies using uv (much faster)
# We install torch CPU explicitly first
RUN uv pip install --system torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 7. Command to start the application using Uvicorn
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT