# Agent Design Guidelines

## Rules for content changes: read these first

Most people working in this repo only change content. Until Cristina is back (about
2026-10-27), Daniel makes those changes for Amanda, Diana and Nico. The person asking
is usually not technical: explain in plain words, and never ask them to edit files,
run commands or fix git themselves.

**Before you start**, run `git pull` so you work on the latest version.

**What you may change:** only `patterns.json`. All other files are blocked in
`.claude/settings.json`, and the publish check refuses anything else, so the site
would not update.

1. **Only edit `patterns.json`.** If a request needs another file (layout, colours,
   the demos, the live examples, the Claude review, the workflows, README or this
   file), don't do it. Tell the person it has to wait for Cristina, and suggest they
   write it down.
2. **Never change, reuse or delete an `"id"`.** That includes pattern, principle and
   group ids, example ids, and the assessment question and domain ids. Ids are used in
   links, the Discovery Engine plugin and PRDs. To rename something, change its
   `"name"` and keep the id. `scripts/ids.json` lists the ids that must stay; never
   edit it.
3. **Never delete anything**: no pattern, principle, group, example, question, domain
   or verdict. If someone asks to remove one, explain it waits for Cristina.
4. **Change only what was asked.** Don't reword, reorder, shorten or "improve" any
   other text, and don't fix things nobody mentioned.
5. **Keep the style:** plain British English, sentence case, short sentences, the
   same tone as the entries around it. Use curly quotes and apostrophes (’ “ ”) in
   text, as the file does.
6. **A new pattern:** copy the shape of an existing pattern in the same group. Give it
   a new id (lowercase words joined by hyphens, not used before). Set
   `"examples": {"intro": "", "items": []}`: live examples need code in `index.html`,
   which waits for Cristina. Add it to a principle's `"patterns"` list or to an
   assessment question only if the person asks.
7. **Assess your agent questions** (`assessment`): every question keeps exactly 3
   `answers` (Not yet, Partly, Yes) and 2 `fixes` (for Not yet and Partly), each fix
   with a `title` and its `ideas`. The Claude review reads these too, so a change here
   changes what Claude checks.
8. **Check before committing**, and only commit when both pass:
   `python3 scripts/build_patterns.py --check` and `python3 scripts/check_protected.py`.
   Then show the person what changed, as a short before and after in plain words, and
   ask them to confirm.
