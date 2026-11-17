# Official Microsoft Playwright Container (Ubuntu Noble + Python 3.12 + Pre-installed Chromium)
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HEADLESS=true \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH="/opt/venv/bin:$PATH"

# Install ffmpeg for autonomous video editing and libportaudio2 for audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated virtual environment to comply with Ubuntu Noble PEP 668
RUN python3 -m venv /opt/venv && \
    pip install --no-cache-dir --upgrade pip

# Install Python dependencies inside virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source tree (including pre-built production frontend dist)
COPY jarvis/ /app/jarvis/

# Expose production ports
EXPOSE 8000 10000

# Render dynamically injects $PORT (defaults to 10000)
CMD ["sh", "-c", "python -m uvicorn jarvis.backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
