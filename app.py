"""The Agent Design Guidelines site on Cloud Run, plus the two endpoints of
"Assess your agent" that call Claude on Vertex AI.

    GET  /, /patterns.json, /patterns.md, /demo/*.html   the site
    POST /api/review   {mode: "instructions" | "spec", text}
    POST /api/ideas    {domain, description, answers: {key: 0 | 1 | 2}}
    POST /api/event    {name, props, role}       usage tracking, see usage.py
    POST /api/feedback {rating, text, role, score, verdict}
    GET  /stats        usage numbers, only for STATS_VIEWERS
    GET  /health

There is no Anthropic API key. Claude runs on Vertex AI in the GCP project,
and the Cloud Run service account (or your gcloud login, locally) is the
credential. Uploaded material is never logged or stored: only sizes, token
counts and cost are.
"""

import datetime
import json
import logging
import os
import time

import anthropic
from anthropic import AnthropicVertex
from flask import Flask, jsonify, request, send_from_directory
from google.auth.transport import requests as google_requests
from google.cloud import firestore
from google.oauth2 import id_token as google_id_token

import review
import stats_page
import usage

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "prod-vpepf-cm")
# "eu" keeps processing in the EU. Single regions such as europe-west1 have no quota.
VERTEX_REGION = os.environ.get("VERTEX_REGION", "eu")
REVIEW_MODEL = os.environ.get("REVIEW_MODEL", "claude-opus-5-5")
IDEAS_MODEL = os.environ.get("IDEAS_MODEL", "claude-sonnet-5-5")
REVIEW_EFFORT = os.environ.get("REVIEW_EFFORT", "medium")
IDEAS_EFFORT = os.environ.get("IDEAS_EFFORT", "low")
# Rejects uploads that are far beyond what a review can use, before calling Claude.
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 1_000_000))

# USD per million tokens, Vertex AI eu. Sonnet input is confirmed on the
# pricing page; the rest assume the same +10% over Anthropic's list price.
PRICES = {
    "claude-opus-5-5": (4.40, 22.00),
    "claude-sonnet-5-5": (2.20, 11.00),
}
# If a model declines a request, it is retried once on the other one.
FALLBACK = {"claude-opus-5-5": "claude-sonnet-5-5", "claude-sonnet-5-5": "claude-opus-5-5"}

# Hard stop on Claude spend per UTC day, across everyone. When it's reached, the
# Claude review and ideas pause until midnight UTC; the questionnaire keeps working.
# $15 is about 240 reviews a day (each with an ideas call), and at most about $450 a month.
DAILY_BUDGET_USD = float(os.environ.get("DAILY_BUDGET_USD", 15))
# Firestore in the same project (DiscoveryBot uses other collections there).
SPEND = "assess_spend"
# Who may open /stats: comma-separated Visma sign-in emails.
STATS_VIEWERS = {e.strip().lower() for e in os.environ.get("STATS_VIEWERS", "cristina.iftode@visma.com").split(",") if e.strip()}

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("assess-agent")

client = AnthropicVertex(project_id=PROJECT_ID, region=VERTEX_REGION)
db = firestore.Client(project=PROJECT_ID)
app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES + 10_000


class ReviewError(Exception):
    def __init__(self, code, status):
        super().__init__(code)
        self.code, self.status = code, status


