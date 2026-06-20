from __future__ import annotations

import json
import sys
from urllib.request import Request, urlopen


BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"


def main() -> None:
    health = get_json("/health")
    holding = post_json(
        "/holdings",
        {
            "symbol": "600519",
            "name": "Offline Smoke 600519",
            "market": "SH",
            "quantity": 100,
            "cost_price": 95,
            "stop_loss": 88,
            "take_profit": 120,
            "max_loss_pct": 8,
            "initial_thesis": "Offline mock smoke-test holding.",
        },
    )
    actions = post_json(
        "/workbench/actions/from-market",
        {"source": "mock", "persist": True, "include_technical": True},
    )
    review = get_json("/reports/daily-review")
    backtest = post_json(
        "/backtests/600519",
        {"source": "mock", "limit": 160, "persist": False},
    )

    print(
        json.dumps(
            {
                "health": health,
                "created_holding_id": holding.get("id"),
                "generated_signals": actions.get("generated_signals"),
                "daily_review_type": review.get("report_type"),
                "backtest_trades": backtest["result"]["metrics"]["total_trades"],
                "backtest_win_rate": backtest["result"]["metrics"]["win_rate"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()
