#!/usr/bin/env python3
"""
Seed data for GPU Runner feature.

Creates:
1. M5 Highlighted Dataset entry
2. M5 Forecasting recipe with container configuration
3. Initial recipe version

Run with:
    python -m scripts.seed_gpu_runner
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from core.config import settings


def seed_gpu_runner():
    """Seed GPU Runner data."""
    print("🚀 Seeding GPU Runner data...")
    
    engine = create_engine(settings.database_url)
    
    with engine.begin() as conn:
        # ========================================
        # 1. Seed M5 Highlighted Dataset
        # ========================================
        print("  📦 Creating M5 highlighted dataset...")
        
        conn.execute(text("""
            INSERT INTO highlighted_datasets (
                id, display_name, description, tags, source_type, 
                availability_state, resolver_config, license_notes, created_at, updated_at
            )
            VALUES (
                'm5_forecasting',
                'M5 Forecasting Dataset',
                'Walmart retail sales data from the M5 Kaggle competition. Includes daily sales for ~3,000 products across 10 stores in 3 states over 5 years. Ideal for demand forecasting, price optimization, and promotional impact analysis.',
                ARRAY['forecasting', 'retail', 'time-series', 'kaggle', 'm5'],
                'manual_upload',
                'NOT_PRESENT',
                '{
                    "dataset_id": "m5",
                    "target_bucket_prefix": "datasets/m5",
                    "ingest_method": "manual_upload",
                    "required_files": ["calendar.csv", "sales_train_validation.csv", "sell_prices.csv"],
                    "optional_files": ["sample_submission.csv"],
                    "kaggle_competition": "m5-forecasting-accuracy"
                }'::jsonb,
                'Kaggle Competition License. Download from https://www.kaggle.com/competitions/m5-forecasting-accuracy/data',
                NOW(),
                NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                description = EXCLUDED.description,
                tags = EXCLUDED.tags,
                resolver_config = EXCLUDED.resolver_config,
                license_notes = EXCLUDED.license_notes,
                updated_at = NOW()
        """))
        
        # ========================================
        # 2. Create/Update M5 Forecasting Recipe
        # ========================================
        print("  🧪 Creating M5 forecasting recipe...")
        
        conn.execute(text("""
            INSERT INTO ml_recipe (
                id, name, model_family, level, status, tags,
                container_image, container_entrypoint, default_compute_target, gpu_required,
                created_at, updated_at
            )
            VALUES (
                'recipe_m5_forecast_v1',
                'M5 Forecasting (LightGBM)',
                'forecasting',
                'baseline',
                'approved',
                ARRAY['m5', 'lightgbm', 'time-series', 'retail', 'demand-forecasting'],
                'nex/forecast-m5:v1',
                ARRAY['python', 'run.py'],
                'local',
                false,
                NOW(),
                NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                container_image = EXCLUDED.container_image,
                container_entrypoint = EXCLUDED.container_entrypoint,
                default_compute_target = EXCLUDED.default_compute_target,
                gpu_required = EXCLUDED.gpu_required,
                tags = EXCLUDED.tags,
                updated_at = NOW()
        """))
        
        # ========================================
        # 3. Create Initial Recipe Version
        # ========================================
        print("  📋 Creating recipe version...")
        
        conn.execute(text("""
            INSERT INTO ml_recipe_version (
                version_id, recipe_id, version_number, manifest_json, change_note, created_at
            )
            VALUES (
                'ver_m5_forecast_v1_100',
                'recipe_m5_forecast_v1',
                '1.0.0',
                '{
                    "name": "M5 Forecasting Recipe",
                    "version": "1.0.0",
                    "description": "LightGBM-based demand forecasting for retail sales data",
                    "model_type": "regression",
                    "algorithm": "lightgbm",
                    "input": {
                        "type": "highlighted_dataset",
                        "dataset_id": "m5_forecasting",
                        "required_columns": ["date", "store_id", "item_id", "sales"]
                    },
                    "parameters": {
                        "horizon": {"type": "int", "default": 28, "min": 1, "max": 365, "description": "Forecast horizon in days"},
                        "n_estimators": {"type": "int", "default": 100, "min": 10, "max": 1000},
                        "learning_rate": {"type": "float", "default": 0.1, "min": 0.001, "max": 1.0},
                        "max_depth": {"type": "int", "default": -1, "description": "-1 for unlimited"},
                        "num_leaves": {"type": "int", "default": 31, "min": 2, "max": 256},
                        "seed": {"type": "int", "default": 42}
                    },
                    "features": {
                        "lag_features": [7, 14, 21, 28],
                        "rolling_windows": [7, 14, 28],
                        "calendar_features": ["dayofweek", "month", "dayofyear", "year"]
                    },
                    "outputs": [
                        {"name": "forecast", "type": "parquet", "description": "Predictions with actual values"},
                        {"name": "metrics", "type": "json", "description": "Evaluation metrics"},
                        {"name": "feature_importance", "type": "json", "description": "Feature importance scores"}
                    ],
                    "metrics": ["mae", "rmse", "r2", "smape", "wape"],
                    "compute_requirements": {
                        "min_memory_gb": 4,
                        "recommended_memory_gb": 8,
                        "gpu_required": false,
                        "estimated_runtime_minutes": 5
                    }
                }'::jsonb,
                'Initial version - LightGBM baseline forecasting',
                NOW()
            )
            ON CONFLICT (version_id) DO NOTHING
        """))
        
        # ========================================
        # 4. Create Sample Dataset for Testing
        # ========================================
        print("  📊 Creating sample highlighted dataset (for testing)...")
        
        conn.execute(text("""
            INSERT INTO highlighted_datasets (
                id, display_name, description, tags, source_type, 
                availability_state, resolver_config, license_notes, created_at, updated_at
            )
            VALUES (
                'sample_retail_sales',
                'Sample Retail Sales',
                'A small sample retail sales dataset for testing the forecasting pipeline. Contains synthetic data in M5 format.',
                ARRAY['sample', 'retail', 'time-series', 'testing'],
                'manual_upload',
                'NOT_PRESENT',
                '{
                    "dataset_id": "sample_retail",
                    "target_bucket_prefix": "datasets/sample_retail",
                    "ingest_method": "manual_upload",
                    "required_files": ["sales.csv"],
                    "is_sample": true
                }'::jsonb,
                'Sample data for testing - no restrictions',
                NOW(),
                NOW()
            )
            ON CONFLICT (id) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                description = EXCLUDED.description,
                updated_at = NOW()
        """))
    
    print("✅ GPU Runner seed data created successfully!")
    print("")
    print("Next steps:")
    print("  1. Build the recipe container: cd recipes/forecast_m5_v1 && docker build -t nex/forecast-m5:v1 .")
    print("  2. Upload M5 data via the API or UI")
    print("  3. Submit a run with recipe_id='recipe_m5_forecast_v1'")


if __name__ == '__main__':
    seed_gpu_runner()
