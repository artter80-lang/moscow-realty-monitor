FROM python:3.12-slim

WORKDIR /app

# Зависимости для lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./pyproject.toml

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

COPY backend/ ./backend/
COPY frontend/ ./frontend/

WORKDIR /app/backend

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
