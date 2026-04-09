# ── Builder stage ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build deps (only if using mysqlclient — remove if not)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ── Production stage ───────────────────────────────────────────
FROM python:3.12-slim

# Runtime MySQL lib only (remove if not using MySQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/*
    
RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser:appuser /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app

COPY --chown=appuser:appuser . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

RUN chmod +x entrypoint.sh

# migrate + collectstatic run at container START, not build time
ENTRYPOINT ["./entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]