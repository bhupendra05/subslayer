"""Render a SubSlayer Report as text or JSON."""
from __future__ import annotations

from .models import Report


def _money(currency: str, amount: float) -> str:
    return f"{currency}{amount:,.0f}"


def to_text(report: Report) -> str:
    c = report.currency
    n = len(report.subscriptions)
    lines = [
        "# SubSlayer — Subscription Audit",
        "",
        f"You have {n} subscription{'s' if n != 1 else ''} costing "
        f"{_money(c, report.total_monthly)}/month ({_money(c, report.total_annual)}/year).",
    ]
    if report.potential_savings_annual > 0:
        lines.append(
            f"💸 Potential savings: {_money(c, report.potential_savings_annual)}/year "
            "by cutting overlaps."
        )
    lines.append("")

    for s in report.subscriptions:
        notes = []
        if s.price_increased:
            notes.append("⚠ price increased")
        for f in s.flags:
            if f.startswith("overlaps:"):
                notes.append(f"⚠ overlaps {f.split(':', 1)[1]}")
        note = ("   " + " · ".join(notes)) if notes else ""
        lines.append(
            f"  {_money(c, s.annual_cost):>11}/yr  {s.merchant:<22} "
            f"{s.category:<14} {s.cadence.value}{note}"
        )

    if not report.subscriptions:
        lines.append("  No recurring subscriptions detected. 🎉")

    lines.append("")
    lines.append("_SubSlayer detects recurring charges from your statement. Review before cancelling._")
    return "\n".join(lines)


def to_json(report: Report) -> str:
    return report.model_dump_json(indent=2)
