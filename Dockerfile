# Frontend build stage
FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build


# Runtime: Python backend + nginx
FROM python:3.11-slim

ENV APP_HOME=/app

ENV PYTHONPATH="$APP_HOME/core" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR $APP_HOME

# System dependencies (nginx + utilities)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx && \
    rm -rf /var/lib/apt/lists/*

# Copy backend core and other necessary files
COPY core/ ./core/
COPY nginx.conf /etc/nginx/nginx.conf

# Install dependencies for the backend
WORKDIR $APP_HOME/core
COPY core/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend build into nginx
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html

# Expose ports:
# - 80: frontend (nginx)
# - 8001: backend Python
EXPOSE 80 8001

# Run both nginx and the Python backend
CMD ["sh", "-c", "nginx -g 'daemon off;' & python -m edge_mining standard"]