"""Add M5-based synthetic examples to existing ML recipes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select, update
from datetime import datetime

from core.config import settings
from db.models import ml_recipe, ml_synthetic_example

# Create engine
engine = create_engine(settings.database_url)


def add_m5_synthetic_examples():
    """Add realistic M5-based synthetic examples to existing recipes."""
    
    print("🌱 Adding M5-based synthetic examples to ML recipes...\n")
    
    with engine.connect() as conn:
        # Get existing recipes
        recipes_result = conn.execute(select(ml_recipe)).fetchall()
        recipes = [dict(row._mapping) for row in recipes_result]
        
        for recipe in recipes:
            print(f"📝 Processing: {recipe['name']}")
            
            if recipe['model_family'] == 'forecasting':
                add_forecasting_example(conn, recipe['id'])
            elif recipe['model_family'] == 'pricing':
                add_pricing_example(conn, recipe['id'])
            elif recipe['model_family'] == 'next_best_action':
                add_nba_example(conn, recipe['id'])
            elif recipe['model_family'] == 'location_scoring':
                add_location_example(conn, recipe['id'])
        
        conn.commit()
        print("\n✨ Successfully added M5 synthetic examples to all recipes!")


def add_forecasting_example(conn, recipe_id: str):
    """Add M5 forecasting example."""
    
    # Check if example already exists
    existing = conn.execute(
        select(ml_synthetic_example).where(
            ml_synthetic_example.c.recipe_id == recipe_id
        )
    ).fetchone()
    
    if existing:
        print(f"   ⏭  Example already exists for {recipe_id}, skipping...")
        return
    
    example_id = f"synth_ex_{recipe_id}"
    
    example_data = {
        "id": example_id,
        "recipe_id": recipe_id,
        "dataset_schema_json": {
            "name": "M5 Forecasting - Walmart Retail Sales",
            "description": "Daily sales data for retail items across multiple stores",
            "source": "M5 Forecasting Competition (Kaggle)",
            "grain": "item_store_day",
            "date_range": "2016-04-01 to 2016-05-15",
            "columns": [
                {"name": "date", "type": "DATE", "description": "Calendar date"},
                {"name": "item_id", "type": "VARCHAR(30)", "description": "Product identifier (e.g., FOODS_1_001)"},
                {"name": "store_id", "type": "VARCHAR(10)", "description": "Store identifier (e.g., CA_1)"},
                {"name": "sales", "type": "INTEGER", "description": "Unit sales for the day"},
                {"name": "sell_price", "type": "NUMERIC(10,2)", "description": "Selling price"},
                {"name": "weekday", "type": "VARCHAR(10)", "description": "Day of week"},
                {"name": "is_weekend", "type": "BOOLEAN", "description": "Weekend indicator"},
                {"name": "event_name", "type": "VARCHAR(50)", "description": "Special event (e.g., Easter, Memorial Day)"},
                {"name": "snap_ca", "type": "INTEGER", "description": "SNAP day indicator for California"}
            ],
            "tables_used": ["m5_sales", "m5_calendar", "m5_items", "m5_prices"]
        },
        "sample_rows_json": [
            {
                "date": "2016-04-01",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 12,
                "sell_price": 3.97,
                "weekday": "Friday",
                "is_weekend": False,
                "event_name": None,
                "snap_ca": 0
            },
            {
                "date": "2016-04-02",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 18,
                "sell_price": 3.97,
                "weekday": "Saturday",
                "is_weekend": True,
                "event_name": None,
                "snap_ca": 1
            },
            {
                "date": "2016-04-03",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 15,
                "sell_price": 3.97,
                "weekday": "Sunday",
                "is_weekend": True,
                "event_name": "Easter",
                "snap_ca": 1
            },
            {
                "date": "2016-04-04",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 8,
                "sell_price": 3.97,
                "weekday": "Monday",
                "is_weekend": False,
                "event_name": None,
                "snap_ca": 0
            },
            {
                "date": "2016-04-05",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 9,
                "sell_price": 3.97,
                "weekday": "Tuesday",
                "is_weekend": False,
                "event_name": None,
                "snap_ca": 0
            },
            {
                "date": "2016-04-06",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 11,
                "sell_price": 4.29,
                "weekday": "Wednesday",
                "is_weekend": False,
                "event_name": None,
                "snap_ca": 0
            },
            {
                "date": "2016-04-07",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 10,
                "sell_price": 4.29,
                "weekday": "Thursday",
                "is_weekend": False,
                "event_name": None,
                "snap_ca": 0
            },
            {
                "date": "2016-04-08",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 14,
                "sell_price": 4.29,
                "weekday": "Friday",
                "is_weekend": False,
                "event_name": None,
                "snap_ca": 0
            },
            {
                "date": "2016-04-09",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 19,
                "sell_price": 4.29,
                "weekday": "Saturday",
                "is_weekend": True,
                "event_name": None,
                "snap_ca": 1
            },
            {
                "date": "2016-04-10",
                "item_id": "FOODS_1_001",
                "store_id": "CA_1",
                "sales": 16,
                "sell_price": 4.29,
                "weekday": "Sunday",
                "is_weekend": True,
                "event_name": None,
                "snap_ca": 1
            }
        ],
        "example_run_json": {
            "description": "Forecast daily sales for FOODS_1_001 at store CA_1 (28-day horizon)",
            "training_period": "2015-01-29 to 2016-03-31 (14 months)",
            "forecast_period": "2016-04-01 to 2016-04-28 (28 days)",
            "features_used": [
                "lag_7d", "lag_14d", "lag_28d",
                "rolling_avg_7d", "rolling_avg_28d",
                "price", "price_change",
                "day_of_week", "is_weekend",
                "is_event_day", "is_snap_day"
            ],
            "expected_metrics": {
                "MAPE": 0.18,
                "RMSE": 2.4,
                "MAE": 1.9,
                "forecast_bias": 0.03,
                "coverage_80": 0.82
            },
            "data_access": {
                "query_template": "SELECT s.*, c.*, p.sell_price FROM m5_sales s JOIN m5_calendar c ON s.d = c.d JOIN m5_prices p ON s.item_id = p.item_id AND s.store_id = p.store_id AND c.wm_yr_wk = p.wm_yr_wk WHERE s.item_store_id = 'FOODS_1_001_CA_1' ORDER BY c.date"
            }
        },
        "created_at": datetime.utcnow()
    }
    
    conn.execute(ml_synthetic_example.insert().values(**example_data))
    print(f"   ✓ Added M5 forecasting example")


def add_pricing_example(conn, recipe_id: str):
    """Add M5 pricing/elasticity example."""
    
    existing = conn.execute(
        select(ml_synthetic_example).where(
            ml_synthetic_example.c.recipe_id == recipe_id
        )
    ).fetchone()
    
    if existing:
        print(f"   ⏭  Example already exists for {recipe_id}, skipping...")
        return
    
    example_id = f"synth_ex_{recipe_id}"
    
    example_data = {
        "id": example_id,
        "recipe_id": recipe_id,
        "dataset_schema_json": {
            "name": "M5 Price Elasticity Analysis",
            "description": "Price-demand data for analyzing price elasticity",
            "source": "M5 Forecasting Competition - Price Data",
            "grain": "item_store_week",
            "columns": [
                {"name": "wm_yr_wk", "type": "INTEGER", "description": "Walmart year-week"},
                {"name": "item_id", "type": "VARCHAR(30)", "description": "Product identifier"},
                {"name": "store_id", "type": "VARCHAR(10)", "description": "Store identifier"},
                {"name": "sell_price", "type": "NUMERIC(10,2)", "description": "Selling price for the week"},
                {"name": "avg_daily_sales", "type": "NUMERIC(10,2)", "description": "Average daily sales during week"},
                {"name": "price_change_pct", "type": "NUMERIC(10,2)", "description": "% change from previous week"},
                {"name": "demand_change_pct", "type": "NUMERIC(10,2)", "description": "% change in demand"}
            ],
            "tables_used": ["m5_prices", "m5_sales", "m5_calendar"]
        },
        "sample_rows_json": [
            {"wm_yr_wk": 11601, "item_id": "FOODS_1_001", "store_id": "CA_1", "sell_price": 3.97, "avg_daily_sales": 11.2, "price_change_pct": 0.0, "demand_change_pct": 2.1},
            {"wm_yr_wk": 11602, "item_id": "FOODS_1_001", "store_id": "CA_1", "sell_price": 3.97, "avg_daily_sales": 10.8, "price_change_pct": 0.0, "demand_change_pct": -3.6},
            {"wm_yr_wk": 11603, "item_id": "FOODS_1_001", "store_id": "CA_1", "sell_price": 4.29, "avg_daily_sales": 8.3, "price_change_pct": 8.1, "demand_change_pct": -23.1},
            {"wm_yr_wk": 11604, "item_id": "FOODS_1_001", "store_id": "CA_1", "sell_price": 4.29, "avg_daily_sales": 8.7, "price_change_pct": 0.0, "demand_change_pct": 4.8},
            {"wm_yr_wk": 11605, "item_id": "FOODS_1_001", "store_id": "CA_1", "sell_price": 3.97, "avg_daily_sales": 12.1, "price_change_pct": -7.5, "demand_change_pct": 39.1},
            {"wm_yr_wk": 11606, "item_id": "FOODS_1_001", "store_id": "CA_1", "sell_price": 3.97, "avg_daily_sales": 11.5, "price_change_pct": 0.0, "demand_change_pct": -5.0}
        ],
        "example_run_json": {
            "description": "Estimate price elasticity for FOODS_1_001 across stores",
            "analysis_period": "52 weeks",
            "expected_metrics": {
                "elasticity_coefficient": -1.82,
                "revenue_lift": 0.034,
                "optimal_price": 4.15,
                "current_price": 3.97,
                "recommended_action": "increase"
            },
            "interpretation": "Product is elastic (elasticity < -1). A price increase of 4.5% is expected to increase revenue by 3.4%"
        },
        "created_at": datetime.utcnow()
    }
    
    conn.execute(ml_synthetic_example.insert().values(**example_data))
    print(f"   ✓ Added M5 pricing example")


def add_nba_example(conn, recipe_id: str):
    """Add NBA example (generic - not M5 specific)."""
    
    existing = conn.execute(
        select(ml_synthetic_example).where(
            ml_synthetic_example.c.recipe_id == recipe_id
        )
    ).fetchone()
    
    if existing:
        print(f"   ⏭  Example already exists for {recipe_id}, skipping...")
        return
    
    example_id = f"synth_ex_{recipe_id}"
    
    example_data = {
        "id": example_id,
        "recipe_id": recipe_id,
        "dataset_schema_json": {
            "name": "Customer Action Propensity",
            "description": "Customer response to marketing actions",
            "source": "Synthetic - Marketing Campaign Data",
            "grain": "customer_day",
            "columns": [
                {"name": "customer_id", "type": "VARCHAR(50)", "description": "Customer identifier"},
                {"name": "date", "type": "DATE", "description": "Date"},
                {"name": "action_type", "type": "VARCHAR(20)", "description": "Recommended action (email, push, offer)"},
                {"name": "did_convert", "type": "BOOLEAN", "description": "Customer converted"},
                {"name": "revenue", "type": "NUMERIC(10,2)", "description": "Revenue generated"}
            ]
        },
        "sample_rows_json": [
            {"customer_id": "C001", "date": "2024-01-01", "action_type": "email", "did_convert": True, "revenue": 45.99},
            {"customer_id": "C002", "date": "2024-01-01", "action_type": "push", "did_convert": False, "revenue": 0.0}
        ],
        "example_run_json": {
            "description": "Predict optimal action per customer",
            "expected_metrics": {
                "uplift": 0.12,
                "precision_at_10": 0.32,
                "incremental_revenue": 125000
            }
        },
        "created_at": datetime.utcnow()
    }
    
    conn.execute(ml_synthetic_example.insert().values(**example_data))
    print(f"   ✓ Added NBA example")


def add_location_example(conn, recipe_id: str):
    """Add location scoring example (generic - not M5 specific)."""
    
    existing = conn.execute(
        select(ml_synthetic_example).where(
            ml_synthetic_example.c.recipe_id == recipe_id
        )
    ).fetchone()
    
    if existing:
        print(f"   ⏭  Example already exists for {recipe_id}, skipping...")
        return
    
    example_id = f"synth_ex_{recipe_id}"
    
    example_data = {
        "id": example_id,
        "recipe_id": recipe_id,
        "dataset_schema_json": {
            "name": "Store Location Analysis",
            "description": "Demographic and performance data for store locations",
            "source": "Synthetic - Retail Site Selection",
            "grain": "location",
            "columns": [
                {"name": "location_id", "type": "VARCHAR(50)", "description": "Location identifier"},
                {"name": "latitude", "type": "NUMERIC(10,6)", "description": "Latitude"},
                {"name": "longitude", "type": "NUMERIC(10,6)", "description": "Longitude"},
                {"name": "population_density", "type": "INTEGER", "description": "People per sq mile"},
                {"name": "median_income", "type": "INTEGER", "description": "Median household income"},
                {"name": "competitor_count", "type": "INTEGER", "description": "Number of competitors within 5 miles"}
            ]
        },
        "sample_rows_json": [
            {"location_id": "LOC001", "latitude": 34.0522, "longitude": -118.2437, "population_density": 8500, "median_income": 68000, "competitor_count": 3},
            {"location_id": "LOC002", "latitude": 36.1699, "longitude": -115.1398, "population_density": 4500, "median_income": 55000, "competitor_count": 1}
        ],
        "example_run_json": {
            "description": "Score potential store locations",
            "expected_metrics": {
                "rank_correlation": 0.78,
                "hit_rate_at_10": 0.45,
                "lift_top_decile": 2.3
            }
        },
        "created_at": datetime.utcnow()
    }
    
    conn.execute(ml_synthetic_example.insert().values(**example_data))
    print(f"   ✓ Added location scoring example")


if __name__ == "__main__":
    add_m5_synthetic_examples()
