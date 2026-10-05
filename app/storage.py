"""Storage layer: the ONLY place that talks SQL. Services never build queries."""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lead, Widget, utcnow


class WidgetRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, widget: Widget) -> Widget:
        self.db.add(widget)
        self.db.commit()
        return widget

    def get(self, widget_id: str) -> Widget | None:
        return self.db.get(Widget, widget_id)

    def list_all(self) -> list[Widget]:
        return list(self.db.scalars(select(Widget).order_by(Widget.created_at.desc())))


class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, lead: Lead) -> Lead:
        self.db.add(lead)
        self.db.commit()
        return lead

    def list_for_widget(
        self, widget_id: str, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Lead]:
        q = select(Lead).where(Lead.widget_id == widget_id)
        if status:
            q = q.where(Lead.status == status)
        q = q.order_by(Lead.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(q))

    def has_recent_duplicate(self, widget_id: str, email: str, since: datetime) -> bool:
        q = select(func.count()).select_from(Lead).where(
            Lead.widget_id == widget_id, Lead.email == email, Lead.created_at >= since
        )
        return (self.db.scalar(q) or 0) > 0

    def stats(self, widget_id: str, days: int = 7) -> dict:
        totals = dict(
            self.db.execute(
                select(Lead.status, func.count()).where(Lead.widget_id == widget_id).group_by(Lead.status)
            ).all()
        )
        since = utcnow() - timedelta(days=days)
        day = func.date(Lead.created_at)
        rows = self.db.execute(
            select(day, Lead.status, func.count())
            .where(Lead.widget_id == widget_id, Lead.created_at >= since)
            .group_by(day, Lead.status)
            .order_by(day)
        ).all()

        by_day: dict[str, dict] = {}
        for d, status, n in rows:
            entry = by_day.setdefault(str(d), {"day": str(d), "accepted": 0, "spam": 0})
            entry[status] = n
        return {
            "accepted": totals.get("accepted", 0),
            "spam": totals.get("spam", 0),
            "by_day": list(by_day.values()),
        }
