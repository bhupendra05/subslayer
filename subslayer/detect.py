"""Recurring-charge detection — the core SubSlayer engine."""
from __future__ import annotations

import re
import statistics
from collections import defaultdict
from typing import List, Tuple

from .models import Cadence, Report, Subscription, Transaction
from .parse import read_transactions

# Words that are payment-rail noise, not the merchant.
_NOISE = re.compile(
    r"\b(upi|pos|ach|autopay|auto|nach|imps|neft|rtgs|ref|txn|payment|purchase|debit"
    r"|card|recurring|mandate|subscription|india|pvt|ltd|limited|in|the)\b",
    re.IGNORECASE,
)
_NUMS = re.compile(r"\d+")
_NONALNUM = re.compile(r"[^a-z0-9 ]")

# Small, editable category map. Used to surface overlapping services.
CATEGORY_KEYWORDS = {
    "Streaming": ["netflix", "prime video", "hotstar", "disney", "sonyliv", "zee5",
                  "jiocinema", "jio cinema", "youtube premium"],
    "Music": ["spotify", "apple music", "gaana", "wynk", "youtube music"],
    "Cloud Storage": ["google one", "icloud", "dropbox", "onedrive"],
    "Software": ["adobe", "canva", "notion", "github", "figma", "microsoft", "office"],
    "Fitness": ["cult", "fitternity", "healthify"],
    "News": ["times prime", "nyt", "new york times", "economist"],
    "Food": ["swiggy one", "zomato gold", "zomato pro"],
    "Telecom": ["airtel", "jio", "vodafone"],
}


def _normalize(desc: str) -> str:
    s = desc.lower()
    s = _NUMS.sub(" ", s)
    s = _NONALNUM.sub(" ", s)
    s = _NOISE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def _category(merchant: str) -> str:
    m = merchant.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in m for k in kws):
            return cat
    return "Other"


def _cadence(days: float) -> Tuple[Cadence, float]:
    if 5 <= days <= 9:
        return Cadence.WEEKLY, 7.0
    if 24 <= days <= 35:
        return Cadence.MONTHLY, 30.4
    if 80 <= days <= 100:
        return Cadence.QUARTERLY, 91.0
    if 330 <= days <= 400:
        return Cadence.YEARLY, 365.0
    return Cadence.IRREGULAR, days


def detect_subscriptions(
    txns: List[Transaction],
    min_occurrences: int = 2,
    max_amount_spread: float = 0.25,
) -> Report:
    """Group transactions and keep those that recur regularly at a stable price."""
    groups = defaultdict(list)
    for t in txns:
        key = _normalize(t.description)
        if key:
            groups[key].append(t)

    subs: List[Subscription] = []
    for key, items in groups.items():
        if len(items) < min_occurrences:
            continue
        items.sort(key=lambda t: t.date)
        amounts = [t.amount for t in items]
        dates = [t.date for t in items]
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        gaps = [g for g in gaps if g > 0]
        if not gaps:
            continue

        cadence, canon = _cadence(statistics.median(gaps))
        if cadence is Cadence.IRREGULAR:
            continue

        mean_amt = statistics.mean(amounts)
        if mean_amt <= 0:
            continue
        if (max(amounts) - min(amounts)) / mean_amt > max_amount_spread:
            continue  # variable price => not a subscription (e.g. food, shopping)

        amount = statistics.median(amounts)
        monthly = amount * (30.4 / canon)
        sub = Subscription(
            merchant=_normalize(key).title(),
            category=_category(key),
            amount=round(amount, 2),
            cadence=cadence,
            cadence_days=round(canon, 1),
            occurrences=len(items),
            first_date=dates[0],
            last_date=dates[-1],
            monthly_cost=round(monthly, 2),
            annual_cost=round(monthly * 12, 2),
            price_increased=amounts[-1] > amounts[0] * 1.05,
        )
        if sub.price_increased:
            sub.flags.append("price_increased")
        subs.append(sub)

    savings = _flag_overlaps(subs)
    subs.sort(key=lambda s: s.annual_cost, reverse=True)
    return Report(
        subscriptions=subs,
        total_monthly=round(sum(s.monthly_cost for s in subs), 2),
        total_annual=round(sum(s.annual_cost for s in subs), 2),
        potential_savings_annual=round(savings, 2),
    )


def _flag_overlaps(subs: List[Subscription]) -> float:
    """Flag duplicate services in the same category; return potential annual savings."""
    by_cat = defaultdict(list)
    for s in subs:
        if s.category != "Other":
            by_cat[s.category].append(s)

    savings = 0.0
    for cat, group in by_cat.items():
        if len(group) > 1:
            for s in group:
                s.flags.append(f"overlaps:{cat}")
            cheapest = min(s.annual_cost for s in group)
            savings += sum(s.annual_cost for s in group) - cheapest
    return savings


def analyze_csv(path: str) -> Report:
    """Parse a statement CSV and detect subscriptions in one step."""
    return detect_subscriptions(read_transactions(path))
