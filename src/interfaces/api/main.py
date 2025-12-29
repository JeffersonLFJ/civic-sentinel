from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from src.config import settings
from src.interfaces.api.routes import health, chat, upload, documents, admin
from src.core.database import db_manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="API for Sentinel Civic v2.0 - Justice Epistemic Algorithmic"
)

# CORS (Configured for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/health", tags=["System"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(upload.router, prefix="/api/upload", tags=["Documents"])
app.include_router(documents.router, prefix="/api/documents", tags=["Management"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Tools"])

# Mount Admin Static Files
# Ensure directory exists to avoid startup error
admin_path = Path(__file__).resolve().parent.parent / "admin"
admin_path.mkdir(parents=True, exist_ok=True)

app.mount("/admin", StaticFiles(directory=str(admin_path), html=True), name="admin")

@app.on_event("startup")
async def startup_event():
    # Setup Logging
    from src.utils.logger import setup_logging
    setup_logging()
    
    # Check DB
    _ = db_manager.chroma_client
    await db_manager.get_sqlite()
    
    # Background Maintenance
    import asyncio
    from src.utils.maintenance import cleanup_stale_uploads
    asyncio.create_task(cleanup_stale_uploads())

@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
