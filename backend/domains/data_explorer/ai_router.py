"""
AI Analysis router for Data Explorer.

Provides endpoints for AI-powered data analysis including EDA, anomaly detection,
and pattern identification.
"""
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from typing import List, Optional
from sqlmodel import Session, select, desc
from uuid import UUID
from datetime import datetime

from .models import AnalysisRequest, AnalysisResponse, AnalysisResult, SavedAnalysis
from .ai_analysis import AIAnalysisService
from .db_models import AIAnalysisResult as DBAnalysisResult
from db_session import get_session


router = APIRouter(prefix="/data-explorer", tags=["data-explorer-ai"])


@router.post("/analyze", response_model=AnalysisResponse)
async def run_analysis(
    request: AnalysisRequest,
    session: Session = Depends(get_session)
):
    """
    Run AI-powered analysis on selected tables.
    
    Performs exploratory data analysis, anomaly detection, and pattern identification
    using the specified LLM model.
    
    Args:
        request: Analysis request with tables, analysis types, and model configuration
        
    Returns:
        Analysis result with insights, summary, and recommendations
    """
    try:
        # Run the AI analysis
        result = await AIAnalysisService.analyze_tables(request)
        
        # Save to database
        db_record = DBAnalysisResult(
            name=f"Analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            description=f"AI analysis of {len(request.tables)} table(s)",
            tables=request.tables,  # Already in correct dict format
            analysis_types=request.analysis_types,
            provider=request.provider,
            model=request.model,
            context=request.context,
            insights=result.insights,
            summary=result.summary,
            recommendations=result.recommendations,
            execution_metadata=result.metadata,
            db_id=request.db_id,
            tags=[]
        )
        
        session.add(db_record)
        session.commit()
        session.refresh(db_record)
        
        # Update result with saved ID
        result.analysis_id = str(db_record.id)
        
        return AnalysisResponse(
            analysis_id=result.analysis_id,
            status="completed",
            result=result
        )
        
    except Exception as e:
        return AnalysisResponse(
            analysis_id="",
            status="failed",
            error=str(e)
        )


@router.get("/analyses", response_model=List[SavedAnalysis])
async def list_analyses(
    db_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """
    List saved AI analysis results.
    
    Args:
        db_id: Filter by database ID (optional)
        limit: Maximum number of results to return
        
    Returns:
        List of saved analyses
    """
    try:
        query = select(DBAnalysisResult).order_by(desc(DBAnalysisResult.created_at)).limit(limit)
        
        if db_id:
            query = query.where(DBAnalysisResult.db_id == db_id)
        
        results = session.exec(query).all()
        
        return [
            SavedAnalysis(
                id=str(r.id),
                name=r.name,
                description=r.description,
                analysis_result=AnalysisResult(
                    analysis_id=str(r.id),
                    tables=r.tables,  # Already in correct dict format from JSONB
                    analysis_types=r.analysis_types,
                    provider=r.provider,
                    model=r.model,
                    insights=r.insights,
                    summary=r.summary,
                    recommendations=r.recommendations or [],
                    metadata=r.execution_metadata or {},
                    created_at=r.created_at.isoformat()
                ),
                saved_at=r.created_at.isoformat(),
                tags=r.tags or []
            )
            for r in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyses/{analysis_id}", response_model=SavedAnalysis)
async def get_analysis(
    analysis_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Get a specific saved analysis by ID.
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        Saved analysis result
    """
    try:
        result = session.get(DBAnalysisResult, analysis_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return SavedAnalysis(
            id=str(result.id),
            name=result.name,
            description=result.description,
            analysis_result=AnalysisResult(
                analysis_id=str(result.id),
                tables=result.tables,  # Already in correct dict format from JSONB
                analysis_types=result.analysis_types,
                provider=result.provider,
                model=result.model,
                insights=result.insights,
                summary=result.summary,
                recommendations=result.recommendations or [],
                metadata=result.execution_metadata or {},
                created_at=result.created_at.isoformat()
            ),
            saved_at=result.created_at.isoformat(),
            tags=result.tags or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(
    analysis_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Delete a saved analysis.
    
    Args:
        analysis_id: Analysis ID
        
    Returns:
        Success message
    """
    try:
        result = session.get(DBAnalysisResult, analysis_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        session.delete(result)
        session.commit()
        
        return {"success": True, "message": "Analysis deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/analyses/{analysis_id}", response_model=SavedAnalysis)
async def update_analysis(
    analysis_id: UUID,
    name: Optional[str] = Body(default=None),
    description: Optional[str] = Body(default=None),
    tags: Optional[List[str]] = Body(default=None),
    session: Session = Depends(get_session)
):
    """
    Update analysis metadata (name, description, tags).
    
    Args:
        analysis_id: Analysis ID
        name: New name (optional)
        description: New description (optional)
        tags: New tags (optional)
        
    Returns:
        Updated saved analysis
    """
    try:
        result = session.get(DBAnalysisResult, analysis_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if name is not None:
            result.name = name
        if description is not None:
            result.description = description
        if tags is not None:
            result.tags = tags
        
        result.updated_at = datetime.utcnow()
        
        session.add(result)
        session.commit()
        session.refresh(result)
        
        return SavedAnalysis(
            id=str(result.id),
            name=result.name,
            description=result.description,
            analysis_result=AnalysisResult(
                analysis_id=str(result.id),
                tables=result.tables,  # Already in correct dict format from JSONB
                analysis_types=result.analysis_types,
                provider=result.provider,
                model=result.model,
                insights=result.insights,
                summary=result.summary,
                recommendations=result.recommendations or [],
                metadata=result.execution_metadata or {},
                created_at=result.created_at.isoformat()
            ),
            saved_at=result.created_at.isoformat(),
            tags=result.tags or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

