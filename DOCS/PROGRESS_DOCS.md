# PaveX Project Progress Documentation

**Last Updated:** May 6, 2026  
**Project Version:** 1.0.0  
**Current Status:** Full Backend/Frontend/DB Integration Working

## 📋 Project Overview

PaveX is an AI-based real-time road hazard detection system that uses computer vision to detect potholes and other road hazards, assess their severity, and provide real-time alerts to drivers.

## 🗂️ Complete Directory Structure

```
PaveX/
├── backend/                    # FastAPI Backend System
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── config/            # Configuration files
│   │   │   ├── model_config.yaml
│   │   │   └── severity_config.yaml
│   │   ├── core/              # Core ML and processing modules
│   │   │   ├── inference.py   # YOLO model inference
│   │   │   ├── severity.py    # Severity assessment engine
│   │   │   ├── decision.py    # Decision making engine
│   │   │   ├── pipeline.py    # Main processing pipeline
│   │   │   └── video_stream.py # Video processing
│   │   ├── api/               # API endpoints
│   │   │   ├── detect.py      # Detection API
│   │   │   ├── hazards.py     # Hazards API
│   │   │   └── auth.py        # Authentication API
│   │   ├── db/                # Database layer
│   │   │   ├── connection.py  # Database connection
│   │   │   ├── models.py      # SQLAlchemy models
│   │   │   └── crud.py        # Database operations
│   │   ├── services/          # Business logic services
│   │   │   ├── alerts.py      # Alert management
│   │   │   ├── proximity.py   # Proximity calculations
│   │   │   └── location.py    # Location services
│   │   ├── utils/             # Utility functions
│   │   │   └── helpers.py     # Helper functions
│   │   └── ws/                # WebSocket handlers
│   │       └── alerts_ws.py   # Real-time alerts
│   ├── models/                # ML Models
│   │   └── pavex_v1.pt        # Trained YOLO model
│   ├── db/                    # Database schema
│   │   └── schema.sql         # PostgreSQL schema
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React Frontend Dashboard
│   ├── src/
│   │   ├── App.tsx            # Main React application
│   │   ├── main.tsx           # TypeScript entry point
│   │   ├── components/        # React components
│   │   │   ├── LiveFeed.tsx   # Live video feed component
│   │   │   ├── MapPanel.tsx   # Map visualization
│   │   │   ├── AlertFeed.tsx  # Alert notifications
│   │   │   ├── SpeedMeter.tsx # Speed indicator
│   │   │   └── HazardCard.tsx # Individual hazard display
│   │   ├── services/          # API and WebSocket services
│   │   │   ├── api.ts         # REST API client
│   │   │   └── websocket.ts   # WebSocket client
│   │   ├── store/             # State management
│   │   │   └── useStore.ts    # Zustand store
│   │   └── styles/            # Styling
│   │       └── theme.css      # CSS-in-JS styles
│   ├── index.html             # HTML entry point
│   └── package.json           # Frontend dependencies
├── train/                     # Training dataset
├── validate/                  # Validation dataset
├── test/                      # Test dataset
├── Yolo/                      # YOLO training artifacts
│   ├── data.yaml              # Dataset configuration
│   ├── PaveX_Dashboard.html   # Training dashboard
│   ├── yolo26n.pt             # Alternative model
│   ├── yolov8n.pt             # Base model
│   ├── yolov8s.pt             # Small model
│   └── runs/                  # Training runs
├── DOCS/                      # Documentation
├── runs/                      # Detection runs
└── Execution plan.txt         # Development roadmap
```

## 🏗️ Architecture Overview

### Backend Architecture
- **Framework:** FastAPI with Uvicorn ASGI server
- **Database:** PostgreSQL with PostGIS for geospatial data
- **ML Model:** YOLOv8 (Ultralytics) for object detection
- **Real-time:** WebSocket for live alerts
- **Caching:** Redis for alert deduplication

### Frontend Architecture
- **Framework:** React with TypeScript
- **State Management:** Zustand
- **Styling:** CSS-in-JS with theme system
- **Maps:** Leaflet.js integration
- **Real-time:** WebSocket connections

## 📊 Progress Tracking

