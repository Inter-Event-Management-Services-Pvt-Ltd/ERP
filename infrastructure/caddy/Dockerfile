# syntax=docker/dockerfile:1

FROM caddy:2-builder-alpine AS builder

ARG CADDY_VERSION=v2.11.4
RUN xcaddy build "${CADDY_VERSION}" --output /usr/bin/caddy

FROM alpine:3.24

RUN apk add --no-cache ca-certificates libcap mailcap \
    && addgroup -g 10001 caddy \
    && adduser -D -u 10001 -G caddy caddy

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
RUN setcap cap_net_bind_service=+ep /usr/bin/caddy

USER caddy
EXPOSE 80 443
WORKDIR /srv
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
