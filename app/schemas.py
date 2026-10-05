"""Request/response shapes. This is the *validation* layer for everything public."""
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ALLOWED_FIELDS = ("name", "email", "phone", "message")
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
_ORIGIN = re.compile(r"^(\*|https?://[A-Za-z0-9.-]+(:\d{1,5})?)$")
_PHONE = re.compile(r"^[0-9+()\-\s.]{5,30}$")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _clean(value: str | None) -> str | None:
    """Strip control characters and surrounding whitespace; empty -> None."""
    if value is None:
        return None
    value = _CONTROL_CHARS.sub("", value).strip()
    return value or None


# ---------- widgets ----------
class WidgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    title: str = Field(default="Get in touch", max_length=100)
    button_text: str = Field(default="Contact us", max_length=40)
    theme_color: str = "#2563eb"
    fields: list[str] = ["name", "email", "message"]
    allowed_origins: list[str] = Field(min_length=1, max_length=20)

    @field_validator("theme_color")
    @classmethod
    def _color(cls, v: str) -> str:
        if not _HEX_COLOR.match(v):
            raise ValueError("theme_color must look like #2563eb")
        return v

    @field_validator("fields")
    @classmethod
    def _fields(cls, v: list[str]) -> list[str]:
        bad = [f for f in v if f not in ALLOWED_FIELDS]
        if bad:
            raise ValueError(f"unknown fields: {bad}; allowed: {list(ALLOWED_FIELDS)}")
        if "email" not in v:
            v = [*v, "email"]
        return list(dict.fromkeys(v))  # de-duplicate, keep order

    @field_validator("allowed_origins")
    @classmethod
    def _origins(cls, v: list[str]) -> list[str]:
        out = []
        for o in v:
            o = o.strip().rstrip("/")
            if not _ORIGIN.match(o):
                raise ValueError(f"bad origin '{o}' (use https://example.com or *)")
            out.append(o)
        return out


class WidgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    title: str
    button_text: str
    theme_color: str
    fields: list[str]
    allowed_origins: list[str]
    is_active: bool
    created_at: datetime
    embed_snippet: str | None = None


class PublicWidgetConfig(BaseModel):
    """The only widget data the public internet gets to see."""
    title: str
    button_text: str
    theme_color: str
    fields: list[str]


# ---------- leads ----------
class LeadSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    message: str | None = Field(default=None, max_length=2000)
    website: str | None = Field(default=None, max_length=200)  # honeypot: humans never see it
    elapsed_ms: int | None = Field(default=None, ge=0, le=86_400_000)  # time-to-submit

    @field_validator("name", "message", "website")
    @classmethod
    def _text(cls, v: str | None) -> str | None:
        return _clean(v)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str | None) -> str | None:
        v = _clean(v)
        if v and not _PHONE.match(v):
            raise ValueError("invalid phone number")
        return v


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    email: str
    phone: str | None
    message: str | None
    status: str
    spam_score: int
    spam_reasons: list[str]
    enrichment: dict
    ip: str | None
    created_at: datetime


class DayStats(BaseModel):
    day: str
    accepted: int
    spam: int


class StatsOut(BaseModel):
    total: int
    accepted: int
    spam: int
    spam_rate: float
    by_day: list[DayStats]
