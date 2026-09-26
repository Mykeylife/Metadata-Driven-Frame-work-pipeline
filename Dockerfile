# Use an official lightweight Python runtime
FROM python:3.11-slim

# Set system environment variables to optimize Python runtime metrics inside containers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIPELINE_DB_PATH="/app/metadata_control.db"

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling packages safely
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry package manager
RUN pip install --no-cache-dir poetry

# Copy dependency locks and configuration mappings
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a separate virtual environment inside the container
RUN poetry config virtualenvs.create false

# Install production dependencies cleanly without trying to install the project root package
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of your core application workspace folders and files
COPY pipeline/ ./pipeline/
COPY init_simulation_db.py orchestrator.py models.py ./

# Expose an environmental port placeholder if needed for future API endpoints
EXPOSE 8080

# Bootstrap database schemas automatically upon container startup before activating orchestrator engine loops
CMD ["sh", "-c", "python init_simulation_db.py && python orchestrator.py"]
