
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.modeling import forecasting


def test_create_supervised_data():
    df = pd.DataFrame({
        "week_start": pd.date_range("2023-01-02", periods=6, freq="W-MON"),
        "job_posting_count": [2, 4, 6, 8, 10, 12],
    })

    result = forecasting.create_supervised_data(df)

    assert len(result) == 2
    assert result.iloc[0]["demand_lag_1"] == 8
    assert result.iloc[0]["demand_lag_2"] == 6
    assert result.iloc[0]["demand_lag_4"] == 2
    assert result.iloc[0]["rolling_mean_4"] == 5


def test_calculate_metrics():
    actual = [10, 20]
    predicted = [8, 22]

    metrics = forecasting.calculate_metrics(actual, predicted)

    assert metrics["MAE"] == 2
    assert metrics["RMSE"] == 2
    assert round(metrics["MAPE"], 2) == 15.00
    assert round(metrics["WAPE"], 2) == 13.33


def test_moving_average_forecast():
    history = [2, 4, 6, 8, 10]

    prediction = forecasting.moving_average_forecast(history)

    assert prediction == 7


def test_load_weekly_demand_data(tmp_path):
    input_file = tmp_path / "weekly.csv"

    df = pd.DataFrame({
        "week_start": ["2023-01-09", "2023-01-02"],
        "job_posting_count": [5, 10],
    })

    df.to_csv(input_file, index=False)

    result = forecasting.load_weekly_demand_data(input_file)

    assert len(result) == 2
    assert result.iloc[0]["week_start"] == pd.Timestamp("2023-01-02")
    assert result["job_posting_count"].tolist() == [10, 5]


def test_run_forecasting_experiment(tmp_path, monkeypatch):
    input_file = tmp_path / "weekly.csv"
    output_dir = tmp_path / "sprint_09"

    df = pd.DataFrame({
        "week_start": pd.date_range("2023-01-02", periods=30, freq="W-MON"),
        "job_posting_count": [
            5, 6, 7, 8, 6, 7, 9, 8, 10, 11,
            9, 10, 12, 11, 13, 12, 14, 13, 15, 14,
            16, 15, 17, 16, 18, 17, 19, 18, 20, 19,
        ],
    })

    df.to_csv(input_file, index=False)

    monkeypatch.setattr(forecasting, "OUTPUT_DIR", output_dir)

    comparison, forecasts = forecasting.run_forecasting_experiment(
        file_path=input_file,
        forecast_horizon=4,
    )

    assert len(comparison) == 3
    assert len(forecasts) == 12
    assert comparison["MAE"].notna().all()
    assert forecasts["predicted_posting_count"].notna().all()

    assert (output_dir / "model_comparison.csv").exists()
    assert (output_dir / "future_demand_forecast.csv").exists()
