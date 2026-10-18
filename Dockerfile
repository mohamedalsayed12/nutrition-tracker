FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/instance && useradd --create-home api && chown -R api:api /app

USER api

EXPOSE 8000
CMD ["sh", "-c", "python -m flask --app main db upgrade && exec gunicorn --bind 0.0.0.0:8000 'main:create_app()'"]
