# Imagen del contenedor web (Gunicorn + Django + LangGraph). Contexto de build: raíz del repo.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

RUN mkdir -p /app/backend/media \
    && useradd --create-home copiloto \
    && chown -R copiloto /app
USER copiloto

WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
