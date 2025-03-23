from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import redis
import json
from app.core.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Connect to Redis
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.rate_limit_window = settings.RATE_LIMIT_WINDOW_SECONDS
        self.rate_limit_requests = settings.RATE_LIMIT_REQUESTS
        self.block_minutes = settings.RATE_LIMIT_BLOCK_MINUTES

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain endpoints
        if self._should_skip_rate_limiting(request.url.path):
            return await call_next(request)
        
        # Get client identifier (IP + user if authenticated)
        client_id = self._get_client_identifier(request)
        
        # Check if client is blocked
        block_key = f"ratelimit_block:{client_id}"
        if self.redis.exists(block_key):
            ttl = self.redis.ttl(block_key)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Try again in {ttl} seconds."
                }
            )
        
        # Check endpoint-specific rate limit
        endpoint = f"{request.method}:{request.url.path}"
        request_key = f"ratelimit:{client_id}:{endpoint}"
        
        # Get current request count
        current_count = self.redis.get(request_key)
        
        if current_count is None:
            # First request in window
            self.redis.setex(request_key, self.rate_limit_window, 1)
        elif int(current_count) < self.rate_limit_requests:
            # Increment request count
            self.redis.incr(request_key)
        else:
            # Rate limit exceeded, block the client
            self.redis.setex(block_key, self.block_minutes * 60, 1)
            
            # Log the violation
            violation_data = {
                "client_id": client_id,
                "endpoint": endpoint,
                "timestamp": time.time()
            }
            self.redis.lpush("rate_limit_violations", json.dumps(violation_data))
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. You are blocked for {self.block_minutes} minutes."
                }
            )
        
        return await call_next(request)
    
    def _should_skip_rate_limiting(self, path: str) -> bool:
        """Skip rate limiting for health check and metrics endpoints."""
        skip_paths = [
            "/health",
            "/metrics",
            "/api/v1/docs",
            "/api/v1/openapi.json"
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get a unique identifier for the client.
        Combines IP address and user ID if authenticated.
        """
        client_host = request.client.host if request.client else "unknown"
        
        # If user is authenticated, include user ID in the identifier
        # This will be implemented when authentication is added
        user_id = "anonymous"  # Placeholder
        
        return f"{client_host}:{user_id}" 