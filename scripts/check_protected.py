#!/usr/bin/env python3
"""Refuses to publish if a protected file changed.

Content editors may change patterns.json, index.html (the site's pages and live
examples) and the demos in demo/ (including adding new demo .html files).
Every other tracked file (the server, the Claude review, usage tracking, the
workflows, these scripts, the rules) is fingerprinted in
scripts/protected-files.sha256. If one of them changes, or a new file appears
outside demo/, this check fails and nothing is published.

    python3 scripts/check_protected.py            # check (runs on every push)
    python3 scripts/check_protected.py --update   # maintainers only: accept code changes

Only run --update when you meant to change code. See CLAUDE.md.

On GitHub the fingerprint file itself is also checked: its hash must match the
repository variable PROTECTED_LOCK_SHA, which only repo admins can change. So
running --update is not enough to get a code change published; an admin also
has to run, after pushing:

    gh variable set PROTECTED_LOCK_SHA --repo Prod-Discovery/agent-design-guidelines \
        --body "$(shasum -a 256 scripts/protected-files.sha256 | cut -d' ' -f1)"
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "scripts" / "protected-files.sha256"
def editable(path):
    """Files content editors may change or add."""
    return path in ("patterns.json", "index.html") or (
        path.startswith("demo/") and path.count("/") == 1 and path.endswith(".html")
    )


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    files = {f for f in out.stdout.splitlines() if f and not editable(f)}
    return sorted(files - {LOCK.relative_to(ROOT).as_posix()})


def fingerprint(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main():
    current = {f: fingerprint(f) for f in tracked_files()}
    if "--update" in sys.argv:
        LOCK.write_text("".join(f"{h}  {f}\n" for f, h in current.items()))
        print(f"Updated {LOCK.name}: {len(current)} protected files.")
        return

    expected = os.environ.get("EXPECTED_LOCK_SHA", "").strip()
    if os.environ.get("CI") == "true" and not expected:
        sys.exit("The repository variable PROTECTED_LOCK_SHA is not set, so nothing is published. An admin has to set it.")
    if expected and hashlib.sha256(LOCK.read_bytes()).hexdigest() != expected:
        print(
            "The list of protected files (scripts/protected-files.sha256) was changed. Nothing was published.\n"
            "Only patterns.json, index.html and demo/*.html can be changed. Ask Claude: \"Put back scripts/protected-files.sha256 and every "
            "protected file exactly as they were on the last green run, and push again.\"",
            file=sys.stderr,
        )
        sys.exit(1)

    locked = {}
    for line in LOCK.read_text().splitlines():
        h, f = line.split("  ", 1)
        locked[f] = h
    changed = sorted(f for f in current if f in locked and current[f] != locked[f])
    added = sorted(f for f in current if f not in locked)
    removed = sorted(f for f in locked if f not in current)
    if not (changed or added or removed):
        print(f"Protected files OK: only patterns.json, index.html and demo/*.html changed ({len(current)} protected files checked).")
        return

    print("Only patterns.json, index.html and demo/*.html can be changed. Nothing was published.", file=sys.stderr)
    for label, files in (("Changed", changed), ("New", added), ("Deleted", removed)):
        for f in files:
            print(f"  {label}: {f}", file=sys.stderr)
    print(
        "\nTo fix it, ask Claude: \"Put back the files listed in the failed check "
        "exactly as they were on the last green run, and push again.\"\n"
        "If the change to these files was meant (code, not content), it has to wait for Cristina.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
