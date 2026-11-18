# Official Microsoft Playwright Container (Ubuntu Noble + Python 3.12 + Pre-installed Chromium)
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HEADLESS=true \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies: ffmpeg for video, libportaudio2 for audio, libgomp1 for OpenMP/OpenCV, nodejs for yt-dlp JS challenges
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libportaudio2 \
    libgomp1 \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with --break-system-packages for Ubuntu 24.04 Noble
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy source tree (including pre-built production frontend dist)
COPY jarvis/ /app/jarvis/

# Expose production ports
EXPOSE 8000 10000

# Render dynamically injects $PORT (defaults to 10000)
CMD ["sh", "-c", "python -m uvicorn jarvis.backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
