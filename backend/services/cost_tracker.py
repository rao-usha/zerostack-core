"""Cost tracking service for ML runs.

Provides:
- Cost estimation before run starts
- Actual cost calculation after completion
- GPU pricing lookup
"""
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from dataclasses import dataclass
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CostEstimate:
    """Cost estimate for a run."""
    estimated_cost_usd: Decimal
    gpu_type: str
    hourly_rate_usd: Decimal
    max_runtime_hours: float
    provider: str
    confidence: str  # 'high', 'medium', 'low'
    
    def to_dict(self) -> dict:
        return {
            'estimated_cost_usd': float(self.estimated_cost_usd),
            'gpu_type': self.gpu_type,
            'hourly_rate_usd': float(self.hourly_rate_usd),
            'max_runtime_hours': self.max_runtime_hours,
            'provider': self.provider,
            'confidence': self.confidence
        }


@dataclass  
class ActualCost:
    """Actual cost after run completion."""
    actual_cost_usd: Decimal
    runtime_seconds: int
    gpu_type: str
    hourly_rate_usd: Decimal
    
    def to_dict(self) -> dict:
        return {
            'actual_cost_usd': float(self.actual_cost_usd),
            'runtime_seconds': self.runtime_seconds,
            'runtime_hours': round(self.runtime_seconds / 3600, 4),
            'gpu_type': self.gpu_type,
            'hourly_rate_usd': float(self.hourly_rate_usd)
        }