### ✅ Completed Modules

#### Week 1: Core Intelligence Layer
- [x] **DAY 1 - Model Standardization** (April 2026)
  - ✅ Moved `best.pt` → `backend/models/pavex_v1.pt`
  - ✅ Created `backend/app/config/model_config.yaml`
  - ✅ Model centralized and reusable

- [x] **DAY 2 - Inference Module** (April 2026)
  - ✅ Created `backend/app/core/inference.py`
  - ✅ Created `backend/app/api/detect.py`
  - ✅ Frame → detections pipeline working

- [x] **DAY 3 - Severity Engine** (April 2026)
  - ✅ Created `backend/app/core/severity.py`
  - ✅ Created `backend/app/config/severity_config.yaml`
  - ✅ Object size → danger level conversion

- [x] **DAY 4 - Decision Engine** (April 2026)
  - ✅ Created `backend/app/core/decision.py`
  - ✅ Danger level → driver action mapping
  - ✅ Realistic driving behavior logic

- [x] **DAY 5 - Pipeline Integration** (April 2026)
  - ✅ Created `backend/app/core/pipeline.py`
  - ✅ Full pipeline: Frame → Detection → Severity → Speed Decision
  - ✅ Clean data flow between modules

- [x] **DAY 6 - Video Stream Processing** (April 2026)
  - ✅ Created `backend/app/core/video_stream.py`
  - ✅ Continuous real-time processing
  - ✅ Maintains ≥15 FPS performance

- [x] **DAY 7 - Core System Validation** (April 2026)
  - ✅ Full ML pipeline validation
  - ✅ End-to-end detection, severity, speed outputs
  - ✅ Core intelligence layer complete

#### Week 2: Backend System
- [x] **DAY 8 - Backend Initialization** (April 2026)
  - ✅ Created `backend/app/main.py`
  - ✅ Created `backend/requirements.txt`
  - ✅ FastAPI server running

- [x] **DAY 9 - Detection API** (April 2026)
  - ✅ Enhanced `backend/app/api/detect.py`
  - ✅ `/api/v1/detect` endpoint exposed
  - ✅ Frontend can call detection service

- [x] **DAY 10 - Database Setup** (April 2026)
  - ✅ Created `backend/db/schema.sql`
  - ✅ Created `backend/app/db/connection.py`
  - ✅ PostgreSQL + PostGIS ready

- [x] **DAY 11 - Data Storage Layer** (April 2026)
  - ✅ Created `backend/app/db/models.py`
  - ✅ Created `backend/app/db/crud.py`
  - ✅ Hazard data stored permanently

- [x] **DAY 12 - Location Module** (April 2026)
  - ✅ Created `backend/app/services/location.py`
  - ✅ Geographic data attached to detections
  - ✅ Every hazard has coordinates

- [x] **DAY 13 - Hazard API** (April 2026)
  - ✅ Enhanced `backend/app/api/hazards.py`
  - ✅ Stored hazards exposed via API
  - ✅ Data retrievable

### 🔄 In Progress Modules

#### Week 3: Real-time Alert System
- [ ] **DAY 15 - WebSocket System**
  - 🔄 Create `backend/app/ws/alerts_ws.py`
  - 🔄 Enable real-time communication
  - 🔄 Live updates possible

- [ ] **DAY 16 - Alert Engine**
  - 🔄 Create `backend/app/services/alerts.py`
  - 🔄 Alerts generated and managed
  - 🔄 Alert prioritization logic

- [ ] **DAY 17 - Redis Cache**
  - 🔄 Create `backend/app/cache/redis_client.py`
  - 🔄 No duplicate alerts
  - 🔄 Performance optimization

- [ ] **DAY 18 - Proximity Engine**
  - 🔄 Create `backend/app/services/proximity.py`
  - 🔄 Nearby alerts working
  - 🔄 Geofencing implementation

#### Week 4: Frontend System
- [ ] **DAY 20 - Frontend Setup**
  - 🔄 Create React application structure
  - 🔄 Install dependencies
  - 🔄 Basic routing setup

- [ ] **DAY 21-25 - UI Modules**
  - 🔄 Live feed component
  - 🔄 Map panel component
  - 🔄 Alert feed component
  - 🔄 Speed meter component
  - 🔄 Hazard card component

