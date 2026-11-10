
"""Weekly job demand forecasting for Sprint 9.

Uses historical Microsoft job-posting counts to compare:
1. Four-week Moving Average baseline
2. Linear Regression
3. Ridge Regression

Evaluation uses chronological validation.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "weekly_demand_features.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "sprint_09"

TARGET = "job_posting_count"
FEATURES = [
    "demand_lag_1",
    "demand_lag_2",
    "demand_lag_4",
    "rolling_mean_4",
]


def load_weekly_demand_data(file_path=INPUT_FILE):
    """Load and validate weekly demand data."""
    df = pd.read_csv(file_path)

    required = {"week_start", TARGET}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["week_start"] = pd.to_datetime(df["week_start"])
    df = df.sort_values("week_start").reset_index(drop=True)

    if df["week_start"].duplicated().any():
        raise ValueError("Duplicate weekly dates found.")

    if df[TARGET].isna().any():
        raise ValueError("Missing target values found.")

    if (df[TARGET] < 0).any():
        raise ValueError("Demand counts cannot be negative.")

    return df[["week_start", TARGET]]


def create_supervised_data(df):
    """Create features using only previous weeks' demand."""
    data = df.copy()

    for lag in [1, 2, 4]:
        data[f"demand_lag_{lag}"] = data[TARGET].shift(lag)

    data["rolling_mean_4"] = (
        data[TARGET].shift(1).rolling(window=4).mean()
    )

    return data.dropna(subset=FEATURES).reset_index(drop=True)


def calculate_metrics(actual, predicted):
    """Calculate forecasting evaluation metrics."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))

    nonzero = actual != 0
    mape = (
        np.mean(np.abs((actual[nonzero] - predicted[nonzero])
                       / actual[nonzero])) * 100
        if nonzero.any()
        else np.nan
    )

    wape = (
        np.sum(np.abs(actual - predicted)) / np.sum(actual) * 100
        if np.sum(actual) != 0
        else np.nan
    )

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape,
        "WAPE": wape,
    }


def moving_average_forecast(history, window=4):
    """Predict demand using the average of the previous weeks."""
    recent = history[-window:]
    return float(np.mean(recent))


def build_future_features(history):
    """Build one forecast row from the latest known demand values."""
    return pd.DataFrame([{
        "demand_lag_1": history[-1],
        "demand_lag_2": history[-2],
        "demand_lag_4": history[-4],
        "rolling_mean_4": np.mean(history[-4:]),
    }])


def run_forecasting_experiment(
    file_path=INPUT_FILE,
    train_fraction=0.80,
    forecast_horizon=4,
):
    """Train, evaluate and generate future weekly forecasts."""
    df = load_weekly_demand_data(file_path)
    supervised = create_supervised_data(df)

    split_index = int(len(supervised) * train_fraction)

    if split_index < 5 or split_index >= len(supervised):
        raise ValueError("Not enough observations for chronological validation.")

    train = supervised.iloc[:split_index]
    test = supervised.iloc[split_index:]

    X_train = train[FEATURES]
    y_train = train[TARGET]

    X_test = test[FEATURES]
    y_test = test[TARGET]

    models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
    }

    results = []
    test_predictions = {}

    # Moving Average baseline
    history = df[TARGET].iloc[:split_index + 4].astype(float).tolist()
    moving_predictions = []

    for actual in y_test:
        prediction = moving_average_forecast(history)
        moving_predictions.append(max(0.0, prediction))
        history.append(float(actual))

    test_predictions["Moving Average"] = moving_predictions

    # Regression models
    for name, model in models.items():
        model.fit(X_train, y_train)
        predictions = np.maximum(0, model.predict(X_test))
        test_predictions[name] = predictions

    # Evaluate all models
    for name, predictions in test_predictions.items():
        metrics = calculate_metrics(y_test, predictions)
        results.append({"Model": name, **metrics})

    results_df = pd.DataFrame(results).sort_values("MAE")

    # Forecast the next weeks using each model recursively
    future_rows = []
    last_date = df["week_start"].max()

    for name, model in models.items():
        history = df[TARGET].astype(float).tolist()

        for step in range(1, forecast_horizon + 1):
            features = build_future_features(history)
            prediction = max(0.0, float(model.predict(features)[0]))
            history.append(prediction)

            future_rows.append({
                "Model": name,
                "forecast_week": (
                    last_date + pd.Timedelta(weeks=step)
                ),
                "predicted_posting_count": prediction,
            })

    # Moving Average future forecast
    history = df[TARGET].astype(float).tolist()

    for step in range(1, forecast_horizon + 1):
        prediction = max(0.0, moving_average_forecast(history))
        history.append(prediction)

        future_rows.append({
            "Model": "Moving Average",
            "forecast_week": last_date + pd.Timedelta(weeks=step),
            "predicted_posting_count": prediction,
        })

    forecast_df = pd.DataFrame(future_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(
        OUTPUT_DIR / "model_comparison.csv", index=False
    )
    forecast_df.to_csv(
        OUTPUT_DIR / "future_demand_forecast.csv", index=False
    )
    save_forecast_visualizations(
    df,
    results_df,
    forecast_df,)
    return results_df, forecast_df

def save_forecast_visualizations(df, comparison, forecasts):
    """Save model comparison and future forecast charts."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Chart 1: Compare model evaluation metrics
    fig, ax = plt.subplots(figsize=(9, 5))

    comparison.plot(
        x="Model",
        y=["MAE", "RMSE"],
        kind="bar",
        ax=ax,
    )

    ax.set_title("Sprint 9 - Forecasting Model Comparison")
    ax.set_xlabel("Forecasting Model")
    ax.set_ylabel("Prediction Error (Postings)")
    ax.legend(title="Metric")
    ax.tick_params(axis="x", rotation=15)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "model_comparison.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Chart 2: Historical demand and future forecasts
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        df["week_start"],
        df[TARGET],
        label="Historical Demand",
        marker="o",
        markersize=3,
    )

    for model_name, group in forecasts.groupby("Model"):
        ax.plot(
            group["forecast_week"],
            group["predicted_posting_count"],
            marker="o",
            linestyle="--",
            label=model_name,
        )

    ax.set_title("Microsoft Weekly Job Demand - Future Forecast")
    ax.set_xlabel("Week")
    ax.set_ylabel("Weekly Job Postings")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        OUTPUT_DIR / "future_demand_forecast.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)



if __name__ == "__main__":
    comparison, forecasts = run_forecasting_experiment()

    print("\nMODEL COMPARISON")
    print(comparison.round(3).to_string(index=False))

    print("\nNEXT FOUR WEEKS FORECAST")

    display_forecasts = forecasts.copy()
    display_forecasts["predicted_posting_count"] = (
    display_forecasts["predicted_posting_count"].round(2))

    print(display_forecasts.to_string(index=False))

    print("\nOutputs saved to:", OUTPUT_DIR)
