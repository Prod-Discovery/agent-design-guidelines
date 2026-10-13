"""Usage tracking: who uses the site, what they read, and how they use Assess.

Every event is one Firestore document in `usage_events`, with the visitor's
company domain (from the Visma sign-in) and an anonymous visitor id. The email
itself, and anything people upload to the Claude review, are never stored.
Events expire after 90 days (Firestore TTL on `expire_at`).

The page sends events to POST /api/event. Only the names and fields listed in
EVENTS are accepted, so the endpoint can't be used to store anything else.
The Claude review and ideas are recorded on the server (see app.py).
"""

import datetime
import hashlib
import hmac
import logging
import os
import secrets

from google.cloud import firestore

log = logging.getLogger("assess-agent")

# Cloud Run sets K_SERVICE. Runs on a laptop write to dev_ collections, so tests
# never show up in the real numbers.
_PREFIX = "" if os.environ.get("K_SERVICE") else "dev_"
COLLECTION = _PREFIX + "usage_events"
FEEDBACK = _PREFIX + "usage_feedback"
RETENTION_DAYS = 90
ROLES = ["Designer", "Product manager", "Developer", "Researcher", "Manager", "Other"]

# Event name -> allowed fields and how to clean each one.
_short = lambda v: str(v)[:80]  # noqa: E731
_level = lambda v: int(v) if v in (0, 1, 2) else None  # noqa: E731
EVENTS = {
    "page_view": {"route": _short},
    "demo_click": {"demo": _short},
    "plugin_click": {},
    "assess_answer": {"question": _short, "level": _level},
    "review_override": {"question": _short, "claude": _level, "person": _level},
    "assess_complete": {"domain": _short, "score": lambda v: max(0, min(100, int(v))),
                        "verdict": _short, "used_review": bool},
    "results_view": {},
    "copy_summary": {},
    "role_set": {"role": lambda v: v if v in ROLES else "Other"},
}


def visitor(headers):
    """(anonymous visitor id, company domain) from the IAP sign-in header."""
    raw = headers.get("X-Goog-Authenticated-User-Email", "")
    email = raw.split(":", 1)[-1].strip().lower()
    if "@" not in email:
        return "anonymous", "unknown"
    digest = hmac.new(_salt(), email.encode(), hashlib.sha256).hexdigest()[:16]
    return digest, email.split("@", 1)[1]


_SALT = None


def _salt():
    """A random secret kept in Firestore, so visitor ids can't be turned back into emails."""
    global _SALT
    if _SALT is None:
        ref = firestore.Client().collection("assess_config").document("visitor_salt")
        snap = ref.get()
        if not snap.exists:
            ref.create({"value": secrets.token_hex(32)})
            snap = ref.get()
        _SALT = snap.to_dict()["value"].encode()
    return _SALT


def clean(name, props):
    """The event's fields, keeping only what EVENTS allows. None if the name is unknown."""
    if name not in EVENTS or not isinstance(props, dict):
        return None
    out = {}
    for key, fix in EVENTS[name].items():
        if key in props and props[key] is not None:
            try:
                out[key] = fix(props[key])
            except (TypeError, ValueError):
                pass
    return out


def record(db, headers, name, props=None, role=None, collection=COLLECTION):
    """Stores one event. Never raises: tracking must not break the site."""
    try:
        vid, domain = visitor(headers)
        now = datetime.datetime.now(datetime.timezone.utc)
        doc = {
            "name": name,
            "props": props or {},
            "visitor": vid,
            "company": domain,
            "day": now.strftime("%Y-%m-%d"),
            "ts": now,
            "expire_at": now + datetime.timedelta(days=RETENTION_DAYS),
        }
        if role in ROLES:
            doc["role"] = role
        db.collection(collection).add(doc)
    except Exception as e:  # noqa: BLE001
        log.error("usage: could not record %s: %s", name, e)


def summary(db, days=30):
    """Everything the stats page shows, counted over the last `days` days."""
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    events = [d.to_dict() for d in db.collection(COLLECTION).where("ts", ">=", since).stream()]
    feedback = [d.to_dict() for d in db.collection(FEEDBACK).where("ts", ">=", since).stream()]
    spend = {d.id: d.to_dict() for d in db.collection("assess_spend").stream() if d.id >= since.strftime("%Y-%m-%d")}

    def count(items, key):
        out = {}
        for i in items:
            k = key(i)
            if k is not None:
                out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: (-kv[1], str(kv[0]))))

    def unique(items, key):
        out = {}
        for i in items:
            out.setdefault(key(i), set()).add(i["visitor"])
        return dict(sorted(((k, len(v)) for k, v in out.items()), key=lambda kv: (-kv[1], str(kv[0]))))

    by = lambda n: [e for e in events if e["name"] == n]  # noqa: E731
    week_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    roles = {}
    for e in events:
        if e.get("role"):
            roles[e["visitor"]] = e["role"]
    reviews = by("review_run")
    overrides = by("review_override")
    reviewed_answers = sum(len(e["props"].get("filled", [])) for e in reviews) or 0
    assess_visitors = {e["visitor"] for e in by("page_view") if e["props"].get("route") == "assess"}
    return {
        "days": days,
        "visitors": len({e["visitor"] for e in events}),
        "visitors_7d": len({e["visitor"] for e in events if e["day"] >= week_ago}),
        "returning": sum(1 for v in unique(events, lambda e: e["visitor"]).values() if v > 1),
        "visitors_per_day": unique(events, lambda e: e["day"]),
        "companies": unique(events, lambda e: e["company"]),
        "roles": count(roles.items(), lambda kv: kv[1]),
        "pages": count(by("page_view"), lambda e: e["props"].get("route")),
        "demo_clicks": count(by("demo_click"), lambda e: e["props"].get("demo")),
        "plugin_clicks": len(by("plugin_click")),
        "funnel": [
            ("Opened Assess your agent", len(assess_visitors)),
            ("Answered at least one question", len({e["visitor"] for e in by("assess_answer")} | {e["visitor"] for e in reviews})),
            ("Ran a Claude review", len({e["visitor"] for e in reviews})),
            ("Answered all six (got a score)", len({e["visitor"] for e in by("assess_complete")})),
            ("Opened their improvements", len({e["visitor"] for e in by("results_view")})),
            ("Asked for ideas", len({e["visitor"] for e in by("ideas_run")})),
            ("Copied the summary", len({e["visitor"] for e in by("copy_summary")})),
            ("Left feedback", len({f["visitor"] for f in feedback})),
        ],
        "review_modes": count(reviews, lambda e: {"instructions": "Agent instructions", "spec": "Prototype"}.get(e["props"].get("mode"))),
        "domains": count(by("assess_complete"), lambda e: e["props"].get("domain")),
        "verdicts": count(by("assess_complete"), lambda e: e["props"].get("verdict")),
        "reviews": len(reviews),
        "review_errors": len(by("review_error")),
        "reviewed_answers": reviewed_answers,
        "overrides": len(overrides),
        "overrides_by_question": count(overrides, lambda e: e["props"].get("question")),
        "feedback": sorted(feedback, key=lambda f: f["ts"], reverse=True),
        "spend": dict(sorted(spend.items(), reverse=True)),
    }