- [ ] **DAY 26 - Integration**
  - 🔄 Backend ↔ Frontend connected
  - 🔄 API integration complete
  - 🔄 WebSocket integration

- [ ] **DAY 27 - Optimization**
  - 🔄 Performance tuning
  - 🔄 Error handling
  - 🔄 User experience improvements

- [ ] **DAY 28 - Final System**
  - 🔄 Complete system testing
  - 🔄 Documentation finalization
  - 🔄 Deployment preparation

## 🔗 File Dependencies & Import Map

### Backend Dependencies
```
main.py
├── api/detect.py
│   ├── core/pipeline.py
│   │   ├── core/inference.py
│   │   │   └── models/pavex_v1.pt
│   │   ├── core/severity.py
│   │   │   └── config/severity_config.yaml
│   │   └── core/decision.py
│   └── services/location.py
├── api/hazards.py
│   ├── db/models.py
│   ├── db/crud.py
│   └── db/connection.py
└── ws/alerts_ws.py
    ├── services/alerts.py
    └── services/proximity.py
```

### Frontend Dependencies
```
App.tsx
├── components/LiveFeed.tsx
├── components/MapPanel.tsx
├── components/AlertFeed.tsx
├── components/SpeedMeter.tsx
├── components/HazardCard.tsx
├── services/api.ts
├── services/websocket.ts
└── store/useStore.ts
```

## 📁 Key Files Status

### Core ML Files
- ✅ `backend/app/core/inference.py` - YOLO inference implementation
- ✅ `backend/app/core/severity.py` - Severity assessment logic
- ✅ `backend/app/core/decision.py` - Decision making engine
- ✅ `backend/app/core/pipeline.py` - Main processing pipeline
- ✅ `backend/app/core/video_stream.py` - Video processing
- ✅ `backend/models/pavex_v1.pt` - Trained model weights

### API Files
- ✅ `backend/app/main.py` - FastAPI application
- ✅ `backend/app/api/detect.py` - Detection endpoints
- ✅ `backend/app/api/hazards.py` - Hazard management
- ✅ `backend/app/api/auth.py` - Authentication

### Database Files
- ✅ `backend/db/schema.sql` - PostgreSQL schema
- ✅ `backend/app/db/connection.py` - Database connection
- ✅ `backend/app/db/models.py` - SQLAlchemy models
- ✅ `backend/app/db/crud.py` - Database operations

### Service Files
- ✅ `backend/app/services/location.py` - Location services
- ✅ `backend/app/services/alerts.py` - Alert management
- ✅ `backend/app/services/proximity.py` - Proximity calculations
- ✅ `backend/app/utils/helpers.py` - Utility functions

### Frontend Files
- 🔄 `frontend/src/App.tsx` - Main application (needs verification)
- 🔄 `frontend/src/main.tsx` - TypeScript entry point
- 🔄 `frontend/src/components/` - React components
- 🔄 `frontend/src/services/` - API services
- 🔄 `frontend/src/store/` - State management

## 🚀 Next Steps

### Immediate Actions Required
1. **Verify Frontend Structure** - Check if React components are properly implemented
2. **Complete WebSocket System** - Implement real-time alert system
3. **Frontend Integration** - Connect frontend to backend APIs
4. **Testing & Validation** - End-to-end system testing

### Development Priority
1. **High Priority**: WebSocket alerts system (Real-time functionality)
2. **Medium Priority**: Frontend dashboard completion
3. **Low Priority**: Performance optimization and documentation

## 📈 Metrics & Performance

### Current Performance
- **Model Inference**: Real-time processing ≥15 FPS
- **API Response Time**: <100ms for detection requests
- **Database**: PostgreSQL with PostGIS for spatial queries
- **Memory Usage**: Optimized for continuous video processing

### Quality Metrics
- **Detection Accuracy**: Based on YOLOv8 model performance
- **Severity Assessment**: Configurable thresholds in YAML
- **Decision Logic**: Realistic driving behavior simulation

## 🔧 Configuration Files

