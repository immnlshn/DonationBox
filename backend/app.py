import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.init_db import run_migrations
from backend.services.gpio.GPIOService import gpio_service
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
    logger.info("Starting GPIO Service...")
    gpio_service.initialize(enable_gpio=settings.ENABLE_GPIO, pin_factory=settings.PIN_FACTORY)
    await gpio_service.start_background_task()

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # First, close all WebSocket connections gracefully
    logger.info("Closing WebSocket connections...")
    await get_websocket_service().close_all_connections()

    # Then stop GPIO service
    logger.info("Stopping GPIO Service...")
    await gpio_service.stop_background_task()

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