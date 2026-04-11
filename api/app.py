from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import datetime
from api.routers.auth import router as auth_router
from api.routers.accounts import router as accounts_router
from api.routers.admin import router as admin_router
from api.schemas import SystemSnapshot
from services.banking_service import BankingService
from persistence.database import engine, Base, get_db
from typing import Optional

# Create FastAPI app
app = FastAPI(
    title="Banking System API",
    description="REST API for banking operations with JWT authentication",
    version="1.0.0"
)

# Add CORS middleware
def get_cors_origins():
    """Get allowed origins from environment or use localhost for development"""
    allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000')
    origins = [origin.strip() for origin in allowed_origins.split(',') if origin.strip()]
    # If '*' is in origins, but we want credentials, we must use a list of origins.
    # CORSMiddleware will handle this by returning the request's origin if it matches.
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods for flexibility
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

app.include_router(
    accounts_router,
    prefix="/api",
    tags=["Banking Operations"]
)

app.include_router(
    admin_router,
    prefix="/admin",
    tags=["Admin Operations"]
)

# Health check endpoints
@app.get("/health")
def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.datetime.now(datetime.UTC).isoformat()}

@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Readiness check - includes database connectivity"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected", "error": str(e)}
        )

# System endpoints
@app.get("/system/snapshot", response_model=SystemSnapshot)
def get_system_snapshot(db: Session = Depends(get_db)):
    """Get system-wide statistics"""
    banking_service = BankingService(db)
    return banking_service.get_system_snapshot()

# Root endpoint with security headers
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Banking System API (PostgreSQL)",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
