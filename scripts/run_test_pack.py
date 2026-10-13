"""Run the six test files through the real review and compare with the answer key.

    .venv/bin/python scripts/run_test_pack.py                       # Opus 5.5, medium effort
    .venv/bin/python scripts/run_test_pack.py claude-sonnet-5-5 high

Each run calls Claude on Vertex AI and costs a few cents per file.
A difference of one level on a question is normal (answer-key.md); two levels
is worth looking into.
"""

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app  # noqa: E402
import review  # noqa: E402

PACK = Path(__file__).resolve().parent.parent / "test-pack"

# From test-pack/answer-key.md: file, mode, domain, expected levels in question order.
CASES = [
    ("instructions-1-collections-weak.md", "instructions", "invoicing", [2, 0, 0, 1, 0, 0]),
    ("instructions-2-payroll-medium.md", "instructions", "payroll", [2, 1, 1, 1, 1, 0]),
    ("instructions-3-vat-strong.md", "instructions", "tax", [2, 2, 2, 2, 2, 2]),
    ("prototype-1-invoice-assistant-weak.html", "spec", "invoicing", [0, 0, 1, 0, 0, 0]),
    ("prototype-2-payroll-run-medium.html", "spec", "payroll", [2, 1, 1, 1, 1, 0]),
    ("prototype-3-bookkeeping-inbox-strong.html", "spec", "close", [2, 2, 2, 2, 2, 2]),
]


def score(domain, levels):
    w = review.DOMAINS[domain]["weights"]
    done = [(review.KEYS[i], lv) for i, lv in enumerate(levels) if lv is not None]
    if not done:
        return None
    total = sum(w.get(k, 1) for k, _ in done)
    return round(100 * sum(w.get(k, 1) * lv / 2 for k, lv in done) / total)


def run_case(case, model, effort):
    name, mode, domain, expected = case
    text = f"--- {name} ---\n" + (PACK / name).read_text()
    result, report = app.run_review(mode, text, model=model, effort=effort)
    got = {a["k"]: a["level"] for a in result["answers"]}
    levels = [got.get(k) for k in review.KEYS]
    return name, domain, expected, levels, report


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else app.REVIEW_MODEL
    effort = sys.argv[2] if len(sys.argv) > 2 else app.REVIEW_EFFORT
    print(f"Model {model}, effort {effort}\n")
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(lambda c: run_case(c, model, effort), CASES))

    total_cost = 0
    big_misses = 0
    print(f"{'File':44} {'Expected':12} {'Got':12} {'Score':>11} {'In/out tokens':>15} {'Cost':>7} {'Time':>6}")
    for name, domain, expected, levels, rep in rows:
        shown = " ".join("-" if lv is None else str(lv) for lv in levels)
        diffs = [abs(e - g) for e, g in zip(expected, levels) if g is not None]
        flag = " <- 2-level miss" if any(d >= 2 for d in diffs) else ""
        big_misses += bool(flag)
        sc = f"{score(domain, levels)} vs {score(domain, expected)}"
        tokens = f"{rep['input_tokens']}/{rep['output_tokens']}"
        print(f"{name:44} {' '.join(map(str, expected)):12} {shown:12} {sc:>11} {tokens:>15} "
              f"${rep['cost_usd']:.3f} {rep['seconds']:5.0f}s{flag}")
        total_cost += rep["cost_usd"]
    print(f"\nTotal ${total_cost:.3f}, average ${total_cost / len(rows):.3f} per review. "
          f"Files with a 2-level miss: {big_misses} of {len(rows)}.")


if __name__ == "__main__":
    main()
