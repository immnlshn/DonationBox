from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core import settings, setup_logging
from .core.lifespan import lifespan
from .routes import api_router

# Initialize logging
setup_logging()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)