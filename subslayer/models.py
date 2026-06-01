"""Data models for SubSlayer."""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class Cadence(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    IRREGULAR = "irregular"


class Transaction(BaseModel):
    date: date
    description: str
    amount: float  # positive = money out (a charge)


class Subscription(BaseModel):
    merchant: str
    category: str = "Other"
    amount: float
    cadence: Cadence
    cadence_days: float
    occurrences: int
    first_date: date
    last_date: date
    monthly_cost: float
    annual_cost: float
    price_increased: bool = False
    flags: List[str] = Field(default_factory=list)


class Report(BaseModel):
    subscriptions: List[Subscription] = Field(default_factory=list)
    total_monthly: float = 0.0
    total_annual: float = 0.0
    potential_savings_annual: float = 0.0
    currency: str = "₹"
