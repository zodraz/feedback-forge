FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY action-planner/pyproject.toml .
COPY action-planner/README.md .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY action-planner/actionplanner/ ./actionplanner/

# Expose port
EXPOSE 8084

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8084
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "-m", "actionplanner"]
