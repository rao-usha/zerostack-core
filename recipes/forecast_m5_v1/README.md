# M5 Forecasting Recipe

A containerized forecasting recipe that trains a LightGBM model on M5-style retail sales data.

## Overview

This recipe demonstrates the NEX GPU Runner pipeline by:
1. Loading data from S3/MinIO
2. Engineering time-series features
3. Training a LightGBM regression model
4. Computing evaluation metrics
5. Saving outputs back to S3/MinIO

## Building

```bash
# From the recipes/forecast_m5_v1 directory
docker build -t nex/forecast-m5:v1 .
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RUN_ID` | Unique run identifier | Yes |
| `INPUT_URI` | S3 URI to dataset (manifest or directory) | Yes |
| `OUTPUT_URI` | S3 URI prefix for outputs | Yes |
| `PARAMS_JSON` | JSON string with hyperparameters | No |
| `S3_ENDPOINT` | MinIO/S3 endpoint URL | Yes |
| `S3_ACCESS_KEY` | Access key | Yes |
| `S3_SECRET_KEY` | Secret key | Yes |
| `S3_BUCKET` | Bucket name | Yes |

## Parameters

Pass via `PARAMS_JSON`:

```json
{
  "horizon": 28,
  "n_estimators": 100,
  "learning_rate": 0.1,
  "max_depth": -1,
  "num_leaves": 31,
  "seed": 42
}
```

## Input Data

Expects CSV files:
- `calendar.csv` - Calendar/date dimension
- `sales_train_validation.csv` or `sales.csv` - Sales data
- `sell_prices.csv` (optional) - Price data

## Outputs

- `outputs/forecast.parquet` - Predictions with actual values
- `outputs/metrics.json` - Evaluation metrics (MAE, RMSE, R², sMAPE, WAPE)
- `outputs/feature_importance.json` - Feature importance scores
- `outputs/run_manifest.json` - Output manifest

## Local Testing

```bash
# Run with sample data
docker run -it --rm \
  -e RUN_ID=test_001 \
  -e INPUT_URI=datasets/m5/v1 \
  -e OUTPUT_URI=runs/test_001 \
  -e S3_ENDPOINT=http://host.docker.internal:9000 \
  -e S3_ACCESS_KEY=minioadmin \
  -e S3_SECRET_KEY=minioadmin \
  -e S3_BUCKET=nex-data \
  nex/forecast-m5:v1
```

## Metrics

| Metric | Description |
|--------|-------------|
| MAE | Mean Absolute Error |
| RMSE | Root Mean Squared Error |
| R² | Coefficient of Determination |
| sMAPE | Symmetric Mean Absolute Percentage Error |
| WAPE | Weighted Absolute Percentage Error |
