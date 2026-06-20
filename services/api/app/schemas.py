from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HoldingBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16)
    name: str | None = None
    market: str | None = "A"
    quantity: float = Field(default=0, ge=0)
    cost_price: float = Field(..., gt=0)
    strategy_horizon: str | None = "swing"
    initial_thesis: str | None = None
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    max_loss_pct: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=16)
    name: str | None = None
    market: str | None = None
    quantity: float | None = Field(default=None, ge=0)
    cost_price: float | None = Field(default=None, gt=0)
    strategy_horizon: str | None = None
    initial_thesis: str | None = None
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    max_loss_pct: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class HoldingOut(HoldingBase):
    id: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class WatchlistBase(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16)
    name: str | None = None
    market: str | None = "A"
    thesis: str | None = None
    buy_zone_low: float | None = Field(default=None, gt=0)
    buy_zone_high: float | None = Field(default=None, gt=0)
    trigger_condition: str | None = None
    invalidation_condition: str | None = None
    priority: int = Field(default=3, ge=1, le=5)
    status: str = "watching"
    notes: str | None = None


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistUpdate(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=16)
    name: str | None = None
    market: str | None = None
    thesis: str | None = None
    buy_zone_low: float | None = Field(default=None, gt=0)
    buy_zone_high: float | None = Field(default=None, gt=0)
    trigger_condition: str | None = None
    invalidation_condition: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    status: str | None = None
    notes: str | None = None


class WatchlistOut(WatchlistBase):
    id: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class SignalEvaluateRequest(BaseModel):
    current_price: float = Field(..., gt=0)
    source_snapshot_id: int | None = None


class SignalOut(BaseModel):
    id: int | None = None
    symbol: str
    signal_type: str
    action: str
    strength: float
    price: float
    risk_level: str
    reasons: list[str]
    next_check: str
    source_snapshot_id: int | None = None
    created_at: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class WorkbenchActionRequest(BaseModel):
    prices: dict[str, float] = Field(
        ...,
        description="Current prices keyed by stock symbol.",
    )
    persist: bool = True


class WorkbenchActionOut(BaseModel):
    generated_at: str
    total_holdings: int
    generated_signals: int
    missing_prices: list[str]
    signals: list[SignalOut]
