# SubSlayer 💸🗡️

**Find and kill forgotten subscriptions.** Point SubSlayer at a bank-statement CSV and it
shows every recurring charge, what you're spending per year, overlapping services you're
paying twice for, and exactly how much you could save.

> The average person has 12+ subscriptions and underestimates the cost by ~2x. SubSlayer
> turns a messy statement into one number: *what you could save.*

```bash
subslayer statement.csv
```

```
# SubSlayer — Subscription Audit

You have 7 subscriptions costing ₹3,971/month (₹47,652/year).
💸 Potential savings: ₹9,216/year by cutting overlaps.

  ₹20,100/yr  Adobe Creative Cloud   Software     monthly
   ₹12,000/yr  Cultfit Membership     Fitness      monthly
    ₹7,788/yr  Netflix                Streaming    monthly   ⚠ price increased
    ₹3,588/yr  Disney Hotstar         Streaming    monthly   ⚠ overlaps Streaming
    ₹1,560/yr  Google One             Cloud Storage monthly
    ₹1,428/yr  Spotify India          Music        monthly   ⚠ overlaps Music
    ₹1,188/yr  Gaana Plus             Music        monthly   ⚠ overlaps Music
```

## What it does

- **Detects recurring charges** — groups your transactions by merchant and finds the ones
  that repeat on a regular cadence (weekly / monthly / quarterly / yearly).
- **Ignores normal spending** — variable charges like food or shopping don't get flagged.
- **Catches price creep** — flags subscriptions whose price quietly went up.
- **Finds overlaps** — two streaming services? two music apps? It shows the duplicates and
  what you'd save by keeping one.
- **One headline number** — total annual spend and potential savings.

Everything runs **locally** — your statement never leaves your machine.

## Install

```bash
pip install subslayer
```

## Usage

```bash
subslayer statement.csv                 # human-readable report
subslayer statement.csv --json          # machine-readable JSON
subslayer statement.csv --currency '$'  # change the symbol
```

Works with most bank CSV exports — it auto-detects the date, description, and debit/amount
columns (`Date`, `Narration`, `Debit`, `Withdrawal`, `Amount`, …).

```python
from subslayer.detect import analyze_csv
report = analyze_csv("statement.csv")
print(report.total_annual, report.potential_savings_annual)
```

## How it works

SubSlayer normalizes each transaction's merchant name, groups them, and keeps a group as a
subscription only if the charges are **regular in time** and **stable in amount** — the
signature of a real subscription versus one-off spending. Categories and overlap detection
use a small, editable keyword map in `subslayer/detect.py`.

## License

MIT
