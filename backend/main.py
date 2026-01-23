from fastapi import FastAPI, UploadFile, File, HTTPException, Request
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
from services.ontology_chat import OntologyChatService
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
from domains.data_explorer.dictionary_semantics_router import router as dictionary_semantics_router
from domains.data_explorer.relationship_intelligence_router import router as relationship_intelligence_router
from domains.data_explorer.mcp_dictionary_router import router as mcp_dictionary_router
from domains.chat.router import router as chat_router
from domains.ml_development.router import router as ml_development_router
from domains.evaluation_packs.router import router as evaluation_packs_router
from domains.distillation.router import router as distillation_router
from domains.highlighted_datasets.router import router as highlighted_datasets_router
from domains.interactions.router import router as interactions_router
from domains.drift.router import router as drift_router
from domains.cost_analytics.router import router as cost_analytics_router
from domains.schedules.router import router as schedules_router
from domains.data_connections.router import router as data_connections_router
from domains.notebooks.router import router as notebooks_router
from domains.files.router import router as files_router
from domains.lineage.router import router as lineage_router
from domains.synthetic.router import router as synthetic_router
from domains.settings.router import router as settings_router
from domains.feature_store.router import router as feature_store_router
from domains.ontology.router import router as ontology_router
from domains.model_monitoring.router import router as model_monitoring_router
from domains.data_ingestion.router import router as data_ingestion_router
from domains.lp_collection.router import router as lp_collection_router
from domains.fo_collection.router import router as fo_collection_router
from domains.investor_ingestion.router import router as investor_ingestion_router
from domains.connectors.codat.router import router as codat_router

# New dataset system imports
from domains.datasets.storage import DatasetStorage, get_dataset_storage
from domains.datasets.db_models import datasets as datasets_table
from db_session import get_session
from uuid import UUID as PyUUID

