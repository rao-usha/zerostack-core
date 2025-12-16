from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, accuracy_score
import io
from datetime import datetime
from pathlib import Path

from services.synthetic_data import SyntheticDataGenerator
from services.insights import InsightsGenerator
from services.chat import ChatService
from services.data_quality import DataQualityAnalyzer
from services.knowledge_gaps import KnowledgeGapIdentifier
from database import Database

# Domain routers
from domains.connectors.router import router as connectors_router
from domains.context.router import router as context_router
from domains.contexts.router import router as contexts_router
from domains.personas.router import router as personas_router
from domains.mcp.router import router as mcp_router
from domains.datasets.router import router as datasets_router
from domains.evaluations.router import router as evaluations_router
from domains.governance.router import router as governance_router
from domains.auth.router import router as auth_router
from domains.jobs.router import router as jobs_router
from domains.insights.router import router as insights_router
from domains.data_explorer.router import router as data_explorer_router
from domains.data_explorer.ai_router import router as data_explorer_ai_router
from domains.data_explorer.jobs_router import router as data_analysis_router
from domains.data_explorer.models_router import router as ai_models_router
from domains.data_explorer.prompt_recipes_router import router as prompt_recipes_router
from domains.data_explorer.dictionary_router import router as data_dictionary_router
from domains.data_explorer.dictionary_enhanced_router import router as dictionary_enhanced_router
from domains.chat.router import router as chat_router
from domains.ml_development.router import router as ml_development_router
from domains.evaluation_packs.router import router as evaluation_packs_router

# Core setup
from core.config import settings
from core.logging import setup_logging

# Setup logging
setup_logging()

