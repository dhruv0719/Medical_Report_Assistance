# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim as builder

# Install build tools
RUN apt-get update && apt-get install -y curl build-essential

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create virtual environment
RUN uv venv /opt/venv
# Use the virtual environment for subsequent commands
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt .

# Install dependencies into the virtual environment
# We verify the index-url is respected for CPU torch
RUN uv pip install --no-cache torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --no-cache -r requirements.txt

# ==========================================
# Stage 2: Runner (Final Image)
# ==========================================
FROM python:3.11-slim

# Install runtime system dependencies (Poppler/Tesseract)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Enable the virtual environment
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy application code
COPY . .

# Run command
CMD uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT