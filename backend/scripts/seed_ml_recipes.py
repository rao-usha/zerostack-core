"""Seed baseline ML recipes for all model families."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from datetime import datetime
from uuid import uuid4

from core.config import settings
from db.models import ml_recipe, ml_recipe_version, ml_synthetic_example

# Create engine
engine = create_engine(settings.database_url)


def seed_recipes():
    """Seed baseline recipes for all 4 model families."""
    
    # Forecasting baseline recipe
    forecasting_recipe = {
        "id": "recipe_forecasting_base",
        "name": "Forecasting Baseline v1",
        "model_family": "forecasting",
        "level": "baseline",
        "status": "approved",
        "parent_id": None,
        "tags": ["baseline", "time-series", "arima"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    forecasting_manifest = {
        "metadata": {
            "id": "recipe_forecasting_base",
            "name": "Forecasting Baseline v1",
            "description": "Baseline forecasting model using ARIMA/Prophet for time series prediction",
            "model_family": "forecasting",
            "level": "baseline",
            "version": "1.0.0"
        },
        "requirements": {
            "feature_sets": {
                "required": ["time_series_features", "calendar_features"],
                "optional": ["economic_indicators", "weather_features"]
            },
            "grain": "daily",
            "labels": ["target_value"],
            "min_history": "2 years"
        },
        "pipeline": {
            "stages": [
                {
                    "name": "data_quality",
                    "type": "quality",
                    "checks": ["missing_values", "outliers", "stationarity"]
                },
                {
                    "name": "feature_engineering",
                    "type": "feature_prep",
                    "transforms": ["lag_features", "rolling_statistics", "seasonality_encoding"]
                },
                {
                    "name": "training",
                    "type": "training",
                    "algorithm": "auto_arima",
                    "hyperparameters": {
                        "seasonal": True,
                        "m": 7,
                        "max_p": 5,
                        "max_q": 5
                    }
                },
                {
                    "name": "evaluation",
                    "type": "evaluation",
                    "metrics": ["MAPE", "RMSE", "MAE", "coverage"]
                },
                {
                    "name": "deployment",
                    "type": "deployment",
                    "mode": "batch",
                    "schedule": "daily"
                }
            ]
        },
        "evaluation": {
            "metrics": {
                "MAPE": {"target": 0.15, "threshold_warning": 0.20, "threshold_critical": 0.30},
                "RMSE": {"target": "auto", "threshold_warning": "auto", "threshold_critical": "auto"},
                "MAE": {"target": "auto", "threshold_warning": "auto", "threshold_critical": "auto"}
            },
            "validation": {
                "method": "time_series_split",
                "n_splits": 5,
                "test_size": "30 days"
            }
        },
        "lineage": {
            "input_features": ["date", "target_value", "lag_1", "lag_7", "rolling_mean_7"],
            "output_features": ["forecast", "lower_bound", "upper_bound", "confidence"]
        },
        "deployment": {
            "mode": "batch",
            "schedule": "0 2 * * *",
            "endpoint_spec": None,
            "output_format": "csv"
        },
        "monitoring": {
            "metrics": ["MAPE", "RMSE", "forecast_bias"],
            "drift": {
                "method": "PSI",
                "threshold": 0.1,
                "features": ["target_value", "lag_features"]
            },
            "freshness": {
                "max_age_hours": 48,
                "features": ["time_series_features"]
            },
            "alerts": {
                "mape_exceeded": {"condition": "MAPE > 0.30", "severity": "critical"},
                "data_stale": {"condition": "freshness > 48h", "severity": "warning"}
            }
        }
    }
    
    forecasting_version = {
        "version_id": "ver_forecasting_base_v1",
        "recipe_id": "recipe_forecasting_base",
        "version_number": "1.0.0",
        "manifest_json": forecasting_manifest,
        "diff_from_prev": None,
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "change_note": "Initial baseline forecasting recipe"
    }
    
    forecasting_example = {
        "id": "example_forecasting_base",
        "recipe_id": "recipe_forecasting_base",
        "dataset_schema_json": {
            "columns": [
                {"name": "date", "type": "date"},
                {"name": "target_value", "type": "float"},
                {"name": "lag_1", "type": "float"},
                {"name": "lag_7", "type": "float"},
                {"name": "rolling_mean_7", "type": "float"}
            ]
        },
        "sample_rows_json": [
            {"date": "2024-01-01", "target_value": 1250.5, "lag_1": 1200.3, "lag_7": 1180.2, "rolling_mean_7": 1195.4},
            {"date": "2024-01-02", "target_value": 1280.3, "lag_1": 1250.5, "lag_7": 1210.5, "rolling_mean_7": 1220.1},
            {"date": "2024-01-03", "target_value": 1310.7, "lag_1": 1280.3, "lag_7": 1230.8, "rolling_mean_7": 1245.3}
        ],
        "example_run_json": {
            "stages": ["quality", "feature_prep", "training", "evaluation"],
            "sample_metrics": {"MAPE": 0.142, "RMSE": 45.2, "MAE": 32.1},
            "sample_output": {"forecast": 1340.2, "lower_bound": 1290.5, "upper_bound": 1390.0}
        },
        "created_at": datetime.utcnow()
    }
    
    # Pricing baseline recipe
    pricing_recipe = {
        "id": "recipe_pricing_base",
        "name": "Pricing Optimization Baseline v1",
        "model_family": "pricing",
        "level": "baseline",
        "status": "approved",
        "parent_id": None,
        "tags": ["baseline", "optimization", "elasticity"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    pricing_manifest = {
        "metadata": {
            "id": "recipe_pricing_base",
            "name": "Pricing Optimization Baseline v1",
            "description": "Baseline pricing model for margin/revenue optimization with elasticity modeling",
            "model_family": "pricing",
            "level": "baseline",
            "version": "1.0.0"
        },
        "requirements": {
            "feature_sets": {
                "required": ["price_history", "sales_volume", "cost_features"],
                "optional": ["competitor_prices", "seasonality", "promotion_flags"]
            },
            "grain": "product-day",
            "labels": ["actual_demand", "actual_revenue"],
            "min_history": "1 year"
        },
        "pipeline": {
            "stages": [
                {
                    "name": "data_quality",
                    "type": "quality",
                    "checks": ["price_bounds", "negative_values", "outliers"]
                },
                {
                    "name": "elasticity_estimation",
                    "type": "feature_prep",
                    "method": "log-log_regression",
                    "segments": ["product_category", "region"]
                },
                {
                    "name": "optimization",
                    "type": "training",
                    "objective": "maximize_margin",
                    "constraints": {
                        "min_price_multiplier": 0.85,
                        "max_price_multiplier": 1.25,
                        "competitive_index": {"min": 0.90, "max": 1.10}
                    }
                },
                {
                    "name": "evaluation",
                    "type": "evaluation",
                    "metrics": ["revenue_lift", "margin_impact", "price_elasticity", "calibration"]
                },
                {
                    "name": "deployment",
                    "type": "deployment",
                    "mode": "batch",
                    "schedule": "weekly"
                }
            ]
        },
        "evaluation": {
            "metrics": {
                "revenue_lift": {"target": 0.03, "threshold_warning": 0.01, "threshold_critical": -0.01},
                "margin_impact": {"target": 0.05, "threshold_warning": 0.02, "threshold_critical": 0.00},
                "elasticity": {"target_range": [-2.0, -0.5], "threshold_critical": [-5.0, 0.0]},
                "calibration": {"target": 0.95, "threshold_warning": 0.90, "threshold_critical": 0.80}
            },
            "validation": {
                "method": "holdout",
                "test_size": 0.2,
                "stratify_by": "product_category"
            }
        },
        "lineage": {
            "input_features": ["base_price", "unit_cost", "competitor_avg_price", "demand_elasticity"],
            "output_features": ["optimal_price", "expected_demand", "expected_revenue", "expected_margin"]
        },
        "deployment": {
            "mode": "batch",
            "schedule": "0 3 * * 0",
            "endpoint_spec": None,
            "output_format": "csv"
        },
        "monitoring": {
            "metrics": ["revenue_lift", "margin_impact", "pricing_adherence"],
            "drift": {
                "method": "KS",
                "threshold": 0.05,
                "features": ["demand_elasticity", "competitor_prices"]
            },
            "freshness": {
                "max_age_hours": 168,
                "features": ["price_history", "sales_volume"]
            },
            "alerts": {
                "negative_lift": {"condition": "revenue_lift < 0", "severity": "critical"},
                "elasticity_drift": {"condition": "drift_score > 0.1", "severity": "warning"}
            }
        }
    }
    
    pricing_version = {
        "version_id": "ver_pricing_base_v1",
        "recipe_id": "recipe_pricing_base",
        "version_number": "1.0.0",
        "manifest_json": pricing_manifest,
        "diff_from_prev": None,
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "change_note": "Initial baseline pricing recipe"
    }
    
    pricing_example = {
        "id": "example_pricing_base",
        "recipe_id": "recipe_pricing_base",
        "dataset_schema_json": {
            "columns": [
                {"name": "product_id", "type": "string"},
                {"name": "base_price", "type": "float"},
                {"name": "unit_cost", "type": "float"},
                {"name": "competitor_avg_price", "type": "float"},
                {"name": "demand_elasticity", "type": "float"}
            ]
        },
        "sample_rows_json": [
            {"product_id": "SKU001", "base_price": 29.99, "unit_cost": 15.00, "competitor_avg_price": 31.50, "demand_elasticity": -1.2},
            {"product_id": "SKU002", "base_price": 49.99, "unit_cost": 22.00, "competitor_avg_price": 48.99, "demand_elasticity": -0.9},
            {"product_id": "SKU003", "base_price": 19.99, "unit_cost": 8.50, "competitor_avg_price": 21.99, "demand_elasticity": -1.5}
        ],
        "example_run_json": {
            "stages": ["quality", "elasticity_estimation", "optimization", "evaluation"],
            "sample_metrics": {"revenue_lift": 0.042, "margin_impact": 0.068, "calibration": 0.94},
            "sample_output": {"optimal_price": 32.49, "expected_demand": 850, "expected_revenue": 27616.50}
        },
        "created_at": datetime.utcnow()
    }
    
    # Next Best Action baseline recipe
    nba_recipe = {
        "id": "recipe_nba_base",
        "name": "Next Best Action Baseline v1",
        "model_family": "next_best_action",
        "level": "baseline",
        "status": "approved",
        "parent_id": None,
        "tags": ["baseline", "recommendation", "uplift"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    nba_manifest = {
        "metadata": {
            "id": "recipe_nba_base",
            "name": "Next Best Action Baseline v1",
            "description": "Baseline NBA model using uplift modeling for personalized action recommendations",
            "model_family": "next_best_action",
            "level": "baseline",
            "version": "1.0.0"
        },
        "requirements": {
            "feature_sets": {
                "required": ["customer_profile", "action_history", "engagement_features"],
                "optional": ["external_signals", "seasonality"]
            },
            "grain": "customer-action",
            "labels": ["action_taken", "outcome_value"],
            "min_history": "6 months"
        },
        "pipeline": {
            "stages": [
                {
                    "name": "data_quality",
                    "type": "quality",
                    "checks": ["missing_features", "label_balance", "treatment_control_split"]
                },
                {
                    "name": "feature_engineering",
                    "type": "feature_prep",
                    "transforms": ["propensity_features", "recency_features", "interaction_terms"]
                },
                {
                    "name": "uplift_modeling",
                    "type": "training",
                    "method": "two_model",
                    "algorithms": ["xgboost", "random_forest"],
                    "action_space": ["email_offer", "push_notification", "sms_coupon", "no_action"]
                },
                {
                    "name": "evaluation",
                    "type": "evaluation",
                    "metrics": ["uplift", "precision_at_k", "incremental_revenue", "qini_coefficient"]
                },
                {
                    "name": "deployment",
                    "type": "deployment",
                    "mode": "realtime",
                    "endpoint_type": "rest_api"
                }
            ]
        },
        "evaluation": {
            "metrics": {
                "uplift": {"target": 0.10, "threshold_warning": 0.05, "threshold_critical": 0.00},
                "precision_at_10": {"target": 0.25, "threshold_warning": 0.15, "threshold_critical": 0.10},
                "incremental_revenue": {"target": 50000, "threshold_warning": 25000, "threshold_critical": 0},
                "qini_coefficient": {"target": 0.15, "threshold_warning": 0.08, "threshold_critical": 0.00}
            },
            "validation": {
                "method": "stratified_split",
                "test_size": 0.25,
                "stratify_by": "customer_segment"
            }
        },
        "lineage": {
            "input_features": ["customer_id", "action_id", "propensity_score", "recency_days", "ltv_score"],
            "output_features": ["recommended_action", "expected_uplift", "confidence_score", "rank"]
        },
        "deployment": {
            "mode": "realtime",
            "schedule": None,
            "endpoint_spec": {
                "type": "rest",
                "path": "/api/v1/nba/recommend",
                "timeout_ms": 200
            },
            "output_format": "json"
        },
        "monitoring": {
            "metrics": ["uplift", "action_distribution", "conversion_rate"],
            "drift": {
                "method": "PSI",
                "threshold": 0.15,
                "features": ["propensity_score", "ltv_score"]
            },
            "freshness": {
                "max_age_hours": 24,
                "features": ["customer_profile", "action_history"]
            },
            "alerts": {
                "uplift_degradation": {"condition": "uplift < 0.05", "severity": "critical"},
                "feature_drift": {"condition": "PSI > 0.2", "severity": "warning"}
            }
        }
    }
    
    nba_version = {
        "version_id": "ver_nba_base_v1",
        "recipe_id": "recipe_nba_base",
        "version_number": "1.0.0",
        "manifest_json": nba_manifest,
        "diff_from_prev": None,
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "change_note": "Initial baseline next best action recipe"
    }
    
    nba_example = {
        "id": "example_nba_base",
        "recipe_id": "recipe_nba_base",
        "dataset_schema_json": {
            "columns": [
                {"name": "customer_id", "type": "string"},
                {"name": "action_id", "type": "string"},
                {"name": "propensity_score", "type": "float"},
                {"name": "recency_days", "type": "integer"},
                {"name": "ltv_score", "type": "float"}
            ]
        },
        "sample_rows_json": [
            {"customer_id": "CUST001", "action_id": "email_offer", "propensity_score": 0.65, "recency_days": 14, "ltv_score": 450.0},
            {"customer_id": "CUST002", "action_id": "push_notification", "propensity_score": 0.42, "recency_days": 3, "ltv_score": 320.0},
            {"customer_id": "CUST003", "action_id": "sms_coupon", "propensity_score": 0.78, "recency_days": 7, "ltv_score": 680.0}
        ],
        "example_run_json": {
            "stages": ["quality", "feature_prep", "uplift_modeling", "evaluation"],
            "sample_metrics": {"uplift": 0.125, "precision_at_10": 0.28, "qini_coefficient": 0.17},
            "sample_output": {"recommended_action": "email_offer", "expected_uplift": 0.15, "confidence_score": 0.82}
        },
        "created_at": datetime.utcnow()
    }
    
    # Location Scoring baseline recipe
    location_recipe = {
        "id": "recipe_location_base",
        "name": "Location Scoring Baseline v1",
        "model_family": "location_scoring",
        "level": "baseline",
        "status": "approved",
        "parent_id": None,
        "tags": ["baseline", "geospatial", "site-selection"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    location_manifest = {
        "metadata": {
            "id": "recipe_location_base",
            "name": "Location Scoring Baseline v1",
            "description": "Baseline location scoring model for site selection and store performance prediction",
            "model_family": "location_scoring",
            "level": "baseline",
            "version": "1.0.0"
        },
        "requirements": {
            "feature_sets": {
                "required": ["demographic_features", "trade_area_features", "competition_features"],
                "optional": ["traffic_patterns", "economic_indicators"]
            },
            "grain": "location",
            "labels": ["revenue", "success_indicator"],
            "min_history": "Existing store data"
        },
        "pipeline": {
            "stages": [
                {
                    "name": "data_quality",
                    "type": "quality",
                    "checks": ["coordinate_validity", "demographic_completeness", "outlier_detection"]
                },
                {
                    "name": "trade_area_analysis",
                    "type": "feature_prep",
                    "methods": ["isochrone", "voronoi", "gravity_model"],
                    "radius": "5 miles"
                },
                {
                    "name": "scoring_model",
                    "type": "training",
                    "algorithm": "gradient_boosting",
                    "target": "revenue_potential",
                    "features_importance": True
                },
                {
                    "name": "evaluation",
                    "type": "evaluation",
                    "metrics": ["rank_correlation", "calibration", "hit_rate_at_k", "lift"]
                },
                {
                    "name": "deployment",
                    "type": "deployment",
                    "mode": "batch",
                    "schedule": "on_demand"
                }
            ]
        },
        "evaluation": {
            "metrics": {
                "rank_correlation": {"target": 0.70, "threshold_warning": 0.60, "threshold_critical": 0.50},
                "calibration": {"target": 0.90, "threshold_warning": 0.80, "threshold_critical": 0.70},
                "hit_rate_at_10": {"target": 0.40, "threshold_warning": 0.30, "threshold_critical": 0.20},
                "lift_top_decile": {"target": 2.5, "threshold_warning": 2.0, "threshold_critical": 1.5}
            },
            "validation": {
                "method": "spatial_cv",
                "n_splits": 5,
                "buffer_distance": "10 miles"
            }
        },
        "lineage": {
            "input_features": ["latitude", "longitude", "population_density", "median_income", "competitor_count"],
            "output_features": ["location_score", "revenue_potential", "risk_level", "rank"]
        },
        "deployment": {
            "mode": "batch",
            "schedule": "on_demand",
            "endpoint_spec": None,
            "output_format": "geojson"
        },
        "monitoring": {
            "metrics": ["score_distribution", "realized_vs_predicted", "geographic_coverage"],
            "drift": {
                "method": "KS",
                "threshold": 0.10,
                "features": ["population_density", "median_income"]
            },
            "freshness": {
                "max_age_months": 12,
                "features": ["demographic_features"]
            },
            "alerts": {
                "calibration_degradation": {"condition": "calibration < 0.80", "severity": "warning"},
                "data_outdated": {"condition": "freshness > 12 months", "severity": "warning"}
            }
        }
    }
    
    location_version = {
        "version_id": "ver_location_base_v1",
        "recipe_id": "recipe_location_base",
        "version_number": "1.0.0",
        "manifest_json": location_manifest,
        "diff_from_prev": None,
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "change_note": "Initial baseline location scoring recipe"
    }
    
    location_example = {
        "id": "example_location_base",
        "recipe_id": "recipe_location_base",
        "dataset_schema_json": {
            "columns": [
                {"name": "location_id", "type": "string"},
                {"name": "latitude", "type": "float"},
                {"name": "longitude", "type": "float"},
                {"name": "population_density", "type": "float"},
                {"name": "median_income", "type": "float"},
                {"name": "competitor_count", "type": "integer"}
            ]
        },
        "sample_rows_json": [
            {"location_id": "LOC001", "latitude": 40.7128, "longitude": -74.0060, "population_density": 28000, "median_income": 72000, "competitor_count": 3},
            {"location_id": "LOC002", "latitude": 34.0522, "longitude": -118.2437, "population_density": 19000, "median_income": 68000, "competitor_count": 5},
            {"location_id": "LOC003", "latitude": 41.8781, "longitude": -87.6298, "population_density": 12000, "median_income": 58000, "competitor_count": 2}
        ],
        "example_run_json": {
            "stages": ["quality", "trade_area_analysis", "scoring_model", "evaluation"],
            "sample_metrics": {"rank_correlation": 0.72, "calibration": 0.88, "hit_rate_at_10": 0.42},
            "sample_output": {"location_score": 0.78, "revenue_potential": 2450000, "risk_level": "low"}
        },
        "created_at": datetime.utcnow()
    }
    
    # Insert all data
    with engine.begin() as conn:
        # Insert recipes
        conn.execute(ml_recipe.insert(), [
            forecasting_recipe,
            pricing_recipe,
            nba_recipe,
            location_recipe
        ])
        
        # Insert versions
        conn.execute(ml_recipe_version.insert(), [
            forecasting_version,
            pricing_version,
            nba_version,
            location_version
        ])
        
        # Insert synthetic examples
        conn.execute(ml_synthetic_example.insert(), [
            forecasting_example,
            pricing_example,
            nba_example,
            location_example
        ])
    
    print("✅ Successfully seeded 4 baseline ML recipes!")
    print("   - Forecasting Baseline v1")
    print("   - Pricing Optimization Baseline v1")
    print("   - Next Best Action Baseline v1")
    print("   - Location Scoring Baseline v1")


if __name__ == "__main__":
    seed_recipes()


