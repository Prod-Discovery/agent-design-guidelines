# Test pack: expected results

Six test agents for the "Assess your agent" page: three sets of agent instructions and three HTML prototypes, each weak, medium or strong.

**How to test:** set the domain shown below, choose "Agent instructions" (paste the .md file) or "Prototype" (upload the .html file), and click "Review my agent". Compare Claude's answers with the expected ones. A difference of one level on a question is normal; a difference of two levels, or a missed trap, is worth looking into.

Levels: 0 = Not yet, 1 = Partly, 2 = Yes.

## Summary

| File | Input | Domain | Expected score | Expected band |
|---|---|---|---|---|
| instructions-1-collections-weak.md | Agent instructions | Invoicing and payments | about 21 | An assistant bolted on |
| instructions-2-payroll-medium.md | Agent instructions | Payroll | about 50 | Useful, not yet trusted |
| instructions-3-vat-strong.md | Agent instructions | Tax and VAT | about 100 | Best-in-class |
| prototype-1-invoice-assistant-weak.html | Prototype | Invoicing and payments | about 9 | An assistant bolted on |
| prototype-2-payroll-run-medium.html | Prototype | Payroll | about 50 | Useful, not yet trusted |
| prototype-3-bookkeeping-inbox-strong.html | Prototype | Bookkeeping and month-end close | about 100 | Best-in-class |

## Expected answers per question

| File | 1 Lead | 2 Stakes | 3 Never hide | 4 Control | 5 Flag new | 6 Earned |
|---|---|---|---|---|---|---|
| Instructions 1, collections | 2 | 0 | 0 | 1 | 0 | 0 |
| Instructions 2, payroll | 2 | 1 | 1 | 1 | 1 | 0 |
| Instructions 3, VAT | 2 | 2 | 2 | 2 | 2 | 2 |
| Prototype 1, invoice assistant | 0 | 0 | 1 | 0 | 0 | 0 |
| Prototype 2, payroll run | 2 | 1 | 1 | 1 | 1 | 0 |
| Prototype 3, bookkeeping inbox | 2 | 2 | 2 | 2 | 2 | 2 |

## Traps a good review should catch

**Instructions 1, collections (weak)**
- Called "Lena", signs as a person, and told to hide that it's automated: breaks principle 3 and the AI Act.
- "If you are unsure, pick the closest match": the opposite of 09 Clarifying questions.
- Sends customer emails directly, writes off amounts automatically, one on/off switch.
- Credit due: it never pays suppliers, and large invoices go to the finance manager.

**Instructions 2, payroll (medium)**
- Good: labelled "Payroll agent", starts on its own, shows progress with rules, before-and-after with accept, edit or reject, payments and filings wait for approval.
- Gaps: one autonomy level for all tasks; undo only in the event log; "continue with what you have" when data is missing hides failures (06 Failure disclosure); silently uses 30% default tax instead of asking (09 Clarifying questions); nothing earns autonomy.

**Instructions 3, VAT (strong)**
- Should find all 14 patterns present, including per-task levels with "never Autopilot" for filing and paying, clarifying questions with a best guess, escalation to a named person, failure disclosure, and earned autonomy that steps back after corrections.

**Prototype 1, invoice assistant (weak)**
- Chat box is the front door; a one-time "This page uses AI" banner; named "Max"; a bare "Confidence 94%".
- Acted immediately: reminders sent, write-offs and VAT changes made, then "Accept all changes" after the fact, with no undo.

**Prototype 2, payroll run (medium)**
- Good: "Agent" labels, started on its own, progress count with rules, per-employee before-and-after with accept, edit or reject.
- Gaps: approval of the whole run is the only control level; undo only in the event log; default 30% tax applied instead of asking; no recap; no earned autonomy.

**Prototype 3, bookkeeping inbox (strong)**
- Should find all 14 patterns: welcome-back brief, exceptions with reasons, clarifying question with best guess, before-and-after correction, escalation to a named person, failure disclosure for the bank sync, undo with a window and a warning, live progress with pause and screen reader note, per-task levels, earned autonomy offer, weekly recap with weak spots, plain-language audit trail.

## Scores, worked out

Each score is the weighted average of the six answers, as a percentage. For example, instructions 1 in "Invoicing and payments": (2×1 + 0×1.3 + 0×1.2 + 1×1 + 0×1.5 + 0×1) ÷ 2 ÷ 7 = 21%. The full formula is in the assessment logic document.
