# Agent Design Guidelines

Principles and patterns for designing AI agents in Visma products, with three interactive demos set in a fictional construction company, Berg Bygg AB.

**Live site, with the Claude review (sign in with your Visma account):** https://agent-design-guidelines-dqrlkyvm4a-nw.a.run.app
**AI-readable version:** https://agent-design-guidelines-dqrlkyvm4a-nw.a.run.app/patterns.md
**Demos (GitHub Pages):** https://prod-discovery.github.io/agent-design-guidelines/demo/front-door.html

The guidelines live on Cloud Run only, so they can go behind Visma sign-in. GitHub Pages serves just the three demos; any old guidelines link there (the home page, `#patterns-…`, `patterns.md`) forwards to the same place on Cloud Run.

## Credits

The guidelines, patterns and demos were created by **Amanda Lundius, Nicolae Socaciu and Diana Almeida**. This repo publishes their work so anyone at Visma can open it. Cristina Iftode maintains the repo.

## One source for the patterns

All pattern and principle content lives in **`patterns.json`**. Everything else reads from it:

- **The website** (`index.html`) loads it when the page opens: the overview, the sidebar, every pattern page (rule, intro, what to look for, do, avoid, example captions), every principle page, and the "Assess your agent" questions.
- **The Claude review** on "Assess your agent" (`review.py`) builds its prompts from it, so Claude always checks against the current names and rules.
- **`patterns.md`**, the AI-readable version, is generated from it on every publish. Never edit it by hand, it isn't even in the repo.
- **The Discovery Engine plugin** and its Agentic Patterns add-on bundle a copy of `patterns.md` at each plugin release. Anyone can also give `patterns.md` to their own AI tool.

So to change a pattern, you edit `patterns.json` and nothing else.

### Ids never change

Every pattern and principle has an `id`, for example `autonomy-levels`. The id is used in page links (`#patterns-autonomy-levels`), in the plugin, and in PRDs that cite a pattern. **Never change or reuse an id.** Everything else can change freely: rename a pattern by editing its `name`, reorder patterns by moving them in the list (the numbers on the site follow the order).

Some ids are older than the current names (`say-its-an-agent` is Agent disclosure, `actions` is Review and approve, `uncertainty` is Clarifying questions, `hand-over` is Escalation, `activity-log` is Audit trail, `autonomy-evolution` is Earned autonomy). That's fine and intended: the id stays, the name moves on.

### What's in patterns.json

| Field | Where it shows up |
|---|---|
| `groups` | The four lifecycle groups, with their one-line summary |
| `patterns[].name`, `rule` | Sidebar, overview card and page title |
| `patterns[].intro` | The opening paragraphs of the pattern page (the first one is shown in bold) |
| `patterns[].look_for`, `do`, `avoid` | The "What to look for" list and the Do / Avoid boxes |
| `patterns[].examples` | The captions of the live examples. The `id` of each example connects it to its interactive code in `index.html`, so don't change example ids |
| `principles` | The principle pages: statement, "In practice" cards (`pita: true` shows the PITA badge) and the patterns it links to |
| `assessment.questions` | "Assess your agent": one question per principle, its three answers (Not yet, Partly, Yes), why it matters, the fix and three ideas for Not yet and for Partly, and the patterns to use. The Claude review reads these too |
| `assessment.domains` | The "What does the agent do?" choices, and which questions count more for each |
| `assessment.verdicts` | The verdict for each score range |

The live, interactive examples themselves (their code) stay in `index.html`.

## What's here

| File | What it is |
|---|---|
| `patterns.json` | **The core file.** All pattern and principle content |
| `index.html` | The guidelines site, rendered from `patterns.json` |
| `demo/payroll.html` | October Payroll Run demo |
| `demo/accounting.html` | October Close demo |
| `demo/front-door.html` | Berg Bygg Overview, the front door that links to the other two demos |
| `scripts/build_patterns.py` | Checks `patterns.json` for mistakes and generates `patterns.md` |
| `app.py`, `review.py` | The Cloud Run server: serves the site and runs the Claude review through Vertex AI. See [CLAUDE.md](CLAUDE.md) |
| `usage.py`, `stats_page.py` | Anonymous usage tracking, the Assess feedback card's storage, and the `/stats` page |
| `scripts/check_site.py` | Checks the pages and demos before publishing (scripts run, noindex tag, no artifact-only links or code) |
| `scripts/find_changes.py` | Lists what an artifact changed compared with the site or a demo |
| `scripts/run_test_pack.py`, `test-pack/` | Checks the Claude review against six test agents with known answers |
| `.github/workflows/pages.yml` | Publishes the demos to GitHub Pages on every push to `main`, plus the redirect for old links |
| `pages/redirect.html` | The redirect GitHub Pages shows for every old guidelines link. Holds the Cloud Run address, like `site` in `patterns.json` |
| `.github/workflows/deploy.yml` | Deploys the site and the Claude review to Cloud Run on every push to `main` |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are. Keep it. |

