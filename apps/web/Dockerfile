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
# NEXT_PUBLIC_* vars are inlined into the client bundle at build time.
# Pass them as build args so the production image has the correct values.
ARG NEXT_PUBLIC_API_URL=/api
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL} \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN mkdir -p public && npm run build

FROM node:24-alpine AS production
WORKDIR /app
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0
RUN addgroup --system --gid 10001 appgroup \
    && adduser --system --uid 10001 appuser
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
