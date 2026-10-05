"""Rule-based spam scoring. Each rule adds points; score >= threshold means spam."""
import re
from dataclasses import dataclass, field

SPAM_WORDS = ("viagra", "casino", "crypto giveaway", "seo services", "backlinks", "loan offer", "click here", "free money", "bitcoin")
_URL = re.compile(r"https?://|www\.", re.I)


@dataclass
class SpamVerdict:
    score: int = 0
    reasons: list[str] = field(default_factory=list)

    def add(self, points: int, reason: str) -> None:
        self.score += points
        self.reasons.append(reason)


def evaluate(
    *,
    message: str | None,
    enrichment: dict,
    honeypot: str | None,
    elapsed_ms: int | None,
    is_duplicate: bool,
) -> SpamVerdict:
    v = SpamVerdict()
    text = (message or "").lower()

    if honeypot:
        v.add(10, "honeypot_filled")
    if elapsed_ms is not None and elapsed_ms < 2000:
        v.add(4, "submitted_too_fast")
    if enrichment.get("device") == "bot":
        v.add(3, "bot_user_agent")
    if enrichment.get("is_disposable_email"):
        v.add(3, "disposable_email")
    if is_duplicate:
        v.add(3, "duplicate_submission")

    links = len(_URL.findall(text))
    if links >= 3:
        v.add(4, "many_links")
    elif links >= 1:
        v.add(1, "contains_link")

    hits = sum(1 for w in SPAM_WORDS if w in text)
    if hits:
        v.add(min(hits * 2, 6), "spam_keywords")

    if message and len(message) > 20 and message.isupper():
        v.add(1, "all_caps")
    return v
