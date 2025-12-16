"""Update existing ML recipes with reference_repos."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from datetime import datetime
import json

from core.config import settings

# Create engine
engine = create_engine(settings.database_url)

# Reference repos for each model family
reference_repos_by_family = {
    "forecasting": [
        {
            "name": "facebook/prophet",
            "url": "https://github.com/facebook/prophet",
            "description": "Facebook's production-ready forecasting framework with automatic seasonality detection",
            "language": "Python",
            "framework": "Prophet",
            "stars": "18.2k",
            "tags": ["time-series", "forecasting", "seasonality", "production"]
        },
        {
            "name": "sktime/sktime",
            "url": "https://github.com/sktime/sktime",
            "description": "Unified framework for time series machine learning with scikit-learn compatible API",
            "language": "Python",
            "framework": "scikit-learn",
            "stars": "7.8k",
            "tags": ["time-series", "sklearn", "forecasting", "ml"]
        },
        {
            "name": "Nixtla/statsforecast",
            "url": "https://github.com/Nixtla/statsforecast",
            "description": "Lightning fast statistical forecasting with GPU support and AutoML",
            "language": "Python",
            "framework": "NumPy",
            "stars": "3.9k",
            "tags": ["forecasting", "automl", "gpu", "fast"]
        },
        {
            "name": "awslabs/gluonts",
            "url": "https://github.com/awslabs/gluonts",
            "description": "AWS deep learning toolkit for probabilistic time series forecasting",
            "language": "Python",
            "framework": "PyTorch",
            "stars": "4.5k",
            "tags": ["deep-learning", "probabilistic", "time-series", "aws"]
        }
    ],
    "pricing": [
        {
            "name": "uber/orbit",
            "url": "https://github.com/uber/orbit",
            "description": "Uber's Bayesian forecasting framework for time series and causal inference",
            "language": "Python",
            "framework": "PyTorch",
            "stars": "1.9k",
            "tags": ["bayesian", "causal-inference", "pricing", "elasticity"]
        },
        {
            "name": "microsoft/EconML",
            "url": "https://github.com/microsoft/EconML",
            "description": "Python package for estimating heterogeneous treatment effects from observational data",
            "language": "Python",
            "framework": "scikit-learn",
            "stars": "3.2k",
            "tags": ["causal-inference", "treatment-effects", "pricing", "economics"]
        },
        {
            "name": "py-why/dowhy",
            "url": "https://github.com/py-why/dowhy",
            "description": "Python library for causal inference that supports explicit modeling and testing of assumptions",
            "language": "Python",
            "framework": "NumPy",
            "stars": "7.1k",
            "tags": ["causal-inference", "elasticity", "optimization"]
        },
        {
            "name": "facebookresearch/Ax",
            "url": "https://github.com/facebookresearch/Ax",
            "description": "Adaptive experimentation platform for Bayesian optimization and A/B testing",
            "language": "Python",
            "framework": "PyTorch",
            "stars": "2.4k",
            "tags": ["optimization", "bayesian", "experimentation", "pricing"]
        }
    ],
    "next_best_action": [
        {
            "name": "uber/causalml",
            "url": "https://github.com/uber/causalml",
            "description": "Uber's Python package for uplift modeling and causal inference with ML",
            "language": "Python",
            "framework": "scikit-learn",
            "stars": "5.1k",
            "tags": ["uplift-modeling", "causal-inference", "ml", "treatment-effects"]
        },
        {
            "name": "spotify/confidence",
            "url": "https://github.com/spotify/confidence",
            "description": "Spotify's library for reliable A/B testing and personalization experimentation",
            "language": "Python",
            "framework": "Pandas",
            "stars": "800",
            "tags": ["ab-testing", "experimentation", "personalization"]
        },
        {
            "name": "microsoft/recommenders",
            "url": "https://github.com/microsoft/recommenders",
            "description": "Best practices for building recommendation systems by Microsoft",
            "language": "Python",
            "framework": "TensorFlow",
            "stars": "19.2k",
            "tags": ["recommendation", "deep-learning", "personalization", "nba"]
        },
        {
            "name": "criteo/deepr",
            "url": "https://github.com/criteo/deepr",
            "description": "Criteo's framework for deep learning on Hadoop/Spark for recommender systems",
            "language": "Python",
            "framework": "TensorFlow",
            "stars": "280",
            "tags": ["deep-learning", "recommendation", "big-data", "spark"]
        }
    ],
    "location_scoring": [
        {
            "name": "gboeing/osmnx",
            "url": "https://github.com/gboeing/osmnx",
            "description": "Download, analyze, and visualize street networks and geospatial data from OpenStreetMap",
            "language": "Python",
            "framework": "NetworkX",
            "stars": "4.8k",
            "tags": ["geospatial", "openstreetmap", "network-analysis", "gis"]
        },
        {
            "name": "ResidentMario/geoplot",
            "url": "https://github.com/ResidentMario/geoplot",
            "description": "High-level Python geospatial plotting library built on top of matplotlib",
            "language": "Python",
            "framework": "Matplotlib",
            "stars": "1.1k",
            "tags": ["geospatial", "visualization", "mapping"]
        },
        {
            "name": "spatial-data-discovery/retail-analytics",
            "url": "https://github.com/microsoft/MLOps",
            "description": "Best practices for MLOps including geospatial model deployment patterns",
            "language": "Python",
            "framework": "Azure ML",
            "stars": "3.6k",
            "tags": ["mlops", "geospatial", "deployment", "site-selection"]
        },
        {
            "name": "geopy/geopy",
            "url": "https://github.com/geopy/geopy",
            "description": "Geocoding library for Python with support for multiple geocoding services",
            "language": "Python",
            "framework": "Requests",
            "stars": "4.4k",
            "tags": ["geocoding", "geospatial", "location", "mapping"]
        },
        {
            "name": "pysal/pysal",
            "url": "https://github.com/pysal/pysal",
            "description": "Python Spatial Analysis Library for spatial econometrics and statistics",
            "language": "Python",
            "framework": "NumPy",
            "stars": "1.4k",
            "tags": ["spatial-analysis", "econometrics", "gis", "statistics"]
        }
    ]
}

def update_recipes():
    """Update all recipe versions with reference_repos."""
    
    with engine.connect() as conn:
        # Get all recipe versions
        result = conn.execute(text("""
            SELECT rv.version_id, rv.recipe_id, rv.manifest_json, r.model_family
            FROM ml_recipe_version rv
            JOIN ml_recipe r ON rv.recipe_id = r.id
        """))
        
        versions = result.fetchall()
        
        for version in versions:
            version_id, recipe_id, manifest_json, model_family = version
            
            # Add reference_repos to manifest if not already present
            if 'reference_repos' not in manifest_json and model_family in reference_repos_by_family:
                manifest_json['reference_repos'] = reference_repos_by_family[model_family]
                
                # Update the version
                conn.execute(
                    text("""
                        UPDATE ml_recipe_version 
                        SET manifest_json = CAST(:manifest_json AS jsonb)
                        WHERE version_id = :version_id
                    """),
                    {"manifest_json": json.dumps(manifest_json), "version_id": version_id}
                )
                
                print(f"✓ Updated {recipe_id} version {version_id} with {len(manifest_json['reference_repos'])} reference repos")
            else:
                print(f"- Skipped {recipe_id} (already has reference_repos or unknown family)")
        
        conn.commit()
        print(f"\n✓ Successfully updated {len(versions)} recipe versions")

if __name__ == "__main__":
    update_recipes()

