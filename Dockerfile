# Use an official lightweight Python runtime
FROM python:3.11-slim

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for compiling packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry package manager
RUN pip install --no-cache-dir poetry

# Copy dependency locks and configuration mappings
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtual environment inside the container
RUN poetry config virtualenvs.create false

# Install production dependencies only
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of your application code
COPY . /app

# Expose an environmental port placeholder if needed
EXPOSE 8080

# Command to execute your pipeline orchestrator unit
CMD ["python", "orchestrator.py"]
