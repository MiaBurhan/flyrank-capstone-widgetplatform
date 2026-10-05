"""Add useful context to a lead (no external calls, so it is fast and offline)."""

FREE_PROVIDERS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "proton.me", "protonmail.com"}
DISPOSABLE_DOMAINS = {"mailinator.com", "10minutemail.com", "guerrillamail.com", "tempmail.com", "yopmail.com", "trashmail.com"}
BOT_MARKERS = ("bot", "crawler", "spider", "curl", "python-requests", "httpclient", "headless", "scrapy")


def _device(user_agent: str) -> str:
    ua = user_agent.lower()
    if not ua:
        return "unknown"
    if any(m in ua for m in BOT_MARKERS):
        return "bot"
    if any(m in ua for m in ("mobile", "android", "iphone")):
        return "mobile"
    return "desktop"


def enrich(email: str, user_agent: str, origin: str | None, country: str | None) -> dict:
    domain = email.rsplit("@", 1)[-1].lower()
    return {
        "email_domain": domain,
        "is_free_email": domain in FREE_PROVIDERS,
        "is_disposable_email": domain in DISPOSABLE_DOMAINS,
        "device": _device(user_agent),
        "source_origin": origin,
        "country": country,  # e.g. from a CDN header like CF-IPCountry
    }
