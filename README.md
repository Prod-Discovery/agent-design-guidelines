# Agent Design Guidelines

Principles and patterns for designing AI agents in Visma products, with three interactive demos set in a fictional construction company, Berg Bygg AB.

**Live site:** https://prod-discovery.github.io/agent-design-guidelines/
**AI-readable version:** https://prod-discovery.github.io/agent-design-guidelines/patterns.md

## Credits

The guidelines, patterns and demos were created by **Amanda Lundius, Nicolae Socaciu and Diana Almeida**. This repo publishes their work so anyone at Visma can open it. Cristina Iftode maintains the repo.

## One source for the patterns

All pattern and principle content lives in **`patterns.json`**. Everything else reads from it:

- **The website** (`index.html`) loads it when the page opens: the overview, the sidebar, every pattern page (rule, intro, what to look for, do, avoid, example captions) and every principle page.
- **`patterns.md`**, the AI-readable version, is generated from it on every publish. Never edit it by hand, it isn't even in the repo.
- **The Discovery Engine plugin** bundles a copy of `patterns.md` at each plugin release.

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
| `.github/workflows/pages.yml` | Publishes the site on every push to `main` |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are. Keep it. |

## How to make a change

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

Every push to `main` runs the **Publish site** workflow (Actions tab). It checks `patterns.json`, generates `patterns.md` and publishes. It takes about a minute.

- **Green:** live. Hard-refresh the page (Cmd+Shift+R), the CDN can cache the old version for a few minutes.
- **Red:** nothing was published and the live site still shows the last good version. Open the failed run, the "Validate patterns.json" step says what to fix.

## Visibility

The repo and site are public: anyone with the link can open them. The noindex tag keeps the pages out of search results, but it does not restrict access, so don't put anything confidential here. `patterns.md` is a plain text file and can't carry a noindex tag. It is only linked from noindex pages, but the repo itself is public on GitHub.

## Related

- [Discovery to Prototype Engine guide](https://prod-discovery.github.io/discovery-engine-guide/)
