from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    allow_origins=settings.cors_origins(),
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

# Mount Frontend - DISABLED in favor of Vite Dev Server (Port 5173)
# To avoid confusion with old build files
# frontend_build_path = Path(__file__).resolve().parent.parent.parent / "interfaces" / "frontend" / "dist"
# 
# if frontend_build_path.exists():
#     # Mount static assets at /admin/assets (because vite base='/admin/')
#     app.mount("/admin/assets", StaticFiles(directory=str(frontend_build_path / "assets")), name="admin_assets")
# 
#     # Catch-all for SPA under /admin
#     @app.get("/admin/{full_path:path}")
#     async def serve_admin_app(full_path: str):
#        index_path = frontend_build_path / "index.html"
#        from fastapi.responses import FileResponse
#        return FileResponse(index_path)
# 
#     # Redirect /admin to /admin/
#     @app.get("/admin")
#     async def redirect_admin():
#         from fastapi.responses import RedirectResponse
#         return RedirectResponse(url="/admin/")
# else:
#     print(f"WARNING: Frontend build disabled for dev mode.")

@app.on_event("startup")
async def startup_event():
    # Setup Logging
    from src.utils.logger import setup_logging
    setup_logging()

    # Security checks for production
    if settings.ENV.lower() in {"prod", "production"}:
        if not settings.ANONYMIZATION_SALT or settings.ANONYMIZATION_SALT == "dev_secret_salt_CHANGE_IN_PROD":
            raise RuntimeError("ANONYMIZATION_SALT not configured for production.")
        if not settings.ADMIN_API_KEY or settings.ADMIN_API_KEY == "dev_admin_key_CHANGE_IN_PROD":
            raise RuntimeError("ADMIN_API_KEY not configured for production.")
    
    # Check DB
    _ = db_manager.chroma_client
    await db_manager.get_sqlite()
    
    # Background Maintenance
    import asyncio
    from src.utils.maintenance import cleanup_stale_uploads_periodically
    asyncio.create_task(cleanup_stale_uploads_periodically())

@app.on_event("shutdown")
async def shutdown_event():
    await db_manager.close()

@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
