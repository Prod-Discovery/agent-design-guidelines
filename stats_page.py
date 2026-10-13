"""The /stats page: usage of the site and of Assess your agent, as plain HTML."""

from html import escape

def _bars(rows, total=None, empty="Nothing yet."):
    rows = list(rows)
    if not rows:
        return f'<p class="muted">{empty}</p>'
    top = total or max(v for _, v in rows) or 1
    out = []
    for label, value in rows:
        pct = round(100 * value / top) if top else 0
        share = f' <span class="muted">{pct}%</span>' if total else ""
        out.append(
            f'<div class="row"><span class="lbl">{escape(str(label))}</span>'
            f'<span class="bar"><i style="width:{max(pct, 2)}%"></i></span>'
            f'<span class="num">{value}{share}</span></div>'
        )
    return "".join(out)


def _card(title, body, note=""):
    note = f'<p class="note">{note}</p>' if note else ""
    return f'<section class="card"><h2>{escape(title)}</h2>{note}{body}</section>'


def render(s):
    import review  # question ids -> readable questions

    qname = {q["key"]: q["question"] for q in review.QUESTIONS}
    dname = {d["id"]: d["name"] for d in review._A["domains"]}
    pages = {"home": "Home", "patterns": "Patterns overview", "principles": "Principles overview",
             "assess": "Assess your agent", "contact": "Contact"}
    pages.update({"patterns-" + p["id"]: "Pattern: " + p["name"] for p in review._D["patterns"]})
    pages.update({"principles-" + p["id"]: "Principle: " + p["name"] for p in review._D["principles"]})
    demos = {"front-door": "Demo: Front door", "payroll": "Demo: Payroll", "accounting": "Demo: Accounting"}
    stars = [f["props"].get("rating") for f in s["feedback"] if f["props"].get("rating")]
    avg = f"{sum(stars) / len(stars):.1f} / 5" if stars else "–"
    spend_total = sum(d.get("cost_usd", 0) for d in s["spend"].values())
    override_rate = (
        f'{round(100 * s["overrides"] / s["reviewed_answers"])}%' if s["reviewed_answers"] else "–"
    )
    opened = s["funnel"][0][1]

    tiles = "".join(
        f'<div class="tile"><b>{v}</b><span>{escape(k)}</span></div>'
        for k, v in [
            (f'Visitors, last {s["days"]} days', s["visitors"]),
            ("Visitors, last 7 days", s["visitors_7d"]),
            ("Came back more than once", s["returning"]),
            ("Claude reviews", s["reviews"]),
            ("Average feedback", avg),
            (f'Claude cost, last {s["days"]} days', f"${spend_total:.2f}"),
        ]
    )

    comments = "".join(
        f'<li><span class="stars">{"★" * f["props"]["rating"]}{"☆" * (5 - f["props"]["rating"])}</span>'
        f'<span class="muted"> {escape(f.get("company", ""))}{" · " + escape(f["role"]) if f.get("role") else ""}'
        f' · {f["day"]}</span>'
        f'{"<p>" + escape(f["props"]["text"]) + "</p>" if f["props"].get("text") else ""}</li>'
        for f in s["feedback"][:30]
    ) or '<li class="muted">No feedback yet.</li>'
    rating_rows = [(f"{n} ★", stars.count(n)) for n in (5, 4, 3, 2, 1)]

    cards = [
        _card("Visitors per day", _bars(sorted(s["visitors_per_day"].items()))),
        _card("Companies", _bars(s["companies"].items()), "From the email domain people sign in with."),
        _card("Roles", _bars(s["roles"].items(), empty="Nobody has picked a role yet."),
              "People can pick their role on Assess your agent. It's optional."),
        _card("Assess your agent: how far people get",
              _bars(s["funnel"], total=opened or None),
              "Unique visitors at each step. Percentages are of those who opened the page."),
        _card("Is Claude's review good?",
              f'<p class="big">{override_rate}</p><p class="muted">of the answers Claude filled in were changed by '
              f'the person ({s["overrides"]} of {s["reviewed_answers"]}). Lower is better.</p>'
              + _bars(((qname.get(k, k), v) for k, v in s["overrides_by_question"].items()),
                      empty="No changes to Claude's answers yet.")
              + (f'<p class="muted">Reviews that failed: {s["review_errors"]}</p>' if s["review_errors"] else "")),
        _card("What people review", _bars(s["review_modes"].items(), empty="No reviews yet.")),
        _card("Domains", _bars(((dname.get(k, k), v) for k, v in s["domains"].items()), empty="No completed assessments yet."),
              "The “What does the agent do?” choice, for completed assessments."),
        _card("Verdicts", _bars(s["verdicts"].items(), empty="No completed assessments yet.")),
        _card("Most viewed pages", _bars([(pages.get(k, k), v) for k, v in s["pages"].items()][:15])),
        _card("Demo and plug-in clicks",
              _bars([(demos.get(k, k), v) for k, v in s["demo_clicks"].items()] + [("Claude plug-in", s["plugin_clicks"])])),
        _card("Feedback", _bars(rating_rows) + f'<ul class="fb">{comments}</ul>',
              "“How useful was this assessment?” and “How will you use these insights?”"),
        _card("Claude cost per day",
              "".join(f'<div class="row"><span class="lbl">{d}</span><span></span>'
                      f'<span class="num">${v.get("cost_usd", 0):.2f} · {v.get("calls", 0)} calls</span></div>'
                      for d, v in s["spend"].items()) or '<p class="muted">No Claude calls yet.</p>',
              "The daily limit is $15. When it's reached, the review pauses until midnight UTC."),
    ]
    periods = " · ".join(
        f'<a href="?days={d}"{" aria-current=\"page\"" if d == s["days"] else ""}>{d} days</a>' for d in (7, 30, 90)
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex, nofollow">
<title>Usage · Agent Design Guidelines</title>
<style>
:root{{--bg:#f7f6f3;--card:#fff;--fg:#17171a;--muted:#6b6b73;--line:#e6e4df;--accent:#5b3fd6}}
@media (prefers-color-scheme:dark){{:root{{--bg:#131316;--card:#1c1c21;--fg:#f2f2f4;--muted:#a3a3ad;--line:#2c2c33;--accent:#a990ff}}}}
*{{box-sizing:border-box}}body{{margin:0;padding:24px 16px 48px;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:1100px;margin:0 auto}}h1{{font-size:26px;margin:0 0 4px}}.top p{{margin:0;color:var(--muted)}}
.top nav{{margin-top:8px}}a{{color:var(--accent)}}a[aria-current]{{font-weight:700;text-decoration:none;color:var(--fg)}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:20px 0}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}}
.tile b{{display:block;font-size:26px;font-variant-numeric:tabular-nums}}.tile span{{color:var(--muted);font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;min-width:0}}
.card h2{{font-size:16px;margin:0 0 6px}}.note{{color:var(--muted);font-size:13px;margin:0 0 10px}}
.row{{display:grid;grid-template-columns:minmax(0,1.4fr) 1fr auto;gap:10px;align-items:center;padding:4px 0;font-size:14px}}
.lbl{{overflow-wrap:anywhere}}.bar{{height:8px;background:var(--line);border-radius:4px;overflow:hidden}}
.bar i{{display:block;height:100%;background:var(--accent)}}.num{{font-variant-numeric:tabular-nums;white-space:nowrap}}
.muted{{color:var(--muted)}}.big{{font-size:30px;font-weight:700;margin:0}}
.fb{{list-style:none;padding:0;margin:12px 0 0;display:grid;gap:10px}}.fb p{{margin:2px 0 0}}.stars{{color:#e0a100}}
footer{{margin-top:20px;color:var(--muted);font-size:13px}}
</style></head><body><main>
<header class="top"><h1>Usage</h1><p>Agent Design Guidelines and Assess your agent, last {s["days"]} days.</p>
<nav>{periods} · <a href="/">Back to the site</a></nav></header>
<div class="tiles">{tiles}</div>
<div class="grid">{"".join(cards)}</div>
<footer>Visitors are counted anonymously: no names or emails are stored, only the company domain. Nothing people upload
is stored. Events are deleted after 90 days.</footer>
</main></body></html>"""