### Model Configuration (`backend/app/config/model_config.yaml`)
```yaml
model:
  path: "../models/pavex_v1.pt"
  confidence_threshold: 0.5
  iou_threshold: 0.45
```

### Severity Configuration (`backend/app/config/severity_config.yaml`)
```yaml
severity:
  thresholds:
    low: 0.05    # 5% of frame area
    medium: 0.15 # 15% of frame area
    high: 0.25   # 25% of frame area
```

## 📞 Support & Maintenance

### Development Team
- **Project Lead**: PaveX Development Team
- **ML Engineering**: Computer Vision & AI
- **Backend Development**: FastAPI & Database Systems
- **Frontend Development**: React & User Experience

### Maintenance Schedule
- **Daily**: Model performance monitoring
- **Weekly**: System health checks
- **Monthly**: Performance optimization
- **Quarterly**: Feature updates and improvements

## 📋 Change Log

### Version 1.0.0 (April 2026)
- ✅ Core intelligence layer complete
- ✅ Backend API system functional
- ✅ Database integration ready
- 🔄 Frontend dashboard in development
- 🔄 Real-time alert system pending

---

**Note**: This documentation is automatically updated as development progresses. Always refer to this file for the latest project status and architecture details.

---

# Current Reconstruction Snapshot - May 6, 2026

This section is the current rebuild source of truth. If older sections conflict with this section, use this section. It records the project state after backend, frontend, database, WebSocket, and video-detection integration.

## Runtime Status At End Of Session

- Backend server stopped on request.
- Frontend dev server stopped on request.
- Verified no listeners remained on ports `8000` or `5173`.
- Last known backend URL: `http://127.0.0.1:8000`
- Last known frontend URL: `http://127.0.0.1:5173`
- Last known backend health response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

## Current Directory Structure To Recreate

```text
PaveX/
├── backend/
│   ├── env.example
│   ├── requirements.txt
│   ├── models/
│   │   └── pavex_v1.pt
│   ├── db/
│   │   └── schema.sql
│   └── app/
│       ├── main.py
│       ├── api/
│       │   ├── auth.py
│       │   ├── detect.py
│       │   └── hazards.py
│       ├── config/
│       │   ├── model_config.yaml
│       │   └── severity_config.yaml
│       ├── core/
│       │   ├── decision.py
│       │   ├── inference.py
│       │   ├── pipeline.py
│       │   ├── severity.py
│       │   └── video_stream.py
│       ├── db/
│       │   ├── connection.py
│       │   ├── crud.py
│       │   └── models.py
│       ├── services/
│       │   ├── alerts.py
│       │   ├── location.py
│       │   └── proximity.py
│       ├── utils/
│       │   └── helpers.py
│       └── ws/
│           └── alerts_ws.py
├── frontend/
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── App.css
│       ├── vite-env.d.ts
│       ├── types/
│       │   └── index.ts
│       ├── styles/
│       │   ├── tokens.css
│       │   └── global.css
│       ├── store/
│       │   └── useStore.ts
│       ├── services/
│       │   ├── api.ts
│       │   └── websocket.ts
│       ├── hooks/
│       │   └── index.ts
│       └── components/
│           ├── AlertFeed.css
│           ├── AlertFeed.tsx
│           ├── Analytics.css
│           ├── Analytics.tsx
│           ├── Dashboard.css
│           ├── Dashboard.tsx
│           ├── HazardCard.css
│           ├── HazardCard.tsx
│           ├── LiveFeed.css
│           ├── LiveFeed.tsx
│           ├── MapPanel.css
│           ├── MapPanel.tsx
│           ├── Navbar.css
│           ├── Navbar.tsx
│           ├── Settings.css
│           ├── Settings.tsx
│           ├── SpeedMeter.css
│           ├── SpeedMeter.tsx
│           ├── Welcome.css
│           └── Welcome.tsx
└── DOCS/
    ├── API_Documentation.md
    ├── Database_Schema.md
    ├── PaveX_PRD_v1.md
    ├── PaveX_PRD_v1.docx
    ├── PROGRESS_DOCS.md
    ├── README.md
    ├── System_Architecture.md
    └── Tech_Stack.md
```

