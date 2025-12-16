"""Seed baseline evaluation packs for all model families."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from datetime import datetime
from uuid import uuid4

from core.config import settings
from db.models import evaluation_pack, evaluation_pack_version

# Create engine
engine = create_engine(settings.database_url)


def seed_evaluation_packs():
    """Seed baseline evaluation packs for all 4 model families."""
    
    # 1. Forecasting Evaluation Pack
    forecasting_pack = {
        "id": "pack_forecasting_standard",
        "name": "Forecasting Standard Evaluation v1",
        "model_family": "forecasting",
        "status": "approved",
        "tags": ["standard", "time-series", "baseline"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    forecasting_pack_json = {
        "id": "pack_forecasting_standard",
        "name": "Forecasting Standard Evaluation v1",
        "model_family": "forecasting",
        "description": "Standard evaluation pack for forecasting models measuring accuracy, bias, and coverage",
        "metrics": [
            {
                "key": "MAPE",
                "display_name": "Mean Absolute Percentage Error",
                "compute": "MAPE",
                "thresholds": {
                    "promote": 0.15,
                    "warn": 0.25,
                    "fail": 0.40
                },
                "direction": "lower_is_better"
            },
            {
                "key": "RMSE",
                "display_name": "Root Mean Squared Error",
                "compute": "RMSE",
                "thresholds": {
                    "promote": 50.0,
                    "warn": 100.0,
                    "fail": 200.0
                },
                "direction": "lower_is_better"
            },
            {
                "key": "MAE",
                "display_name": "Mean Absolute Error",
                "compute": "MAE",
                "thresholds": {
                    "promote": 30.0,
                    "warn": 60.0,
                    "fail": 120.0
                },
                "direction": "lower_is_better"
            },
            {
                "key": "forecast_bias",
                "display_name": "Forecast Bias",
                "compute": "forecast_bias",
                "thresholds": {
                    "promote": 0.05,
                    "warn": 0.15,
                    "fail": 0.30
                },
                "direction": "lower_is_better"
            },
            {
                "key": "coverage_80",
                "display_name": "80% Prediction Interval Coverage",
                "compute": "coverage",
                "thresholds": {
                    "promote": 0.75,
                    "warn": 0.65,
                    "fail": 0.50
                },
                "direction": "higher_is_better"
            }
        ],
        "slices": [
            {"dimension": "product_category", "values": None},
            {"dimension": "region", "values": None}
        ],
        "comparators": [
            {"type": "baseline", "reference_id": "naive_forecast"},
            {"type": "prior_model", "reference_id": None}
        ],
        "economic_mapping": [
            {
                "metric_key": "MAPE",
                "dollar_per_unit": 10000,
                "unit_label": "$/percentage point MAPE improvement"
            }
        ],
        "outputs": {
            "artifacts": ["forecast_plot", "residuals_plot", "seasonality_chart"],
            "reports": ["pdf_summary", "html_dashboard"]
        }
    }
    
    forecasting_version = {
        "version_id": "ver_pack_forecasting_standard_v1",
        "pack_id": "pack_forecasting_standard",
        "version_number": "1.0.0",
        "pack_json": forecasting_pack_json,
        "diff_from_prev": None,
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "change_note": "Initial baseline forecasting evaluation pack"
    }
    
    # 2. Pricing Evaluation Pack
    pricing_pack = {
        "id": "pack_pricing_standard",
        "name": "Pricing Standard Evaluation v1",
        "model_family": "pricing",
        "status": "approved",
        "tags": ["standard", "optimization", "baseline"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    pricing_pack_json = {
        "id": "pack_pricing_standard",
        "name": "Pricing Standard Evaluation v1",
        "model_family": "pricing",
        "description": "Standard evaluation pack for pricing models measuring lift, calibration, and elasticity accuracy",
        "metrics": [
            {
                "key": "revenue_lift",
                "display_name": "Revenue Lift %",
                "compute": "revenue_lift",
                "thresholds": {
                    "promote": 0.03,
                    "warn": 0.01,
                    "fail": -0.01
                },
                "direction": "higher_is_better"
            },
            {
                "key": "margin_impact",
                "display_name": "Margin Impact %",
                "compute": "margin_impact",
                "thresholds": {
                    "promote": 0.05,
                    "warn": 0.02,
                    "fail": 0.00
                },
                "direction": "higher_is_better"
            },
            {
                "key": "elasticity_accuracy",
                "display_name": "Elasticity Prediction Accuracy",
                "compute": "elasticity_mae",
                "thresholds": {
                    "promote": 0.15,
                    "warn": 0.30,
                    "fail": 0.50
                },
                "direction": "lower_is_better"
            },
            {
                "key": "calibration",
                "display_name": "Demand Forecast Calibration",
                "compute": "calibration",
                "thresholds": {
                    "promote": 0.95,
                    "warn": 0.85,
                    "fail": 0.70
                },
                "direction": "higher_is_better"
            },
            {
                "key": "constraint_violations",
                "display_name": "Price Constraint Violations",
                "compute": "constraint_violations",
                "thresholds": {
                    "promote": 0.00,
                    "warn": 0.02,
                    "fail": 0.10
                },
                "direction": "lower_is_better"
            }
        ],
        "slices": [
            {"dimension": "product_tier", "values": ["premium", "standard", "value"]},
            {"dimension": "market_segment", "values": None}
        ],
        "comparators": [
            {"type": "baseline", "reference_id": "current_pricing"},
            {"type": "rules_engine", "reference_id": "legacy_pricing_rules"}
        ],
        "economic_mapping": [
            {
                "metric_key": "revenue_lift",
                "dollar_per_unit": 1000000,
                "unit_label": "$/percentage point revenue lift"
            },
            {
                "metric_key": "margin_impact",
                "dollar_per_unit": 500000,
                "unit_label": "$/percentage point margin improvement"
            }
        ],
        "outputs": {
            "artifacts": ["price_response_curves", "elasticity_heatmap", "lift_by_segment"],
            "reports": ["pricing_strategy_summary", "a_b_test_recommendations"]
        }
    }
    
    pricing_version = {
        "version_id": "ver_pack_pricing_standard_v1",
        "pack_id": "pack_pricing_standard",
        "version_number": "1.0.0",
        "pack_json": pricing_pack_json,
        "diff_from_prev": None,
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "change_note": "Initial baseline pricing evaluation pack"
    }
    
    # 3. Next Best Action Evaluation Pack
    nba_pack = {
        "id": "pack_nba_standard",
        "name": "NBA Standard Evaluation v1",
        "model_family": "next_best_action",
        "status": "approved",
        "tags": ["standard", "uplift", "personalization", "baseline"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    nba_pack_json = {
        "id": "pack_nba_standard",
        "name": "NBA Standard Evaluation v1",
        "model_family": "next_best_action",
        "description": "Standard evaluation pack for NBA models measuring uplift, precision, and incremental value",
        "metrics": [
            {
                "key": "uplift",
                "display_name": "Average Treatment Effect (Uplift)",
                "compute": "uplift",
                "thresholds": {
                    "promote": 0.10,
                    "warn": 0.05,
                    "fail": 0.00
                },
                "direction": "higher_is_better"
            },
            {
                "key": "precision_at_10",
                "display_name": "Precision @ Top 10%",
                "compute": "precision_at_k",
                "thresholds": {
                    "promote": 0.30,
                    "warn": 0.20,
                    "fail": 0.10
                },
                "direction": "higher_is_better"
            },
            {
                "key": "qini_coefficient",
                "display_name": "Qini Coefficient",
                "compute": "qini",
                "thresholds": {
                    "promote": 0.15,
                    "warn": 0.08,
                    "fail": 0.00
                },
                "direction": "higher_is_better"
            },
            {
                "key": "incremental_revenue",
                "display_name": "Incremental Revenue ($)",
                "compute": "incremental_revenue",
                "thresholds": {
                    "promote": 100000,
                    "warn": 50000,
                    "fail": 0
                },
                "direction": "higher_is_better"
            },
            {
                "key": "action_distribution",
                "display_name": "Action Distribution Balance",
                "compute": "action_entropy",
                "thresholds": {
                    "promote": 0.70,
                    "warn": 0.50,
                    "fail": 0.30
                },
                "direction": "higher_is_better"
            }
        ],
        "slices": [
            {"dimension": "customer_segment", "values": ["high_value", "medium_value", "low_value"]},
            {"dimension": "action_type", "values": ["email", "push", "sms", "offer"]}
        ],
        "comparators": [
            {"type": "baseline", "reference_id": "random_assignment"},
            {"type": "rules_engine", "reference_id": "legacy_campaign_rules"}
        ],
        "economic_mapping": [
            {
                "metric_key": "uplift",
                "dollar_per_unit": 200000,
                "unit_label": "$/percentage point uplift"
            },
            {
                "metric_key": "incremental_revenue",
                "dollar_per_unit": 1,
                "unit_label": "direct revenue"
            }
        ],
        "outputs": {
            "artifacts": ["uplift_curve", "qini_curve", "action_distribution_chart", "segment_performance"],
            "reports": ["campaign_optimization_report", "holdout_analysis"]
        }
    }
    
    nba_version = {
        "version_id": "ver_pack_nba_standard_v1",
        "pack_id": "pack_nba_standard",
        "version_number": "1.0.0",
        "pack_json": nba_pack_json,
        "diff_from_prev": None,
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "change_note": "Initial baseline NBA evaluation pack"
    }
    
    # 4. Location Scoring Evaluation Pack
    location_pack = {
        "id": "pack_location_standard",
        "name": "Location Scoring Standard Evaluation v1",
        "model_family": "location_scoring",
        "status": "approved",
        "tags": ["standard", "geospatial", "site-selection", "baseline"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    location_pack_json = {
        "id": "pack_location_standard",
        "name": "Location Scoring Standard Evaluation v1",
        "model_family": "location_scoring",
        "description": "Standard evaluation pack for location scoring models measuring rank accuracy, calibration, and hit rate",
        "metrics": [
            {
                "key": "rank_correlation",
                "display_name": "Rank Correlation (Spearman)",
                "compute": "spearman_correlation",
                "thresholds": {
                    "promote": 0.75,
                    "warn": 0.60,
                    "fail": 0.45
                },
                "direction": "higher_is_better"
            },
            {
                "key": "calibration",
                "display_name": "Score Calibration",
                "compute": "calibration",
                "thresholds": {
                    "promote": 0.90,
                    "warn": 0.75,
                    "fail": 0.60
                },
                "direction": "higher_is_better"
            },
            {
                "key": "hit_rate_at_10",
                "display_name": "Hit Rate @ Top 10",
                "compute": "hit_rate_at_k",
                "thresholds": {
                    "promote": 0.50,
                    "warn": 0.35,
                    "fail": 0.20
                },
                "direction": "higher_is_better"
            },
            {
                "key": "lift_top_decile",
                "display_name": "Revenue Lift in Top Decile",
                "compute": "lift",
                "thresholds": {
                    "promote": 2.5,
                    "warn": 1.8,
                    "fail": 1.2
                },
                "direction": "higher_is_better"
            },
            {
                "key": "geographic_coverage",
                "display_name": "Geographic Coverage",
                "compute": "coverage",
                "thresholds": {
                    "promote": 0.90,
                    "warn": 0.75,
                    "fail": 0.50
                },
                "direction": "higher_is_better"
            }
        ],
        "slices": [
            {"dimension": "market_type", "values": ["urban", "suburban", "rural"]},
            {"dimension": "store_format", "values": None}
        ],
        "comparators": [
            {"type": "baseline", "reference_id": "population_density_only"},
            {"type": "prior_model", "reference_id": None}
        ],
        "economic_mapping": [
            {
                "metric_key": "lift_top_decile",
                "dollar_per_unit": 2000000,
                "unit_label": "$/lift unit per location"
            }
        ],
        "outputs": {
            "artifacts": ["location_heatmap", "feature_importance_map", "trade_area_visualization"],
            "reports": ["site_selection_recommendations", "market_penetration_analysis"]
        }
    }
    
    location_version = {
        "version_id": "ver_pack_location_standard_v1",
        "pack_id": "pack_location_standard",
        "version_number": "1.0.0",
        "pack_json": location_pack_json,
        "diff_from_prev": None,
        "created_by": "system",
        "created_at": datetime.utcnow(),
        "change_note": "Initial baseline location scoring evaluation pack"
    }
    
    # Insert into database
    with engine.connect() as conn:
        # Insert packs
        conn.execute(
            evaluation_pack.insert(),
            [forecasting_pack, pricing_pack, nba_pack, location_pack]
        )
        
        # Insert versions
        conn.execute(
            evaluation_pack_version.insert(),
            [forecasting_version, pricing_version, nba_version, location_version]
        )
        
        conn.commit()
        
        print("✓ Successfully seeded 4 evaluation packs:")
        print("  - Forecasting Standard Evaluation v1")
        print("  - Pricing Standard Evaluation v1")
        print("  - NBA Standard Evaluation v1")
        print("  - Location Scoring Standard Evaluation v1")


if __name__ == "__main__":
    seed_evaluation_packs()

