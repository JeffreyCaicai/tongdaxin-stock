"""Explicit acquisition and offline Chan research commands; never starts the application."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api.app.chan_baseline import MODEL_VERSION, RULE_CONFIG, analyze_frame, baseline_fingerprint
from services.api.app.chan_dataset import (
    canonical_json, canonical_symbol, load_dataset, read_json, save_dataset, write_bytes_exclusive, write_json_exclusive,
)
from services.api.app.chan_outcomes import evaluate_observations
from services.api.app.chan_quality import dataset_quality
from services.api.app.chan_replay import replay_symbol
from services.api.app.chan_report import render_report
from services.api.app.market_time import local_timestamp


class ResearchParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("invalid_arguments")


def _parser():
    parser = ResearchParser(description="Bounded capture and offline daily Chan validation (not trading).")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="Capture explicit securities using the official provider")
    capture.add_argument("--symbols", nargs="+", required=True)
    capture.add_argument("--periods", nargs="+", default=["daily"])
    capture.add_argument("--as-of", required=True)
    capture.add_argument("--root", type=Path, default=PROJECT_ROOT / "data/cache/chan_validation")
    capture.add_argument("--calendar", type=Path)
    capture.add_argument("--page-size", type=int, default=1000)
    capture.add_argument("--max-pages", type=int, default=1)
    for command in ("replay", "frame", "report"):
        sub = commands.add_parser(command, help="Read a fixed dataset without network or database access")
        sub.add_argument("--dataset", type=Path, required=True)
        sub.add_argument("--as-of", required=True)
        sub.add_argument("--output", type=Path, required=True)
        if command == "frame":
            sub.add_argument("--symbol", required=True)
        if command == "report":
            sub.add_argument("--language", choices=("zh", "en"), default="zh")
    return parser


def _manifest(dataset, as_of):
    return {"dataset_id": dataset["dataset_id"], "model_version": MODEL_VERSION,
            "baseline_fingerprint": baseline_fingerprint(), "config": dict(RULE_CONFIG), "as_of": as_of,
            "input": {key: dataset[key] for key in ("source", "selection", "price_basis", "calendar", "collection")}}


def _replay(dataset, as_of):
    report = {"schema_version": "chan_replay_v1", **_manifest(dataset, as_of),
              "frames": [], "observations": [], "events": [], "issues": []}
    report["data_quality"] = dataset_quality(dataset, as_of)
    for quality in report["data_quality"]["items"]:
        symbol = quality["symbol"]
        daily = dataset["series"][symbol].get("daily", {"bars": [], "issues": []})
        result = replay_symbol(symbol=symbol, bars=daily["bars"], as_of=as_of, quality_issues=quality["issues"])
        for key in ("frames", "observations", "events"):
            report[key].extend(result[key])
        report["issues"].extend({"symbol": symbol, "code": issue} for issue in result["issues"])
    report["price_observations"] = evaluate_observations(observations=report["observations"], dataset=dataset, as_of=as_of)
    report["dataset_issues"] = dataset["issues"]
    return report


def _frame(dataset, symbol, as_of):
    symbol = canonical_symbol(symbol)
    if symbol not in dataset["selection"]["symbols"]:
        raise ValueError("symbol_not_selected")
    daily = dataset["series"][symbol].get("daily", {"bars": [], "issues": []})
    quality = dataset_quality(dataset, as_of, [symbol])
    visible_issues = [i for i in quality["items"][0]["issues"] if i["code"] != "truncated"]
    analysis = analyze_frame(symbol=symbol, bars=daily["bars"], as_of=as_of)
    return {"schema_version": "chan_frame_v1", **_manifest(dataset, as_of), "analysis": analysis,
            "external_issues": visible_issues, "data_quality": quality,
            "eligible_for_observation": not visible_issues and analysis["data_quality"]["status"] == "complete"}


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        as_of = local_timestamp(args.as_of).isoformat()
        if args.command == "capture":
            from services.api.app.chan_capture import capture_dataset
            dataset = capture_dataset(symbols=args.symbols, periods=args.periods, as_of=as_of,
                                      page_size=args.page_size, max_pages=args.max_pages,
                                      calendar=read_json(args.calendar) if args.calendar else None)
            path = save_dataset(dataset, args.root)
            print(canonical_json({"dataset_id": dataset["dataset_id"], "path": str(path),
                                  "status": dataset["collection"]["status"], "issues": dataset["issues"]}).decode())
            return 1 if dataset["collection"]["status"] == "partial" else 0
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError("output_exists")
        dataset = load_dataset(args.dataset)
        report = _frame(dataset, args.symbol, as_of) if args.command == "frame" else _replay(dataset, as_of)
        if args.command == "report":
            write_bytes_exclusive(args.output, render_report(dataset, report, language=args.language).encode("utf-8"))
        else:
            write_json_exclusive(args.output, report)
        print(canonical_json({"status": "written", "path": str(args.output), "dataset_id": dataset["dataset_id"]}).decode())
        return 0
    except SystemExit as exc:
        return int(exc.code)
    except FileExistsError:
        print("error: output_exists; choose a new output path", file=sys.stderr)
        return 2
    except (ValueError, TypeError, KeyError):
        print("error: invalid_arguments_or_dataset; check schema, hash, timestamps and --help", file=sys.stderr)
        return 2
    except OSError:
        print("error: file_io_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
