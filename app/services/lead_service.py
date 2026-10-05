"""The lead pipeline: guard -> sanitize -> enrich -> spam-filter -> store."""
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import ForbiddenError, NotFoundError, RateLimitedError
from app.models import Lead, utcnow
from app.schemas import LeadSubmit, StatsOut
from app.security import limiter, origin_allowed
from app.services import enrichment, spam, widget_service
from app.storage import LeadRepository, WidgetRepository


@dataclass
class RequestContext:
    ip: str
    user_agent: str
    origin: str | None
    country: str | None


def submit_lead(db: Session, widget_id: str, payload: LeadSubmit, ctx: RequestContext) -> Lead:
    settings = get_settings()

    # 1. guards
    widget = WidgetRepository(db).get(widget_id)
    if widget is None or not widget.is_active:
        raise NotFoundError("Widget not found")
    if not origin_allowed(widget, ctx.origin):
        raise ForbiddenError("Origin not allowed")
    if not limiter.allow(f"{widget_id}:{ctx.ip}", settings.rate_limit_per_minute):
        raise RateLimitedError("Too many submissions, try again in a minute")

    # 2. sanitize: only keep fields this widget actually asks for
    email = payload.email.lower()
    data = {f: getattr(payload, f) for f in ("name", "phone", "message") if f in widget.fields}

    # 3. enrich
    info = enrichment.enrich(email, ctx.user_agent, ctx.origin, ctx.country)

    # 4. spam filter
    leads = LeadRepository(db)
    since = utcnow() - timedelta(minutes=settings.duplicate_window_minutes)
    verdict = spam.evaluate(
        message=data.get("message"),
        enrichment=info,
        honeypot=payload.website,
        elapsed_ms=payload.elapsed_ms,
        is_duplicate=leads.has_recent_duplicate(widget_id, email, since),
    )
    status = "spam" if verdict.score >= settings.spam_threshold else "accepted"

    # 5. store (spam is kept, flagged, so you can review false positives)
    return leads.add(
        Lead(
            widget_id=widget_id,
            email=email,
            status=status,
            spam_score=verdict.score,
            spam_reasons=verdict.reasons,
            enrichment=info,
            ip=ctx.ip,
            user_agent=ctx.user_agent,
            origin=ctx.origin,
            **data,
        )
    )


def list_leads(db: Session, widget_id: str, status: str | None, limit: int, offset: int) -> list[Lead]:
    widget_service.require_widget(db, widget_id)
    return LeadRepository(db).list_for_widget(widget_id, status, limit, offset)


def get_stats(db: Session, widget_id: str) -> StatsOut:
    widget_service.require_widget(db, widget_id)
    s = LeadRepository(db).stats(widget_id)
    total = s["accepted"] + s["spam"]
    return StatsOut(
        total=total,
        accepted=s["accepted"],
        spam=s["spam"],
        spam_rate=round(s["spam"] / total, 3) if total else 0.0,
        by_day=s["by_day"],
    )