def _today():
    return db.collection(SPEND).document(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"))


def check_budget():
    """Refuses the call once today's spend has reached the daily budget.

    If Firestore can't be read, the call goes ahead: --max-instances still caps
    spend, and a Firestore hiccup shouldn't take the review down.
    """
    try:
        snap = _today().get()
        spent = (snap.to_dict() or {}).get("cost_usd", 0) if snap.exists else 0
    except Exception as e:  # noqa: BLE001 - any Firestore failure fails open
        log.error("daily budget: could not read today's spend: %s", e)
        return
    if spent >= DAILY_BUDGET_USD:
        log.warning("daily budget reached: $%.2f of $%.2f", spent, DAILY_BUDGET_USD)
        raise ReviewError("daily_limit", 429)


def record_spend(report):
    try:
        _today().set(
            {"cost_usd": firestore.Increment(report["cost_usd"]), "calls": firestore.Increment(1)},
            merge=True,
        )
    except Exception as e:  # noqa: BLE001
        log.error("daily budget: could not record spend: %s", e)


def cost(model, usage):
    p_in, p_out = PRICES.get(model, (0, 0))
    return (usage.input_tokens * p_in + usage.output_tokens * p_out) / 1_000_000


def ask_claude(endpoint, model, effort, system, user, max_tokens):
    """Ask Claude for a JSON reply. Returns (parsed JSON, usage report).

    Tries twice: a refusal moves to the other model, and a reply that isn't
    valid JSON is asked again once.
    """
    check_budget()
    started = time.monotonic()
    report = {"model": model, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "attempts": 0}
    data = None
    try:
        data, model = _ask(endpoint, model, effort, system, user, max_tokens, report)
    finally:
        # Recorded even when the call fails halfway, so a retry loop can't overspend.
        if report["cost_usd"]:
            record_spend(report)
    report["cost_usd"] = round(report["cost_usd"], 4)
    report["seconds"] = round(time.monotonic() - started, 1)
    log.info("%s %s", endpoint, json.dumps(report))
    if data is None:
        raise ReviewError("invalid_json", 502)
    return data, report


def _ask(endpoint, model, effort, system, user, max_tokens, report):
    data = None
    for _ in range(2):
        report["attempts"] += 1
        try:
            r = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"effort": effort},
            )
        except anthropic.RateLimitError:
            raise ReviewError("rate_limited", 429)
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            log.error("%s Claude call failed: %s", endpoint, e)
            raise ReviewError("unavailable", 502)
        report["input_tokens"] += r.usage.input_tokens
        report["output_tokens"] += r.usage.output_tokens
        report["cost_usd"] += cost(model, r.usage)
        if r.stop_reason == "refusal":
            log.warning("%s refused on %s, retrying on %s", endpoint, model, FALLBACK[model])
            model = report["model"] = FALLBACK[model]
            continue
        try:
            data = review.parse_json(next((b.text for b in r.content if b.type == "text"), ""))
            break
        except ValueError:
            log.warning("%s reply was not valid JSON (stop_reason=%s)", endpoint, r.stop_reason)
    return data, model


def run_review(mode, text, model=REVIEW_MODEL, effort=REVIEW_EFFORT):
    system, user, truncated = review.review_prompt(mode, text)
    data, report = ask_claude("review", model, effort, system, user, 16000)
    result = review.clean_review(data)
    result["truncated"] = truncated
    return result, report


def run_ideas(domain, description, answers, model=IDEAS_MODEL, effort=IDEAS_EFFORT):
    system, user = review.ideas_prompt(domain, description, answers)
    data, report = ask_claude("ideas", model, effort, system, user, 8000)
    return {"ideas": data.get("ideas", [])[:5]}, report


@app.errorhandler(ReviewError)
def review_error(e):
    return jsonify({"code": e.code}), e.status


@app.errorhandler(413)
def too_large(_):
    return jsonify({"code": "too_large"}), 413


def _role(body):
    r = body.get("role")
    return r if r in usage.ROLES else None


@app.post("/api/review")
def api_review():
    body = request.get_json(silent=True) or {}
    mode, text = body.get("mode"), body.get("text")
    domain = body.get("domain") if body.get("domain") in review.DOMAINS else None
    if mode not in review.MODES or not isinstance(text, str) or not text.strip():
        return jsonify({"code": "bad_request"}), 400
    log.info("review request mode=%s bytes=%d", mode, len(text.encode()))
    try:
        result, _ = run_review(mode, text)
    except ReviewError as e:
        usage.record(db, request.headers, "review_error", {"mode": mode, "code": e.code}, _role(body))
        raise
    filled = [a["k"] for a in result["answers"] if a.get("level") is not None]
    usage.record(db, request.headers, "review_run",
                 {"mode": mode, "domain": domain, "filled": filled, "truncated": result["truncated"]}, _role(body))
    return jsonify(result)


