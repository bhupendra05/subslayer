"""Parse a bank-statement CSV into transactions. Auto-detects common column names."""
from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import List, Optional

from .models import Transaction

_DATE_KEYS = ["date", "txn date", "transaction date", "value date", "posting date"]
_DESC_KEYS = ["description", "narration", "details", "particulars", "merchant", "remarks"]
_DEBIT_KEYS = ["debit", "withdrawal", "withdrawal amt", "amount debited", "debit amount", "dr"]
_AMOUNT_KEYS = ["amount", "amount (inr)", "transaction amount", "amt"]
_DATE_FMTS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y",
    "%d %b %Y", "%d-%b-%Y", "%d %B %Y", "%Y/%m/%d",
]


def _pick(headers: List[str], keys: List[str]) -> Optional[str]:
    low = {h.lower().strip(): h for h in headers}
    for k in keys:
        if k in low:
            return low[k]
    for h in headers:
        hl = h.lower().strip()
        for k in keys:
            if k in hl:
                return h
    return None


def _money(v) -> float:
    if v is None:
        return 0.0
    s = str(v).strip()
    for junk in (",", "₹", "INR", "Rs.", "Rs", " "):
        s = s.replace(junk, "")
    if s in ("", "-"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_date(v):
    s = str(v).strip()
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def read_transactions(path: str) -> List[Transaction]:
    """Read charges (money out) from a bank-statement CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        date_col = _pick(headers, _DATE_KEYS)
        desc_col = _pick(headers, _DESC_KEYS)
        debit_col = _pick(headers, _DEBIT_KEYS)
        amount_col = None if debit_col else _pick(headers, _AMOUNT_KEYS)
        if not date_col or not desc_col:
            raise ValueError("Could not find date / description columns in the CSV.")

        txns: List[Transaction] = []
        for row in reader:
            d = _parse_date(row.get(date_col, ""))
            if not d:
                continue
            desc = (row.get(desc_col) or "").strip()
            if not desc:
                continue
            if debit_col:
                amt = _money(row.get(debit_col))
                if amt <= 0:
                    continue
            else:
                a = _money(row.get(amount_col)) if amount_col else 0.0
                if a >= 0:  # treat negative amounts as charges (money out)
                    continue
                amt = abs(a)
            txns.append(Transaction(date=d, description=desc, amount=amt))
        return txns
