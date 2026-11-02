"""Monthly revenue forecast: linear trend + month-of-year effects (ordinary least squares).

Why this model: it is explainable (one slope, twelve seasonal offsets), needs no extra libraries and is
honest about a short history. It is compared against a seasonal-naive baseline (same month last year)
on a held-out final stretch of months, using MAE and RMSE.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

MIN_MONTHS = 24
Z_95 = 1.96


@dataclass
class ForecastResult:
    history: pd.DataFrame      # month, revenue
    forecast: pd.DataFrame     # month, forecast, lower, upper
    backtest: pd.DataFrame     # month, actual, model, naive  (held-out months)
    metrics: dict              # mae, rmse, naive_mae, naive_rmse, test_months, beats_naive
    sigma: float
    trend_per_month: float


def _design(t: np.ndarray, months: np.ndarray) -> np.ndarray:
    """Columns: intercept, time index, and dummies for calendar months 2..12 (January is the base)."""
    cols = [np.ones_like(t, dtype=float), t.astype(float)]
    cols += [(months == m).astype(float) for m in range(2, 13)]
    return np.column_stack(cols)


def _fit(t, months, y):
    X = _design(t, months)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def _predict(beta, t, months):
    return _design(np.asarray(t), np.asarray(months)) @ beta


def forecast_revenue(monthly: pd.DataFrame, horizon: int = 6, test_months: int = 6) -> ForecastResult:
    """`monthly` needs columns month (month-start dates) and revenue. Raises ValueError if history is too short."""
    if not 1 <= horizon <= 12:
        raise ValueError("horizon must be between 1 and 12 months")
    s = monthly[["month", "revenue"]].dropna().copy()
    s["month"] = pd.to_datetime(s["month"])
    s = s.sort_values("month").reset_index(drop=True)
    n = len(s)
    if n < MIN_MONTHS:
        raise ValueError(f"Forecasting needs at least {MIN_MONTHS} months of history; the current selection has {n}.")

    t = np.arange(n)
    mo = s["month"].dt.month.to_numpy()
    y = s["revenue"].to_numpy(dtype=float)

    # Back-test: fit on everything except the last `test_months`, predict them.
    n_train = n - test_months
    beta_bt = _fit(t[:n_train], mo[:n_train], y[:n_train])
    pred_bt = np.maximum(_predict(beta_bt, t[n_train:], mo[n_train:]), 0)
    actual = y[n_train:]
    naive = y[n_train - 12:n - 12] if n_train >= 12 else np.full(test_months, np.nan)
    backtest = pd.DataFrame({"month": s["month"].iloc[n_train:].to_numpy(), "actual": actual, "model": pred_bt, "naive": naive})

    mae = float(np.mean(np.abs(actual - pred_bt)))
    rmse = float(np.sqrt(np.mean((actual - pred_bt) ** 2)))
    naive_mae = float(np.mean(np.abs(actual - naive))) if not np.isnan(naive).any() else None
    naive_rmse = float(np.sqrt(np.mean((actual - naive) ** 2))) if not np.isnan(naive).any() else None

    # Final model on all data; interval from in-sample residual spread (approximate).
    beta = _fit(t, mo, y)
    resid = y - _predict(beta, t, mo)
    dof = max(n - len(beta), 1)
    sigma = float(np.sqrt(np.sum(resid ** 2) / dof))
    f_t = np.arange(n, n + horizon)
    f_months = pd.date_range(s["month"].iloc[-1] + pd.offsets.MonthBegin(1), periods=horizon, freq="MS")
    f_pred = _predict(beta, f_t, f_months.month.to_numpy())
    forecast = pd.DataFrame({
        "month": f_months, "forecast": np.maximum(f_pred, 0),
        "lower": np.maximum(f_pred - Z_95 * sigma, 0), "upper": np.maximum(f_pred + Z_95 * sigma, 0),
    })
    return ForecastResult(
        history=s, forecast=forecast, backtest=backtest, sigma=sigma, trend_per_month=float(beta[1]),
        metrics={"mae": mae, "rmse": rmse, "naive_mae": naive_mae, "naive_rmse": naive_rmse,
                 "test_months": test_months, "beats_naive": (naive_mae is not None and mae < naive_mae)},
    )


LIMITATIONS = (
    "Based on a short history (about four years), so seasonality is estimated from only a few observations per month. "
    "The shaded band is an approximate 95% range from past model error; it does not include uncertainty in the "
    "trend or future shocks. Treat the forecast as a planning baseline, not a prediction you can rely on."
)
