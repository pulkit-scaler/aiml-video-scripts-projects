# Build from this folder:  docker build -t northwind-triage .
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Render and Railway set $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn steps.step5_service:app --host 0.0.0.0 --port ${PORT:-8000}"]
