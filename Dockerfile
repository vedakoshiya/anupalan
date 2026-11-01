# Multi-stage production container for Anupalan Compliance Engine
FROM python:3.11-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy packaging configuration and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn[standard] pydantic starlette httpx

# Copy project source trees
COPY packages/ packages/
COPY services/ services/
COPY data/ data/
COPY db/ db/
COPY web/ web/
COPY eval/ eval/

# Expose API service port
EXPOSE 8000

# Container liveness check
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Launch production ASGI server
CMD ["uvicorn", "services.api.src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
