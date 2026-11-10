FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_DIR=/app/models STORAGE_DIR=/app/storage \n    # Zero-setup defaults for single-container hosts (Hugging Face Spaces); compose and
    # hosted deployments override these with a real DATABASE_URL and a worker.
    DATABASE_URL=sqlite:////app/storage/placement.db JOBS_INLINE=true
WORKDIR /app
COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY migrations ./migrations
RUN pip install --no-cache-dir .
# Bootstrap readiness model on SYNTHETIC data so a fresh deploy can score immediately.
RUN python -c "from app.ml.readiness.model import ensure_model; ensure_model()"
# UID 1000 is what Hugging Face Spaces runs containers as.
RUN useradd --create-home --uid 1000 appuser && mkdir -p /app/storage && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
