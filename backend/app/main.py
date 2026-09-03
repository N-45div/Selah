import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import root_dir
from .routes import plan, console, closeout

app = FastAPI(
    title="Selah Telecast Copilot",
    description="The live telecast copilot for church media volunteers. Keeps church livestreams legal, active, and unmuted.",
    version="1.0.0"
)

# CORS middleware — allow_credentials=True is invalid with allow_origins=["*"] per spec.
# For a public demo, wildcard origin without credentials is correct.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(plan.router)
app.include_router(console.router)
app.include_router(closeout.router)

dist_dir = root_dir / "frontend" / "dist"
assets_dir = dist_dir / "assets"

if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Cloud Run and automated evaluators."""
    return {
        "ok": True,
        "app": "Selah",
        "version": "1.0.0",
        "sdk": "google-adk + google-genai + parallel-web"
    }


# Catch-all SPA route — MUST NOT swallow /api/ routes.
# Only serves index.html for non-API, non-asset paths.
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Never serve HTML for API routes — return proper 404 JSON
    if full_path.startswith("api/") or full_path.startswith("api"):
        return JSONResponse(
            status_code=404,
            content={"detail": f"API endpoint '/{full_path}' not found."}
        )

    index_file = dist_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": "Selah API is running. Build frontend with 'npm run build' in frontend/ or start Vite dev server."
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=True)
