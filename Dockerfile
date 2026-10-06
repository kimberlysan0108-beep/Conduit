FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY backend backend
COPY benchmark benchmark
RUN pip install --no-cache-dir .
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head && python -m backend.seed && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