app = FastAPI(title=settings.app_name, version=settings.app_version)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include domain routers
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(connectors_router, prefix=settings.api_prefix)
app.include_router(context_router, prefix=settings.api_prefix)
app.include_router(contexts_router, prefix=settings.api_prefix)
app.include_router(personas_router, prefix=settings.api_prefix)
app.include_router(mcp_router, prefix=settings.api_prefix)
app.include_router(datasets_router, prefix=settings.api_prefix)
app.include_router(evaluations_router, prefix=settings.api_prefix)
app.include_router(governance_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)
app.include_router(insights_router, prefix=settings.api_prefix)
app.include_router(data_explorer_router, prefix=settings.api_prefix)
app.include_router(data_explorer_ai_router, prefix=settings.api_prefix)
app.include_router(data_analysis_router, prefix=settings.api_prefix)
app.include_router(ai_models_router, prefix=settings.api_prefix)
app.include_router(prompt_recipes_router)
app.include_router(data_dictionary_router, prefix=settings.api_prefix)
app.include_router(dictionary_enhanced_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(ml_development_router, prefix=settings.api_prefix)
app.include_router(evaluation_packs_router, prefix=settings.api_prefix)

# Initialize services
db = Database()
synthetic_gen = SyntheticDataGenerator()
insights_gen = InsightsGenerator()
chat_service = ChatService()
quality_analyzer = DataQualityAnalyzer()
gap_identifier = KnowledgeGapIdentifier()

# Data storage directory
DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    return {"message": "NEX.AI - AI Native Data Platform API", "status": "running"}

@app.get("/health/config")
async def health_config():
    """Check configuration, especially OpenAI API key status."""
    from core.config import settings
    import os
    
    has_settings_key = bool(settings.openai_api_key)
    has_env_key = bool(os.environ.get('OPENAI_API_KEY'))
    
    return {
        "openai_api_key_configured": has_settings_key or has_env_key,
        "from_settings": has_settings_key,
        "from_env": has_env_key,
        "key_preview": (
            settings.openai_api_key[:10] + "..." if settings.openai_api_key 
            else (os.environ.get('OPENAI_API_KEY', '')[:10] + "..." if os.environ.get('OPENAI_API_KEY') else None)
        )
    }


@app.get("/health")
async def health():
    """Health check endpoint with database connectivity."""
    from sqlalchemy import create_engine, text
    from core.config import settings
    
    health_status = {
        "status": "healthy",
        "service": "NEX.AI API",
        "database": "unknown"
    }
    
    try:
        # Test database connection
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database"] = f"error: {str(e)}"
    
    return health_status


@app.post("/api/upload")
async def upload_data(file: UploadFile = File(...)):
    """Upload and store dataset"""
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Store dataset
        dataset_id = db.save_dataset(file.filename, df)
        
        return {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": df.columns.tolist(),
            "message": "Dataset uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/datasets")
async def list_datasets():
    """List all uploaded datasets"""
    return db.get_all_datasets()


@app.get("/api/dataset/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get dataset preview"""
    try:
        dataset = db.get_dataset(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = pd.read_json(dataset['data'], orient='records')
        
        return {
            "dataset_id": dataset_id,
            "filename": dataset['filename'],
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": df.columns.tolist(),
            "preview": df.head(100).to_dict(orient='records'),
            "dtypes": df.dtypes.astype(str).to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/synthetic/generate")
async def generate_synthetic(request: Dict[str, Any]):
    """Generate synthetic data from sample dataset"""
    try:
        dataset_id = request.get("dataset_id")
        num_rows = request.get("num_rows", 1000)
        
        dataset = db.get_dataset(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = pd.read_json(dataset['data'], orient='records')
        synthetic_df = synthetic_gen.generate(df, num_rows)
        
        # Store synthetic dataset
        synthetic_id = db.save_dataset(f"synthetic_{dataset['filename']}", synthetic_df)
        
        return {
            "synthetic_dataset_id": synthetic_id,
            "original_dataset_id": dataset_id,
            "num_rows": len(synthetic_df),
            "columns": synthetic_df.columns.tolist(),
            "preview": synthetic_df.head(50).to_dict(orient='records')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/models/predictive")
async def build_predictive_model(request: Dict[str, Any]):
    """Build predictive model"""
    try:
        dataset_id = request.get("dataset_id")
        target_column = request.get("target_column")
        model_type = request.get("model_type", "regression")  # regression or classification
        
        dataset = db.get_dataset(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = pd.read_json(dataset['data'], orient='records')
        
        if target_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Target column {target_column} not found")
        
        # Prepare data
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Handle non-numeric columns
        X_numeric = pd.get_dummies(X, drop_first=True)
        
        # Encode target for classification
        is_classification = df[target_column].dtype == 'object' or df[target_column].nunique() < 10
        if is_classification and model_type == "classification":
            le = LabelEncoder()
            y_encoded = le.fit_transform(y)
        else:
            y_encoded = y
            model_type = "regression"
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_numeric, y_encoded, test_size=0.2, random_state=42
        )
        
        # Train model
        if model_type == "classification":
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            accuracy = accuracy_score(y_test, predictions)
            
            # Feature importance
            feature_importance = dict(zip(X_numeric.columns, model.feature_importances_))
            
            return {
                "model_type": "classification",
                "accuracy": float(accuracy),
                "feature_importance": {k: float(v) for k, v in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]},
                "target_column": target_column,
                "dataset_id": dataset_id
            }
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            r2 = r2_score(y_test, predictions)
            
            # Feature importance
            feature_importance = dict(zip(X_numeric.columns, model.feature_importances_))
            
            return {
                "model_type": "regression",
                "r2_score": float(r2),
                "feature_importance": {k: float(v) for k, v in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]},
                "target_column": target_column,
                "dataset_id": dataset_id
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/insights/generate")
async def generate_insights(request: Dict[str, Any]):
    """Generate strategic insights"""
    try:
        dataset_id = request.get("dataset_id")
        context = request.get("context", "general business")
        
        dataset = db.get_dataset(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = pd.read_json(dataset['data'], orient='records')
        insights = insights_gen.generate(df, context)
        
        return insights
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat")
async def chat(request: Dict[str, Any]):
    """Chat interface for asking questions about data"""
    try:
        query = request.get("query")
        dataset_id = request.get("dataset_id")
        
        if dataset_id:
            dataset = db.get_dataset(dataset_id)
            if dataset is None:
                raise HTTPException(status_code=404, detail="Dataset not found")
            df = pd.read_json(dataset['data'], orient='records')
        else:
            df = None
        
        response = chat_service.query(query, df, dataset_id)
        
        return {
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/quality/{dataset_id}")
async def get_data_quality(dataset_id: str):
    """Get data quality assessment"""
    try:
        dataset = db.get_dataset(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = pd.read_json(dataset['data'], orient='records')
        quality_report = quality_analyzer.analyze(df)
        
        return quality_report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/knowledge-gaps/{dataset_id}")
async def get_knowledge_gaps(dataset_id: str):
    """Identify knowledge gaps in the dataset"""
    try:
        dataset = db.get_dataset(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = pd.read_json(dataset['data'], orient='records')
        gaps = gap_identifier.identify(df)
        
        return gaps
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

