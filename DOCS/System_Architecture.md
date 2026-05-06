# System Architecture Document

## High-Level Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Vehicle       │    │   PaveX Backend  │    │   PaveX Frontend   │
│   Camera System │◄──►│   (FastAPI)      │◄──►│   (SPA Dashboard)  │
│                 │    │                  │    │                      │
│  - USB/IP Camera│    │  - Model Service │    │  - Video Feed      │
│  - Power Supply │    │  - Detection API │    │  - Hazard Overlays │
│  - Processing   │    │  - WebSocket Srv │    │  - Alert System    │
│    Unit         │    │  - Stats Manager │    │  - Map View        │
└─────────────────┘    └──────────────────┘    └────────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │   YOLOv8 Model   │
                     │   (Ultralytics)  │
                     └──────────────────┘
```

## Component Details

### 1. Vehicle Camera System
- Captures video stream from front-facing vehicle camera
- Provides raw video frames to the processing unit
- May include preprocessing (resizing, format conversion)

### 2. PaveX Backend (FastAPI Application)
- **API Layer**: RESTful endpoints for configuration and status
- **WebSocket Layer**: Real-time bidirectional communication
- **Model Service**: YOLOv8 model loading and inference execution
- **Processing Pipeline**: Frame preprocessing → Model inference → Post-processing
- **State Management**: Hazard statistics, detection history, system metrics
- **Configuration Service**: Centralized configuration management

### 3. PaveX Frontend (Single Page Application)
- **Presentation Layer**: HTML/CSS/JavaScript UI
- **Media Layer**: Video capture and display functionality
- **Visualization Layer**: Hazard overlays, mapping, charts
- **Interaction Layer**: User controls, settings, alerts
- **Communication Layer**: WebSocket client for real-time updates

### 4. YOLOv8 Model
- Pre-trained object detection model fine-tuned for road hazards
- Detects two classes: potholes and speed humps
- Outputs bounding boxes, class IDs, and confidence scores
- Optimized for real-time inference on CPU

## Data Flow
1. Video frames captured by vehicle camera system
2. Frames sent to backend via WebSocket (or REST for initial implementation)
3. Backend preprocesses frames (resize, normalize)
4. YOLOv8 model processes frames and returns detections2
5. Post-processing converts raw detections to hazard objects
6. Hazard data stored in memory and sent to frontend via WebSocket
7. Frontend updates UI with detections, statistics, and alerts
8. Hazard history persisted in browser storage (localStorage)

## External Interfaces
- **Input**: USB/IP video stream (640x480 recommended)
- **Output**: Visual dashboard with real-time overlays
- **Control**: Web-based UI for settings and configuration
- **Persistence**: Browser localStorage for hazard history
- **Communication**: HTTP REST API and WebSocket (ws://localhost:8000)
