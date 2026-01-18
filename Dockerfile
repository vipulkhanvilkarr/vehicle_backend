FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc netcat \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install -r requirements.txt

# Copy project
COPY . .

# Make start script executable
COPY backend/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000
CMD ["/start.sh"]
