# 1) Build stage (optional but keeps runtime slim)
FROM python:3.11-slim AS base

# Avoid prompts
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 2) App files
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# 3) Cloud Run expects the server to listen on $PORT
ENV PORT=8080
EXPOSE 8080

# 4) Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
