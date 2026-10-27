FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_DIR=/app/models STORAGE_DIR=/app/storage
WORKDIR /app
COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY migrations ./migrations
RUN pip install --no-cache-dir .
# Bootstrap readiness model on SYNTHETIC data so a fresh deploy can score immediately.
RUN python -c "from app.ml.readiness.model import ensure_model; ensure_model()"
RUN useradd --create-home appuser && mkdir -p /app/storage && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
