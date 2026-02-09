# DonationBox

A Raspberry Pi-based interactive donation system with real-time voting capabilities, GPIO hardware control, and a modern web interface.

## 🎯 Overview

DonationBox is a full-stack application designed for physical donation boxes that allow donors to vote on different categories while making their donations. The system features:

- **Interactive Voting**: Donors can choose between multiple categories when donating
- **Real-time Updates**: WebSocket-based communication for instant feedback
- **Hardware Integration**: GPIO control for physical buttons, sensors, and displays
- **Visual Dashboard**: Modern React-based frontend displaying voting results and donation statistics
- **Mock Mode**: Full development support without physical hardware

## 🏗️ Architecture

The project consists of two main components:

### Backend (FastAPI)
- RESTful API for managing votes, categories, and donations
- WebSocket server for real-time communication
- GPIO service for Raspberry Pi hardware control
- SQLite database with Alembic migrations
- Async/await architecture for optimal performance

### Frontend (React + Vite)
- Modern, responsive UI built with React 19
- Real-time data visualization
- QR code integration for charity information
- Animated voting results display

## 📋 Features

- ✅ Create and manage voting campaigns with multiple categories
- ✅ Track donations in real-time with category association
- ✅ Display voting results as they happen
- ✅ WebSocket support for live updates across all connected clients
- ✅ GPIO integration for physical buttons and sensors
- ✅ Mock GPIO mode for development without hardware
- ✅ Debug endpoints for testing and development
- ✅ Database migrations with Alembic
- ✅ CORS support for frontend-backend communication
- ✅ Comprehensive logging system

## 🚀 Quick Start

### Prerequisites

- **Backend**:
  - Python 3.10 or higher (tested with Python 3.14)
  - pip package manager
  - Raspberry Pi with GPIO pins (for production) or any system (for development)

- **Frontend**:
  - Node.js 16+ and npm/yarn
  - Modern web browser

### ⚙️ Installation

The full installation and deployment process is documented in the dedicated [README](deploy/README.md) inside the `deploy/` directory.
This includes instructions for configuring the Raspberry Pi environment, installing dependencies, setting environment variables, and running the required deployment scripts.

Please follow the steps described in the [deployment README](deploy/README.md) and execute the provided scripts as outlined to ensure a correct and reproducible installation.

## 📖 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Voting
- `GET /api/voting/` - Get the current active vote
- `GET /api/voting/{vote_id}/totals` - Get donation totals for a vote

#### WebSocket
- `WS /api/ws` - WebSocket connection for real-time updates

#### Debug (Development Only)
- `POST /api/debug/gpio-pulse` - Trigger a GPIO pulse simulation
- `GET /api/debug/gpio-status` - Check GPIO service status

## 🎮 Usage

### Creating a Voting Campaign

1. Use the database or API to create a new vote with categories
2. Set the vote as active
3. The frontend will automatically display the active vote
4. Donors can select a category and make their donation
5. Results update in real-time for all connected clients

### Hardware Integration

For Raspberry Pi deployment:

1. Set `ENABLE_GPIO=true` in your `.env` file
2. Set `PIN_FACTORY=native` for production hardware
3. Configure GPIO pins in the `GPIOService.py`
4. Connect physical buttons/sensors to the configured pins

### Development Without Hardware

The system includes a mock GPIO mode that allows full development and testing without physical hardware:
- Set `ENABLE_GPIO=false` or `PIN_FACTORY=mock`
- Use debug endpoints to simulate GPIO events
- WebSocket connections work identically to production

## 🗂️ Project Structure

```
DonationBox/
├── backend/                               # FastAPI backend
│   ├── alembic/                           # Database migrations (Alembic)
│   │   └── versions/                      # Migration versions (schema history)
│   ├── core/                              # Core infrastructure (config, DI, lifecycle, logging)
│   ├── gpio/                              # Raspberry Pi GPIO integration
│   │   └── components/                    # GPIO hardware components (button, coin validator, etc.)
│   ├── models/                            # SQLAlchemy ORM models
│   ├── repositories/                      # Data access layer (CRUD + queries)
│   ├── routes/                            # API endpoints (REST + WebSocket)
│   ├── schemas/                           # Pydantic schemas (request/response DTOs)
│   ├── services/                          # Business logic layer
│   │   ├── category/                      # Category management logic
│   │   ├── donation/                      # Donation creation + aggregation + events
│   │   ├── voting/                        # Voting logic + result aggregation
│   │   └── websocket/                     # WebSocket connections + broadcasting
│   ├── app.py                             # Application entry point (FastAPI app)
│   └── requirements.txt                   # Python dependencies
│
├── deploy/                                # Deployment assets
└── frontend/                              # React frontend (Vite)
    ├── public/                            # Public static files
    ├── src/                               # Frontend source code
    │   ├── assets/                        # Images, icons, etc.
    │   ├── components/                    # UI components
    │   ├── services/                      # REST + WebSocket clients
    │   ├── state/                         # Global state management
    │   ├── App.jsx                        # Main application component
    │   ├── AppRouter.jsx                  # Client-side routing
    │   └── main.jsx                       # Application entry point
    ├── package.json                       # Node.js dependencies & scripts
    └── vite.config.js                     # Vite configuration
```

## 🔧 Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `"FastAPI"` | Application name |
| `ENV` | `"production"` | Environment (development/production) |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `"INFO"` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `DATABASE_URL` | `"sqlite:///./backend/database.db"` | Database connection string |
| `ALLOWED_ORIGINS` | `[]` | CORS allowed origins |
| `ENABLE_GPIO` | `false` | Enable GPIO hardware control |
| `PIN_FACTORY` | `"mock"` | GPIO pin factory (mock/native) |

## 🛠️ Development

### Backend Development

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate

# Run with auto-reload
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Run linting (if configured)
pylint backend/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

## 📝 License

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

This project is licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute this software under the conditions stated in the LICENSE file.

## 📧 Contact

This project is part of a university group project at the **University of Cologne** and the **Cologne Institute for Information Systems (CIIS)**, conducted within the course [**Sustainable Digital Innovation Lab (SDIL)**](https://ciis.uni-koeln.de/en/teaching/master-and-phd-courses/sustainable-digital-innovation-lab) by the following contributors:

- **Immanuel Sohn**:<br>
  📧 [isohn1@smail.uni-koeln.de](mailto:isohn@smail.uni-koeln.de)
- **Chiara Döring**:<br>
  📧 [cdoerin1@smail.uni-koeln.de](mailto:cdoerin1@smail.uni-koeln.de)
- **Luca Schröder**:<br>
  📧 [lschro34@smail.uni-koeln.de](mailto:lschro34@smail.uni-koeln.de)
- **Marlon Spiess**:<br>
  📧 [mspiess1@smail.uni-koeln.de](mailto:mspiess1@smail.uni-koeln.de)  
  
## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://react.dev/) and [Vite](https://vitejs.dev/)
- GPIO control via [gpiozero](https://gpiozero.readthedocs.io/)
- Database management with [SQLAlchemy](https://www.sqlalchemy.org/) and [Alembic](https://alembic.sqlalchemy.org/)

---

Made with ❤️ for interactive charitable giving
