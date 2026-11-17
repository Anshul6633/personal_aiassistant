# Multi-stage production container build for JARVIS

# Stage 1: Build React SPA
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY jarvis/frontend/package*.json ./
RUN npm install
COPY jarvis/frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (ffmpeg for video/audio pipeline, git, OpenGL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies and Playwright Chromium headless browser
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

# Copy source tree and built frontend bundle
COPY jarvis/ /app/jarvis/
COPY --from=frontend-builder /app/frontend/dist /app/jarvis/frontend/dist

# Expose production port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV HEADLESS=true

# Render dynamically injects $PORT; fallback to 8000 if not set
CMD ["sh", "-c", "python -m uvicorn jarvis.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