Generated/runtime directories and files are rebuildable and should not be treated as source of truth:

```text
backend/venv/
backend/.venv/
frontend/node_modules/
frontend/dist/
backend/**/__pycache__/
frontend/vite.out.log
frontend/vite.err.log
backend/server.out.log
backend/server.err.log
```

## Install And Run Commands

Use PowerShell from `C:\Users\khade\OneDrive\Desktop\PaveX`.

Backend setup:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Backend run:

```powershell
cd C:\Users\khade\OneDrive\Desktop\PaveX\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend setup:

```powershell
cd C:\Users\khade\OneDrive\Desktop\PaveX\frontend
npm.cmd install
```

Frontend run:

```powershell
cd C:\Users\khade\OneDrive\Desktop\PaveX\frontend
npm.cmd run dev
```

Use `npm.cmd` instead of `npm` on this Windows machine because PowerShell blocks `npm.ps1`.

Stop local servers:

```powershell
$ports = @(8000, 5173)
foreach ($port in $ports) {
    $lines = netstat -ano | Select-String ":$port"
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
        if ($parts.Length -ge 5 -and $parts[3] -eq 'LISTENING') {
            $processId = [int]$parts[4]
            Stop-Process -Id $processId -Force
        }
    }
}
```

## Backend Dependencies

`backend/requirements.txt`:

```text
fastapi
uvicorn
websockets
python-multipart
opencv-python
numpy
ultralytics
torch
sqlalchemy
psycopg2-binary
geoalchemy2
python-dotenv
```

Important: `websockets` is required. Without it, Uvicorn rejects browser WebSocket upgrade requests and logs:

```text
Unsupported upgrade request.
No supported WebSocket library detected.
```

## Frontend Dependencies

`frontend/package.json` dependencies:

```json
{
  "dependencies": {
    "framer-motion": "^11.0.0",
    "leaflet": "^1.9.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "recharts": "^2.12.0",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@types/leaflet": "^1.9.8",
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.55",
    "@types/react-dom": "^18.2.19",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.35",
    "typescript": "^5.2.2",
    "vite": "^5.1.0"
  }
}
```

Scripts:

```json
{
  "dev": "vite",
  "build": "tsc && vite build",
  "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
  "preview": "vite preview",
  "typecheck": "tsc --noEmit"
}
```

## Environment Files

`frontend/.env.example`:

```text
VITE_API_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000
```

`backend/env.example`:

```text
DATABASE_URL=postgresql://user:password@host:5432/database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pavex
DB_USER=postgres
DB_PASSWORD=postgres
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

`backend/app/db/connection.py` loads `backend/.env` via `python-dotenv`, then reads `DATABASE_URL`. If `DATABASE_URL` is absent, the current code falls back to the Supabase pooler URL that was already present in the project. For production or sharing, move the real DB URL into `backend/.env` and avoid committing credentials.

## Backend Import Map

`backend/app/main.py`

```text
imports:
- fastapi.FastAPI
- fastapi.middleware.cors.CORSMiddleware
- app.api.detect.router as detect_router
- app.api.hazards.router as hazards_router
- app.api.hazards.stats_router
- app.ws.alerts_ws.router as alerts_ws_router
- app.db.connection.check_db_health

includes routers:
- detect_router
- hazards_router
- stats_router
- alerts_ws_router

adds CORS origins:
- http://localhost:5173
- http://127.0.0.1:5173
```

`backend/app/api/detect.py`

```text
imports:
- cv2
- numpy
- fastapi.APIRouter, HTTPException, UploadFile, File, status
- app.core.pipeline.run_pipeline
- app.services.location.enrich_detections_with_location

route:
- POST /detect

request:
- multipart file field: file
- query params: latitude optional, longitude optional

response:
- num_detections
- detections
- processing_time_ms
```

`backend/app/core/pipeline.py`

```text
imports:
- app.core.inference.run_inference
- app.core.severity.enrich_detections_with_severity
- app.core.decision.enrich_detections_with_decision

flow:
frame -> YOLO inference -> severity enrichment -> decision enrichment -> response
```

`backend/app/core/inference.py`

