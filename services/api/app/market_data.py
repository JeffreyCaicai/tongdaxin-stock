from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any, Protocol

from .repository import normalize_symbol, utc_now


class MarketDataError(RuntimeError):
    pass


class MarketDataProvider(Protocol):
    name: str

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        raise NotImplementedError

    def fetch_kline(
        self,
        symbol: str,
        *,
        period: str = "daily",
        limit: int = 120,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class MockMarketDataProvider:
    name = "mock"

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        normalized_symbol = normalize_symbol(symbol)
        base = _symbol_base_price(normalized_symbol)
        drift = _symbol_drift(normalized_symbol)
        current = round(base * (1 + drift), 3)
        previous_close = round(base, 3)
        change = round(current - previous_close, 3)
        pct_change = round((change / previous_close) * 100, 3)

        return {
            "symbol": normalized_symbol,
            "name": f"Mock {normalized_symbol}",
            "source": self.name,
            "price": current,
            "open": round(previous_close * 0.997, 3),
            "high": round(max(current, previous_close) * 1.012, 3),
            "low": round(min(current, previous_close) * 0.988, 3),
            "previous_close": previous_close,
            "change": change,
            "pct_change": pct_change,
            "volume": int((_symbol_seed(normalized_symbol) % 9000 + 1000) * 100),
            "amount": round(current * (_symbol_seed(normalized_symbol) % 9000 + 1000) * 100, 2),
            "fetched_at": utc_now(),
            "is_mock": True,
        }

    def fetch_kline(
        self,
        symbol: str,
        *,
        period: str = "daily",
        limit: int = 120,
    ) -> list[dict[str, Any]]:
        if period != "daily":
            raise MarketDataError("Mock provider currently supports daily kline only")

        normalized_symbol = normalize_symbol(symbol)
        seed = _symbol_seed(normalized_symbol)
        base = _symbol_base_price(normalized_symbol)
        today = date.today()
        bars: list[dict[str, Any]] = []

        for index in range(max(1, min(limit, 1000))):
            days_back = limit - index - 1
            trade_date = today - timedelta(days=days_back)
            wave = math.sin((index + seed % 17) / 5) * 0.025
            trend = (index - limit / 2) * 0.0008
            close = base * (1 + wave + trend)
            open_price = close * (1 + math.sin(index / 3) * 0.006)
            high = max(open_price, close) * 1.012
            low = min(open_price, close) * 0.988
            volume = int((seed % 5000 + 5000) * (1 + abs(wave) * 8))

            bars.append(
                {
                    "symbol": normalized_symbol,
                    "source": self.name,
                    "period": period,
                    "trade_date": trade_date.isoformat(),
                    "open": round(open_price, 3),
                    "high": round(high, 3),
                    "low": round(low, 3),
                    "close": round(close, 3),
                    "volume": volume,
                    "amount": round(volume * close, 2),
                    "payload": {"is_mock": True},
                }
            )

        return bars


class AkShareMarketDataProvider:
    name = "akshare"

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        akshare = _load_akshare()
        normalized_symbol = normalize_symbol(symbol)
        spot = akshare.stock_zh_a_spot_em()
        row = spot.loc[spot["代码"] == normalized_symbol]
        if row.empty:
            raise MarketDataError(f"AkShare quote not found for {normalized_symbol}")
        data = row.iloc[0].to_dict()
        price = _required_float(data.get("最新价"), "最新价")
        previous_close = _safe_float(data.get("昨收"))
        change = _safe_float(data.get("涨跌额"))
        pct_change = _safe_float(data.get("涨跌幅"))

        return {
            "symbol": normalized_symbol,
            "name": data.get("名称"),
            "source": self.name,
            "price": price,
            "open": _safe_float(data.get("今开")),
            "high": _safe_float(data.get("最高")),
            "low": _safe_float(data.get("最低")),
            "previous_close": previous_close,
            "change": change,
            "pct_change": pct_change,
            "volume": _safe_float(data.get("成交量")),
            "amount": _safe_float(data.get("成交额")),
            "turnover_rate": _safe_float(data.get("换手率")),
            "fetched_at": utc_now(),
            "raw": _jsonable(data),
        }

    def fetch_kline(
        self,
        symbol: str,
        *,
        period: str = "daily",
        limit: int = 120,
    ) -> list[dict[str, Any]]:
        if period != "daily":
            raise MarketDataError("AkShare provider currently supports daily kline only")

        akshare = _load_akshare()
        normalized_symbol = normalize_symbol(symbol)
        start_date = (date.today() - timedelta(days=max(limit * 3, 365))).strftime("%Y%m%d")
        end_date = date.today().strftime("%Y%m%d")
        history = akshare.stock_zh_a_hist(
            symbol=normalized_symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        if history.empty:
            raise MarketDataError(f"AkShare kline not found for {normalized_symbol}")

        bars: list[dict[str, Any]] = []
        for _, row in history.tail(limit).iterrows():
            data = row.to_dict()
            bars.append(
                {
                    "symbol": normalized_symbol,
                    "source": self.name,
                    "period": period,
                    "trade_date": str(data["日期"]),
                    "open": _required_float(data.get("开盘"), "开盘"),
                    "high": _required_float(data.get("最高"), "最高"),
                    "low": _required_float(data.get("最低"), "最低"),
                    "close": _required_float(data.get("收盘"), "收盘"),
                    "volume": _safe_float(data.get("成交量")),
                    "amount": _safe_float(data.get("成交额")),
                    "payload": _jsonable(data),
                }
            )
        return bars


def get_market_data_provider(source: str | None) -> MarketDataProvider:
    source_name = (source or "mock").strip().lower()
    if source_name == "mock":
        return MockMarketDataProvider()
    if source_name == "akshare":
        return AkShareMarketDataProvider()
    raise MarketDataError(
        f"Unsupported market data source '{source_name}'. Available sources: mock, akshare."
    )


def _symbol_seed(symbol: str) -> int:
    digits = "".join(character for character in symbol if character.isdigit())
    if digits:
        return int(digits)
    return sum(ord(character) for character in symbol)


def _symbol_base_price(symbol: str) -> float:
    seed = _symbol_seed(symbol)
    return round((seed % 18000) / 100 + 8, 3)


def _symbol_drift(symbol: str) -> float:
    seed = _symbol_seed(symbol)
    return ((seed % 700) - 350) / 10000


def _load_akshare() -> Any:
    try:
        import akshare  # type: ignore
    except ModuleNotFoundError as exc:
        raise MarketDataError(
            "AkShare is not installed. Install it with 'pip install akshare' or use source=mock."
        ) from exc
    return akshare


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if value != value:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _required_float(value: Any, field_name: str) -> float:
    parsed = _safe_float(value)
    if parsed is None:
        raise MarketDataError(f"AkShare returned empty numeric field: {field_name}")
    return parsed


def _jsonable(row: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in row.items():
        if hasattr(value, "item"):
            value = value.item()
        if isinstance(value, (int, float, str, bool)) or value is None:
            output[str(key)] = value
        else:
            output[str(key)] = str(value)
    return output
