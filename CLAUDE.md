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
| Cloud Run service `agent-design-guidelines`, private | `.github/workflows/deploy.yml` | The whole site plus the Claude review. |

Pages goes away once login for Visma accounts is added on Cloud Run.

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
- Claude runs on **Vertex AI, `eu` multi-region**: Opus 5.5 for reviews, Sonnet 5.5 for ideas, enabled in Model Garden on 2026-10-12. No Anthropic API key.

## Decisions, not accidents

1. **Prompts are built on the server**, from `patterns.json`. The endpoint takes material, never a prompt, so it can't be used as a general-purpose Claude.
2. **No structured outputs.** Visma's org policy (`constraints/vertexai.allowedPartnerModelFeatures`) blocks them for Claude. Prompts ask for JSON; `review.parse_json` reads it; a broken reply is retried once.
3. **Region `eu`.** `europe-west1` has zero Claude quota in this project.
4. **Nothing uploaded is logged or stored.** Logs hold sizes, tokens, cost and duration only.
5. **A refusal is retried once on the other model**, since Vertex has no server-side fallbacks.
6. **`/health`, not `/healthz`**: Cloud Run's front end reserves paths ending in `z`.
7. **API paths are relative** (`api/review`, `health`), so the page works at any base path.

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

- **Login** for Visma accounts on Cloud Run. Then turn off `pages.yml` and make the repo internal.
- **Budget**: Cristina has no access to billing account `01C3B7-C9B9D8-A97125`; a billing admin has to create it. `--max-instances=3` caps spend meanwhile.
- **Per-user daily limit**, after login.
- The old test service `assess-agent` in the same project can be deleted once `agent-design-guidelines` is live.
