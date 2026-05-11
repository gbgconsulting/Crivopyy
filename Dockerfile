FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/data/media /app/data/chroma_db \
    && chmod +x scripts/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "/app/scripts/docker-entrypoint.sh"]
