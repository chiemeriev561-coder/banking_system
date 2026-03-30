from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from api.routers.auth import router as auth_router
from api.routers.accounts import router as accounts_router
from api.routers.admin import router as admin_router
from api.schemas import SystemSnapshot
from services.banking_service import BankingService
from persistence.database import engine, Base, get_db
from typing import Optional

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Banking System API",
    description="REST API for banking operations with JWT authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
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

# System endpoints
@app.get("/system/snapshot", response_model=SystemSnapshot)
async def get_system_snapshot(db: Session = Depends(get_db)):
    """Get system-wide statistics"""
    banking_service = BankingService(db)
    return banking_service.get_system_snapshot()

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Banking System API (PostgreSQL)",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
