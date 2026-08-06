FROM python:3.12-slim

# Install system dependencies including Tesseract OCR and OpenCV requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 botuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R botuser:botuser /app
USER botuser

ENV PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=2 \
    TESSERACT_CMD=/usr/bin/tesseract

CMD ["python", "-m", "app.main"]
