#!/usr/bin/env python3
"""
M5 Forecasting Recipe

Trains a LightGBM model on M5 retail sales data and produces forecasts.
This is a baseline implementation suitable for demonstrating the GPU Runner pipeline.

Environment Variables:
    RUN_ID: Unique identifier for this run
    INPUT_URI: S3 URI to input dataset manifest or root
    OUTPUT_URI: S3 URI prefix for outputs (runs/{run_id}/)
    PARAMS_JSON: JSON string with parameters
    S3_ENDPOINT: MinIO/S3 endpoint URL
    S3_ACCESS_KEY: Access key
    S3_SECRET_KEY: Secret key
    S3_BUCKET: Bucket name

Outputs:
    - outputs/forecast.parquet: Predictions
    - outputs/metrics.json: Evaluation metrics
    - outputs/run_manifest.json: Output manifest
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, List
from io import BytesIO

import boto3
import pandas as pd
import numpy as np
from botocore.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class S3Client:
    """Simple S3 client wrapper."""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=os.environ.get('S3_ENDPOINT', 'http://localhost:9000'),
            aws_access_key_id=os.environ.get('S3_ACCESS_KEY', 'minioadmin'),
            aws_secret_access_key=os.environ.get('S3_SECRET_KEY', 'minioadmin'),
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        self.bucket = os.environ.get('S3_BUCKET', 'nex-data')
    
    def parse_uri(self, uri: str) -> Tuple[str, str]:
        """Parse s3://bucket/key into (bucket, key)."""
        if uri.startswith('s3://'):
            parts = uri[5:].split('/', 1)
            return parts[0], parts[1] if len(parts) > 1 else ''
        return self.bucket, uri
    
    def get_json(self, key: str) -> dict:
        """Read JSON from S3."""
        bucket, key = self.parse_uri(key)
        response = self.client.get_object(Bucket=bucket, Key=key)
        return json.loads(response['Body'].read().decode('utf-8'))
    
    def get_csv(self, key: str) -> pd.DataFrame:
        """Read CSV from S3."""
        bucket, key = self.parse_uri(key)
        response = self.client.get_object(Bucket=bucket, Key=key)
        return pd.read_csv(response['Body'])
    
    def put_json(self, key: str, data: dict):
        """Write JSON to S3."""
        bucket, key = self.parse_uri(key)
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2, default=str).encode('utf-8'),
            ContentType='application/json'
        )
    
    def put_parquet(self, key: str, df: pd.DataFrame):
        """Write DataFrame as Parquet to S3."""
        bucket, key = self.parse_uri(key)
        buffer = BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType='application/octet-stream'
        )
    
    def list_objects(self, prefix: str) -> List[dict]:
        """List objects with prefix."""
        bucket, prefix = self.parse_uri(prefix)
        response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return response.get('Contents', [])


def load_dataset(s3: S3Client, input_uri: str) -> Dict[str, pd.DataFrame]:
    """
    Load M5 dataset from S3.
    
    Expects CSV files in the input location:
    - calendar.csv
    - sales_train_validation.csv (or sales.csv)
    - sell_prices.csv (optional)
    """
    logger.info(f"Loading dataset from {input_uri}")
    
    # List files in the input location
    bucket, prefix = s3.parse_uri(input_uri)
    
    # Handle both manifest URI and directory URI
    if prefix.endswith('manifest.json'):
        # Read manifest to find files
        manifest = s3.get_json(input_uri)
        base_prefix = prefix.rsplit('/', 1)[0]
        files = {f['path'].split('/')[-1]: f"{base_prefix}/{f['path']}" for f in manifest.get('files', [])}
    else:
        # Scan directory for CSV files
        objects = s3.list_objects(prefix)
        files = {}
        for obj in objects:
            key = obj['Key']
            if key.endswith('.csv'):
                filename = key.split('/')[-1]
                files[filename] = key
    
    logger.info(f"Found files: {list(files.keys())}")
    
    data = {}
    
    # Load calendar
    for name in ['calendar.csv', 'Calendar.csv']:
        if name in files:
            logger.info(f"Loading {name}...")
            data['calendar'] = s3.get_csv(files[name])
            break
    
    # Load sales data
    for name in ['sales_train_validation.csv', 'sales.csv', 'Sales.csv']:
        if name in files:
            logger.info(f"Loading {name}...")
            data['sales'] = s3.get_csv(files[name])
            break
    
    # Load prices (optional)
    for name in ['sell_prices.csv', 'prices.csv', 'Prices.csv']:
        if name in files:
            logger.info(f"Loading {name}...")
            data['prices'] = s3.get_csv(files[name])
            break
    
    if 'sales' not in data:
        # Create sample data if no sales file found
        logger.warning("No sales data found, creating sample data for testing")
        data['sales'] = create_sample_sales_data()
    
    return data


