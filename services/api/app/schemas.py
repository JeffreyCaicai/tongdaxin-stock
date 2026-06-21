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


class StockPoolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: str | None = None
    is_default: bool = False


class StockPoolCreate(StockPoolBase):
    pass


class StockPoolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    is_default: bool | None = None


class StockPoolOut(StockPoolBase):
    id: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class WatchlistBase(BaseModel):
    pool_id: int | None = None
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
    pool_id: int | None = None


class WorkbenchActionOut(BaseModel):
    generated_at: str
    total_holdings: int
    generated_signals: int
    missing_prices: list[str]
    signals: list[SignalOut]


class MarketQuoteOut(BaseModel):
    snapshot_id: int
    symbol: str
    name: str | None = None
    source: str
    price: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    previous_close: float | None = None
    change: float | None = None
    pct_change: float | None = None
    volume: float | None = None
    amount: float | None = None
    fetched_at: str
    payload: dict[str, Any] = Field(default_factory=dict)


class StockSearchOut(BaseModel):
    symbol: str
    name: str | None = None
    source: str
    market: str | None = None
    price: float | None = None


class MarketKlineBarOut(BaseModel):
    symbol: str
    source: str
    period: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    amount: float | None = None
    fetched_at: str


class MarketKlineOut(BaseModel):
    symbol: str
    source: str
    period: str
    count: int
    bars: list[MarketKlineBarOut]


class MarketFetchLogOut(BaseModel):
    id: int
    symbol: str
    source: str
    data_type: str
    status: str
    message: str | None = None
    fetched_at: str


class WorkbenchMarketActionRequest(BaseModel):
    source: str = "tongdaxin"
    persist: bool = True
    include_technical: bool = False
    kline_limit: int = Field(default=120, ge=35, le=1000)
    pool_id: int | None = None


class McpToolCallRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


class McpToolListOut(BaseModel):
    server: str
    tools: list[dict[str, Any]]


class McpToolCallOut(BaseModel):
    server: str
    tool_name: str
    result: dict[str, Any]


class StockPoolMcpAnalysisRequest(BaseModel):
    persist: bool = True
    max_symbols: int = Field(default=30, ge=1, le=100)
    quote_tool: str | None = None
    profile_tool: str | None = None
    include_profile: bool = True
    quote_arguments: dict[str, Any] | None = None
    profile_arguments: dict[str, Any] | None = None


class StockPoolMarketAnalysisRequest(BaseModel):
    source: str = "tdx-official"
    persist: bool = True
    max_symbols: int = Field(default=30, ge=1, le=100)


class StockPoolChanAnalysisRequest(BaseModel):
    source: str = "tdx-official"
    period: str = "daily"
    persist: bool = True
    max_symbols: int = Field(default=30, ge=1, le=100)
    kline_limit: int = Field(default=240, ge=35, le=1000)


class IndicatorSnapshotOut(BaseModel):
    symbol: str
    source: str
    period: str
    snapshot: dict[str, Any]


class ReportOut(BaseModel):
    id: int | None = None
    report_type: str
    symbol: str | None = None
    created_at: str | None = None
    payload: dict[str, Any]


class BacktestRequest(BaseModel):
    source: str = "tongdaxin"
    period: str = "daily"
    limit: int = Field(default=240, ge=80, le=1000)
    initial_equity: float = Field(default=100000.0, gt=0)
    stop_loss_pct: float = Field(default=6.0, gt=0, le=50)
    take_profit_pct: float = Field(default=12.0, gt=0, le=200)
    persist: bool = True


class BacktestOut(BaseModel):
    id: int | None = None
    symbol: str
    source: str
    strategy_name: str
    created_at: str | None = None
    config: dict[str, Any]
    result: dict[str, Any]


class SignalReviewOut(BaseModel):
    generated_at: str
    count: int
    reviews: list[dict[str, Any]]
