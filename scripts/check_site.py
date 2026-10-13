#!/usr/bin/env python3
"""Checks the site's HTML before it is published: index.html and demo/*.html.

Changes often arrive from Claude artifacts. This catches what usually goes wrong
when they are brought over: a script that no longer runs, a missing noindex tag,
links that only work inside claude.ai, and index.html replaced by the artifact's
own copy of the site (which would drop patterns.json, the Claude review and the
usage tracking without any visible error).

    python3 scripts/check_site.py

Uses only the standard library, plus `node` to check JavaScript if it's installed.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOINDEX = '<meta name="robots" content="noindex, nofollow">'
# Things that only work inside a claude.ai artifact, or point at one.
FORBIDDEN = {
    "window.claude": "uses Claude's artifact features (window.claude), which don't work outside claude.ai",
    "claude.ai/artifact": "links to a claude.ai artifact, which only people it was shared with can open",
    "claude.ai/code/artifact": "links to a claude.ai artifact, which only people it was shared with can open",
    "localhost:": "links to localhost, which only works on one computer",
}
# index.html must keep these, or the site silently stops using the shared pieces.
INDEX_NEEDS = {
    "fetch('patterns.json'": "loading patterns.json (the content would no longer come from the shared file)",
    "aApi('api/review'": "the Claude review on Assess your agent",
    "aApi('api/ideas'": "the ideas for your agent on Assess your agent",
    "track('page_view'": "the usage tracking",
    "id=\"aFeedback\"": "the feedback card on Assess your agent",
}


def scripts_ok(path, html, errors):
    blocks = [b for b in re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.S | re.I) if b.strip()]
    node = shutil.which("node")
    if not node:
        print(f"  (node not installed, JavaScript in {path} not checked)")
        return
    for i, block in enumerate(blocks, 1):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(block)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        Path(f.name).unlink()
        if r.returncode:
            detail = next((ln for ln in r.stderr.splitlines() if "Error" in ln), r.stderr.strip()[:200])
            errors.append(f"{path}: script {i} has a JavaScript error and would stop the page working: {detail}")


def check_page(path, errors, needs=None):
    html = (ROOT / path).read_text(encoding="utf-8")
    if NOINDEX not in html:
        errors.append(f'{path}: the noindex tag is missing. Add {NOINDEX} inside <head>, so search engines skip it')
    if not re.search(r"<html[^>]*\blang=", html, flags=re.I):
        errors.append(f'{path}: <html> needs lang="en" (screen readers use it)')
    for needle, why in FORBIDDEN.items():
        if needle in html:
            errors.append(f"{path}: {why}. Remove it")
    for needle, what in (needs or {}).items():
        if needle not in html:
            errors.append(
                f"{path}: it no longer contains {needle!r}, which is {what}. This usually means the file was "
                "replaced by an artifact's copy of the site. Put the original back and bring over only the changes"
            )
    scripts_ok(path, html, errors)
    return html


def main():
    errors = []
    index = check_page("index.html", errors, INDEX_NEEDS)
    demos = sorted((ROOT / "demo").glob("*.html"))
    for d in demos:
        check_page(f"demo/{d.name}", errors)
    unlinked = [d.name for d in demos if f"demo/{d.name}" not in index]
    if errors:
        print("The site has problems. Nothing was published:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Site OK: index.html and {len(demos)} demos checked.")
    for name in unlinked:
        print(f"  Note: demo/{name} isn't linked from the site yet (add it to the Demo menu in index.html).")


if __name__ == "__main__":
    main()
