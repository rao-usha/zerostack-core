"""Tests for Phase B features: Cost tracking, reuse engine, state machine, RunPod."""
import pytest
import json
import hashlib
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# ========================================
# Cost Tracker Tests
# ========================================

class TestCostTracker:
    """Tests for the cost tracking service."""
    
    def test_compute_estimate_local(self):
        """Local compute should be free."""
        from services.cost_tracker import CostTracker
        
        tracker = CostTracker.__new__(CostTracker)
        tracker._pricing_cache = {}
        tracker.engine = Mock()
        
        # Mock the get_pricing_by_id to return local pricing
        tracker.get_pricing_by_id = Mock(return_value={
            'id': 'local_any',
            'provider': 'local',
            'gpu_type': 'any',
            'hourly_rate_usd': Decimal('0.00')
        })
        tracker.get_gpu_pricing = Mock(return_value=[])
        
        estimate = tracker.estimate_cost(provider='local', max_runtime_seconds=3600)
        
        assert estimate.estimated_cost_usd == Decimal('0.00')
        assert estimate.provider == 'local'
    
    def test_compute_estimate_runpod(self):
        """RunPod should have non-zero cost."""
        from services.cost_tracker import CostTracker
        
        tracker = CostTracker.__new__(CostTracker)
        tracker._pricing_cache = {}
        tracker.engine = Mock()
        
        # Mock RunPod pricing
        tracker.get_gpu_pricing = Mock(return_value=[{
            'id': 'runpod_rtx_a4000',
            'provider': 'runpod',
            'gpu_type': 'NVIDIA RTX A4000',
            'hourly_rate_usd': Decimal('0.20')
        }])
        tracker.get_pricing_by_id = Mock(return_value=None)
        
        estimate = tracker.estimate_cost(
            provider='runpod',
            max_runtime_seconds=7200  # 2 hours
        )
        
        assert estimate.estimated_cost_usd == Decimal('0.40')
        assert estimate.provider == 'runpod'
        assert estimate.hourly_rate_usd == Decimal('0.20')
    
    def test_actual_cost_calculation(self):
        """Actual cost should be based on actual runtime."""
        from services.cost_tracker import CostTracker
        
        tracker = CostTracker.__new__(CostTracker)
        tracker._pricing_cache = {}
        tracker.engine = Mock()
        
        tracker.get_gpu_pricing = Mock(return_value=[{
            'id': 'runpod_a100',
            'provider': 'runpod',
            'gpu_type': 'NVIDIA A100 40GB',
            'hourly_rate_usd': Decimal('1.09')
        }])
        tracker.get_pricing_by_id = Mock(return_value=None)
        
        # 30 minutes = 0.5 hours
        actual = tracker.calculate_actual_cost(
            runtime_seconds=1800,
            provider='runpod'
        )
        
        expected = Decimal('1.09') * Decimal('0.5')
        assert actual.actual_cost_usd == round(expected, 4)
        assert actual.runtime_seconds == 1800


# ========================================
# Reuse Engine Tests
# ========================================

