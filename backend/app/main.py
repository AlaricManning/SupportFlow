from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api import tickets_router, stats_router
from app.services.knowledge_base import kb


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)

    # Load knowledge base
    try:
        kb.load_documents("./knowledge_base")
        print("✓ Knowledge base loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load knowledge base: {e}")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SupportFlow API",
    description="AI-native multi-agent customer support automation system",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets_router)
app.include_router(stats_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to SupportFlow API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
