# Production Dockerfile for Backend
FROM python:3.12-slim

WORKDIR /app

# Evita criação de __pycache__ e garante logs sem buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv for faster package installation
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with uv
RUN uv pip install --system -r requirements.txt

# Copy source code
COPY . .

# Change to app directory
WORKDIR /app/app

# Expose port
EXPOSE 8000

# Start production server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]