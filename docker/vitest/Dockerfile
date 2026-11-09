FROM node:22-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY vitest.config.js vitest.setup.js ./
COPY src/ /app/src/

CMD ["npm", "run", "test"]
