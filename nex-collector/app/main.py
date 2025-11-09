"""Main FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routes import contexts, aggregator, datasets, teachers
from .auth import verify_token
from .config import settings


app = FastAPI(
    title="NEX Context Aggregator",
    description="Context Aggregation and Dataset Building Service",
    version="1.0.0"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Auth middleware
# @app.middleware("http")
# async def auth_middleware(request: Request, call_next):
#     """Verify token for /v1/ routes."""
#     if request.url.path.startswith("/v1/"):
#         await verify_token(request)
#     return await call_next(request)

# Health check
@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    return {"ok": True, "mode": settings.MODE_INTEGRATION}


# Include routers
app.include_router(contexts.router)
app.include_router(aggregator.router)
app.include_router(datasets.router)
app.include_router(teachers.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

