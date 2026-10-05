from app.services.enrichment import enrich
from app.services.spam import evaluate


def run(**kw):
    base = dict(message="Hi, I'd like a demo.", enrichment=enrich("a@acme.com", "Mozilla/5.0", None, None),
                honeypot=None, elapsed_ms=8000, is_duplicate=False)
    base.update(kw)
    return evaluate(**base)


def test_clean_lead_scores_zero():
    assert run().score == 0


def test_honeypot_alone_is_spam():
    assert run(honeypot="http://spam.biz").score >= 5


def test_fast_bot_with_links_is_spam():
    info = enrich("x@mailinator.com", "python-requests/2.31", None, None)
    v = run(message="buy bitcoin http://a.co http://b.co http://c.co", enrichment=info, elapsed_ms=300)
    assert v.score >= 5
    assert "disposable_email" in v.reasons and "bot_user_agent" in v.reasons


def test_enrichment_flags():
    info = enrich("me@gmail.com", "Mozilla/5.0 (iPhone)", "https://shop.com", "PK")
    assert info["is_free_email"] and info["device"] == "mobile" and info["country"] == "PK"
