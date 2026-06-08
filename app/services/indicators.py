from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from app.models import MarketBar


BarLike = MarketBar | Mapping[str, Any] | Any


def _bar_value(bar: BarLike, field: str, default: Any = None) -> Any:
    if isinstance(bar, Mapping):
        return bar.get(field, default)
    return getattr(bar, field, default)


def bars_to_frame(bars: list[BarLike]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for bar in bars:
        rows.append(
            {
                "date": str(_bar_value(bar, "date", "")),
                "open": _bar_value(bar, "open", 0.0),
                "high": _bar_value(bar, "high", 0.0),
                "low": _bar_value(bar, "low", 0.0),
                "close": _bar_value(bar, "close", 0.0),
                "volume": _bar_value(bar, "volume", 0),
            }
        )

    frame = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    if frame.empty:
        return frame

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["date", "open", "high", "low", "close"]).sort_values("date")
    frame["volume"] = frame["volume"].fillna(0.0)
    return frame.reset_index(drop=True)


def _series_to_list(series: pd.Series, digits: int = 4) -> list[float | None]:
    result: list[float | None] = []
    for value in series.tolist():
        if pd.isna(value):
            result.append(None)
        else:
            result.append(round(float(value), digits))
    return result


def compute_ma(bars: list[BarLike], windows: tuple[int, ...] = (5, 10, 20, 60)) -> dict[str, list[float | None]]:
    frame = bars_to_frame(bars)
    if frame.empty:
        return {f"ma{window}": [] for window in windows}

    close = frame["close"]
    result: dict[str, list[float | None]] = {}
    for window in windows:
        result[f"ma{window}"] = _series_to_list(close.rolling(window=window, min_periods=1).mean())
    return result


def compute_macd(
    bars: list[BarLike], short: int = 12, long: int = 26, signal: int = 9
) -> dict[str, list[float | None]]:
    frame = bars_to_frame(bars)
    if frame.empty:
        return {"dif": [], "dea": [], "hist": []}

    close = frame["close"]
    ema_short = close.ewm(span=short, adjust=False).mean()
    ema_long = close.ewm(span=long, adjust=False).mean()
    dif = ema_short - ema_long
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = (dif - dea) * 2
    return {
        "dif": _series_to_list(dif),
        "dea": _series_to_list(dea),
        "hist": _series_to_list(hist),
    }


def compute_kdj(bars: list[BarLike], period: int = 9) -> dict[str, list[float | None]]:
    frame = bars_to_frame(bars)
    if frame.empty:
        return {"k": [], "d": [], "j": []}

    low_n = frame["low"].rolling(window=period, min_periods=1).min()
    high_n = frame["high"].rolling(window=period, min_periods=1).max()
    denominator = (high_n - low_n).replace(0, pd.NA)
    rsv = ((frame["close"] - low_n) / denominator * 100).fillna(50.0)

    k_values: list[float] = []
    d_values: list[float] = []
    k_prev = 50.0
    d_prev = 50.0
    for rsv_value in rsv.tolist():
        current_rsv = float(rsv_value)
        k_now = (2.0 / 3.0) * k_prev + (1.0 / 3.0) * current_rsv
        d_now = (2.0 / 3.0) * d_prev + (1.0 / 3.0) * k_now
        k_values.append(k_now)
        d_values.append(d_now)
        k_prev = k_now
        d_prev = d_now

    k_series = pd.Series(k_values)
    d_series = pd.Series(d_values)
    j_series = 3 * k_series - 2 * d_series
    return {
        "k": _series_to_list(k_series),
        "d": _series_to_list(d_series),
        "j": _series_to_list(j_series),
    }


def compute_boll(
    bars: list[BarLike], window: int = 20, std_factor: float = 2.0
) -> dict[str, list[float | None]]:
    frame = bars_to_frame(bars)
    if frame.empty:
        return {"upper": [], "mid": [], "lower": []}

    close = frame["close"]
    mid = close.rolling(window=window, min_periods=1).mean()
    std = close.rolling(window=window, min_periods=1).std(ddof=0).fillna(0.0)
    upper = mid + std_factor * std
    lower = mid - std_factor * std
    return {
        "upper": _series_to_list(upper),
        "mid": _series_to_list(mid),
        "lower": _series_to_list(lower),
    }


def compute_rsi(bars: list[BarLike], period: int = 14) -> list[float | None]:
    frame = bars_to_frame(bars)
    if frame.empty:
        return []

    close = frame["close"]
    delta = close.diff().fillna(0.0)
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - 100 / (1 + rs)
    rsi = rsi.fillna(100.0)
    return _series_to_list(rsi)


def build_indicators(bars: list[BarLike]) -> dict[str, Any]:
    return {
        "ma": compute_ma(bars, windows=(5, 10, 20, 60)),
        "macd": compute_macd(bars),
        "kdj": compute_kdj(bars),
        "boll": compute_boll(bars),
        "rsi": compute_rsi(bars),
    }
