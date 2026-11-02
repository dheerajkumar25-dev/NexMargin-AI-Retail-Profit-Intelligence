import numpy as np
import pandas as pd
import pytest

from nexmargin.forecasting import MIN_MONTHS, forecast_revenue


def _series(n=40, trend=10.0, amp=100.0, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    months = pd.date_range("2014-01-01", periods=n, freq="MS")
    t = np.arange(n)
    y = 1000 + trend * t + amp * np.sin(2 * np.pi * months.month / 12) + rng.normal(0, noise, n)
    return pd.DataFrame({"month": months, "revenue": y})


def test_recovers_trend_and_seasonality_on_clean_series():
    s = _series()
    r = forecast_revenue(s, horizon=6)
    truth = 1000 + 10 * np.arange(40, 46) + 100 * np.sin(2 * np.pi * r.forecast["month"].dt.month / 12)
    assert np.allclose(r.forecast["forecast"], truth, rtol=0.01)
    assert r.trend_per_month == pytest.approx(10, rel=0.05)
    assert r.metrics["mae"] < 5 and r.metrics["rmse"] < 5
    assert r.metrics["beats_naive"]                      # a trending series defeats "same month last year"


def test_output_shape_and_interval_ordering():
    r = forecast_revenue(_series(noise=30, seed=2), horizon=8)
    f = r.forecast
    assert len(f) == 8 and f["month"].iloc[0] == pd.Timestamp("2017-05-01")
    assert (f["lower"] <= f["forecast"]).all() and (f["forecast"] <= f["upper"]).all() and (f["lower"] >= 0).all()
    assert len(r.backtest) == 6 and {"actual", "model", "naive"} <= set(r.backtest.columns)
    assert r.metrics["rmse"] >= r.metrics["mae"] > 0 and r.sigma > 0


def test_too_little_history_is_rejected():
    with pytest.raises(ValueError, match=str(MIN_MONTHS)):
        forecast_revenue(_series(n=MIN_MONTHS - 1))
    with pytest.raises(ValueError):
        forecast_revenue(pd.DataFrame(columns=["month", "revenue"]))


def test_invalid_horizon():
    for h in (0, 13):
        with pytest.raises(ValueError, match="horizon"):
            forecast_revenue(_series(), horizon=h)


def test_never_forecasts_negative_revenue():
    s = _series(trend=-30.0, amp=10)
    assert (forecast_revenue(s, horizon=12).forecast["forecast"] >= 0).all()
