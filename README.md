# Agent Design Guidelines

Principles and patterns for designing AI agents in Visma products, with three interactive demos set in a fictional construction company, Berg Bygg AB.

**Live site:** https://prod-discovery.github.io/agent-design-guidelines/

## Credits

The guidelines, patterns and demos were created by **Amanda, Nico and Diana**. This repo publishes their work so anyone at Visma can open it. Cristina Iftode maintains the repo.

## What's here

| File | Page | Live link |
|---|---|---|
| `index.html` | Agent Design Guidelines (principles, patterns) | [open](https://prod-discovery.github.io/agent-design-guidelines/) |
| `demo/payroll.html` | October Payroll Run | [open](https://prod-discovery.github.io/agent-design-guidelines/demo/payroll.html) |
| `demo/accounting.html` | October Close | [open](https://prod-discovery.github.io/agent-design-guidelines/demo/accounting.html) |
| `demo/front-door.html` | Berg Bygg Overview, the front door that links to the other two demos | [open](https://prod-discovery.github.io/agent-design-guidelines/demo/front-door.html) |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are. Keep it. | |

Each page is a single self-contained HTML file. The only external dependency is Google Fonts (Inter, IBM Plex Mono).

This repo is the source of truth. The original Claude artifacts are no longer updated.

## How to update a page

1. Edit the HTML file (or replace it with a new version).
2. Keep these two lines in the `<head>` of every page:
   ```html
   <meta name="robots" content="noindex, nofollow">
   <link rel="icon" href="data:image/svg+xml,...">
   ```
   The first keeps the pages out of Google and other search engines. If you paste in a fresh export from a Claude artifact, add them back.
3. Links between pages must be relative (`payroll.html`, `demo/payroll.html`), never `claude.ai/artifact/...` links, since those only open for people the artifact is shared with.
4. Check it locally before pushing:
   ```bash
   python3 -m http.server 8765
   ```
   then open http://localhost:8765
5. Commit and push to `main`. The site rebuilds automatically.

## How to check a change is live

GitHub Pages usually rebuilds in 1 to 10 minutes after a push. To check:

- **Actions tab** in this repo: the "pages build and deployment" run should be green.
- Or from the terminal:
  ```bash
  gh api repos/Prod-Discovery/agent-design-guidelines/pages --jq .status
  ```
  `built` means it is live. `errored` means the build failed (check the Actions tab).
- Then hard-refresh the page (Cmd+Shift+R), the CDN can cache the old version for a few minutes.

## Visibility

The repo and site are public: anyone with the link can open them. The noindex tag keeps them out of search results, but it does not restrict access, so don't put anything confidential here.

## Related

- [Discovery to Prototype Engine guide](https://prod-discovery.github.io/discovery-engine-guide/)