# Core setup
from core.config import settings
from core.logging import setup_logging
from core.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Setup logging
setup_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    redirect_slashes=False  # Prevent 307 redirects that break Docker networking
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

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
app.include_router(dictionary_semantics_router, prefix=settings.api_prefix)
app.include_router(relationship_intelligence_router, prefix=settings.api_prefix)
app.include_router(mcp_dictionary_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(ml_development_router, prefix=settings.api_prefix)
app.include_router(evaluation_packs_router, prefix=settings.api_prefix)
app.include_router(distillation_router, prefix=settings.api_prefix)
app.include_router(highlighted_datasets_router, prefix=settings.api_prefix)
app.include_router(interactions_router, prefix=settings.api_prefix)
app.include_router(drift_router, prefix=settings.api_prefix)
app.include_router(cost_analytics_router, prefix=settings.api_prefix)
app.include_router(schedules_router, prefix=settings.api_prefix)
app.include_router(data_connections_router, prefix=settings.api_prefix)
app.include_router(notebooks_router, prefix=settings.api_prefix)
app.include_router(files_router)
app.include_router(lineage_router)
app.include_router(synthetic_router, prefix=settings.api_prefix)
app.include_router(settings_router, prefix=settings.api_prefix)
app.include_router(feature_store_router, prefix=settings.api_prefix)
app.include_router(ontology_router, prefix=settings.api_prefix)
app.include_router(model_monitoring_router)
app.include_router(data_ingestion_router)
app.include_router(lp_collection_router, prefix=settings.api_prefix)
app.include_router(fo_collection_router, prefix=settings.api_prefix)
app.include_router(investor_ingestion_router, prefix=settings.api_prefix)
app.include_router(codat_router, prefix=settings.api_prefix)


# ========================================
# Background Tasks (GPU Runner Finalizer)
# ========================================
import asyncio
from contextlib import asynccontextmanager

# Global finalizer reference
_finalizer = None


@asynccontextmanager
async def lifespan(app):
    """Application lifespan handler - starts/stops background tasks."""
    global _finalizer

    # Start background finalizer if compute adapter is not local-only dev
    if settings.compute_adapter != "disabled":
        try:
            from services.compute import get_compute_adapter
            from services.compute.finalizer import RunFinalizer
            from services.object_store import ObjectStoreClient
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker

            # Create async engine
            async_url = settings.database_url.replace('postgresql+psycopg', 'postgresql+asyncpg')
            if 'asyncpg' not in async_url:
                async_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')

            async_engine = create_async_engine(async_url)
            async_session_factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

            # Initialize finalizer
            compute_adapter = get_compute_adapter()
            object_store = ObjectStoreClient.get_instance()

            _finalizer = RunFinalizer(
                compute_adapter=compute_adapter,
                object_store=object_store,
                async_session_factory=async_session_factory
            )

            # Start finalizer in background
            asyncio.create_task(_finalizer.start())
            print(f"[OK] GPU Runner finalizer started (polling every {settings.finalizer_poll_interval_seconds}s)")
        except Exception as e:
            print(f"[WARN] Could not start GPU Runner finalizer: {e}")

    yield

    # Shutdown
    if _finalizer:
        await _finalizer.stop()
        print("[STOP] GPU Runner finalizer stopped")


# Update app to use lifespan
app.router.lifespan_context = lifespan

# Initialize services
db = Database()
synthetic_gen = SyntheticDataGenerator()
insights_gen = InsightsGenerator()
chat_service = ChatService()
ontology_chat_service = OntologyChatService()
quality_analyzer = DataQualityAnalyzer()
gap_identifier = KnowledgeGapIdentifier()

# Data storage directory
DATA_DIR = Path("data_storage")
DATA_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    return {"message": "zerostack - AI Native Data Platform API", "status": "running"}

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
        "service": "zerostack API",
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
@limiter.limit("5/minute")
async def generate_synthetic(request: Request, body: Dict[str, Any]):
    """Generate synthetic data from sample dataset"""
    try:
        dataset_id = body.get("dataset_id")
        num_rows = body.get("num_rows", 1000)
        
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
@limiter.limit("10/minute")
async def generate_insights(request: Request, body: Dict[str, Any]):
    """Generate strategic insights.

    Supports datasets from both:
    - New system: PostgreSQL metadata + MinIO/Parquet storage (Task 1.1)
    - Legacy system: SQLite with JSON data
    """
    try:
        dataset_id = body.get("dataset_id")
        context = body.get("context", "general business")

        if not dataset_id:
            raise HTTPException(status_code=400, detail="dataset_id is required")

        df = None

        # Try new dataset system first (PostgreSQL + MinIO)
        try:
            with next(get_session()) as session:
                # Check if dataset exists in new system
                result = session.execute(
                    datasets_table.select().where(datasets_table.c.id == PyUUID(dataset_id))
                )
                row = result.fetchone()

                if row:
                    # Load from MinIO storage
                    storage = get_dataset_storage()
                    df = storage.read_dataframe(
                        PyUUID(dataset_id),
                        row.current_version_number or 1,
                        row.storage_format or "parquet"
                    )
        except Exception as e:
            # New system failed, will try legacy
            pass

        # Fall back to legacy SQLite system
        if df is None:
            dataset = db.get_dataset(dataset_id)
            if dataset is None:
                raise HTTPException(status_code=404, detail="Dataset not found")
            df = pd.read_json(dataset['data'], orient='records')

        insights = insights_gen.generate(df, context)

        return insights
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat(request: Request, body: Dict[str, Any]):
    """Enhanced chat interface supporting both data analysis and ontology management"""
    try:
        query = body.get("query", "")
        dataset_id = body.get("dataset_id")
        session_id = body.get("session_id", "default")
        action = body.get("action")
        payload = body.get("payload")
        
        # If there's an action (like "confirm"), execute it
        if action == "confirm" and payload:
            action_type = payload.get("type")
            params = payload.get("params", {})
            
            if action_type == "create_ontology":
                # Execute ontology creation
                from services.ontology.manager import OntologyManager
                mgr = OntologyManager()
                result = mgr.create(
                    params.get("org_id", "demo"),
                    params.get("name", "New Ontology"),
                    params.get("description"),
                    params.get("actor", "user")
                )
                
                # Set as current ontology in session
                ontology_chat_service.set_current_ontology(session_id, {
                    "id": result["ontology_id"],
                    "name": params.get("name", "New Ontology")
                })
                
                return {
                    "query": query,
                    "response": f"✅ Created ontology **{params.get('name')}**!\n\nOntology ID: `{result['ontology_id']}`\n\n💡 You can now:\n• Add terms: \"suggest terms for {params.get('name').lower()}\"\n• View it: \"show me the ontology\"\n• Publish a version: \"publish version\"",
                    "response_type": "success",
                    "metadata": {"ontology_id": result["ontology_id"]},
                    "timestamp": datetime.now().isoformat()
                }
        
        # Check if this is an ontology-related query
        ontology_intent = ontology_chat_service.detect_ontology_intent(query, session_id)
        
        if ontology_intent:
            # This is an ontology query - return structured response
            structured_response = ontology_chat_service.generate_response(ontology_intent, session_id)
            return {
                "query": query,
                "response": structured_response.get("message"),
                "response_type": structured_response.get("type"),
                "action": structured_response.get("action"),
                "ui_elements": structured_response.get("ui_elements", []),
                "metadata": structured_response.get("metadata", {}),
                "timestamp": datetime.now().isoformat()
            }
        
        # Not an ontology query - handle as data analysis
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
            "response_type": "text",
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

