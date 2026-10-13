#!/usr/bin/env python3
"""Lists what an artifact changed compared with the site, to bring over only those changes.

The team edits copies of the site and demos in Claude artifacts. Those copies
have the text written straight into the HTML, while here most text lives in
patterns.json. This script pulls every piece of text out of the artifact and
out of the repo, and prints:

  NEW      text in the artifact that the repo doesn't have (added or reworded)
  GONE     text in the repo's target file that the artifact doesn't have (removed,
           or the old version of a reworded text)

For each NEW text it also says the closest existing text and where that lives
(patterns.json path, index.html or a demo), so you know where the change goes.

    python3 scripts/find_changes.py path/to/artifact.html                 # vs the site
    python3 scripts/find_changes.py path/to/artifact.html demo/payroll.html  # vs a demo

Standard library only. It finds text changes; layout and code changes still
need reading the HTML side by side.
"""
import difflib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN = 18  # shorter strings are mostly code, ids and labels


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = s.replace("\\n", " ").replace("\\'", "'").replace('\\"', '"')
    return re.sub(r"\s+", " ", s).strip()


def texts_from_html(src):
    """Visible text and the text inside JavaScript strings."""
    found = set()
    no_style = re.sub(r"<style.*?</style>", " ", src, flags=re.S | re.I)
    for m in re.finditer(r"'((?:[^'\\\n]|\\.){%d,})'|\"((?:[^\"\\\n]|\\.){%d,})\"|`([^`]{%d,})`" % (MIN, MIN, MIN), no_style):
        found.add(norm(next(g for g in m.groups() if g)))
    body = re.sub(r"<script.*?</script>", " ", no_style, flags=re.S | re.I)
    for chunk in re.split(r"<[^>]+>", body):
        found.add(norm(chunk))
    return {t for t in found if len(t) >= MIN and re.search(r"[a-z]{3,} [a-z]{2,}", t, flags=re.I)
            and not re.search(r"[{};=]|=>|\$\{|function|const |var\(|px\b|rgba?\(", t)}


def texts_from_json(node, path="patterns.json"):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from texts_from_json(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            label = v.get("id") if isinstance(v, dict) and "id" in v else i
            yield from texts_from_json(v, f"{path}[{label}]")
    elif isinstance(node, str) and len(node) >= MIN:
        yield norm(node), path


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    artifact_src = Path(sys.argv[1]).read_text(encoding="utf-8")
    artifact = texts_from_html(artifact_src)
    target = sys.argv[2] if len(sys.argv) > 2 else "index.html"
    target_src = (ROOT / target).read_text(encoding="utf-8")
    repo = {}
    repo_src = target_src
    if target == "index.html":
        pj = (ROOT / "patterns.json").read_text(encoding="utf-8")
        repo_src += " " + pj
        for t, where in texts_from_json(json.loads(pj)):
            repo.setdefault(t, where)
    for t in texts_from_html(target_src):
        repo.setdefault(t, target)

    # Compare by searching each text in the other side's whole source: sturdier than
    # matching extracted strings, since quotes inside code confuse the extraction.
    artifact_blob, repo_blob = norm(artifact_src), norm(repo_src)
    new = sorted(t for t in artifact if t not in repo_blob)
    gone = sorted(t for t in repo if t not in artifact_blob)
    repo_list = list(repo)
    print(f"Comparing {sys.argv[1]} with {target}" + (" and patterns.json" if target == "index.html" else ""))
    print(f"\nNEW in the artifact ({len(new)}):")
    for t in new:
        close = difflib.get_close_matches(t, repo_list, n=1, cutoff=0.6)
        hint = f"\n      reworded from: {close[0][:140]}\n      lives in: {repo[close[0]]}" if close else "\n      (no similar text: probably added)"
        print(f"  + {t[:300]}{hint}")
    print(f"\nGONE from the artifact ({len(gone)}), only removals or old versions matter:")
    for t in gone:
        print(f"  - {t[:200]}   [{repo[t]}]")


if __name__ == "__main__":
    main()
