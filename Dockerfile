# FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
FROM python:3.11-slim

WORKDIR GPoliciesT

# Copy dependency file first for layer caching
COPY pyproject.toml .

# Install uv
RUN pip install --no-cache-dir uv

# Install dependencies
RUN uv pip install --system --no-cache .

# Copy application code
COPY src/ src/

# Create non-root user
RUN useradd --create-home appuser && chown -R appuser:appuser ./
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]