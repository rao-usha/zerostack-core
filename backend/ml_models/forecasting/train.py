#!/usr/bin/env python3
"""
M5 Forecasting with LightGBM

This script:
1. Loads M5 data from Parquet files (exported from PostgreSQL)
2. Creates features (lags, rolling means, calendar features)
3. Trains a LightGBM model
4. Generates forecasts
5. Outputs results and metrics

Usage:
    python train.py --input /path/to/data --output /path/to/results --horizon 28
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_data(input_path: str) -> tuple:
    """Load M5 data from parquet files."""
    logger.info(f"Loading data from {input_path}")
    
    sales = pd.read_parquet(os.path.join(input_path, 'sales.parquet'))
    calendar = pd.read_parquet(os.path.join(input_path, 'calendar.parquet'))
    prices = pd.read_parquet(os.path.join(input_path, 'prices.parquet'))
    
    logger.info(f"Loaded: sales={len(sales):,}, calendar={len(calendar):,}, prices={len(prices):,}")
    
    return sales, calendar, prices


def create_features(sales: pd.DataFrame, calendar: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Create features for forecasting."""
    logger.info("Creating features...")
    
    # Check if sales already has a 'date' column
    if 'date' in sales.columns:
        # Use sales date directly, drop calendar date to avoid conflict
        calendar_cols = ['d', 'wm_yr_wk', 'weekday', 'wday', 'month', 'year', 
                        'event_name_1', 'event_type_1', 'snap_ca', 'snap_tx', 'snap_wi']
        df = sales.merge(calendar[calendar_cols], on='d', how='left')
    else:
        # Need date from calendar
        df = sales.merge(calendar[['d', 'date', 'wm_yr_wk', 'weekday', 'wday', 'month', 'year', 
                                   'event_name_1', 'event_type_1', 'snap_ca', 'snap_tx', 'snap_wi']], 
                         on='d', how='left')
    
    # Merge with prices (drop any existing sell_price column to avoid conflict)
    prices_cols = ['store_id', 'item_id', 'wm_yr_wk', 'sell_price']
    df = df.merge(prices[prices_cols], on=['store_id', 'item_id', 'wm_yr_wk'], how='left')
    
    # Sort by item and date
    df = df.sort_values(['item_store_id', 'date']).reset_index(drop=True)
    
    # Create lag features
    logger.info("Creating lag features...")
    for lag in [7, 14, 21, 28]:
        df[f'lag_{lag}'] = df.groupby('item_store_id')['sales'].shift(lag)
    
    # Rolling mean features
    logger.info("Creating rolling features...")
    for window in [7, 14, 28]:
        df[f'rolling_mean_{window}'] = df.groupby('item_store_id')['sales'].transform(
            lambda x: x.shift(1).rolling(window, min_periods=1).mean()
        )
        df[f'rolling_std_{window}'] = df.groupby('item_store_id')['sales'].transform(
            lambda x: x.shift(1).rolling(window, min_periods=1).std()
        )
    
    # Encode categorical features
    df['weekday_num'] = pd.Categorical(df['weekday']).codes
    df['has_event'] = df['event_name_1'].notna().astype(int)
    
    # Extract store/item info
    df['store_num'] = df['store_id'].str.extract(r'(\d+)').astype(float)
    df['state'] = df['store_id'].str.extract(r'([A-Z]+)')
    df['state_num'] = pd.Categorical(df['state']).codes
    
    # Fill NaN values
    df = df.fillna(0)
    
    logger.info(f"Created {len(df):,} rows with {len(df.columns)} features")
    
    return df


