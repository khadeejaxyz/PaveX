"""
PaveX API - Central FastAPI Backend Controller
AI-based real-time road hazard detection system
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.detect import router as detect_router
from app.api.hazards import router as hazards_router, stats_router
from app.ws.alerts_ws import router as alerts_ws_router
from app.db.connection import check_db_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="PaveX API",
    description="AI-based real-time road hazard detection system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detect_router)
app.include_router(hazards_router)
app.include_router(stats_router)
app.include_router(alerts_ws_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PaveX API is running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    db_connected = check_db_health()
    return {
        "status": "ok" if db_connected else "degraded",
        "database": "connected" if db_connected else "disconnected",
    }


@app.on_event("startup")
async def startup_event():
    """Log when server starts"""
    logger.info("PaveX API server starting...")
    logger.info("API documentation available at /docs")

    if check_db_health():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
