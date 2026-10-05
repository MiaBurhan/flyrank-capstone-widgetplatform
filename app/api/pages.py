"""Serves the embeddable script and the dashboard page."""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

STATIC = Path(__file__).resolve().parent.parent / "static"
router = APIRouter()


@router.get("/embed.js", include_in_schema=False)
def embed_js():
    return FileResponse(
        STATIC / "embed.js",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC / "dashboard.html")
