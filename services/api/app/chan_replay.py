"""Prefix-only replay, with immutable first observations and append-only state events."""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from .chan_baseline import MODEL_VERSION, RULE_CONFIG, analyze_frame, baseline_fingerprint, visible_daily_prefix
from .chan_dataset import canonical_symbol, digest
from .market_time import finite_number, price_values


def _candidate(analysis: dict, at: str) -> dict | None:
    signal = analysis["signal"]
    direction = {"suspected_third_buy": "up", "suspected_third_sell": "down"}.get(signal["type"])
    if not direction or signal.get("status") != "candidate":
        return None
    center = analysis.get("latest_center")
    stable = [s for s in analysis.get("chart", {}).get("strokes", []) if s.get("confirmed")]
    if not center:
        raise ValueError("invalid_candidate_evidence")
    start = center["stroke_start"]
    group = stable[start:start + 3]
    if len(group) != 3 or any(not s.get("confirmed_at") or s["confirmed_at"][:10] > at[:10]
                              or s["end_date"] > at[:10] for s in stable):
        raise ValueError("invalid_candidate_evidence")
    anchor = [{key: s[key] for key in ("direction", "start_date", "end_date")} for s in group]
    boundary = finite_number(center["upper" if direction == "up" else "lower"])
    if boundary is None or boundary <= 0:
        raise ValueError("invalid_candidate_evidence")
    return {"direction": direction, "anchor": anchor, "frozen_boundary": boundary,
            "pivot_at": stable[-1]["end_date"], "evidence": deepcopy(signal)}


def _visible_issues(issues, day):
    # Truncation describes acquisition depth, not corruption in the observed prefix.
    return [i for i in issues if i["code"] != "truncated" and
            (i["scope"] == "series" or i["bar_key"][:10] <= day)]


def _prefix_hash(prefix, issues, fingerprint):
    material = [{"trade_date": b["trade_date"], **{
        k: finite_number(b.get(k)) for k in ("open", "high", "low", "close", "volume", "amount")}}
        for b in prefix]
    return digest({"bars": material, "quality_issues": issues, "baseline": fingerprint, "config": RULE_CONFIG})


def replay_symbol(*, symbol: str, bars: list[dict], as_of: str, quality_issues: list[dict],
                  analyzer: Callable[..., dict] | None = None) -> dict:
    fingerprint = baseline_fingerprint()
    symbol = canonical_symbol(symbol)
    visible = visible_daily_prefix(bars, as_of=as_of)
    analyze = analyzer or analyze_frame
    result = {"frames": [], "observations": [], "events": [], "issues": []}
    if len(visible) < RULE_CONFIG["minimum_bars"]:
        result["issues"].append("insufficient_bars")
        return result
    states, latest, armed = {}, {}, set()

    def event(observation, kind, at, data_hash, *, details=None, transition=True):
        state = states[observation["observation_id"]]
        if transition and state["status"] == kind:
            return
        result["events"].append({
            "event_id": digest({"observation_id": observation["observation_id"], "at": at, "type": kind}),
            "observation_id": observation["observation_id"], "symbol": symbol, "model_version": MODEL_VERSION,
            "type": kind, "at": at, "data_hash": data_hash, "details": details or {},
        })
        if transition:
            state["status"] = kind
            if kind != "data_unavailable":
                state["last_valid_status"] = kind

    for count in range(RULE_CONFIG["minimum_bars"], len(visible) + 1):
        prefix = visible[:count]
        day = prefix[-1]["trade_date"]
        at = day + "T15:00:00+08:00"
        external = _visible_issues(quality_issues, day)
        data_hash = _prefix_hash(prefix, external, fingerprint)
        analysis = analyze(symbol=symbol, bars=deepcopy(prefix), as_of=at)
        quality = deepcopy(analysis["data_quality"])
        quality["external_issues"] = [i["code"] for i in external]
        usable = quality["status"] == "complete" and not external
        candidate = None
        if usable:
            try:
                price_values(prefix[-1])
                candidate = _candidate(analysis, at)
            except (ValueError, TypeError, KeyError):
                usable = False
                quality["external_issues"].append("invalid_candidate_evidence")
        result["frames"].append({"symbol": symbol, "at": at, "bar_count": count, "data_hash": data_hash,
                                 "signal": deepcopy(analysis["signal"]), "data_quality": quality,
                                 "eligible": usable, "latest_center": deepcopy(analysis.get("latest_center")),
                                 "structure_key": analysis.get("structure_key")})
        if not usable:
            for observation in result["observations"]:
                if states[observation["observation_id"]]["last_valid_status"] != "invalidated":
                    event(observation, "data_unavailable", at, data_hash)
            continue
        key = digest({"anchor": candidate["anchor"], "direction": candidate["direction"]}) if candidate else None
        for observation in result["observations"]:
            state = states[observation["observation_id"]]
            boundary = observation["frozen_boundary"]
            upward = observation["direction"] == "up"
            if state["key"] != key:
                armed.add(state["key"])
            if state["last_valid_status"] == "invalidated":
                continue
            price = prefix[-1]
            invalidated = price["close"] <= boundary if upward else price["close"] >= boundary
            if invalidated:
                event(observation, "invalidated", at, data_hash, details={"close": price["close"], "boundary": boundary})
                continue
            touched = price["low"] <= boundary if upward else price["high"] >= boundary
            if touched and not state["touched"]:
                event(observation, "boundary_touch", at, data_hash, details={"boundary": boundary}, transition=False)
            state["touched"] = touched
            is_current = latest.get(state["key"]) == observation["observation_id"]
            if state["key"] != key or not is_current or state["last_valid_status"] == "withdrawn":
                event(observation, "withdrawn", at, data_hash)
            elif state["last_valid_status"] == "candidate":
                event(observation, "candidate", at, data_hash)
        if candidate:
            prior_id = latest.get(key)
            prior = states.get(prior_id)
            new_episode = prior is None or prior["last_valid_status"] == "withdrawn" or (
                prior["last_valid_status"] == "invalidated" and key in armed)
            if new_episode:
                # A reappearance must also satisfy the first frozen boundary at its observation close.
                boundary, upward = candidate["frozen_boundary"], candidate["direction"] == "up"
                if (prefix[-1]["close"] <= boundary if upward else prefix[-1]["close"] >= boundary):
                    continue
                identity = {"model": MODEL_VERSION, "symbol": symbol, "anchor": candidate["anchor"],
                            "direction": candidate["direction"], "first_seen_at": at}
                observation = {**candidate, "observation_id": digest(identity), "symbol": symbol,
                               "model_version": MODEL_VERSION, "config": dict(RULE_CONFIG), "status": "candidate",
                               "first_seen_at": at, "confirmed_at": None, "data_hash": data_hash,
                               "invalidation_mode": "close", "overlapping_episode": bool(result["observations"])}
                result["observations"].append(observation)
                latest[key] = observation["observation_id"]
                states[observation["observation_id"]] = {"key": key, "status": None,
                    "last_valid_status": None, "touched": False}
                armed.discard(key)
                event(observation, "candidate", at, data_hash)
    return result