class TestReuseEngine:
    """Tests for the reuse-before-rerun engine."""
    
    def test_similarity_hash_deterministic(self):
        """Same inputs should produce same hash."""
        from services.reuse_engine import ReuseEngine
        
        hash1 = ReuseEngine.compute_similarity_hash(
            recipe_id='recipe_1',
            dataset_version_id='dataset_v1',
            parameters={'lr': 0.01, 'epochs': 10}
        )
        
        hash2 = ReuseEngine.compute_similarity_hash(
            recipe_id='recipe_1',
            dataset_version_id='dataset_v1',
            parameters={'epochs': 10, 'lr': 0.01}  # Same params, different order
        )
        
        assert hash1 == hash2
        assert len(hash1) == 16  # 16 hex chars
    
    def test_similarity_hash_different_params(self):
        """Different inputs should produce different hash."""
        from services.reuse_engine import ReuseEngine
        
        hash1 = ReuseEngine.compute_similarity_hash(
            recipe_id='recipe_1',
            dataset_version_id='dataset_v1',
            parameters={'lr': 0.01}
        )
        
        hash2 = ReuseEngine.compute_similarity_hash(
            recipe_id='recipe_1',
            dataset_version_id='dataset_v1',
            parameters={'lr': 0.001}  # Different learning rate
        )
        
        assert hash1 != hash2
    
    def test_evaluate_reuse_no_matches(self):
        """Should recommend PROCEED when no matches found."""
        from services.reuse_engine import ReuseEngine, ReuseAction
        
        engine = ReuseEngine.__new__(ReuseEngine)
        engine.engine = Mock()
        engine.max_age_days = 30
        engine.min_confidence_for_reuse = 0.8
        engine.find_matching_runs = Mock(return_value=[])
        
        decision = engine.evaluate_reuse(
            recipe_id='recipe_1',
            dataset_version_id='v1',
            parameters={}
        )
        
        assert decision.action == ReuseAction.PROCEED
        assert len(decision.matching_runs) == 0
        assert decision.best_match is None
    
    def test_evaluate_reuse_with_match(self):
        """Should recommend REUSE when match found."""
        from services.reuse_engine import ReuseEngine, ReuseAction, MatchingRun
        
        engine = ReuseEngine.__new__(ReuseEngine)
        engine.engine = Mock()
        engine.max_age_days = 30
        engine.min_confidence_for_reuse = 0.8
        
        mock_match = MatchingRun(
            run_id='run_existing',
            status='succeeded',
            created_at=datetime.utcnow() - timedelta(days=1),
            metrics_json={'accuracy': 0.95},
            similarity_score=1.0,
            cost_usd=0.50
        )
        engine.find_matching_runs = Mock(return_value=[mock_match])
        
        decision = engine.evaluate_reuse(
            recipe_id='recipe_1',
            dataset_version_id='v1',
            parameters={},
            estimated_cost_usd=0.50
        )
        
        assert decision.action in [ReuseAction.REUSE_RECOMMENDED, ReuseAction.REUSE_REQUIRED]
        assert decision.best_match.run_id == 'run_existing'
        assert decision.potential_savings_usd == 0.50
    
    def test_force_rerun_bypasses_reuse(self):
        """Force rerun should always return PROCEED."""
        from services.reuse_engine import ReuseEngine, ReuseAction
        
        engine = ReuseEngine.__new__(ReuseEngine)
        engine.engine = Mock()
        
        decision = engine.evaluate_reuse(
            recipe_id='recipe_1',
            dataset_version_id='v1',
            parameters={},
            force_rerun=True
        )
        
        assert decision.action == ReuseAction.PROCEED
        assert "Forced rerun" in decision.reason


# ========================================
# State Machine Tests
# ========================================

class TestStateMachine:
    """Tests for the run state machine."""
    
    def test_valid_transitions(self):
        """Test valid state transitions."""
        from domains.ml_development.state_machine import RunStateMachine, RunState
        
        machine = RunStateMachine.__new__(RunStateMachine)
        
        # Valid transitions from QUEUED
        assert machine.can_transition(RunState.QUEUED, RunState.SCHEDULED)
        assert machine.can_transition(RunState.QUEUED, RunState.CANCELLED)
        
        # Valid transitions from RUNNING
        assert machine.can_transition(RunState.RUNNING, RunState.SUCCEEDED)
        assert machine.can_transition(RunState.RUNNING, RunState.FAILED)
        assert machine.can_transition(RunState.RUNNING, RunState.RETRYING)
    
    def test_invalid_transitions(self):
        """Test invalid state transitions are rejected."""
        from domains.ml_development.state_machine import RunStateMachine, RunState
        
        machine = RunStateMachine.__new__(RunStateMachine)
        
        # Cannot go backwards
        assert not machine.can_transition(RunState.RUNNING, RunState.QUEUED)
        assert not machine.can_transition(RunState.SUCCEEDED, RunState.RUNNING)
        
        # Cannot transition from terminal states
        assert not machine.can_transition(RunState.SUCCEEDED, RunState.FAILED)
        assert not machine.can_transition(RunState.FAILED, RunState.SUCCEEDED)
    
    def test_failure_classification_infra(self):
        """Infrastructure errors should be classified correctly."""
        from domains.ml_development.state_machine import RunStateMachine, FailureType
        
        machine = RunStateMachine.__new__(RunStateMachine)
        
        assert machine.classify_failure("Connection refused") == FailureType.INFRA
        assert machine.classify_failure("CUDA error: out of memory") == FailureType.INFRA
        assert machine.classify_failure("GPU memory exhausted") == FailureType.INFRA
        assert machine.classify_failure("Pod evicted by scheduler") == FailureType.INFRA
    
    def test_failure_classification_model(self):
        """Model errors should be classified correctly."""
        from domains.ml_development.state_machine import RunStateMachine, FailureType
        
        machine = RunStateMachine.__new__(RunStateMachine)
        
        assert machine.classify_failure("ValueError: invalid input shape") == FailureType.MODEL
        assert machine.classify_failure("AssertionError in training loop") == FailureType.MODEL
    
    def test_should_retry_infra_error(self):
        """Should retry infrastructure errors."""
        from domains.ml_development.state_machine import RunStateMachine, FailureType
        
        machine = RunStateMachine.__new__(RunStateMachine)
        
        assert machine.should_retry(FailureType.INFRA, retry_count=0, max_retries=2)
        assert machine.should_retry(FailureType.INFRA, retry_count=1, max_retries=2)
        assert not machine.should_retry(FailureType.INFRA, retry_count=2, max_retries=2)
    
    def test_should_not_retry_model_error(self):
        """Should not retry model errors by default."""
        from domains.ml_development.state_machine import RunStateMachine, FailureType
        
        machine = RunStateMachine.__new__(RunStateMachine)
        
        assert not machine.should_retry(FailureType.MODEL, retry_count=0, max_retries=2)


