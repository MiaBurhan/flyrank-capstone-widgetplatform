"""Database tables."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)  # public id, e.g. wgt_abc123
    name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(100), default="Get in touch")
    button_text: Mapped[str] = mapped_column(String(40), default="Contact us")
    theme_color: Mapped[str] = mapped_column(String(7), default="#2563eb")
    fields: Mapped[list] = mapped_column(JSON, default=list)
    allowed_origins: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    leads: Mapped[list["Lead"]] = relationship(back_populates="widget")


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (Index("ix_leads_widget_created", "widget_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    widget_id: Mapped[str] = mapped_column(ForeignKey("widgets.id"), index=True)

    name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    message: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(10), index=True)  # "accepted" | "spam"
    spam_score: Mapped[int] = mapped_column(Integer, default=0)
    spam_reasons: Mapped[list] = mapped_column(JSON, default=list)
    enrichment: Mapped[dict] = mapped_column(JSON, default=dict)

    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    origin: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    widget: Mapped[Widget] = relationship(back_populates="leads")
