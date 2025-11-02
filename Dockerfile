# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/downloads

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV IS_PRODUCTION=true

# Expose port (Railway, Render will override this)
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; import os; port=os.getenv('PORT', '10000'); requests.get(f'http://localhost:{port}/health', timeout=5)" || exit 1

# Run the application using Gunicorn WSGI server
# Use shell form to allow environment variable expansion
CMD gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT wsgi:app