# ========================================
# RunPod Adapter Tests
# ========================================

class TestRunPodAdapter:
    """Tests for the RunPod compute adapter."""
    
    def test_adapter_type(self):
        """Adapter should identify as runpod."""
        from services.compute.runpod_adapter import RunPodAdapter
        
        with patch.object(RunPodAdapter, '__init__', lambda self: None):
            adapter = RunPodAdapter()
            adapter.api_key = None
            adapter.default_gpu = 'NVIDIA RTX A4000'
            adapter.template_id = None
            
            assert adapter.adapter_type == 'runpod'
    
    def test_gpu_type_mapping(self):
        """GPU types should map to RunPod IDs correctly."""
        from services.compute.runpod_adapter import RunPodAdapter
        
        with patch.object(RunPodAdapter, '__init__', lambda self: None):
            adapter = RunPodAdapter()
            
            assert adapter._map_gpu_type('NVIDIA RTX A4000') == 'NVIDIA RTX A4000'
            assert adapter._map_gpu_type('NVIDIA A100 40GB') == 'NVIDIA A100-SXM4-40GB'
            assert adapter._map_gpu_type('NVIDIA H100 80GB') == 'NVIDIA H100 80GB HBM3'
    
    def test_status_mapping(self):
        """RunPod statuses should map to JobState correctly."""
        from services.compute.runpod_adapter import RunPodAdapter
        from services.compute.adapter import JobState
        
        with patch.object(RunPodAdapter, '__init__', lambda self: None):
            adapter = RunPodAdapter()
            
            assert adapter._map_status('CREATED') == JobState.PENDING
            assert adapter._map_status('RUNNING') == JobState.RUNNING
            assert adapter._map_status('TERMINATED') == JobState.CANCELLED
    
    @pytest.mark.asyncio
    async def test_is_healthy_without_api_key(self):
        """Health check should fail without API key."""
        from services.compute.runpod_adapter import RunPodAdapter
        
        with patch.object(RunPodAdapter, '__init__', lambda self: None):
            adapter = RunPodAdapter()
            adapter.api_key = None
            
            result = await adapter.is_healthy()
            assert result is False


# ========================================
# Integration Tests
# ========================================

class TestPhaseBIntegration:
    """Integration tests for Phase B features."""
    
    def test_full_reuse_workflow(self):
        """Test complete reuse-before-rerun workflow."""
        from services.reuse_engine import ReuseEngine
        from services.cost_tracker import CostTracker
        
        # This would require a test database
        # Placeholder for integration test
        pass
    
    def test_cost_tracking_end_to_end(self):
        """Test cost tracking from estimate to actual."""
        # Placeholder for integration test
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
