from __future__ import annotations

import math
import json
from datetime import date, timedelta
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import get_tdx_api_endpoint, get_tdx_api_key
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


class EltdxMarketDataProvider:
    name = "eltdx"

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        TdxClient, to_jsonable = _load_eltdx()
        normalized_symbol = normalize_symbol(symbol)
        tdx_code = _tdx_code(normalized_symbol)
        try:
            with TdxClient(timeout=5) as client:
                raw_quote = client.get_quote([tdx_code])[0]
        except Exception as exc:
            raise MarketDataError(
                f"eltdx quote request failed for {normalized_symbol}: {exc}. "
                "This usually means the Tongdaxin server connection was reset, timed out, "
                "or is temporarily unavailable."
            ) from exc
        data = to_jsonable(raw_quote) if to_jsonable else _jsonable_object(raw_quote)

        price = _first_required_float(
            data,
            ("price", "last_price", "now", "现价", "最新价", "close"),
            "price",
        )
        previous_close = _first_float(data, ("previous_close", "pre_close", "昨收"))
        change = _first_float(data, ("change", "涨跌", "涨跌额"))
        pct_change = _first_float(data, ("pct_change", "change_pct", "涨幅", "涨跌幅"))

        return {
            "symbol": normalized_symbol,
            "name": _first_text(data, ("name", "stock_name", "名称")),
            "source": self.name,
            "price": price,
            "open": _first_float(data, ("open", "开盘", "今开")),
            "high": _first_float(data, ("high", "最高")),
            "low": _first_float(data, ("low", "最低")),
            "previous_close": previous_close,
            "change": change,
            "pct_change": pct_change,
            "volume": _first_float(data, ("volume", "vol", "成交量")),
            "amount": _first_float(data, ("amount", "成交额")),
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
        TdxClient, to_jsonable = _load_eltdx()
        normalized_symbol = normalize_symbol(symbol)
        tdx_code = _tdx_code(normalized_symbol)
        try:
            with TdxClient(timeout=5) as client:
                series = client.get_kline(_tdx_period(period), tdx_code, count=limit)
        except Exception as exc:
            raise MarketDataError(
                f"eltdx kline request failed for {normalized_symbol}: {exc}. "
                "This usually means the Tongdaxin server connection was reset, timed out, "
                "or is temporarily unavailable."
            ) from exc
        data = to_jsonable(series) if to_jsonable else _jsonable_object(series)
        raw_bars = data.get("bars") if isinstance(data, dict) else data
        if not raw_bars:
            raise MarketDataError(f"eltdx kline not found for {normalized_symbol}")

        bars: list[dict[str, Any]] = []
        for row in raw_bars[-limit:]:
            item = _jsonable_object(row)
            bars.append(
                {
                    "symbol": normalized_symbol,
                    "source": self.name,
                    "period": "daily",
                    "trade_date": str(
                        _first_value(item, ("trade_date", "date", "time", "日期", "时间"))
                    )[:10],
                    "open": _first_required_float(item, ("open", "开盘"), "open"),
                    "high": _first_required_float(item, ("high", "最高"), "high"),
                    "low": _first_required_float(item, ("low", "最低"), "low"),
                    "close": _first_required_float(item, ("close", "收盘"), "close"),
                    "volume": _first_float(item, ("volume", "volume_lots", "成交量")),
                    "amount": _first_float(item, ("amount", "成交额")),
                    "payload": _jsonable(item),
                }
            )
        return bars


class TdxOfficialMarketDataProvider:
    name = "tdx-official"

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        normalized_symbol = normalize_symbol(symbol)
        payload = _tdx_official_post(
            "TdxShare.PBHQInfo",
            {
                "Head": {"Target": "0", "CharSet": "UTF8"},
                "Code": normalized_symbol,
                "Setcode": _tdx_official_setcode(normalized_symbol),
                "HasHQInfo": "1",
                "HasExtInfo": "1",
                "BspNum": "5",
                "HasProInfo": "0",
                "HasCalcInfo": "1",
                "HasCwInfo": "0",
                "HasStatInfo": "0",
            },
        )
        _raise_tdx_official_error(payload, normalized_symbol, "quote")

        base_info = _as_dict(payload.get("BaseInfo"))
        hq_info = _as_dict(payload.get("HQInfo"))
        calc_info = _as_dict(payload.get("CalcInfo"))
        if not hq_info:
            raise MarketDataError(
                f"tdx-official quote response did not include HQInfo for {normalized_symbol}"
            )

        price = _required_tdx_official_float(
            _first_value(hq_info, ("Now", "now", "Price", "price", "最新价", "现价")),
            "price",
        )
        previous_close = _first_float(
            hq_info,
            ("Close", "close", "PreClose", "pre_close", "previous_close", "昨收"),
        )
        change = _first_float(hq_info, ("ZDE", "Change", "change", "涨跌", "涨跌额"))
        if change is None and previous_close not in {None, 0}:
            change = round(price - float(previous_close), 4)
        pct_change = _first_float(
            calc_info,
            ("CAZAF", "PctChange", "pct_change", "change_pct", "涨幅", "涨跌幅"),
        )
        if pct_change is None:
            pct_change = _first_float(hq_info, ("ZDF", "PctChange", "涨幅", "涨跌幅"))
        if pct_change is None and previous_close not in {None, 0}:
            pct_change = round((price - float(previous_close)) / float(previous_close) * 100, 4)

        return {
            "symbol": normalized_symbol,
            "name": _first_text(base_info, ("Name", "name", "名称")),
            "source": self.name,
            "price": price,
            "open": _first_float(hq_info, ("Open", "open", "今开", "开盘")),
            "high": _first_float(hq_info, ("High", "high", "最高")),
            "low": _first_float(hq_info, ("Low", "low", "最低")),
            "previous_close": previous_close,
            "change": change,
            "pct_change": pct_change,
            "volume": _first_float(hq_info, ("Volume", "volume", "Vol", "成交量")),
            "amount": _first_float(hq_info, ("Amount", "amount", "成交额")),
            "turnover_rate": _first_float(hq_info, ("HSL", "hsl", "turnover_rate", "换手率")),
            "fetched_at": utc_now(),
            "raw": _jsonable(payload),
        }

    def fetch_kline(
        self,
        symbol: str,
        *,
        period: str = "daily",
        limit: int = 120,
    ) -> list[dict[str, Any]]:
        normalized_symbol = normalize_symbol(symbol)
        payload = _tdx_official_post(
            "TdxShare.PBFXT",
            {
                "Head": {"Target": 0, "CharSet": "UTF8"},
                "Code": normalized_symbol,
                "Setcode": int(_tdx_official_setcode(normalized_symbol)),
                "Period": int(_tdx_official_period(period)),
                "Startxh": 0,
                "WantNum": max(1, min(limit, 1000)),
                "TQFlag": 11,
                "MPData": 0,
                "HasAttachInfo": 1,
                "HasLtgb": 0,
                "ForRefresh": 0,
                "HasIpoPrice": 0,
            },
        )
        _raise_tdx_official_error(payload, normalized_symbol, "kline")

        raw_bars = payload.get("ListItem") or payload.get("listItem") or payload.get("items")
        if not isinstance(raw_bars, list) or not raw_bars:
            raise MarketDataError(
                f"tdx-official kline response did not include ListItem for {normalized_symbol}"
            )

        bars: list[dict[str, Any]] = []
        for row in raw_bars[-limit:]:
            item = _as_dict(row)
            values = item.get("Item") or item.get("item")
            values = values if isinstance(values, list) else None
            trade_date = _tdx_official_kline_value(
                item,
                values,
                ("TradeDate", "trade_date", "Date", "date", "Time", "time", "日期", "时间"),
                (0, 1),
            )
            bars.append(
                {
                    "symbol": normalized_symbol,
                    "source": self.name,
                    "period": period,
                    "trade_date": _tdx_official_date_text(trade_date),
                    "open": _required_tdx_official_float(
                        _tdx_official_kline_value(
                            item, values, ("Open", "open", "开盘"), (2, 1)
                        ),
                        "open",
                    ),
                    "high": _required_tdx_official_float(
                        _tdx_official_kline_value(
                            item, values, ("High", "high", "最高"), (3, 2)
                        ),
                        "high",
                    ),
                    "low": _required_tdx_official_float(
                        _tdx_official_kline_value(
                            item, values, ("Low", "low", "最低"), (4, 3)
                        ),
                        "low",
                    ),
                    "close": _required_tdx_official_float(
                        _tdx_official_kline_value(
                            item, values, ("Close", "close", "收盘"), (5, 4)
                        ),
                        "close",
                    ),
                    "volume": _safe_float(
                        _tdx_official_kline_value(
                            item, values, ("Volume", "volume", "Vol", "成交量"), (6, 5)
                        )
                    ),
                    "amount": _safe_float(
                        _tdx_official_kline_value(
                            item, values, ("Amount", "amount", "成交额"), (7, 6)
                        )
                    ),
                    "payload": _jsonable(item),
                }
            )

        if not bars:
            raise MarketDataError(f"tdx-official kline payload was empty for {normalized_symbol}")
        return bars


class EastmoneyMarketDataProvider:
    name = "eastmoney"

    def fetch_quote(self, symbol: str) -> dict[str, Any]:
        normalized_symbol = normalize_symbol(symbol)
        data = _eastmoney_json(
            "https://push2.eastmoney.com/api/qt/stock/get",
            {
                "secid": _eastmoney_secid(normalized_symbol),
                "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f59,f60,f169,f170",
            },
        ).get("data")
        if not data:
            raise MarketDataError(f"Eastmoney quote not found for {normalized_symbol}")

        price = _required_eastmoney_price(data.get("f43"), "最新价")
        previous_close = _eastmoney_price(data.get("f60"))
        change = _eastmoney_price(data.get("f169"))
        pct_change = _eastmoney_percent(data.get("f170"))

        return {
            "symbol": normalized_symbol,
            "name": data.get("f58"),
            "source": self.name,
            "price": price,
            "open": _eastmoney_price(data.get("f46")),
            "high": _eastmoney_price(data.get("f44")),
            "low": _eastmoney_price(data.get("f45")),
            "previous_close": previous_close,
            "change": change,
            "pct_change": pct_change,
            "volume": _safe_float(data.get("f47")),
            "amount": _safe_float(data.get("f48")),
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
            raise MarketDataError("Eastmoney provider currently supports daily kline only")

        normalized_symbol = normalize_symbol(symbol)
        data = _eastmoney_json(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            {
                "secid": _eastmoney_secid(normalized_symbol),
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": "101",
                "fqt": "1",
                "end": "20500101",
                "lmt": str(max(1, min(limit, 1000))),
            },
        ).get("data")
        if not data or not data.get("klines"):
            raise MarketDataError(f"Eastmoney kline not found for {normalized_symbol}")

        bars: list[dict[str, Any]] = []
        for raw in data["klines"][-limit:]:
            fields = raw.split(",")
            if len(fields) < 11:
                continue
            bars.append(
                {
                    "symbol": normalized_symbol,
                    "source": self.name,
                    "period": period,
                    "trade_date": fields[0],
                    "open": _required_float(fields[1], "开盘"),
                    "close": _required_float(fields[2], "收盘"),
                    "high": _required_float(fields[3], "最高"),
                    "low": _required_float(fields[4], "最低"),
                    "volume": _safe_float(fields[5]),
                    "amount": _safe_float(fields[6]),
                    "payload": {
                        "amplitude": _safe_float(fields[7]),
                        "pct_change": _safe_float(fields[8]),
                        "change": _safe_float(fields[9]),
                        "turnover_rate": _safe_float(fields[10]),
                        "name": data.get("name"),
                    },
                }
            )

        if not bars:
            raise MarketDataError(f"Eastmoney kline payload was empty for {normalized_symbol}")
        return bars


def get_market_data_provider(source: str | None) -> MarketDataProvider:
    source_name = (source or "tongdaxin").strip().lower()
    if source_name == "mock":
        return MockMarketDataProvider()
    if source_name in {"tdx", "tongdaxin", "eltdx"}:
        return EltdxMarketDataProvider()
    if source_name in {"tdx-official", "tdx_token", "tdx-token", "official", "openclaw"}:
        return TdxOfficialMarketDataProvider()
    if source_name in {"eastmoney", "real"}:
        return EastmoneyMarketDataProvider()
    if source_name == "akshare":
        return AkShareMarketDataProvider()
    raise MarketDataError(
        "Unsupported market data source "
        f"'{source_name}'. Available sources: tongdaxin, tdx-official, eastmoney, akshare, mock."
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


def _load_eltdx() -> tuple[Any, Any | None]:
    try:
        from eltdx import TdxClient  # type: ignore
    except ModuleNotFoundError as exc:
        raise MarketDataError(
            "eltdx is not installed. Install it with 'pip install \"eltdx[mcp]\"' "
            "and optionally run 'eltdx-mcp' for MCP tooling, or switch source=eastmoney."
        ) from exc
    try:
        from eltdx import to_jsonable  # type: ignore
    except (ImportError, ModuleNotFoundError):
        to_jsonable = None
    return TdxClient, to_jsonable


def _tdx_code(symbol: str) -> str:
    normalized_symbol = normalize_symbol(symbol)
    if normalized_symbol.startswith(("4", "8", "9")):
        return f"bj{normalized_symbol}"
    if normalized_symbol.startswith(("5", "6")):
        return f"sh{normalized_symbol}"
    return f"sz{normalized_symbol}"


def _tdx_period(period: str) -> str:
    period_name = (period or "daily").lower()
    if period_name in {"daily", "day", "d"}:
        return "day"
    if period_name in {"weekly", "week", "w"}:
        return "week"
    if period_name in {"monthly", "month", "m"}:
        return "month"
    return period_name


def _tdx_official_setcode(symbol: str) -> str:
    normalized_symbol = normalize_symbol(symbol)
    if normalized_symbol.startswith(("4", "8")):
        return "2"
    if normalized_symbol.startswith(("5", "6", "9")):
        return "1"
    return "0"


def _tdx_official_period(period: str) -> str:
    period_name = (period or "daily").lower()
    mapping = {
        "daily": "4",
        "day": "4",
        "d": "4",
        "weekly": "5",
        "week": "5",
        "w": "5",
        "monthly": "6",
        "month": "6",
        "m": "6",
        "60min": "3",
        "60m": "3",
        "hour": "3",
        "1min": "9",
        "1m": "9",
        "5min": "0",
        "5m": "0",
    }
    return mapping.get(period_name, period_name)


def _tdx_official_post(entry: str, body: dict[str, Any]) -> dict[str, Any]:
    token = get_tdx_api_key()
    if not token:
        raise MarketDataError(
            "TDX_API_KEY is not configured. Set it in your shell or local .env, "
            "or switch to source=eastmoney."
        )

    endpoint = get_tdx_api_endpoint().rstrip("?")
    url = f"{endpoint}?Entry={entry}"
    request = Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "token": token},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = _read_http_error(exc)
        if exc.code in {401, 403}:
            raise MarketDataError(
                f"tdx-official request was rejected with HTTP {exc.code}. "
                "Check that TDX_API_KEY is valid and has data-service permission."
                f"{detail}"
            ) from exc
        raise MarketDataError(
            f"tdx-official request failed with HTTP {exc.code}.{detail}"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise MarketDataError(
            f"tdx-official request failed: {exc}. "
            "Check network access to tdxhub.icfqs.com:7615 or switch source=eastmoney."
        ) from exc
    except json.JSONDecodeError as exc:
        raise MarketDataError(f"tdx-official returned invalid JSON: {exc}") from exc


def _read_http_error(error: HTTPError) -> str:
    try:
        body = error.read().decode("utf-8", errors="replace").strip()
    except Exception:
        body = ""
    return f" Response: {body[:500]}" if body else ""


def _raise_tdx_official_error(payload: dict[str, Any], symbol: str, data_type: str) -> None:
    error = _first_value(
        payload,
        (
            "error",
            "Error",
            "errmsg",
            "ErrMsg",
            "message",
            "Message",
            "ErrorInfo",
            "ErrInfo",
        ),
    )
    if error:
        raise MarketDataError(
            f"tdx-official {data_type} request failed for {symbol}: {error}"
        )


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _tdx_official_kline_value(
    item: dict[str, Any],
    values: list[Any] | None,
    keys: tuple[str, ...],
    indexes: tuple[int, ...],
) -> Any:
    value = _first_value(item, keys)
    if value not in {None, ""}:
        return value
    if not values:
        return None
    for index in indexes:
        if index < len(values) and values[index] not in {None, ""}:
            return values[index]
    return None


def _tdx_official_date_text(value: Any) -> str:
    if value is None:
        raise MarketDataError("tdx-official returned empty K-line trade date")
    text = str(value).strip()
    if len(text) >= 8 and text[:8].isdigit():
        compact = text[:8]
        return f"{compact[:4]}-{compact[4:6]}-{compact[6:8]}"
    return text[:10]


def _required_tdx_official_float(value: Any, field_name: str) -> float:
    parsed = _safe_float(value)
    if parsed is None:
        raise MarketDataError(f"tdx-official returned empty numeric field: {field_name}")
    return parsed


def _eastmoney_secid(symbol: str) -> str:
    normalized_symbol = normalize_symbol(symbol)
    if normalized_symbol.startswith(("5", "6", "9")):
        market_id = "1"
    else:
        market_id = "0"
    return f"{market_id}.{normalized_symbol}"


def _eastmoney_json(base_url: str, params: dict[str, str]) -> dict[str, Any]:
    url = f"{base_url}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        },
    )
    last_error: Exception | None = None
    for _ in range(2):
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = exc
    else:
        raise MarketDataError(f"Eastmoney request failed: {last_error}") from last_error
    if payload.get("rc") not in {0, None}:
        raise MarketDataError(f"Eastmoney returned error code {payload.get('rc')}")
    return payload


def _eastmoney_price(value: Any) -> float | None:
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return round(parsed / 100, 4)


def _required_eastmoney_price(value: Any, field_name: str) -> float:
    parsed = _eastmoney_price(value)
    if parsed is None:
        raise MarketDataError(f"Eastmoney returned empty numeric field: {field_name}")
    return parsed


def _eastmoney_percent(value: Any) -> float | None:
    parsed = _safe_float(value)
    if parsed is None:
        return None
    return round(parsed / 100, 4)


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


def _jsonable_object(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return value


def _first_value(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data and data[key] not in {None, ""}:
            return data[key]
    return None


def _first_float(data: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    return _safe_float(_first_value(data, keys))


def _first_required_float(
    data: dict[str, Any],
    keys: tuple[str, ...],
    field_name: str,
) -> float:
    parsed = _first_float(data, keys)
    if parsed is None:
        raise MarketDataError(f"eltdx returned empty numeric field: {field_name}")
    return parsed


def _first_text(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    value = _first_value(data, keys)
    return None if value is None else str(value)


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
