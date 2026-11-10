# Sprint 9 Report: Weekly Job Demand Forecasting

## 1. Objective

The objective of Sprint 9 was to develop and evaluate machine learning models to forecast weekly Microsoft job-posting demand using historical job-posting data.

The forecasting system compares a Moving Average baseline, Linear Regression and Ridge Regression.

## 2. Dataset

- **Source:** Previously processed Microsoft job-posting dataset.
- **Company:** Microsoft.
- **Time period:** 2 January 2023 to 25 December 2023.
- **Total job postings:** 498.
- **Weekly observations:** 52.
- **Average weekly demand:** 9.58 postings.
- **Minimum weekly demand:** 1 posting.
- **Maximum weekly demand:** 23 postings.
- **Zero-demand weeks:** 0.

The target variable was `job_posting_count`.

## 3. Data Preparation

The weekly demand dataset was sorted chronologically.

The following historical features were used:

- Demand lag 1 week.
- Demand lag 2 weeks.
- Demand lag 4 weeks.
- Four-week rolling average.

The first four observations were excluded from supervised model training because sufficient historical values were not available to calculate all lag features.

## 4. Forecasting Models

Three approaches were implemented:

1. **Moving Average:** Uses the average demand from the previous four weeks as a baseline forecast.
2. **Linear Regression:** Learns a linear relationship between previous demand values and future weekly demand.
3. **Ridge Regression:** Uses regularized linear regression to reduce model complexity and help limit overfitting.

## 5. Training and Validation

A chronological 80:20 split was used.

- Supervised observations: 48.
- Training observations: 38.
- Testing observations: 10.

The models were evaluated on later weeks rather than randomly selected observations. This preserves the time order of the data.

For the test period, each prediction uses historical observations available up to that week. Future forecasts use recursively generated predictions.

## 6. Evaluation Metrics

The following metrics were calculated:

- **MAE:** Mean Absolute Error.
- **RMSE:** Root Mean Squared Error.
- **MAPE:** Mean Absolute Percentage Error.
- **WAPE:** Weighted Absolute Percentage Error.

There were no zero-demand weeks in the dataset, so MAPE could be calculated without division-by-zero issues.

## 7. Model Comparison Results

| Model | MAE | RMSE | MAPE (%) | WAPE (%) |
|---|---:|---:|---:|---:|
| Moving Average | 5.050 | 6.131 | 36.993 | 32.792 |
| Linear Regression | 5.946 | 7.114 | 39.380 | 38.610 |
| Ridge Regression | 5.949 | 7.109 | 39.397 | 38.630 |

The Moving Average model achieved the lowest MAE and RMSE and performed best among the three evaluated approaches.

This result shows that a simple baseline can outperform more complex models when the available time-series dataset is small.

## 8. Four-Week Forecast

The models generated forecasts for the four weeks following the historical dataset.

| Forecast Week | Moving Average | Linear Regression | Ridge Regression |
|---|---:|---:|---:|
| 1 Jan 2024 | 17.75 | 11.92 | 11.94 |
| 8 Jan 2024 | 18.44 | 12.91 | 12.92 |
| 15 Jan 2024 | 17.30 | 11.96 | 11.96 |
| 22 Jan 2024 | 17.12 | 10.81 | 10.80 |

These are illustrative forecasts based on historical 2023 data, not verified hiring figures or predictions of current hiring demand.

## 9. Visualizations

The following visualizations were generated:

- `model_comparison.png` — compares the MAE and RMSE of all three forecasting models.
- `future_demand_forecast.png` — displays historical weekly demand and the four-week forecasts from each model.

## 10. Output Files

Generated under `outputs/sprint_09/`:

- `model_comparison.csv`
- `future_demand_forecast.csv`
- `model_comparison.png`
- `future_demand_forecast.png`

## 11. Testing

Five new forecasting tests were added in `tests/test_forecasting.py`.

The complete project test suite passed:

**199 tests passed.**

## 12. Limitations

- The dataset contains only 52 weekly observations from 2023.
- Job postings represent advertised opportunities, not confirmed hires.
- The forecasts are short-term extrapolations from historical data.
- The evaluation period contains only 10 observations.
- The models may not capture seasonal changes, economic conditions or sudden hiring changes.
- Competitor forecasting was not included because the existing competitor weekly datasets were empty.

## 13. Conclusion

Sprint 9 successfully implemented a weekly job-demand forecasting pipeline for Microsoft.

Three forecasting approaches were evaluated using chronological validation. The Moving Average baseline achieved the best evaluation results.

The project now supports historical demand analysis, forecasting model comparison, evaluation metrics and four-week future demand forecasts.
