# Donation Box Backend

A FastAPI-based backend service for managing a donation box system with GPIO control capabilities, real-time WebSocket communication, and debug interfaces.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Project Structure](#project-structure)

## Overview

This backend application provides a REST API and WebSocket server for a Raspberry Pi-based donation box. It supports GPIO pin control for physical hardware interaction, real-time communication via WebSockets, and includes debugging capabilities for development without physical hardware.

## Features

- **FastAPI Framework**: Modern, fast (high-performance) web framework for building APIs
- **WebSocket Support**: Real-time bidirectional communication with clients
- **GPIO Control**: Interface with Raspberry Pi GPIO pins using gpiozero
- **Mock Mode**: Development mode with mock GPIO factory for testing without hardware
- **Debug Endpoints**: Special endpoints for debugging GPIO operations
- **CORS Support**: Configurable Cross-Origin Resource Sharing
- **Environment-based Configuration**: Flexible settings via environment variables
- **Structured Logging**: Comprehensive logging system with configurable levels
- **Async/Await**: Full asynchronous support for optimal performance

## Prerequisites

- Python 3.10 or higher (tested with Python 3.14)
- Raspberry Pi with GPIO pins (for production) or any system (for development with mock GPIO)
- pip package manager

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd DonationBox/backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the backend directory based on `.env.example`:

```bash
cp .env.example .env
```

### Configuration Options

| Variable                      | Type    | Default                   | Description                              |
|-------------------------------|---------|---------------------------|------------------------------------------|
| `APP_NAME`                    | string  | "FastAPI"                 | Application name displayed in API docs   |
| `ENV`                         | string  | "production"              | Environment (development/production)     |
| `DEBUG`                       | boolean | false                     | Enable debug mode                        |
| `LOG_LEVEL`                   | string  | "INFO"                    | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `LOG_FORMAT`                  | string  | "plain"                   | Log output format                        |
| `SECRET_KEY`                  | string  | "your-secret-key"         | Secret key for authentication            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | 15                        | JWT token expiration time                |
| `DATABASE_URL`                | string  | "sqlite:///./database.db" | Database connection URL                  |
| `ALLOWED_ORIGINS`             | list    | []                        | CORS allowed origins (JSON array)        |
| `ENABLE_GPIO`                 | boolean | false                     | Enable real GPIO hardware control        |
| `PIN_FACTORY`                 | string  | "mock"                    | GPIO pin factory ("mock" or "native")    |

### Example `.env` for Development

```dotenv
APP_NAME='Donation Box Backend'
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

SECRET_KEY=super-secret-development-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

DATABASE_URL=sqlite:///./database.db

ENABLE_GPIO=false
PIN_FACTORY=mock
```

### Example `.env` for Production (Raspberry Pi)

```dotenv
APP_NAME='Donation Box Backend'
ENV=production
DEBUG=false
LOG_LEVEL=INFO

SECRET_KEY=<your-secure-random-key>
ACCESS_TOKEN_EXPIRE_MINUTES=15
ALLOWED_ORIGINS=["https://your-domain.com"]

DATABASE_URL=sqlite:///./database.db

ENABLE_GPIO=true
PIN_FACTORY=native
```

## Running the Application

### Development Mode

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-reload on code changes.

### Production Mode

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Python Module

From the project root:
```bash
cd backend
python -m uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### WebSocket Service

Located in `services/websocket/WebSocketService.py`

**Features:**
- Connection pool management
- Thread-safe operations
- JSON message support
- Broadcasting to all connected clients
- Custom message handlers

**Usage:**
```python
from services.websocket.WebSocketService import websocket_service

# Broadcast to all connected clients
await websocket_service.broadcast_json({
    "type": "notification",
    "message": "Donation received!"
})

# Send to specific client
await websocket_service.send_json(websocket, {
    "type": "response",
    "data": {"status": "ok"}
})
```

## Development

### Adding New Routes

1. Create a new file in `backend/routes/`:
   ```python
   # routes/MyNewRoute.py
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.get('/my-endpoint')
   async def my_endpoint():
       return {"message": "Hello from new endpoint"}
   ```

2. Register the router in `routes/__init__.py`:
   ```python
   from . import MyNewRoute
   
   api_router.include_router(MyNewRoute.router, prefix="/api", tags=["my_tag"])
   ```

### Adding New Services

1. Create a new service directory in `backend/services/`:
   ```bash
   mkdir -p services/my_service
   touch services/my_service/__init__.py
   touch services/my_service/MyService.py
   ```

2. Implement your service:
   ```python
   # services/my_service/MyService.py
   class MyService:
       def __init__(self):
           pass
       
       async def do_something(self):
           # Your logic here
           pass
   
   # Global instance
   my_service = MyService()
   ```

3. Use the service in routes:
   ```python
   from services.my_service.MyService import my_service
   
   @router.get('/use-service')
   async def use_service():
       result = await my_service.do_something()
       return {"result": result}
   ```

### Logging

The application uses Python's built-in logging module:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

Configure log level via `LOG_LEVEL` environment variable.

## Project Structure

```
backend/
├── app.py                          # FastAPI app initialization & lifespan
├── settings.py                     # Configuration via Pydantic Settings
├── .env                            # Environment variables (not in git)
├── .env.example                    # Environment variables template
│
├── routes/                         # API endpoints
│   ├── __init__.py                 # Router registration
│   ├── HelloWorld.py               # GET / - Health check
│   ├── WebSocket.py                # WebSocket /ws
│   └── DebugGPIO.py                # POST /debug/gpio - Debug GPIO
│
├── services/                       # Business logic services
│   ├── __init__.py
│   ├── gpio/                       # GPIO hardware control
│   │   ├── __init__.py
│   │   └── GPIOService.py          # GPIO management with background task
│   ├── websocket/                  # WebSocket management
│   │   ├── __init__.py
│   │   └── WebSocketService.py     # Connection pool & broadcasting
│   ├── donation/                   # Donation logic (planned)
│   │   └── __init__.py
│   └── voting/                     # Voting system (planned)
│       └── __init__.py
│
└── models/                         # Database models (planned)
    └── __init__.py
```

