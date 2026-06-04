# syntax=docker/dockerfile:1

FROM node:24-alpine AS base
WORKDIR /app

FROM base AS development
COPY package*.json ./
RUN npm ci || npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]

FROM base AS deps
COPY package*.json ./
RUN npm ci

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:24-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 10001 appgroup \
    && adduser --system --uid 10001 appuser
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
