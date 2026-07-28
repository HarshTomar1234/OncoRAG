# Official Python base image, not the deprecated tiangolo/uvicorn-gunicorn-fastapi
# image (confirmed via FastAPI's current docs before writing this).
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml /app/
COPY src /app/src
RUN pip install --no-cache-dir .

COPY static /app/static

EXPOSE 8000

# Secrets are passed at `docker run` time (--env-file .env), never baked
# into the image.
CMD ["fastapi", "run", "src/oncorag/api/main.py", "--host", "0.0.0.0", "--port", "8000"]
