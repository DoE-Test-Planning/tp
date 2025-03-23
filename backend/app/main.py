from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.middleware import RateLimitMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="0.1.0",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Set up Sentry for error monitoring
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.5,
        environment=settings.ENVIRONMENT,
    )

# Set up Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 