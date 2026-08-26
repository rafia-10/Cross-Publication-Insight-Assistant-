# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (git, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY . .

# Expose ports: 8000 for FastAPI, 8501 for Streamlit
EXPOSE 8000 8501

# Default command starts FastAPI backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
