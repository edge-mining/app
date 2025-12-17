FROM node:20-alpine AS build

WORKDIR /app

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

COPY . .

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
