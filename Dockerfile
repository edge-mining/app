FROM python:3.11-slim

# Environment Variables
ENV PYTHONUNBUFFERED=1
ENV WATCHFILES_FORCE_POLLING=true

# Create app directory
WORKDIR /app

# Install system deps (if needed, extend this list)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml requirements.txt ./

# Install dependencies
RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy the rest of the source code
COPY . .

# Execute the application
CMD ["python", "-m", "edge_mining", "standard"]
