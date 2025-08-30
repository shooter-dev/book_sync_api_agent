# Dockerfile pour l'application Django BookSync
FROM python:3.12-alpine

# Variables d'environnement
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache gcc musl-dev postgresql-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 3000

# Lancer l'app FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${CONTAINER_APP_PORT}"]