```text
imports:
- os
- pathlib.Path
- numpy
- ultralytics.YOLO

model path:
- default: backend/models/pavex_v1.pt
- env override: PAVEX_MODEL_PATH

important fix:
- model path is anchored to backend directory, not current terminal directory.

output detection shape:
- class
- confidence
- bbox as [x1, y1, x2, y2]
```

`backend/app/core/severity.py`

```text
imports:
- os
- pathlib.Path
- yaml

config path:
- default: backend/app/config/severity_config.yaml
- env override: PAVEX_SEVERITY_CONFIG

important fix:
- config path is anchored to backend directory.
```

`backend/app/api/hazards.py`

```text
imports:
- datetime.datetime, datetime.timezone
- uuid.UUID
- fastapi.APIRouter, Depends, HTTPException, Query, status
- pydantic.BaseModel
- sqlalchemy.orm.Session
- app.db.connection.get_db
- app.db.crud
- app.db.models.HazardEvent

routers:
- router with prefix /hazards
- stats_router with route /statistics
```

`backend/app/db/models.py`

```text
imports:
- sqlalchemy Column, String, Float, Integer, DateTime, Enum
- sqlalchemy.dialects.postgresql.UUID
- geoalchemy2.Geometry
- uuid
- enum
- datetime.datetime
- app.db.connection.Base

important enum fix:
- SQLAlchemy Enum uses values_callable to store/read lowercase DB values.
- hazard_type DB values: pothole, speed_hump
- severity DB values: low, medium, high
```

`backend/app/db/crud.py`

```text
imports:
- sqlalchemy.orm.Session
- sqlalchemy.and_
- geoalchemy2.Geography
- geoalchemy2.functions ST_DWithin, ST_SetSRID, ST_MakePoint
- datetime.datetime, datetime.timedelta
- app.db.models HazardEvent, HazardType, SeverityLevel

important geospatial fix:
- ST_DWithin casts geometry to Geography so radius is meters.

deduplication:
- DEDUP_RADIUS_METERS = 8
- DEDUP_TIME_WINDOW_SECONDS = 5
```

`backend/app/ws/alerts_ws.py`

```text
imports:
- datetime.datetime, datetime.timezone
- fastapi.APIRouter, WebSocket, WebSocketDisconnect

route:
- websocket /ws/alerts

on connect sends:
- type: connection
- type: system_status with websocket connected and detection active
```

## Backend Routes

```text
GET    /
GET    /health
POST   /detect
GET    /hazards
POST   /hazards
GET    /hazards/nearby?latitude=...&longitude=...&radius_meters=...
GET    /hazards/{hazard_id}
PATCH  /hazards/{hazard_id}
DELETE /hazards/{hazard_id}
GET    /statistics
WS     /ws/alerts
```

`GET /health` response when healthy:

```json
{
  "status": "ok",
  "database": "connected"
}
```

Response when DB fails:

```json
{
  "status": "degraded",
  "database": "disconnected"
}
```

## Database Schema Contract

Table: `hazard_events`

```text
id UUID primary key
hazard_type VARCHAR(50) check in ('pothole', 'speed_hump')
severity VARCHAR(20) check in ('low', 'medium', 'high')
confidence FLOAT check 0..1
bbox_area_pct FLOAT check 0..100
latitude DOUBLE PRECISION
longitude DOUBLE PRECISION
location GEOMETRY(Point, 4326)
speed_recommendation INTEGER
video_source VARCHAR(255)
captured_at TIMESTAMPTZ
```

Required extensions:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

Important DB behavior:

- `hazard_type` and `severity` are lowercase strings in PostgreSQL.
- SQLAlchemy must not expect enum names like `POTHOLE`; it must use enum values like `pothole`.
- Nearby queries cast `location` and query point to `Geography` for meter-based radius.
- Frontend can send `critical`, but DB only supports `high`; backend maps `critical` to `high` before insert.

## Frontend Import Map

`frontend/src/App.tsx`

