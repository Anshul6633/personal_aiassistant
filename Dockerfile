# Production Docker Container for JARVIS Autonomous Assistant
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies:
# - ffmpeg: audio & video processing pipeline
# - curl & git: cloud sync & downloads
# - libportaudio2: audio stream support
# - libgl1 & libglib2.0-0: headless OpenCV support
# - Headless browser libraries for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    git \
    sudo \
    libportaudio2 \
    libgl1 \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium headless binary
RUN playwright install chromium

# Copy application source tree (includes pre-built frontend dist)
COPY jarvis/ /app/jarvis/

# Expose production port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true

# Render dynamically injects $PORT; fallback to 8000 if not set
CMD ["sh", "-c", "python -m uvicorn jarvis.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
