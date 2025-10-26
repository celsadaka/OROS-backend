from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from .models.base import Base
from .models import *  
from .routes import (
    doctors,
    patients,
    notes,
    transcriptions,
    surgeries,
    operating_rooms,
    notifications,
    dashboard,
)
from . import auth 


# Create FastAPI app instance
app = FastAPI(
    title="OROS API",
    description="Backend API for the OROS Doctor–Patient Recording and Operating Room Management System.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
app.include_router(patients.router, prefix="/patients", tags=["Patients"])
app.include_router(notes.router, prefix="/notes", tags=["Notes"])
app.include_router(transcriptions.router, prefix="/transcriptions", tags=["Transcriptions"])
app.include_router(surgeries.router, prefix="/surgeries", tags=["Surgeries"])
app.include_router(operating_rooms.router, prefix="/operating-rooms", tags=["Operating Rooms"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(auth.router)  
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

@app.get("/", tags=["Root"])
def root():
    """Basic root endpoint for API health check."""
    return {
        "status": "running",
        "message": "Welcome to the OROS API",
        "docs_url": "/docs",
        "endpoints": [
            "/auth/login",
            "/auth/me",
            "/doctors",
            "/patients",
            "/notes",
            "/transcriptions",
            "/surgeries",
            "/operating-rooms",
            "/notifications",
        ],
    }
