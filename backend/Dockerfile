# Multi-stage Dockerfile for Pathavana Backend
# Optimized for production with security scanning and minimal attack surface

# Base stage with Python and system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install security updates
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Development stage
FROM base as development

# Install development dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create app directory
WORKDIR /app

# Copy application code
COPY . /app/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Install only production dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install gunicorn for production
RUN pip install --no-cache-dir gunicorn==21.2.0

# Create app directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . /app/

# Remove development files
RUN rm -rf tests/ .pytest_cache/ .git/ .gitignore

# Create necessary directories
RUN mkdir -p /app/logs /app/cache && \
    chown -R appuser:appuser /app/logs /app/cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application with gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--keep-alive", "2"]

# Security scanning stage
FROM production as security-scan

USER root

# Install security scanning tools
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Add security scanner (example with safety for Python dependencies)
RUN pip install --no-cache-dir safety bandit

# Run security scans
RUN safety check --json || true
RUN bandit -r /app -f json || true

USER appuser