"""Tests for SubSlayer detection."""
import os
from datetime import date, timedelta

from subslayer.detect import analyze_csv, detect_subscriptions
from subslayer.models import Cadence, Transaction

SAMPLE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "sample_statement.csv")
)


def _monthly(desc, amount, n=4, start=date(2026, 1, 5), step=30):
    return [
        Transaction(date=start + timedelta(days=step * i), description=desc, amount=amount)
        for i in range(n)
    ]


def test_detects_monthly_subscription():
    r = detect_subscriptions(_monthly("NETFLIX", 649))
    assert len(r.subscriptions) == 1
    s = r.subscriptions[0]
    assert s.cadence is Cadence.MONTHLY
    assert s.occurrences == 4
    assert abs(s.annual_cost - 649 * 12) < 1


def test_ignores_variable_spend():
    txns = [
        Transaction(date=date(2026, 1, 3), description="SWIGGY", amount=320),
        Transaction(date=date(2026, 1, 20), description="SWIGGY", amount=540),
        Transaction(date=date(2026, 2, 8), description="SWIGGY", amount=210),
        Transaction(date=date(2026, 3, 1), description="SWIGGY", amount=615),
    ]
    assert detect_subscriptions(txns).subscriptions == []


def test_ignores_single_charge():
    txns = [Transaction(date=date(2026, 1, 1), description="AMAZON", amount=2499)]
    assert detect_subscriptions(txns).subscriptions == []


def test_price_increase_flagged():
    txns = _monthly("NETFLIX", 649, n=3)
    txns.append(Transaction(date=date(2026, 4, 5), description="NETFLIX", amount=699))
    s = detect_subscriptions(txns).subscriptions[0]
    assert s.price_increased
    assert "price_increased" in s.flags


def test_overlap_savings():
    txns = _monthly("NETFLIX", 649) + _monthly("DISNEY HOTSTAR", 299)
    r = detect_subscriptions(txns)
    assert r.potential_savings_annual > 0
    # the more expensive duplicate is what you could cut
    assert any("overlaps:Streaming" in s.flags for s in r.subscriptions)


def test_csv_pipeline():
    r = analyze_csv(SAMPLE)
    merchants = {s.merchant for s in r.subscriptions}
    assert len(r.subscriptions) == 7
    assert "Netflix" in merchants
    assert not any("swiggy" in m.lower() for m in merchants)  # variable spend excluded
    assert r.total_annual > 0
    assert r.potential_savings_annual > 9000  # Streaming + Music overlaps
    netflix = next(s for s in r.subscriptions if s.merchant == "Netflix")
    assert netflix.price_increased
