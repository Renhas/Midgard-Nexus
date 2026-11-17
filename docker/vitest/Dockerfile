FROM node:26-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY vitest.config.js vitest.setup.js jsconfig.json ./
COPY src/ /app/src/

CMD ["npm", "run", "test"]
