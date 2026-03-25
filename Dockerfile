FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies, build wheels, then remove build deps to keep image small
RUN apk add --no-cache \
    libpq \
    libffi \
    && apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY backend/ ./backend/

# Collect static files at build time (needs SECRET_KEY)
RUN SECRET_KEY=build-placeholder DJANGO_SETTINGS_MODULE=config.settings \
    python backend/manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000