```text
imports:
- react useEffect
- react-router-dom BrowserRouter, Routes, Route, Navigate
- hooks useGeolocation, useWebSocket
- services/api.api
- store/useStore
- Navbar, Welcome, Dashboard, Analytics, Settings
- App.css

routes:
- / -> Welcome
- /dashboard -> Navbar + Dashboard
- /analytics -> Navbar + Analytics
- /settings -> Navbar + Settings
- * -> redirect /

GlobalInit:
- starts geolocation watcher
- starts WebSocket subscription
- fetches statistics and stores them
```

`frontend/src/services/api.ts`

```text
imports types:
- Detection
- HazardEvent
- DetectionResponse
- HazardsResponse
- StatsResponse
- Location
- Statistics

base URL:
- import.meta.env.VITE_API_URL
- fallback http://127.0.0.1:8000

methods:
- healthCheck -> GET /health
- detectImage -> POST /detect?latitude=...&longitude=...
- detectVideoFrame -> wraps canvas blob as frame.jpg and calls detectImage
- getNearbyHazards -> GET /hazards/nearby with radius_meters
- getHazard -> GET /hazards/{id}
- getStatistics -> GET /statistics
- reportHazard -> POST /hazards
- updateHazard -> PATCH /hazards/{id}
- deleteHazard -> DELETE /hazards/{id}
- saveDetection -> converts Detection to HazardEvent-like payload then reportHazard

important fixes:
- detection coordinates are query params, not form-data fields.
- backend bbox array [x1,y1,x2,y2] is preserved.
- backend detection class field `class` maps to frontend hazardType.
- backend snake_case hazard rows transform to frontend camelCase HazardEvent objects.
```

`frontend/src/services/websocket.ts`

```text
imports:
- Alert
- WSMessage

base URL:
- import.meta.env.VITE_WS_URL
- fallback ws://127.0.0.1:8000

connects:
- ws://127.0.0.1:8000/ws/alerts

behavior:
- auto-connects on service construction
- reconnects up to 10 times
- transforms backend hazard_alert snake_case format into frontend Alert format
- notifies connection handlers so dashboard can show Live/Offline
```

`frontend/src/hooks/index.ts`

```text
hooks:
- useGeolocation
- useWebSocket
- useMediaStream
- useDetection
- useFPS
- useReducedMotion
- useIntersectionObserver

important current behavior:
- detectImage adds detections to store history and saves to backend.
- detectVideoFrame replaces currentDetections for the current video frame, then saves detections to backend.
- replacing currentDetections prevents stale old-frame boxes from staying over new video frames.
- useMediaStream accepts an enabled flag so uploaded video mode does not also open camera.
```

`frontend/src/store/useStore.ts`

```text
library:
- Zustand
- devtools middleware
- persist middleware

state:
- currentDetections
- detectionHistory
- isDetecting
- inputSource
- alerts
- unacknowledgedAlerts
- currentLocation
- nearbyHazards
- systemStatus
- statistics
- settings
- selectedHazard
- isMapExpanded
- isSidebarOpen

persisted:
- settings
- isSidebarOpen
```

`frontend/src/components/Dashboard.tsx`

```text
imports:
- useEffect, useRef, useState
- useStore
- api
- useDetection
- LiveFeed
- MapPanel
- AlertFeed
- SpeedMeter
- HazardCard
- InputSource
- Dashboard.css

flow:
- source buttons: camera, video, image
- image mode opens image picker/dropzone and runs detectImage
- video mode opens video picker/dropzone and passes object URL to LiveFeed
- camera mode uses LiveFeed without videoSrc
- location changes trigger api.getNearbyHazards
- recent detections show HazardCard items
- source switches clear stale detections
```

`frontend/src/components/LiveFeed.tsx`

```text
imports:
- useEffect, useRef
- useMediaStream, useDetection, useFPS
- useStore
- LiveFeedProps, Detection
- LiveFeed.css

camera flow:
- useMediaStream opens camera when no videoSrc is passed.
- visible video plays live camera.
- hidden canvas captures frames.
- api.detectVideoFrame sends frame to backend ML.
- current detections are drawn on overlay canvas.

uploaded video flow:
- videoSrc object URL is loaded into same video element.
- video is paused and advanced frame-by-frame.
- cadence uses 30ms to match backend/app/core/video_stream.py cv2.waitKey(30).
- backend ML receives the same frame that is displayed.
- after backend response, video currentTime advances by 0.03 seconds.

bbox alignment:
- CSS uses object-fit: contain.
- overlay canvas matches displayed video element size.
- bbox scale uses min(display/source) for contain.
- offsetX/offsetY account for letterboxing.
- x/y coordinates are clamped to overlay bounds.
- old video-frame boxes are replaced, not appended.
```

