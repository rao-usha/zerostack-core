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

app = FastAPI(title="NEX.AI - AI Native Data Platform", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

