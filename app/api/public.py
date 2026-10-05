"""Public endpoints, called from customers' websites by embed.js."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import LeadSubmit, PublicWidgetConfig
from app.security import client_ip
from app.services import lead_service, widget_service
from app.services.lead_service import RequestContext

router = APIRouter(prefix="/public", tags=["public"])


def _ctx(request: Request) -> RequestContext:
    return RequestContext(
        ip=client_ip(request),
        user_agent=(request.headers.get("user-agent") or "")[:300],
        origin=request.headers.get("origin"),
        country=request.headers.get("cf-ipcountry"),
    )


@router.get("/widgets/{widget_id}/config", response_model=PublicWidgetConfig)
def widget_config(widget_id: str, request: Request, db: Session = Depends(get_db)):
    return widget_service.get_public_config(db, widget_id, request.headers.get("origin"))


@router.post("/widgets/{widget_id}/leads", status_code=201)
def submit(widget_id: str, payload: LeadSubmit, request: Request, db: Session = Depends(get_db)):
    lead_service.submit_lead(db, widget_id, payload, _ctx(request))
    # Same answer for accepted and spam: never tell a bot it was caught.
    return {"ok": True}