9. **Publish** by committing with a clear one-line message (for example "Reword the
   Undo rule, asked by Amanda") and running `git push origin main`. Publishing is
   automatic: two workflows run, "Deploy to Cloud Run" (the guidelines) and "Publish demos" (the demos on GitHub Pages). Wait with
   `gh run watch` until both are green (about 4 minutes), then give the person the link:
   https://agent-design-guidelines-dqrlkyvm4a-nw.a.run.app (refresh with Cmd+Shift+R).
10. **If a run is red,** nothing was published and the site and the demos still show the last
    good version. Read the error with `gh run view <id> --log-failed`, explain it in one
    plain sentence, fix it in `patterns.json` only, and push again.
11. **Never** run `gcloud`, change GitHub settings or variables, force-push, rebase,
    reset or rewrite history, and never run `scripts/check_protected.py --update`.
    If `git push` is rejected because someone else pushed first, run `git pull` (a
    normal merge) and push again.

Everything below is for maintainers (Cristina) and explains how the site works.

## Maintainers: changing code

The rules above block code changes on purpose. To change code, a maintainer:

1. Temporarily moves `.claude/settings.json` aside, or edits files outside Claude Code.
2. After the change, runs `python3 scripts/check_protected.py --update` and commits
   `scripts/protected-files.sha256` with the change.
3. Before pushing, updates the admin-only repository variable to the new fingerprint
   file (Daniel can't change it):
   `gh variable set PROTECTED_LOCK_SHA --repo Prod-Discovery/agent-design-guidelines --body "$(shasum -a 256 scripts/protected-files.sha256 | cut -d' ' -f1)"`.
   If you forget, the workflows fail safely; set it and rerun them from the Actions tab.
4. If ids were intentionally removed, updates `scripts/ids.json`.

## The one rule

**`patterns.json` is the single source.** The site, the Claude review prompts,
`patterns.md` and the Discovery Engine plugin all read from it. Content changes go
there and nowhere else. Ids never change (see README).

## Where it is published

Every push to `main` publishes to two places:

| Where | Workflow | What people get |
|---|---|---|
| GitHub Pages, public | `.github/workflows/pages.yml` | **Only the three demos** (since 2026-10-13). `index.html` and `404.html` there are `pages/redirect.html`, which forwards every old guidelines link to the same path and `#anchor` on Cloud Run. |
| Cloud Run service `agent-design-guidelines`, **public until about 2026-10-27** (see below) | `.github/workflows/deploy.yml` | The whole site plus the Claude review. https://agent-design-guidelines-dqrlkyvm4a-nw.a.run.app |

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

**Public since 2026-10-13, on purpose, while Cristina is away (back about 2026-10-27).**
Anyone with the link can open the Cloud Run site and run the Claude review. The
content is in the public repo anyway; the daily budget below caps what strangers
can spend. Deploys don't change this setting: `deploy.yml` has no
`--allow-unauthenticated` / `--no-allow-unauthenticated` flag on purpose, so the
service keeps whatever is set here.

How it was made public:

```bash
gcloud run services update agent-design-guidelines --region=europe-west2 --project=prod-vpepf-cm --no-iap
gcloud run services add-iam-policy-binding agent-design-guidelines --region=europe-west2 \
    --project=prod-vpepf-cm --member=allUsers --role=roles/run.invoker
```

**To put the Visma sign-in back** (Google accounts on `@visma.com`; it was tested and
worked on 2026-10-13):

```bash
gcloud run services remove-iam-policy-binding agent-design-guidelines --region=europe-west2 \
    --project=prod-vpepf-cm --member=allUsers --role=roles/run.invoker
gcloud run services update agent-design-guidelines --region=europe-west2 --project=prod-vpepf-cm --iap
gcloud iap web add-iam-policy-binding --resource-type=cloud-run --service=agent-design-guidelines \
    --region=europe-west2 --project=prod-vpepf-cm --role=roles/iap.httpsResourceAccessor \
    --member=domain:visma.com      # repeat for other domains, or user:name@example.com
```

**Not everyone at Visma has a Google account; most sign in with Microsoft Entra ID.**
IAP supports that through Identity Platform with Entra as an OIDC provider, but it
needs an app registration in Visma's Entra tenant (client id and secret), which only
Visma IT can create.

## Daily budget

`DAILY_BUDGET_USD` (15, set in `deploy.yml`; about 240 reviews a day) is a hard stop on Claude spend per UTC
day, across everyone. Each call's cost is added to Firestore, collection
`assess_spend`, one document per day (`cost_usd`, `calls`). When the day's total
reaches the budget, the Claude review and ideas answer "reached today's limit" until
midnight UTC; the questionnaire keeps working. If Firestore can't be read, calls go
ahead (fail open) and `--max-instances=3` still limits spend. To see today's spend,
open Firestore in the Google Cloud console, collection `assess_spend`.

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

- **Sign-in**: the site is public until Cristina is back. Then put the Visma sign-in back, ideally with Entra ID (see "Who can open the site"), and make the repo internal. Keep `pages.yml`: it only serves the demos now.
- **Billing budget alert**: Cristina has no access to billing account `01C3B7-C9B9D8-A97125`; a billing admin has to create it. The daily budget above is the hard stop meanwhile.
- **Per-user daily limit**: once sign-in is back, IAP passes the email in the `X-Goog-Authenticated-User-Email` header, so it can be added to `check_budget`.
