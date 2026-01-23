# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# 1. Install system dependencies
# We need poppler-utils for pdf2image and tesseract-ocr for OCR
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up working directory
WORKDIR /app

# 3. Copy requirements first to cache dependencies
COPY requirements.txt .

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Expose the port the app runs on
EXPOSE 8000

# 7. Command to start the application using Uvicorn
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]