def train_model(df: pd.DataFrame, horizon: int = 28) -> tuple:
    """Train LightGBM model."""
    logger.info(f"Training model with horizon={horizon}...")
    
    # Define features
    feature_cols = [
        'wday', 'month', 'year', 'weekday_num', 'has_event',
        'snap_ca', 'snap_tx', 'snap_wi',
        'sell_price', 'store_num', 'state_num',
        'lag_7', 'lag_14', 'lag_21', 'lag_28',
        'rolling_mean_7', 'rolling_mean_14', 'rolling_mean_28',
        'rolling_std_7', 'rolling_std_14', 'rolling_std_28'
    ]
    
    # Use available features
    feature_cols = [c for c in feature_cols if c in df.columns]
    
    # Split train/validation
    max_date = df['date'].max()
    val_start = max_date - pd.Timedelta(days=horizon)
    
    train_mask = df['date'] < val_start
    val_mask = (df['date'] >= val_start) & (df['date'] < max_date)
    
    X_train = df.loc[train_mask, feature_cols]
    y_train = df.loc[train_mask, 'sales']
    X_val = df.loc[val_mask, feature_cols]
    y_val = df.loc[val_mask, 'sales']
    
    logger.info(f"Train: {len(X_train):,} rows, Val: {len(X_val):,} rows")
    
    # Train LightGBM
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    params = {
        'objective': 'regression',
        'metric': 'mae',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1
    }
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, val_data],
        valid_names=['train', 'valid'],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
    )
    
    # Evaluate
    y_pred = model.predict(X_val)
    mae = mean_absolute_error(y_val, y_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    
    logger.info(f"Validation MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    return model, feature_cols, {'mae': mae, 'rmse': rmse}


def generate_forecasts(model, df: pd.DataFrame, feature_cols: list, horizon: int = 28) -> pd.DataFrame:
    """Generate forecasts for the next N days."""
    logger.info(f"Generating {horizon}-day forecasts...")
    
    # Get latest data for each item
    latest = df.groupby('item_store_id').tail(1).copy()
    
    # Make predictions
    X = latest[feature_cols]
    predictions = model.predict(X)
    
    forecasts = pd.DataFrame({
        'item_store_id': latest['item_store_id'].values,
        'item_id': latest['item_id'].values,
        'store_id': latest['store_id'].values,
        'forecast_sales': predictions,
        'forecast_date': latest['date'].values + pd.Timedelta(days=1)
    })
    
    logger.info(f"Generated {len(forecasts):,} forecasts")
    
    return forecasts


def main():
    parser = argparse.ArgumentParser(description='M5 Forecasting with LightGBM')
    parser.add_argument('--input', required=True, help='Input directory with parquet files')
    parser.add_argument('--output', required=True, help='Output directory for results')
    parser.add_argument('--horizon', type=int, default=28, help='Forecast horizon in days')
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info("="*60)
    logger.info("M5 FORECASTING WITH LIGHTGBM")
    logger.info("="*60)
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    logger.info(f"Horizon: {args.horizon} days")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load data
    sales, calendar, prices = load_data(args.input)
    
    # Create features
    df = create_features(sales, calendar, prices)
    
    # Train model
    model, feature_cols, metrics = train_model(df, args.horizon)
    
    # Generate forecasts
    forecasts = generate_forecasts(model, df, feature_cols, args.horizon)
    
    # Save results
    logger.info("Saving results...")
    
    # Save model
    model_path = os.path.join(args.output, 'model.txt')
    model.save_model(model_path)
    
    # Save forecasts
    forecast_path = os.path.join(args.output, 'forecasts.parquet')
    forecasts.to_parquet(forecast_path)
    
    # Save forecasts as CSV for easy viewing
    csv_path = os.path.join(args.output, 'forecasts.csv')
    forecasts.to_csv(csv_path, index=False)
    
    # Save metrics
    elapsed = (datetime.now() - start_time).total_seconds()
    metrics['training_time_seconds'] = elapsed
    metrics['horizon_days'] = args.horizon
    metrics['num_items'] = len(forecasts)
    metrics['timestamp'] = datetime.now().isoformat()
    
    metrics_path = os.path.join(args.output, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importance()
    }).sort_values('importance', ascending=False)
    importance.to_csv(os.path.join(args.output, 'feature_importance.csv'), index=False)
    
    logger.info("="*60)
    logger.info("RESULTS")
    logger.info("="*60)
    logger.info(f"Model saved: {model_path}")
    logger.info(f"Forecasts saved: {forecast_path}")
    logger.info(f"Metrics: MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}")
    logger.info(f"Total time: {elapsed:.1f} seconds")
    logger.info("="*60)
    
    print("\n--- METRICS JSON ---")
    print(json.dumps(metrics, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
