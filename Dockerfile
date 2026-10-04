# =====================================================================
# Stage 1: Builder (Compiles requirements and down-selects production)
# =====================================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies safely in the builder layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry package manager
RUN pip install --no-cache-dir poetry

# Copy your standardized project configurations
COPY pyproject.toml poetry.lock ./

# Export strict production dependencies directly to requirements.txt (no dev groups)
RUN poetry export --without-hashes --format=requirements.txt --output=requirements.txt

# =====================================================================
# Stage 2: Final Production Runtime (Slim and Secure)
# =====================================================================
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIPELINE_DB_PATH="/app/metadata_control.db"

WORKDIR /app

# Install minimal runtime requirements only (SQLite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from the builder stage
COPY --from=builder /build/requirements.txt .

# Install production packages cleanly
RUN pip install --no-cache-dir -r requirements.txt

# Copy core workspace folders and orchestration modules
COPY pipeline/ ./pipeline/
COPY init_simulation_db.py orchestrator.py models.py ./

# Create pristine persistent directories for metadata state footprints
RUN mkdir -p /app/logs

# Declare mount volumes mapping boundaries for external state persistence
VOLUME ["/app/logs"]

EXPOSE 8080

# Bootstrap database schemas and activate orchestrator natively 
CMD ["sh", "-c", "python init_simulation_db.py && python orchestrator.py"]
