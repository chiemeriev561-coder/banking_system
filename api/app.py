from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
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

# Add HTTPS redirect middleware for production
if os.getenv('FORCE_HTTPS', 'false').lower() == 'true':
    app.add_middleware(HTTPSRedirectMiddleware)

# Add CORS middleware
def get_cors_origins():
    """Get allowed origins from environment or use localhost for development"""
    allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000')
    return [origin.strip() for origin in allowed_origins.split(',') if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Be more specific
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
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.datetime.now(datetime.UTC).isoformat()}

@app.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check - includes database connectivity"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}, 503

# System endpoints
@app.get("/system/snapshot", response_model=SystemSnapshot)
async def get_system_snapshot(db: Session = Depends(get_db)):
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
