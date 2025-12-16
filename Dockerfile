FROM node:20-alpine

# Create app directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN if [ -f package-lock.json ]; then \
        npm ci; \
    elif [ -f pnpm-lock.yaml ]; then \
        npm install -g pnpm && pnpm install; \
    elif [ -f yarn.lock ]; then \
        npm install -g yarn && yarn install; \
    else \
        npm install; \
    fi

# Copy source
COPY . .

# Expose port and start application
ENV HOST=0.0.0.0
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