@app.post("/api/ideas")
def api_ideas():
    body = request.get_json(silent=True) or {}
    domain, description = body.get("domain"), body.get("description")
    answers = body.get("answers") or {}
    if domain not in review.DOMAINS or not isinstance(description, str) or not description.strip():
        return jsonify({"code": "bad_request"}), 400
    if not isinstance(answers, dict):
        return jsonify({"code": "bad_request"}), 400
    answers = {k: v for k, v in answers.items() if k in review.KEYS and v in (0, 1, 2)}
    result, _ = run_ideas(domain, description[:600], answers)
    usage.record(db, request.headers, "ideas_run", {"domain": domain}, _role(body))
    return jsonify(result)


@app.post("/api/event")
def api_event():
    body = request.get_json(silent=True, force=True) or {}
    props = usage.clean(body.get("name"), body.get("props") or {})
    if props is None:
        return jsonify({"code": "bad_request"}), 400
    usage.record(db, request.headers, body["name"], props, _role(body))
    return ("", 204)


@app.post("/api/feedback")
def api_feedback():
    body = request.get_json(silent=True) or {}
    rating, text = body.get("rating"), body.get("text") or ""
    if rating not in (1, 2, 3, 4, 5) or not isinstance(text, str):
        return jsonify({"code": "bad_request"}), 400
    props = {"rating": rating, "text": text.strip()[:1000]}
    for k, fix in (("score", int), ("verdict", lambda v: str(v)[:80])):
        try:
            if body.get(k) is not None:
                props[k] = fix(body[k])
        except (TypeError, ValueError):
            pass
    usage.record(db, request.headers, "feedback", props, _role(body), collection=usage.FEEDBACK)
    return ("", 204)


def signed_in_email():
    """The email from IAP's signed token, or None. Unlike the plain email header, it
    can't be faked, so it still protects /stats if the site is ever made public."""
    token = request.headers.get("X-Goog-IAP-JWT-Assertion")
    if not token:
        return None
    try:
        claims = google_id_token.verify_token(
            token, google_requests.Request(), certs_url="https://www.gstatic.com/iap/verify/public_key"
        )
    except Exception as e:  # noqa: BLE001
        log.warning("stats: IAP token not valid: %s", e)
        return None
    if claims.get("iss") != "https://cloud.google.com/iap":
        return None
    return (claims.get("email") or "").lower() or None


@app.get("/stats")
def stats():
    email = signed_in_email()
    local = request.remote_addr in ("127.0.0.1", "::1") and "X-Goog-IAP-JWT-Assertion" not in request.headers
    if email not in STATS_VIEWERS and not local:
        return ("The usage numbers are only for the site's owners. Ask Cristina for access.", 403)
    days = 30
    try:
        days = max(1, min(90, int(request.args.get("days", 30))))
    except ValueError:
        pass
    return stats_page.render(usage.summary(db, days))


@app.get("/health")
def health():
    return jsonify({"ok": True, "review_model": REVIEW_MODEL, "ideas_model": IDEAS_MODEL})


SITE = os.path.dirname(os.path.abspath(__file__))


@app.get("/")
def index():
    return send_from_directory(SITE, "index.html")


# Only the site's own files are served, never the code next to them.
@app.get("/<name>")
def site_file(name):
    if name not in ("patterns.json", "patterns.md"):
        return jsonify({"code": "not_found"}), 404
    return send_from_directory(SITE, name, max_age=60)


@app.get("/demo/<name>")
def demo(name):
    if not name.endswith(".html"):
        return jsonify({"code": "not_found"}), 404
    return send_from_directory(os.path.join(SITE, "demo"), name)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8090)), debug=False)
