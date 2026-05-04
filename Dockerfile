# ── Stage 1: Build React frontend ────────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend + serve frontend ──────────────────
FROM python:3.11-slim

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built React files into the location Flask expects
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Environment defaults (override via docker run -e or docker-compose)
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV PORT=8000

EXPOSE 8000

# Run with gunicorn in production
CMD ["sh", "-c", "cd backend && gunicorn -w 4 -b 0.0.0.0:${PORT} 'app:create_app()'"]
