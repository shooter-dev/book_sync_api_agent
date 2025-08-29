FROM python:3.12-slim

WORKDIR /code

# Copier les fichiers de dépendances et installer
COPY ./requirements.txt ./code
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copier le code source
COPY ./app ./code/app

ENV PYTHONPATH=/app

# Exposer le port
EXPOSE 80

# Lancer l'app FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]