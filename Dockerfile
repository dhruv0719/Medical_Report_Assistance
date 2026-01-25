# Use Python 3.11 slim image
FROM python:3.11-slim

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Install uv (Faster pip replacement)
# We install it to a specific location /usr/local/bin so it's globally available
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 3. Copy requirements
COPY requirements.txt .

# 4. Install dependencies using uv
# Use the full path to be 100% sure, or ensure ENV is picked up
RUN /root/.cargo/bin/uv pip install --system torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN /root/.cargo/bin/uv pip install --system -r requirements.txt

# 5. Copy application code
COPY . .

# 6. Run command
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT