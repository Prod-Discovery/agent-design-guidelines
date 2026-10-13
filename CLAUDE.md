# Agent Design Guidelines

## Rules for changes to the site: read these first

Until Cristina is back (about 2026-10-27), **Daniel** makes the changes Amanda, Diana
and Nico ask for. They usually work in **Claude artifacts** (a copy of the site, or a
demo) and send Daniel the artifact when it's ready. The person asking is not
technical: explain in plain words, and never ask them to edit files, run commands or
fix git themselves.

**Before you start**, run `git pull` so you work on the latest version.

### What you may change

| File | What's in it |
|---|---|
| `patterns.json` | All text of patterns, principles, groups and Assess your agent (questions, answers, fixes, domains, verdicts). **Text goes here, not into index.html.** |
| `index.html` | The site's pages: home page, layout, Demo menu, the live examples' code, the Assess page's layout and intro text. |
| `demo/*.html` | The demos. Editing them and **adding new demo files** is fine. |

Everything else is blocked in `.claude/settings.json` and refused by the publish
check: the server, the Claude review, usage tracking, workflows, scripts, README and
this file. If a request needs one of those, say it waits for Cristina.

### Bringing over changes from an artifact

1. **Get the artifact's HTML.** If you can read the claude.ai link (it must be shared
   with Daniel), read it. Otherwise ask the person to download it or send the file,
   and save it **outside the repo** (for example in `~/Downloads`). Never commit it.
2. **Find what changed:** `python3 scripts/find_changes.py <artifact.html>` for a copy
   of the site, or `python3 scripts/find_changes.py <artifact.html> demo/<name>.html`
   for a demo. It lists text that is NEW in the artifact (with where the old version
   lives) and text that is GONE. Some GONE lines exist only in the repo on purpose
   (error messages, the feedback card, the "review isn't available" note): keep those.
   Also read the HTML side by side for layout or example-code changes, which the
   script doesn't show.
3. **Bring over only the changes, never the whole file.** The artifact's copy of the
   site has the text written into the HTML; the real `index.html` reads it from
   `patterns.json` and has extra parts the artifact doesn't (the Claude review calls,
   usage tracking, the feedback card, the role picker). Pasting the artifact over
   `index.html` breaks all of that, and the publish check refuses it.
   - Pattern, principle and Assess text: edit it in `patterns.json`.
   - Home page, layout, Demo menu, live examples: edit `index.html`.
   - A demo: edit `demo/<name>.html`. For a new demo, save it as `demo/<short-name>.html`
     (lowercase, hyphens), and add it to the Demo menu in `index.html`.
4. **Fix what artifacts usually bring with them:**
   - Links to other pages are relative (`demo/payroll.html`, `#patterns-undo`),
     never `claude.ai/artifact/...` links (only people they're shared with can open them).
   - No `window.claude` code: it only works inside claude.ai.
   - Every page keeps `<html lang="en">` and, in `<head>`,
     `<meta name="robots" content="noindex, nofollow">`.
   - A new live example in `index.html` needs a matching entry in that pattern's
     `examples.items` in `patterns.json` (same `id`), and the other way round.
5. **Ids:** never change or reuse an id. Ids connect the site, the plugin, links and
   PRDs; `scripts/ids.json` lists them. To rename something, change its `"name"` and
   keep the id. A new pattern gets a new id (lowercase words joined by hyphens).
   - **Patterns may be removed** when the team asks. Remove the pattern from
     `patterns.json` and from every `"patterns"` list that mentions it (principles and
     assessment questions); its live example code in `index.html` can go too. The check
     refuses a removal that leaves links behind, and refuses a removed id that comes
     back under a new id with the same or a similar name.
   - Examples may be added, changed or removed.
   - Principles, groups, assessment questions and domains are never deleted; if
     someone asks, say it waits for Cristina.
6. **Change only what was asked**, and keep the style: plain British English,
   sentence case, short sentences, curly quotes and apostrophes (’ “ ”) in text.

### Check, show, publish

7. **Run all three checks**; only continue when they pass:
   `python3 scripts/build_patterns.py --check`,
   `python3 scripts/check_protected.py` and `python3 scripts/check_site.py`.
8. **Look at it:** run `python3 -m http.server 8765` and open http://localhost:8765
   (the Claude review shows as unavailable there; that's expected). Check the pages you
   changed. Then show the person a short list of what changed, in plain words, and ask
   them to confirm.
9. **Publish through a pull request:** create a branch, commit with a clear message
   ("Bring over Amanda's example clean-up from her artifact"), push the branch, and
   open a pull request with `gh pr create`. Wait for its check with `gh pr checks`.
   When it's green and the person has confirmed, merge it with
   `gh pr merge --merge --delete-branch`.
10. **After merging,** two workflows run: "Deploy to Cloud Run" (the site) and
    "Publish demos" (GitHub Pages). Wait with `gh run watch` until both are green
    (about 4 minutes), then send the person the link to what changed:
    https://agent-design-guidelines-dqrlkyvm4a-nw.a.run.app (it needs a Visma sign-in;
    refresh with Cmd+Shift+R).
11. **If a check or run is red,** nothing was published. Read the error
    (`gh run view <id> --log-failed`), explain it in one plain sentence, fix it in the
    files above, and push again.
12. **Never** run `gcloud`, change GitHub settings or variables, force-push, rebase,
    reset or rewrite history, and never run `scripts/check_protected.py --update`. If a
    push is rejected because someone else pushed first, run `git pull` and push again.
    Who can open the site and `/stats` is for Cristina.

Everything below is for maintainers (Cristina) and explains how the site works.

## Maintainers: changing code

The rules above keep the server, workflows and scripts out of reach on purpose. To change code, a maintainer:

1. Temporarily moves `.claude/settings.json` aside, or edits files outside Claude Code.
2. After the change, runs `python3 scripts/check_protected.py --update` and commits
   `scripts/protected-files.sha256` with the change.
3. Before pushing, updates the admin-only repository variable to the new fingerprint
   file (Daniel can't change it):
   `gh variable set PROTECTED_LOCK_SHA --repo Prod-Discovery/agent-design-guidelines --body "$(shasum -a 256 scripts/protected-files.sha256 | cut -d' ' -f1)"`.
   If you forget, the workflows fail safely; set it and rerun them from the Actions tab.
4. If ids were intentionally removed, updates `scripts/ids.json`.

## The one rule

**`patterns.json` is the single source for text.** The site, the Claude review
prompts, `patterns.md` and the Discovery Engine plugin all read from it. Pattern,
principle and Assess text goes there, never into `index.html`. Ids never change.

## Where it is published

Every push to `main` publishes to two places:

| Where | Workflow | What people get |
|---|---|---|
| GitHub Pages, public | `.github/workflows/pages.yml` | **Only the three demos** (since 2026-10-13). `index.html` and `404.html` there are `pages/redirect.html`, which forwards every old guidelines link to the same path and `#anchor` on Cloud Run. |
| Cloud Run service `agent-design-guidelines`, **behind Visma sign-in** (see below) | `.github/workflows/deploy.yml` | The whole site plus the Claude review. https://agent-design-guidelines-dqrlkyvm4a-nw.a.run.app |

The guidelines are on Cloud Run only, so they can go behind sign-in. The demos stay on Pages. If the Cloud Run address changes, update `site` in `patterns.json` and `SITE` in `pages/redirect.html`.

## Where things live

| Path | What it is |
|---|---|
| `patterns.json` | All content, including `assessment` (questions, domains, verdicts). |
| `index.html` | The site. Renders from `patterns.json`. Live examples' code is here. |
| `demo/*.html` | Three standalone demos. |
| `app.py` | Flask: serves `/`, `/patterns.json`, `/patterns.md`, `/demo/*.html`, `POST /api/review`, `POST /api/ideas`, `GET /health`. Only those files are served, never the code. |
| `review.py` | Builds both prompts from `patterns.json`, parses Claude's JSON. Prompt wording is Diana's. |
| `scripts/build_patterns.py` | Validates `patterns.json` (including `assessment`), writes `patterns.md`. Runs in both workflows and in the Docker build. |
| `scripts/check_site.py` | Publish check for `index.html` and `demo/*.html`: JavaScript runs, noindex and lang present, no `window.claude` or artifact links, and `index.html` still has the patterns.json, Claude review, tracking and feedback hooks. |
| `scripts/find_changes.py` | Lists text an artifact added or removed compared with the site or a demo, and where each text lives. |
| `scripts/run_test_pack.py`, `test-pack/` | Six test agents with expected answers. |
| `scripts/setup_github_deploy.sh` | One-time GCP setup for keyless deploys from GitHub. Already run on 2026-10-13. |

## Infrastructure

- GCP project `prod-vpepf-cm` (also hosts DiscoveryBot), Cloud Run in `europe-west2`.
- The service runs as `assess-agent@prod-vpepf-cm.iam.gserviceaccount.com`, which has `roles/aiplatform.user` and nothing else.
- GitHub deploys as `github-deployer@prod-vpepf-cm.iam.gserviceaccount.com` through Workload Identity Federation (pool `github`, provider `agent-design-guidelines`). Google only accepts tokens from **`main` of `Prod-Discovery/agent-design-guidelines`**: other branches, forks and PRs cannot deploy. There is no key or secret anywhere.
- The runtime account also has `roles/datastore.user`, for the daily budget in Firestore.
- Claude runs on **Vertex AI, `eu` multi-region**: Opus 5.5 for reviews, Sonnet 5.5 for ideas, enabled in Model Garden on 2026-10-12. No Anthropic API key.

## Decisions, not accidents

1. **Prompts are built on the server**, from `patterns.json`. The endpoint takes material, never a prompt, so it can't be used as a general-purpose Claude.
2. **No structured outputs.** Visma's org policy (`constraints/vertexai.allowedPartnerModelFeatures`) blocks them for Claude. Prompts ask for JSON; `review.parse_json` reads it; a broken reply is retried once.
3. **Region `eu`.** `europe-west1` has zero Claude quota in this project.
4. **Nothing uploaded is logged or stored.** Logs hold sizes, tokens, cost and duration only.
5. **A refusal is retried once on the other model**, since Vertex has no server-side fallbacks.
6. **`/health`, not `/healthz`**: Cloud Run's front end reserves paths ending in `z`.
7. **API paths are relative** (`api/review`, `health`), so the page works at any base path.

## Who can open the site

**Only people signed in with a Visma Google account** (Identity-Aware Proxy), since
2026-10-13, agreed with Amanda and Diana. `domain:visma.com` is allowed; Cristina is
adding the other Visma companies' domains. Anyone else is sent to Google sign-in. The
demos on GitHub Pages stay public. Deploys don't change this setting: `deploy.yml`
has no `--allow-unauthenticated` / `--no-allow-unauthenticated` flag on purpose.

If someone can't get in, they're probably on a domain that isn't allowed yet. Don't
change access yourself: tell Cristina which address they sign in with.

Maintainers, to allow another domain or one person:

```bash
gcloud iap web add-iam-policy-binding --resource-type=cloud-run --service=agent-design-guidelines \
    --region=europe-west2 --project=prod-vpepf-cm --role=roles/iap.httpsResourceAccessor \
    --member=domain:example.com      # or user:name@example.com
```

To make the site public again (it was public for a few hours on 2026-10-13):

```bash
gcloud run services update agent-design-guidelines --region=europe-west2 --project=prod-vpepf-cm --no-iap
gcloud run services add-iam-policy-binding agent-design-guidelines --region=europe-west2 \
    --project=prod-vpepf-cm --member=allUsers --role=roles/run.invoker
```

and to undo that, `remove-iam-policy-binding` with the same member and role, then
`--iap` instead of `--no-iap`.

**Microsoft Entra ID:** people without a Visma Google account would need sign-in
through Entra ID, via Identity Platform with Entra as an OIDC provider. That needs an
app registration from Visma IT. According to Visma, the Google sign-in covers all
Visma companies, so this may not be needed.

`patterns.md` on Cloud Run is behind sign-in too. Tools that fetch the patterns by URL
should read `patterns.json` from GitHub instead (the repo is public), as the Discovery
Engine plugin does:
https://raw.githubusercontent.com/Prod-Discovery/agent-design-guidelines/main/patterns.json

## Daily budget

`DAILY_BUDGET_USD` (15, set in `deploy.yml`; about 240 reviews a day) is a hard stop on Claude spend per UTC
day, across everyone. Each call's cost is added to Firestore, collection
`assess_spend`, one document per day (`cost_usd`, `calls`). When the day's total
reaches the budget, the Claude review and ideas answer "reached today's limit" until
midnight UTC; the questionnaire keeps working. If Firestore can't be read, calls go
ahead (fail open) and `--max-instances=3` still limits spend. To see today's spend,
open Firestore in the Google Cloud console, collection `assess_spend`.

## Usage tracking and /stats

Counted on our own server, no Google Analytics and no cookies (`usage.py`):

- The page sends a small event to `POST /api/event` for page views, demo and plug-in
  clicks, answers in Assess (and whether someone changed Claude's suggested answer),
  completed assessments, opening the improvements, and copying the summary. Only the
  event names and fields in `usage.EVENTS` are accepted.
- Claude reviews, failed reviews and ideas are recorded by the server itself.
- The feedback card on Assess ("How useful was this assessment?", stars and a comment)
  posts to `POST /api/feedback`.
- An optional "Your role" picker on Assess is remembered in the visitor's browser and
  sent with their events. The roles are listed in both `usage.ROLES` and `ROLES` in
  `index.html`; keep them the same.
- Each event stores the company domain from the sign-in email and an anonymous visitor
  id (a keyed hash of the email; the key is in Firestore, `assess_config/visitor_salt`).
  No email, name or uploaded material is stored. Events are kept, with no automatic
  deletion (Cristina's decision, 2026-10-13), in `usage_events` and `usage_feedback`.
  Older events have an unused `expire_at` field; no deletion rule reads it.
- Runs on a laptop write to `dev_usage_events` and `dev_usage_feedback` instead, so
  tests never show up in the real numbers.

**`/stats`** shows the numbers for the last 7, 30 or 90 days: visitors, companies, roles,
the Assess funnel, how often Claude's answers are changed, review modes, domains,
verdicts, most viewed pages, demo clicks, feedback and Claude cost per day. Only emails
in `STATS_VIEWERS` (set in `deploy.yml`) can open it; the email comes from IAP's signed
token, so the page stays closed even if the site is made public. Content editors don't
change who can see `/stats`: tell Cristina.

## Running locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
gcloud auth application-default login      # once; Vertex uses your Google login locally
.venv/bin/python app.py                    # http://127.0.0.1:8090/#assess
```

Use `127.0.0.1`, not `localhost`, on Cristina's Mac: Apache listens on 8080 on IPv6.
For the site without the Claude review, `python3 -m http.server 8765` still works.

## Testing the Claude review

```bash
.venv/bin/python scripts/run_test_pack.py                       # Opus 5.5, about $0.33
.venv/bin/python scripts/run_test_pack.py claude-sonnet-5-5 high # about $0.12
```

A one-level difference from the answer key is normal; a two-level miss is not.
On 2026-10-13 neither model had a two-level miss; Opus averaged $0.054 per review.
Run it after changing `review.py`, the questions in `patterns.json`, or the model.

## Not done yet

- **Sign-in for every Visma company**: add their domains (see "Who can open the site"). Then consider making the repo internal. Keep `pages.yml`: it serves the demos.
- **Billing budget alert**: Cristina has no access to billing account `01C3B7-C9B9D8-A97125`; a billing admin has to create it. The daily budget above is the hard stop meanwhile.
- **Per-user daily limit**: IAP passes the email in the `X-Goog-Authenticated-User-Email` header, so it can be added to `check_budget`.
