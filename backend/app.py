import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .gpio import registry
from .gpio.components import setup_components
from .routes import api_router
from .services.dependencies import get_websocket_service
from .settings import settings

def setup_logging():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Uvicorn Logger mitziehen
    logging.getLogger("uvicorn").setLevel(settings.LOG_LEVEL)
    logging.getLogger("uvicorn.error").setLevel(settings.LOG_LEVEL)
    logging.getLogger("uvicorn.access").setLevel(settings.LOG_LEVEL)

setup_logging()
logger = logging.getLogger(__name__)
logger.info(f"LOG_LEVEL={settings.LOG_LEVEL}")

@asynccontextmanager
async def lifespan(_):
    # Startup
    logger.info("Initializing GPIO...")
    registry.initialize(enable_gpio=settings.ENABLE_GPIO, pin_factory=settings.PIN_FACTORY)

    # Setup GPIO components from configuration
    setup_components(registry)
    logger.info(f"Registered {len(registry.list_components())} GPIO components")

    logger.info("Starting GPIO registry...")
    await registry.start()

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # First, close all WebSocket connections gracefully
    logger.info("Closing WebSocket connections...")
    await get_websocket_service().close_all_connections()

    # Then stop GPIO registry
    logger.info("Stopping GPIO registry...")
    await registry.stop()

    logger.info("Application shutdown complete")

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)