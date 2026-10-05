"""Business logic for widgets."""
import secrets

from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import ForbiddenError, NotFoundError
from app.models import Widget
from app.schemas import PublicWidgetConfig, WidgetCreate
from app.security import origin_allowed
from app.storage import WidgetRepository


def embed_snippet(widget: Widget) -> str:
    base = get_settings().public_base_url.rstrip("/")
    return f'<script src="{base}/embed.js" data-widget="{widget.id}" async></script>'


def create_widget(db: Session, data: WidgetCreate) -> Widget:
    widget = Widget(id="wgt_" + secrets.token_urlsafe(8), **data.model_dump())
    return WidgetRepository(db).add(widget)


def list_widgets(db: Session) -> list[Widget]:
    return WidgetRepository(db).list_all()


def require_widget(db: Session, widget_id: str) -> Widget:
    widget = WidgetRepository(db).get(widget_id)
    if widget is None:
        raise NotFoundError("Widget not found")
    return widget


def get_public_config(db: Session, widget_id: str, origin: str | None) -> PublicWidgetConfig:
    widget = require_widget(db, widget_id)
    if not widget.is_active:
        raise NotFoundError("Widget not found")
    if not origin_allowed(widget, origin):
        raise ForbiddenError("Origin not allowed")
    return PublicWidgetConfig(
        title=widget.title,
        button_text=widget.button_text,
        theme_color=widget.theme_color,
        fields=widget.fields,
    )
