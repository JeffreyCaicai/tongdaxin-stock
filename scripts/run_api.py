from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api.app.backtest import run_ma_volume_backtest
from services.api.app.config import get_api_host, get_api_port
from services.api.app.database import connect, init_db
from services.api.app.indicators import calculate_indicator_snapshot
from services.api.app.market_data import MarketDataError, get_market_data_provider
from services.api.app.repository import (
    create_backtest,
    create_holding,
    create_market_fetch_log,
    create_market_snapshot,
    create_signal,
    list_holdings,
    list_market_fetch_logs,
    list_signals,
    normalize_symbol,
    upsert_market_klines,
    utc_now,
)
from services.api.app.reports import generate_daily_review
from services.api.app.signal_engine import evaluate_holding_signal


def main() -> None:
    init_db()
    host = get_api_host()
    port = get_api_port()
    try:
        import uvicorn  # type: ignore

        print(f"Starting FastAPI service on http://{host}:{port}")
        uvicorn.run("services.api.app.main:app", host=host, port=port, reload=False)
    except ModuleNotFoundError:
        print("FastAPI/uvicorn not installed; starting dependency-free fallback API.")
        print(f"Open http://{host}:{port}")
        server = ThreadingHTTPServer((host, port), FallbackHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping API server.")
        finally:
            server.server_close()


class FallbackHandler(BaseHTTPRequestHandler):
    server_version = "TongdaxinStockFallback/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        path = parsed.path.rstrip("/") or "/"

        try:
            if path == "/":
                self._send_html(_index_html())
            elif path == "/health":
                self._send_json({"status": "ok", "mode": "fallback"})
            elif path == "/holdings":
                with connect() as db:
                    self._send_json(list_holdings(db))
            elif path == "/signals":
                with connect() as db:
                    self._send_json([_signal_row_to_output(row) for row in list_signals(db)])
            elif path == "/market/fetch-logs":
                with connect() as db:
                    self._send_json(list_market_fetch_logs(db))
            elif path == "/reports/daily-review":
                with connect() as db:
                    signals = [_signal_row_to_output(row) for row in list_signals(db)]
                    report = generate_daily_review(
                        holdings=list_holdings(db),
                        signals=signals,
                        fetch_logs=list_market_fetch_logs(db),
                    )
                    self._send_json(report)
            elif path.startswith("/market/quote/"):
                symbol = path.rsplit("/", 1)[-1]
                source = _query_value(query, "source", "mock")
                with connect() as db:
                    self._send_json(_fetch_quote(db, symbol=symbol, source=source))
            elif path.startswith("/market/kline/"):
                symbol = path.rsplit("/", 1)[-1]
                source = _query_value(query, "source", "mock")
                limit = int(_query_value(query, "limit", "120"))
                with connect() as db:
                    self._send_json(_fetch_kline(db, symbol=symbol, source=source, limit=limit))
            else:
                self._send_json({"detail": "Not found"}, status=404)
        except (ValueError, MarketDataError) as exc:
            self._send_json({"detail": str(exc)}, status=400)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        payload = self._read_json()

        try:
            if path == "/holdings":
                with connect() as db:
                    self._send_json(create_holding(db, payload), status=201)
            elif path == "/workbench/actions/from-market":
                with connect() as db:
                    self._send_json(_workbench_actions_from_market(db, payload))
            elif path.startswith("/backtests/"):
                symbol = path.rsplit("/", 1)[-1]
                with connect() as db:
                    self._send_json(_run_backtest(db, symbol=symbol, payload=payload))
            else:
                self._send_json({"detail": "Not found"}, status=404)
        except (KeyError, ValueError, MarketDataError) as exc:
            self._send_json({"detail": str(exc)}, status=400)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        body = self.rfile.read(length).decode("utf-8")
        return json.loads(body)

    def _send_json(self, payload: object, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_html(self, html: str, status: int = 200) -> None:
        encoded = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def _fetch_quote(db, *, symbol: str, source: str) -> dict:
    provider = get_market_data_provider(source)
    quote = provider.fetch_quote(symbol)
    snapshot = create_market_snapshot(
        db,
        symbol=symbol,
        source=provider.name,
        payload=quote,
        fetched_at=quote.get("fetched_at"),
    )
    create_market_fetch_log(
        db,
        symbol=symbol,
        source=provider.name,
        data_type="quote",
        status="success",
        fetched_at=snapshot["fetched_at"],
    )
    return {"snapshot_id": snapshot["id"], **quote}


def _fetch_kline(db, *, symbol: str, source: str, limit: int) -> dict:
    provider = get_market_data_provider(source)
    bars = provider.fetch_kline(symbol, limit=limit)
    cached_bars = upsert_market_klines(
        db,
        symbol=symbol,
        source=provider.name,
        period="daily",
        bars=bars,
    )
    create_market_fetch_log(
        db,
        symbol=symbol,
        source=provider.name,
        data_type="kline",
        status="success",
        message=f"Fetched {len(bars)} daily bars.",
    )
    return {
        "symbol": normalize_symbol(symbol),
        "source": provider.name,
        "period": "daily",
        "count": len(cached_bars),
        "bars": list(reversed(cached_bars)),
    }


def _workbench_actions_from_market(db, payload: dict) -> dict:
    source = payload.get("source", "mock")
    persist = bool(payload.get("persist", True))
    include_technical = bool(payload.get("include_technical", True))
    kline_limit = int(payload.get("kline_limit", 120))
    signals: list[dict] = []
    missing_prices: list[str] = []
    holdings = list_holdings(db)

    for holding in holdings:
        symbol = normalize_symbol(holding["symbol"])
        try:
            quote = _fetch_quote(db, symbol=symbol, source=source)
            indicators = None
            if include_technical:
                kline = _fetch_kline(db, symbol=symbol, source=source, limit=kline_limit)
                indicators = calculate_indicator_snapshot(kline["bars"])
            signal = evaluate_holding_signal(
                holding,
                current_price=quote["price"],
                source_snapshot_id=quote["snapshot_id"],
                indicators=indicators,
            )
            signals.append(_save_signal(db, signal) if persist else signal)
        except MarketDataError:
            missing_prices.append(symbol)

    return {
        "generated_at": utc_now(),
        "total_holdings": len(holdings),
        "generated_signals": len(signals),
        "missing_prices": missing_prices,
        "signals": signals,
    }


def _run_backtest(db, *, symbol: str, payload: dict) -> dict:
    source = payload.get("source", "mock")
    limit = int(payload.get("limit", 240))
    initial_equity = float(payload.get("initial_equity", 100000.0))
    stop_loss_pct = float(payload.get("stop_loss_pct", 6.0))
    take_profit_pct = float(payload.get("take_profit_pct", 12.0))
    persist = bool(payload.get("persist", True))
    kline = _fetch_kline(db, symbol=symbol, source=source, limit=limit)
    result = run_ma_volume_backtest(
        symbol=symbol,
        bars=kline["bars"],
        initial_equity=initial_equity,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
    )
    config = {
        "source": source,
        "period": "daily",
        "limit": limit,
        "initial_equity": initial_equity,
        "stop_loss_pct": stop_loss_pct,
        "take_profit_pct": take_profit_pct,
    }
    if persist:
        row = create_backtest(
            db,
            symbol=symbol,
            source=kline["source"],
            strategy_name=result["strategy_name"],
            config=config,
            result=result,
            created_at=result["generated_at"],
        )
        return {
            "id": row["id"],
            "symbol": row["symbol"],
            "source": row["source"],
            "strategy_name": row["strategy_name"],
            "created_at": row["created_at"],
            "config": json.loads(row["config_json"]),
            "result": json.loads(row["result_json"]),
        }
    return {
        "id": None,
        "symbol": normalize_symbol(symbol),
        "source": kline["source"],
        "strategy_name": result["strategy_name"],
        "created_at": result["generated_at"],
        "config": config,
        "result": result,
    }


def _save_signal(db, signal: dict) -> dict:
    row = create_signal(
        db,
        symbol=signal["symbol"],
        signal_type=signal["signal_type"],
        action=signal["action"],
        strength=signal["strength"],
        price=signal["price"],
        reason_json={
            "risk_level": signal["risk_level"],
            "reasons": signal["reasons"],
            "next_check": signal["next_check"],
            "extra": signal["extra"],
        },
        source_snapshot_id=signal["source_snapshot_id"],
    )
    return _signal_row_to_output(row)


def _signal_row_to_output(row: dict) -> dict:
    reason_json = json.loads(row["reason_json"])
    return {
        "id": row["id"],
        "symbol": row["symbol"],
        "signal_type": row["signal_type"],
        "action": row["action"],
        "strength": row["strength"],
        "price": row["price"],
        "risk_level": reason_json["risk_level"],
        "reasons": reason_json["reasons"],
        "next_check": reason_json["next_check"],
        "source_snapshot_id": row["source_snapshot_id"],
        "created_at": row["created_at"],
        "extra": reason_json.get("extra", {}),
    }


def _query_value(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    return values[0] if values else default


def _index_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Tongdaxin Stock Local API</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.5; }
    code { background: #f2f2f2; padding: 2px 5px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Tongdaxin Stock Local API</h1>
  <p>Fallback API is running without external Python dependencies.</p>
  <ul>
    <li><code>GET /health</code></li>
    <li><code>GET /holdings</code>, <code>POST /holdings</code></li>
    <li><code>GET /market/quote/600519</code></li>
    <li><code>GET /market/kline/600519?limit=120</code></li>
    <li><code>POST /workbench/actions/from-market</code></li>
    <li><code>GET /reports/daily-review</code></li>
    <li><code>POST /backtests/600519</code></li>
  </ul>
</body>
</html>"""


if __name__ == "__main__":
    main()