## ML Detection Flow

The frontend does not generate detections. It captures frames and draws returned boxes.

```text
Camera or uploaded video
-> HTMLVideoElement
-> hidden canvas frame
-> Blob JPEG
-> frontend api.detectVideoFrame
-> POST /detect
-> backend api/detect.py decodes image with OpenCV
-> backend core/pipeline.py
-> backend core/inference.py
-> YOLO backend/models/pavex_v1.pt
-> bbox [x1,y1,x2,y2], class, confidence
-> severity.py enriches severity
-> decision.py enriches speed/action
-> detect.py adds latitude/longitude if available
-> frontend receives response
-> LiveFeed draws bbox overlay on video
-> saveDetection persists hazard to PostgreSQL/PostGIS
```

## Video FPS And Synchronization Notes

Backend `video_stream.py` uses:

```python
cv2.waitKey(30)
```

Frontend uploaded-video mode mirrors this:

```text
videoFrameDelay = 30 ms
videoFrameStepSeconds = 0.03
```

Reason:

- Before the fix, uploaded video played continuously while backend ML processed older frames.
- Boxes could appear late or in the wrong place because they belonged to previous frames.
- Now uploaded video pauses during backend inference and advances only after detection completes.
- This makes bbox overlays correspond to the displayed frame.

Camera mode remains live and samples detection periodically:

```text
cameraDetectionInterval = 500 ms
```

This keeps camera preview smooth while backend ML updates boxes about twice per second.

## Verification Commands Used

Frontend build:

```powershell
cd frontend
npm.cmd run build
```

Known successful result:

```text
tsc && vite build
874 modules transformed
built successfully
```

Backend import:

```powershell
backend\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend'); import app.main; print('backend import ok')"
```

DB health:

```powershell
backend\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend'); from app.db.connection import check_db_health; print(check_db_health())"
```

WebSocket verification:

```text
After installing websockets and restarting backend, /ws/alerts accepted a real WebSocket connection.
Backend log showed: WebSocket /ws/alerts [accepted]
```

DB smoke test performed:

```text
1. check_db_health returned True.
2. Inserted temporary hazard.
3. Nearby query found the temporary hazard.
4. Statistics query read totals.
5. Temporary hazard was deleted.
```

## Recent Change Log - May 6, 2026

- Stopped backend and frontend servers on request.
- Confirmed no listeners on `8000` or `5173`.
- Fixed YOLO model path to resolve from `backend/models/pavex_v1.pt` regardless of terminal working directory.
- Fixed severity config path to resolve from `backend/app/config/severity_config.yaml`.
- Confirmed DB connection works with configured Supabase/PostgreSQL database.
- Added backend startup DB success/failure logging.
- Updated `/health` to expose DB connection status.
- Added CORS for Vite dev server.
- Added `/statistics`.
- Added `/ws/alerts`.
- Installed and documented `websockets` because Uvicorn requires it for browser WebSocket support.
- Fixed SQLAlchemy enum mapping so lowercase DB values load correctly.
- Fixed hazard serializer to use `captured_at`.
- Added frontend-to-backend hazard create/read/update/delete compatibility.
- Fixed frontend detection API to send coordinates as query params.
- Fixed frontend hazard transforms from backend snake_case to frontend camelCase.
- Added frontend `.env.example`.
- Added Vite env type file `frontend/src/vite-env.d.ts`.
- Fixed TypeScript unused import/unused variable build errors.
- Added video upload picker behavior to the existing Video source button.
- Made uploaded video detection use backend ML through `/detect`.
- Synchronized uploaded-video frame stepping to backend `cv2.waitKey(30)` cadence.
- Fixed bbox display scaling with `object-fit: contain`, letterbox offsets, and clamping.
- Changed video-frame detections to replace current boxes instead of appending stale boxes.
- Cleared stale detections when switching sources.
