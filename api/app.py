from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers.auth import router as auth_router
from api.routers.accounts import router as accounts_router
from api.routers.admin import router as admin_router
from api.schemas import SystemSnapshot
from services.banking_service import BankingService
from bank import Bank
from persistence.store import load_data, save_data, clear_data
from typing import Optional

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

# Global bank instance
_bank: Optional[Bank] = None

def get_bank() -> Bank:
    """Get or create bank instance"""
    global _bank
    if _bank is None:
        _bank = load_data() or Bank("Secure Bank")
    return _bank

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
async def get_system_snapshot():
    """Get system-wide statistics"""
    bank = get_bank()
    banking_service = BankingService(bank)
    return banking_service.get_system_snapshot()

@app.post("/system/save")
async def save_system_data():
    """Save all system data"""
    bank = get_bank()
    success = save_data(bank)
    if success:
        return {"message": "Data saved successfully"}
    else:
        return {"error": "Failed to save data"}

@app.post("/system/clear")
async def clear_system_data():
    """Clear all system data (dangerous!)"""
    global _bank
    success = clear_data()
    if success:
        _bank = Bank("Fresh Bank")  # Reset to fresh bank
        return {"message": "All data cleared"}
    else:
        return {"message": "No data to clear"}

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Banking System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)