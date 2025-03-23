from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import redis
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Initialize redis client to None
        self.redis = None
        self.rate_limit_window = settings.RATE_LIMIT_WINDOW_SECONDS
        self.rate_limit_requests = settings.RATE_LIMIT_REQUESTS
        self.block_minutes = settings.RATE_LIMIT_BLOCK_MINUTES
        
        # Try to connect to Redis
        self._connect_to_redis()

    def _connect_to_redis(self):
        """Try to connect to Redis and handle potential connection issues."""
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=2,  # Short timeout for connection
                socket_timeout=2,
                health_check_interval=30
            )
            # Ping Redis to ensure connection works
            self.redis.ping()
            logger.info("Successfully connected to Redis")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Could not connect to Redis: {e}")
            self.redis = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.redis = None

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain endpoints
        if self._should_skip_rate_limiting(request.url.path):
            return await call_next(request)
        
        # Skip rate limiting if Redis is not available
        if self.redis is None:
            # Try to reconnect to Redis
            self._connect_to_redis()
            if self.redis is None:
                logger.warning("Redis is unavailable, skipping rate limiting")
                return await call_next(request)
        
        try:
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
        except (redis.ConnectionError, redis.TimeoutError) as e:
            # If Redis connection fails during processing, log and continue
            logger.error(f"Redis connection error during rate limiting: {e}")
            self.redis = None  # Reset connection to trigger reconnect next time
        except Exception as e:
            # For any other exception, log it but don't fail the request
            logger.error(f"Error during rate limiting: {e}")
        
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