## Making changes

**With Claude Code (recommended).** Open this repo in Claude Code. Claude follows the rules in [CLAUDE.md](CLAUDE.md): it brings over only the changes, keeps the ids, runs the checks, shows you what changed, and publishes through a pull request once you confirm. It can change the text (`patterns.json`), the pages (`index.html`) and the demos (`demo/`), including adding new demos. The server, the workflows and the rules are out of its reach.

Prompts to copy and fill in:

- **Changes from an artifact (the site):**
  > *"Amanda sent her updated artifact: [link or path to the downloaded HTML]. Find what she changed compared with the site, bring over only those changes, check them, show me the list of changes, and publish when I confirm."*
- **Changes to a demo from an artifact:**
  > *"Nicolae updated the Payroll demo in this artifact: [link or path]. Bring his changes into demo/payroll.html, check, show me, and publish when I confirm."*
- **A new demo:**
  > *"Nicolae made a new demo: [link or path]. Add it as a new demo called '[name]', link it from the Demo menu, check, show me, and publish when I confirm."*
- **A text change described in a message:**
  > *"Amanda asked: [paste her message]. Make this change, check it, show me the change, and publish it when I confirm."*
- **If something went red:**
  > *"The last publish failed. Find out why, explain it simply, fix it, and publish again."*

If Claude can't open an artifact link, ask its author to share the artifact with you, or to download it and send you the HTML file.

**In the browser (no Python, no terminal):** the checks and publishing run by themselves.

1. Open [patterns.json on GitHub](https://github.com/Prod-Discovery/agent-design-guidelines/blob/main/patterns.json) and click the pencil icon (Edit this file).
2. Make the change. Keep the quotes, commas and brackets as they are; only change the text between the quotes. Use `Cmd+F` to find the pattern by its name.
3. Click **Commit changes**, write one line about what you changed, and commit to `main`.
4. Open the **Actions** tab. Two runs start: **Deploy to Cloud Run** (the guidelines) and **Publish demos** (GitHub Pages). Wait for both to turn green, about 4 and 1 minutes.
5. If one turns red, nothing was published and the live sites still show the last good version. Open the run: the **Check patterns.json** step says exactly what's wrong, for example "missing comma" or "links to pattern 'x', which does not exist". Fix it the same way and commit again.

**Adding a pattern:** copy an existing pattern block in `patterns.json`, from its `{` to its `},`, paste it where the new one should go, give it a new `id` (lowercase words joined by hyphens, never reused) and change the text. The new pattern gets a page and a number automatically. A live example for it needs code in `index.html`, so ask someone who knows HTML, or leave `examples.items` empty for now.

**Not sure how to write the change?** Paste the request and the part of `patterns.json` into Claude and ask for the edited version, then paste that back.

## How to make a change on your computer

1. Edit `patterns.json` (content) or an HTML file (layout, live examples, demos).
2. Check for mistakes and build `patterns.md`:
   ```bash
   python3 scripts/build_patterns.py
   ```
   It tells you exactly what is wrong if something is, for example a duplicated id or a principle that links to a pattern that doesn't exist.
3. Look at it locally. The site has to be opened through a small web server, not by double-clicking the file:
   ```bash
   python3 -m http.server 8765
   ```
   then open http://localhost:8765
4. Commit and push to `main`.

If you edit HTML, keep these two lines in the `<head>` of every page. The first keeps the pages out of Google and other search engines:
```html
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="data:image/svg+xml,...">
```
Links between pages must be relative (`demo/payroll.html`), never `claude.ai/artifact/...` links, since those only open for people the artifact is shared with.

## How to check a change is live

Every push to `main` runs two workflows (Actions tab), both of which check `patterns.json` first:

- **Deploy to Cloud Run** deploys the guidelines and the Claude review in about 4 minutes. This is the one that matters for pattern changes.
- **Publish demos** publishes the demos and the redirect to GitHub Pages in about a minute.

- **Green:** live. Hard-refresh the page (Cmd+Shift+R), the CDN can cache the old version for a few minutes.
- **Red:** nothing was published and the live site still shows the last good version. Open the failed run, the check step says what to fix.

A run that failed for another reason (for example Google Cloud was briefly unavailable) can be retried from the run page with **Re-run jobs**, or started again with **Run workflow** on the workflow's page.

## Visibility

The repo and the GitHub Pages demos are public: anyone with the link can open them. The noindex tag keeps the pages out of search results, but it does not restrict access, so don't put anything confidential here. `patterns.md` is a plain text file and can't carry a noindex tag. It is only linked from noindex pages, but the repo itself is public on GitHub.

The site on Cloud Run needs a Visma sign-in. The Claude review there stops for the day once it has cost $15. GitHub Pages serves only the demos, and its redirect for old links leads to the sign-in.

## Related

- [Discovery to Prototype Engine guide](https://prod-discovery.github.io/discovery-engine-guide/)