def create_sample_sales_data() -> pd.DataFrame:
    """Create sample sales data for testing when M5 data isn't available."""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=365, freq='D')
    stores = ['CA_1', 'CA_2', 'TX_1']
    items = ['ITEM_001', 'ITEM_002', 'ITEM_003']
    
    records = []
    for store in stores:
        for item in items:
            base_sales = np.random.randint(10, 100)
            for date in dates:
                # Add trend, seasonality, and noise
                trend = (date - dates[0]).days * 0.01
                seasonality = 10 * np.sin(2 * np.pi * date.dayofyear / 365)
                noise = np.random.normal(0, 5)
                sales = max(0, int(base_sales + trend + seasonality + noise))
                records.append({
                    'date': date,
                    'store_id': store,
                    'item_id': item,
                    'sales': sales
                })
    
    return pd.DataFrame(records)


def prepare_features(data: Dict[str, pd.DataFrame], params: dict) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features for training.
    
    Creates lag features, rolling statistics, and calendar features.
    """
    logger.info("Preparing features...")
    
    sales = data['sales'].copy()
    
    # Ensure we have the required columns
    if 'date' not in sales.columns:
        # Try to find date column
        date_cols = [c for c in sales.columns if 'date' in c.lower() or c == 'd']
        if date_cols:
            sales['date'] = pd.to_datetime(sales[date_cols[0]])
    
    if 'sales' not in sales.columns:
        # M5 format might have sales in different format
        value_cols = [c for c in sales.columns if c.startswith('d_')]
        if value_cols:
            # Melt from wide to long format
            id_cols = [c for c in sales.columns if not c.startswith('d_')]
            sales = sales.melt(id_vars=id_cols, value_vars=value_cols, 
                              var_name='d', value_name='sales')
    
    # Convert date if needed
    if 'date' in sales.columns and not pd.api.types.is_datetime64_any_dtype(sales['date']):
        sales['date'] = pd.to_datetime(sales['date'])
    
    # Add calendar features
    if 'date' in sales.columns:
        sales['dayofweek'] = sales['date'].dt.dayofweek
        sales['month'] = sales['date'].dt.month
        sales['dayofyear'] = sales['date'].dt.dayofyear
        sales['year'] = sales['date'].dt.year
    
    # Group columns for lag calculation
    group_cols = []
    if 'store_id' in sales.columns:
        group_cols.append('store_id')
    if 'item_id' in sales.columns:
        group_cols.append('item_id')
    
    # Sort for lag features
    sort_cols = group_cols + (['date'] if 'date' in sales.columns else [])
    if sort_cols:
        sales = sales.sort_values(sort_cols)
    
    # Create lag features
    for lag in [7, 14, 21, 28]:
        if group_cols:
            sales[f'lag_{lag}'] = sales.groupby(group_cols)['sales'].shift(lag)
        else:
            sales[f'lag_{lag}'] = sales['sales'].shift(lag)
    
    # Create rolling features
    for window in [7, 14, 28]:
        if group_cols:
            sales[f'rolling_mean_{window}'] = sales.groupby(group_cols)['sales'].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).mean()
            )
            sales[f'rolling_std_{window}'] = sales.groupby(group_cols)['sales'].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).std()
            )
        else:
            sales[f'rolling_mean_{window}'] = sales['sales'].shift(1).rolling(window, min_periods=1).mean()
            sales[f'rolling_std_{window}'] = sales['sales'].shift(1).rolling(window, min_periods=1).std()
    
    # Drop rows with NaN (from lag features)
    sales = sales.dropna()
    
    logger.info(f"Dataset shape after feature engineering: {sales.shape}")
    
    # Select features
    feature_cols = [c for c in sales.columns if any([
        c.startswith('lag_'),
        c.startswith('rolling_'),
        c in ['dayofweek', 'month', 'dayofyear', 'year']
    ])]
    
    if not feature_cols:
        raise ValueError("No features could be created from the data")
    
    logger.info(f"Using features: {feature_cols}")
    
    X = sales[feature_cols].fillna(0)
    y = sales['sales']
    
    return X, y, sales


def train_model(X: pd.DataFrame, y: pd.Series, params: dict):
    """Train LightGBM model."""
    from lightgbm import LGBMRegressor
    
    logger.info("Training LightGBM model...")
    
    # Train/validation split (last 28 days as validation)
    horizon = params.get('horizon', 28)
    split_idx = max(0, len(X) - horizon * 100)  # Approximate split
    
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Validation set: {len(X_val)} samples")
    
    model = LGBMRegressor(
        n_estimators=params.get('n_estimators', 100),
        learning_rate=params.get('learning_rate', 0.1),
        max_depth=params.get('max_depth', -1),
        num_leaves=params.get('num_leaves', 31),
        min_child_samples=params.get('min_child_samples', 20),
        random_state=params.get('seed', 42),
        n_jobs=-1,
        verbose=-1
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
    )
    
    return model, X_val, y_val


def compute_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    """Compute evaluation metrics."""
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    # sMAPE (Symmetric Mean Absolute Percentage Error)
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
    smape = np.mean(np.abs(y_true - y_pred) / np.where(denominator == 0, 1, denominator)) * 100
    
    # WAPE (Weighted Absolute Percentage Error)
    wape = np.sum(np.abs(y_true - y_pred)) / np.sum(np.abs(y_true)) * 100
    
    return {
        'mae': round(float(mae), 4),
        'rmse': round(float(rmse), 4),
        'r2': round(float(r2), 4),
        'smape': round(float(smape), 4),
        'wape': round(float(wape), 4),
        'samples': int(len(y_true))
    }


def save_outputs(s3: S3Client, output_uri: str, run_id: str, 
                 forecast_df: pd.DataFrame, metrics: dict, feature_importance: dict):
    """Save all outputs to S3."""
    logger.info("Saving outputs...")
    
    # Normalize output URI
    if not output_uri.endswith('/'):
        output_uri += '/'
    
    # Save forecast
    forecast_key = f"{output_uri}outputs/forecast.parquet"
    s3.put_parquet(forecast_key, forecast_df)
    logger.info(f"Saved forecast to {forecast_key}")
    
    # Save metrics
    metrics_key = f"{output_uri}outputs/metrics.json"
    s3.put_json(metrics_key, metrics)
    logger.info(f"Saved metrics to {metrics_key}")
    
    # Save feature importance
    importance_key = f"{output_uri}outputs/feature_importance.json"
    s3.put_json(importance_key, feature_importance)
    logger.info(f"Saved feature importance to {importance_key}")
    
    # Create run manifest
    manifest = {
        'run_id': run_id,
        'completed_at': datetime.utcnow().isoformat(),
        'outputs': [
            {'name': 'forecast', 'path': 'outputs/forecast.parquet', 'type': 'parquet'},
            {'name': 'metrics', 'path': 'outputs/metrics.json', 'type': 'json'},
            {'name': 'feature_importance', 'path': 'outputs/feature_importance.json', 'type': 'json'}
        ],
        'metrics': metrics
    }
    manifest_key = f"{output_uri}outputs/run_manifest.json"
    s3.put_json(manifest_key, manifest)
    logger.info(f"Saved manifest to {manifest_key}")


def main():
    """Main entry point."""
    # Get environment variables
    run_id = os.environ.get('RUN_ID', 'test_run')
    input_uri = os.environ.get('INPUT_URI', '')
    output_uri = os.environ.get('OUTPUT_URI', f'runs/{run_id}/')
    params_json = os.environ.get('PARAMS_JSON', '{}')
    
    params = json.loads(params_json)
    
    logger.info("=" * 60)
    logger.info("M5 Forecasting Recipe")
    logger.info("=" * 60)
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Input URI: {input_uri}")
    logger.info(f"Output URI: {output_uri}")
    logger.info(f"Parameters: {params}")
    logger.info("=" * 60)
    
    try:
        # Initialize S3 client
        s3 = S3Client()
        
        # Load dataset
        data = load_dataset(s3, input_uri)
        
        # Prepare features
        X, y, full_df = prepare_features(data, params)
        logger.info(f"Feature matrix shape: {X.shape}")
        
        # Train model
        model, X_val, y_val = train_model(X, y, params)
        
        # Generate predictions
        logger.info("Generating predictions...")
        y_pred = model.predict(X_val)
        
        # Compute metrics
        metrics = compute_metrics(y_val, y_pred)
        logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
        
        # Get feature importance
        feature_importance = dict(zip(X.columns, model.feature_importances_.tolist()))
        
        # Create forecast DataFrame
        forecast_df = pd.DataFrame({
            'actual': y_val.values,
            'predicted': y_pred,
            'residual': y_val.values - y_pred
        })
        
        # Save outputs
        save_outputs(s3, output_uri, run_id, forecast_df, metrics, feature_importance)
        
        logger.info("=" * 60)
        logger.info(f"Run {run_id} completed successfully!")
        logger.info("=" * 60)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Run failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
