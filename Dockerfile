FROM python:3.10-slim
COPY . /app
WORKDIR /app
ENV PYTHONPATH=/app
# Configurar DNS y repositorios
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY migrate_to_db.py .
COPY .env .
COPY data/ ./data/
CMD ["python", "-m", "src.main"]