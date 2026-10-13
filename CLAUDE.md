# Agent Design Guidelines: orientation

The guidelines site (principles, patterns, demos, "Assess your agent") and the small
server that runs the Claude review on "Assess your agent". Read this and `README.md`
before changing anything.

## The one rule

**`patterns.json` is the single source.** The site, the Claude review prompts,
`patterns.md` and the Discovery Engine plugin all read from it. Content changes go
there and nowhere else. Ids never change (see README).

## Where it is published

Every push to `main` publishes to two places:

| Where | Workflow | What people get |
|---|---|---|
| GitHub Pages, public | `.github/workflows/pages.yml` | The whole site. "Assess your agent" works as a questionnaire only: the page calls `health`, gets no answer, and hides the Claude review. |
| Cloud Run service `agent-design-guidelines`, behind Google sign-in for `@visma.com` | `.github/workflows/deploy.yml` | The whole site plus the Claude review. https://agent-design-guidelines-dqrlkyvm4a-nw.a.run.app |

Pages can be turned off once everyone who needs the site can sign in on Cloud Run (see Login).

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

## Login

Identity-Aware Proxy (IAP) on the Cloud Run service, turned on 2026-10-13 with
`gcloud run services update agent-design-guidelines --iap`. Anyone with a
`@visma.com` Google account can open the site (`roles/iap.httpsResourceAccessor`
for `domain:visma.com`). Deploys keep IAP on; the deploy workflow doesn't touch it.

To let in another domain or a person:

```bash
gcloud iap web add-iam-policy-binding --resource-type=cloud-run --service=agent-design-guidelines \
    --region=europe-west2 --project=prod-vpepf-cm --role=roles/iap.httpsResourceAccessor \
    --member=domain:example.com      # or user:name@example.com
```

**Not everyone at Visma has a Google account; most sign in with Microsoft Entra ID.**
IAP supports that through Identity Platform with Entra as an OIDC provider, but it
needs an app registration in Visma's Entra tenant (client id and secret), which only
Visma IT can create. Until then, people without a Google account use GitHub Pages.

## Daily budget

`DAILY_BUDGET_USD` (10, set in `deploy.yml`) is a hard stop on Claude spend per UTC
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

- **Entra ID sign-in**, for people without a Google account (see Login). Then turn off `pages.yml` and make the repo internal.
- **Billing budget alert**: Cristina has no access to billing account `01C3B7-C9B9D8-A97125`; a billing admin has to create it. The daily budget above is the hard stop meanwhile.
- **Per-user daily limit**: IAP passes the signed-in email in the `X-Goog-Authenticated-User-Email` header, so it can be added to `check_budget`.
- The old test service `assess-agent` in the same project can be deleted once `agent-design-guidelines` is live.
