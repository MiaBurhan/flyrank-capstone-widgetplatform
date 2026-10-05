"""Admin endpoints (protected by the X-Admin-Key header)."""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LeadOut, StatsOut, WidgetCreate, WidgetOut
from app.security import require_admin
from app.services import lead_service, widget_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _out(widget) -> WidgetOut:
    out = WidgetOut.model_validate(widget)
    out.embed_snippet = widget_service.embed_snippet(widget)
    return out


@router.post("/widgets", response_model=WidgetOut, status_code=201)
def create_widget(data: WidgetCreate, db: Session = Depends(get_db)):
    return _out(widget_service.create_widget(db, data))


@router.get("/widgets", response_model=list[WidgetOut])
def list_widgets(db: Session = Depends(get_db)):
    return [_out(w) for w in widget_service.list_widgets(db)]


@router.get("/widgets/{widget_id}/leads", response_model=list[LeadOut])
def list_leads(
    widget_id: str,
    status: Literal["accepted", "spam"] | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return lead_service.list_leads(db, widget_id, status, limit, offset)


@router.get("/widgets/{widget_id}/stats", response_model=StatsOut)
def stats(widget_id: str, db: Session = Depends(get_db)):
    return lead_service.get_stats(db, widget_id)