class CostTracker:
    """Service for tracking ML run costs."""
    
    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)
        self._pricing_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_gpu_pricing(self, provider: str = None, gpu_type: str = None) -> list[dict]:
        """
        Get GPU pricing options.
        
        Args:
            provider: Filter by provider (e.g., 'runpod', 'local')
            gpu_type: Filter by GPU type
            
        Returns:
            List of pricing options
        """
        query = "SELECT * FROM gpu_pricing WHERE is_active = true"
        params = {}
        
        if provider:
            query += " AND provider = :provider"
            params['provider'] = provider
        if gpu_type:
            query += " AND gpu_type = :gpu_type"
            params['gpu_type'] = gpu_type
            
        query += " ORDER BY hourly_rate_usd ASC"
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            return [dict(row._mapping) for row in result]
    
    def get_pricing_by_id(self, pricing_id: str) -> Optional[dict]:
        """Get specific pricing by ID."""
        if pricing_id in self._pricing_cache:
            return self._pricing_cache[pricing_id]
            
        with self.engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM gpu_pricing WHERE id = :id"),
                {'id': pricing_id}
            ).fetchone()
            
            if result:
                pricing = dict(result._mapping)
                self._pricing_cache[pricing_id] = pricing
                return pricing
        return None
    
    def estimate_cost(
        self,
        gpu_type: str = None,
        provider: str = None,
        max_runtime_seconds: int = None,
        pricing_id: str = None
    ) -> CostEstimate:
        """
        Estimate cost for a run before execution.
        
        Args:
            gpu_type: GPU type (e.g., 'NVIDIA RTX A4000')
            provider: Provider (e.g., 'runpod', 'local')
            max_runtime_seconds: Maximum expected runtime
            pricing_id: Specific pricing ID to use
            
        Returns:
            CostEstimate with projected cost
        """
        # Default runtime from settings
        if max_runtime_seconds is None:
            max_runtime_seconds = settings.run_timeout_seconds
        
        max_runtime_hours = max_runtime_seconds / 3600
        
        # Look up pricing
        pricing = None
        
        if pricing_id:
            pricing = self.get_pricing_by_id(pricing_id)
        elif provider and gpu_type:
            options = self.get_gpu_pricing(provider=provider, gpu_type=gpu_type)
            if options:
                pricing = options[0]
        elif provider:
            # Get cheapest option for provider
            options = self.get_gpu_pricing(provider=provider)
            if options:
                pricing = options[0]
        
        # Fallback to local (free)
        if not pricing:
            pricing = self.get_pricing_by_id('local_any') or {
                'id': 'local_any',
                'provider': 'local',
                'gpu_type': 'any',
                'hourly_rate_usd': Decimal('0.00')
            }
        
        hourly_rate = Decimal(str(pricing['hourly_rate_usd']))
        estimated_cost = hourly_rate * Decimal(str(max_runtime_hours))
        
        # Determine confidence based on runtime estimate accuracy
        confidence = 'medium'
        if max_runtime_seconds == settings.run_timeout_seconds:
            confidence = 'low'  # Using default timeout, actual may be much less
        elif max_runtime_seconds < 600:  # < 10 minutes
            confidence = 'high'  # Short runs are more predictable
        
        return CostEstimate(
            estimated_cost_usd=round(estimated_cost, 4),
            gpu_type=pricing['gpu_type'],
            hourly_rate_usd=hourly_rate,
            max_runtime_hours=round(max_runtime_hours, 4),
            provider=pricing['provider'],
            confidence=confidence
        )
    
    def calculate_actual_cost(
        self,
        runtime_seconds: int,
        gpu_type: str = None,
        provider: str = None,
        pricing_id: str = None
    ) -> ActualCost:
        """
        Calculate actual cost after run completion.
        
        Args:
            runtime_seconds: Actual runtime in seconds
            gpu_type: GPU type used
            provider: Provider used
            pricing_id: Specific pricing ID
            
        Returns:
            ActualCost with calculated cost
        """
        # Look up pricing (same logic as estimate)
        pricing = None
        
        if pricing_id:
            pricing = self.get_pricing_by_id(pricing_id)
        elif provider and gpu_type:
            options = self.get_gpu_pricing(provider=provider, gpu_type=gpu_type)
            if options:
                pricing = options[0]
        elif provider:
            options = self.get_gpu_pricing(provider=provider)
            if options:
                pricing = options[0]
        
        if not pricing:
            pricing = {
                'gpu_type': gpu_type or 'unknown',
                'hourly_rate_usd': Decimal('0.00')
            }
        
        hourly_rate = Decimal(str(pricing['hourly_rate_usd']))
        runtime_hours = Decimal(str(runtime_seconds)) / Decimal('3600')
        actual_cost = hourly_rate * runtime_hours
        
        return ActualCost(
            actual_cost_usd=round(actual_cost, 4),
            runtime_seconds=runtime_seconds,
            gpu_type=pricing['gpu_type'],
            hourly_rate_usd=hourly_rate
        )
    
    def update_run_cost(
        self,
        run_id: str,
        estimated: CostEstimate = None,
        actual: ActualCost = None
    ):
        """
        Update run record with cost information.
        
        Args:
            run_id: The run ID to update
            estimated: Cost estimate (set at submission)
            actual: Actual cost (set at completion)
        """
        updates = []
        params = {'run_id': run_id}
        
        if estimated:
            updates.extend([
                'estimated_cost_usd = :estimated_cost',
                'gpu_type = :gpu_type'
            ])
            params['estimated_cost'] = float(estimated.estimated_cost_usd)
            params['gpu_type'] = estimated.gpu_type
        
        if actual:
            updates.extend([
                'actual_cost_usd = :actual_cost',
                'runtime_seconds = :runtime_seconds'
            ])
            params['actual_cost'] = float(actual.actual_cost_usd)
            params['runtime_seconds'] = actual.runtime_seconds
            if not estimated:
                params['gpu_type'] = actual.gpu_type
                updates.append('gpu_type = :gpu_type')
        
        if updates:
            query = f"UPDATE ml_run SET {', '.join(updates)} WHERE id = :run_id"
            with self.engine.begin() as conn:
                conn.execute(text(query), params)
                logger.info(f"Updated cost for run {run_id}")


# Singleton instance
_tracker_instance: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get singleton cost tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = CostTracker()
    return _tracker_instance
