FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install plugent
COPY . .
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 plugent && chown -R plugent:plugent /app
USER plugent

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the server
CMD ["plugent", "serve", "--host", "0.0.0.0", "--port", "8000"]