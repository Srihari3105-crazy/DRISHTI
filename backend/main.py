"""
DRISHTI-LENS Backend — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config import settings
from core.database import init_db, close_db
from core.events import event_bus, Events
from services.notification_service import on_appointment_scheduled, on_visit_verified
from services.doctor_verify_service import load_doctor_csv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("drishti-lens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup + shutdown."""
    logger.info("=" * 60)
    logger.info("  DRISHTI-LENS MVP Backend Starting...")
    logger.info("=" * 60)

    # Initialize database tables
    await init_db()
    logger.info("✓ Database tables created")

    # Load doctor registry CSV
    load_doctor_csv()
    logger.info("✓ Doctor registry CSV loaded")

    # Register event handlers
    event_bus.subscribe(Events.APPOINTMENT_SCHEDULED, on_appointment_scheduled)
    event_bus.subscribe(Events.VISIT_VERIFIED, on_visit_verified)
    logger.info("✓ Event handlers registered")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"✓ Upload directory ready: {settings.UPLOAD_DIR}")

    logger.info("=" * 60)
    logger.info(f"  Server running at http://localhost:8000")
    logger.info(f"  API docs at http://localhost:8000/docs")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down DRISHTI-LENS backend...")
    event_bus.clear()
    await close_db()
    logger.info("Shutdown complete.")


# Create FastAPI app
app = FastAPI(
    title="DRISHTI-LENS MVP API",
    description=(
        "Offline-First Diabetic Retinopathy Screening Loop — "
        "Capture → Grade → Refer → Assign → Schedule → Visit → Close"
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded images
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API routers
from api.auth import router as auth_router
from api.patients import router as patients_router
from api.screenings import router as screenings_router
from api.referrals import router as referrals_router
from api.doctors import router as doctors_router
from api.officers import router as officers_router
from api.exports import router as exports_router
from api.pincode import router as pincode_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(screenings_router, prefix="/api/v1")
app.include_router(referrals_router, prefix="/api/v1")
app.include_router(doctors_router, prefix="/api/v1")
app.include_router(officers_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(pincode_router, prefix="/api/v1")



@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "DRISHTI-LENS MVP",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
