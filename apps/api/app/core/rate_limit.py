import asyncio
import hashlib
import ipaddress
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from time import time
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings

RequestHandler = Callable[[Request], Awaitable[Response]]

LOGGER = logging.getLogger("iems.api.rate_limit")


@dataclass(frozen=True)
class RateLimitDecision:
    limit: int
    remaining: int
    retry_after_seconds: int
    reset_epoch_seconds: int
    group: str


@dataclass(frozen=True)
class RateLimitRule:
    group: str
    limit: int


class InMemoryRateLimitStore:
    def __init__(self) -> None:
        self._counters: dict[str, tuple[int, int]] = {}
        self._lock = asyncio.Lock()

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        now = int(time())
        reset_at = now + window_seconds
        async with self._lock:
            current = self._counters.get(key)
            if current is None or current[1] <= now:
                self._counters[key] = (1, reset_at)
                return 1, reset_at

            count, existing_reset_at = current
            count += 1
            self._counters[key] = (count, existing_reset_at)
            return count, existing_reset_at


class RedisRateLimitStore:
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, window_seconds)

        ttl = await self._redis.ttl(key)
        if ttl < 0:
            ttl = window_seconds
            await self._redis.expire(key, window_seconds)
        return count, int(time()) + ttl


class RateLimiter:
    def __init__(
        self,
        *,
        settings: Settings,
        store: InMemoryRateLimitStore | RedisRateLimitStore,
        fallback_store: InMemoryRateLimitStore | None = None,
    ) -> None:
        self._settings = settings
        self._store = store
        self._fallback_store = fallback_store or InMemoryRateLimitStore()

    async def check(self, request: Request) -> RateLimitDecision | None:
        if not self._settings.rate_limit_enabled or _is_exempt_request(request):
            return None

        rule = _rule_for_request(request, self._settings)
        if rule.limit <= 0:
            return None

        identifier = _client_identifier(
            request,
            trust_proxy_headers=self._settings.rate_limit_trust_proxy_headers,
        )
        period = int(time()) // self._settings.rate_limit_window_seconds
        key = f"iems:rate-limit:{rule.group}:{identifier}:{period}"

        try:
            count, reset_at = await self._store.increment(
                key,
                self._settings.rate_limit_window_seconds,
            )
        except RedisError:
            LOGGER.exception("rate_limit_redis_failed_using_memory_fallback")
            count, reset_at = await self._fallback_store.increment(
                key,
                self._settings.rate_limit_window_seconds,
            )

        remaining = max(rule.limit - count, 0)
        if count <= rule.limit:
            return RateLimitDecision(
                limit=rule.limit,
                remaining=remaining,
                retry_after_seconds=0,
                reset_epoch_seconds=reset_at,
                group=rule.group,
            )

        retry_after = max(reset_at - int(time()), 1)
        return RateLimitDecision(
            limit=rule.limit,
            remaining=0,
            retry_after_seconds=retry_after,
            reset_epoch_seconds=reset_at,
            group=rule.group,
        )


def create_rate_limiter(settings: Settings) -> RateLimiter:
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return RateLimiter(settings=settings, store=RedisRateLimitStore(redis_client))


async def close_rate_limiter(rate_limiter: RateLimiter | None) -> None:
    store = getattr(rate_limiter, "_store", None)
    redis_client = getattr(store, "_redis", None)
    if isinstance(redis_client, Redis):
        await redis_client.aclose()


async def rate_limit_middleware(request: Request, call_next: RequestHandler) -> Response:
    rate_limiter = getattr(request.app.state, "rate_limiter", None)
    if not isinstance(rate_limiter, RateLimiter):
        rate_limiter = RateLimiter(
            settings=request.app.state.settings,
            store=InMemoryRateLimitStore(),
        )
        request.app.state.rate_limiter = rate_limiter

    decision = await rate_limiter.check(request)
    if decision is not None and decision.retry_after_seconds > 0:
        return _rate_limited_response(request, decision)

    response = await call_next(request)
    if decision is not None:
        response.headers["X-RateLimit-Limit"] = str(decision.limit)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        response.headers["X-RateLimit-Reset"] = str(decision.reset_epoch_seconds)
        response.headers["X-RateLimit-Policy"] = decision.group
    return response


def _rate_limited_response(request: Request, decision: RateLimitDecision) -> JSONResponse:
    request_id = str(
        getattr(request.state, "request_id", None)
        or request.headers.get("X-Request-ID")
        or uuid4()
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please retry after the rate-limit window resets.",
                "request_id": request_id,
            }
        },
        headers={
            "Retry-After": str(decision.retry_after_seconds),
            "X-Request-ID": request_id,
            "X-RateLimit-Limit": str(decision.limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(decision.reset_epoch_seconds),
            "X-RateLimit-Policy": decision.group,
        },
    )


def _is_exempt_request(request: Request) -> bool:
    return request.method == "OPTIONS" or request.url.path in {"/health", "/ready"}


def _rule_for_request(request: Request, settings: Settings) -> RateLimitRule:
    path = request.url.path
    method = request.method

    if path in {"/v1/me", "/v1/me/permissions"}:
        return RateLimitRule("auth", settings.rate_limit_auth_requests)
    if method == "POST" and path.startswith("/v1/folders/") and path.endswith("/documents"):
        return RateLimitRule("upload", settings.rate_limit_upload_requests)
    if method == "POST" and path.startswith("/v1/documents/") and path.endswith("/versions"):
        return RateLimitRule("upload", settings.rate_limit_upload_requests)
    if method == "POST" and path.startswith("/v1/projects/") and path.endswith("/exports"):
        return RateLimitRule("export", settings.rate_limit_export_requests)
    if method == "POST" and path.startswith("/v1/exports/") and path.endswith("/cancel"):
        return RateLimitRule("export", settings.rate_limit_export_requests)
    if path.startswith(("/v1/admin", "/v1/audit-events", "/v1/director")):
        return RateLimitRule("admin", settings.rate_limit_admin_requests)
    return RateLimitRule("default", settings.rate_limit_default_requests)


def _client_identifier(request: Request, *, trust_proxy_headers: bool) -> str:
    token = _bearer_token(request)
    if token is not None:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:24]
        return f"token:{digest}"

    ip_address = _client_ip(request, trust_proxy_headers=trust_proxy_headers)
    return f"ip:{ip_address}"


def _bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _client_ip(request: Request, *, trust_proxy_headers: bool) -> str:
    if trust_proxy_headers:
        for value in (
            request.headers.get("CF-Connecting-IP"),
            _first_forwarded_for(request.headers.get("X-Forwarded-For")),
        ):
            if value is not None and _is_valid_ip(value):
                return value

    if request.client is None:
        return "unknown"
    return request.client.host


def _first_forwarded_for(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    first_value = raw_value.split(",", maxsplit=1)[0].strip()
    return first_value or None


def _is_valid_ip(raw_value: str) -> bool:
    try:
        ipaddress.ip_address(raw_value)
    except ValueError:
        return False
    return True
