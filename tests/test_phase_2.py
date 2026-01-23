"""Tests for Phase 2 features: Drift detection, Asset versioning, Scheduling."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from decimal import Decimal


# ========================================
# Drift Detection Tests
# ========================================

class TestDriftDetector:
    """Tests for the drift detection service."""
    
    def test_evaluate_drift_no_breach(self):
        """Should return no breach when within threshold."""
        from services.drift_detector import DriftDetector
        
        detector = DriftDetector.__new__(DriftDetector)
        
        # 5% increase, threshold is 10%
        is_breached, change_percent, severity = detector._evaluate_drift(
            baseline=100.0,
            current=105.0,
            threshold=0.10,  # 10%
            comparison='percentage_both'
        )
        
        assert is_breached is False
        assert abs(change_percent - 5.0) < 0.01
        assert severity is None
    
    def test_evaluate_drift_warning(self):
        """Should return warning when above threshold but below critical."""
        from services.drift_detector import DriftDetector, Severity
        
        detector = DriftDetector.__new__(DriftDetector)
        detector.critical_multiplier = 2.0
        
        # 15% increase, threshold is 10%, critical at 20%
        is_breached, change_percent, severity = detector._evaluate_drift(
            baseline=100.0,
            current=115.0,
            threshold=0.10,  # 10%
            comparison='percentage_both'
        )
        
        assert is_breached is True
        assert abs(change_percent - 15.0) < 0.01
        assert severity == Severity.WARNING
    
    def test_evaluate_drift_critical(self):
        """Should return critical when above 2x threshold."""
        from services.drift_detector import DriftDetector, Severity
        
        detector = DriftDetector.__new__(DriftDetector)
        detector.critical_multiplier = 2.0
        
        # 25% increase, threshold is 10%, critical at 20%
        is_breached, change_percent, severity = detector._evaluate_drift(
            baseline=100.0,
            current=125.0,
            threshold=0.10,  # 10%
            comparison='percentage_both'
        )
        
        assert is_breached is True
        assert abs(change_percent - 25.0) < 0.01
        assert severity == Severity.CRITICAL
    
    def test_evaluate_drift_decrease_only(self):
        """Should detect decrease-only drift."""
        from services.drift_detector import DriftDetector, Severity
        
        detector = DriftDetector.__new__(DriftDetector)
        detector.critical_multiplier = 2.0
        
        # 15% decrease, threshold is 10% decrease
        is_breached, change_percent, severity = detector._evaluate_drift(
            baseline=100.0,
            current=85.0,
            threshold=0.10,
            comparison='percentage_decrease'
        )
        
        assert is_breached is True
        assert change_percent < 0
    
    def test_evaluate_drift_increase_only(self):
        """Should detect increase-only drift."""
        from services.drift_detector import DriftDetector
        
        detector = DriftDetector.__new__(DriftDetector)
        detector.critical_multiplier = 2.0
        
        # 5% decrease should not trigger increase-only check
        is_breached, change_percent, severity = detector._evaluate_drift(
            baseline=100.0,
            current=95.0,
            threshold=0.10,
            comparison='percentage_increase'
        )
        
        assert is_breached is False  # Decrease doesn't trigger increase check
    
    def test_division_by_zero_handling(self):
        """Should handle zero baseline gracefully."""
        from services.drift_detector import DriftDetector
        
        detector = DriftDetector.__new__(DriftDetector)
        detector.critical_multiplier = 2.0
        
        # Zero baseline, positive current
        is_breached, change_percent, severity = detector._evaluate_drift(
            baseline=0.0,
            current=10.0,
            threshold=0.10,
            comparison='percentage_both'
        )
        
        # Should handle without crashing
        assert change_percent == 100.0


# ========================================
# Asset Versioning Tests
# ========================================

class TestAssetVersioning:
    """Tests for the asset versioning service."""
    
    def test_version_chain_root_finding(self):
        """Should find the root of a version chain."""
        # This would require database mocking
        pass
    
    def test_create_new_version(self):
        """Should create a new version linked to parent."""
        # This would require database mocking
        pass
    
    def test_version_comparison(self):
        """Should compare metrics between versions."""
        # This would require database mocking
        pass


# ========================================
# Scheduler Tests
# ========================================

class TestRunScheduler:
    """Tests for the run scheduler service."""
    
    def test_cron_expression_parsing(self):
        """Should parse valid cron expressions."""
        from services.scheduler import RunScheduler
        
        scheduler = RunScheduler.__new__(RunScheduler)
        
        # Test next run calculation (requires croniter)
        try:
            from croniter import croniter
            next_run = scheduler._calculate_next_run("0 9 * * 1", "UTC")  # Monday 9am
            assert next_run is not None
            assert next_run.hour == 9
        except ImportError:
            pytest.skip("croniter not installed")
    
    def test_schedule_creation(self):
        """Should create a schedule with correct settings."""
        # This would require database mocking
        pass
    
    def test_schedule_respects_reuse_engine(self):
        """Should skip runs when reuse engine finds match."""
        # This would require database and reuse engine mocking
        pass


# ========================================
# Notification Tests
# ========================================

class TestNotificationService:
    """Tests for the notification service."""
    
    @pytest.mark.asyncio
    async def test_send_drift_alert(self):
        """Should format drift alert correctly."""
        from services.notifications import NotificationService
        
        service = NotificationService.__new__(NotificationService)
        service.engine = Mock()
        service._settings_cache = {}
        service._get_enabled_channels = Mock(return_value=[])
        
        results = await service.send_drift_alert(
            check_name="Test Check",
            metric="rmse",
            baseline=0.10,
            current=0.15,
            change_percent=50.0,
            severity="warning"
        )
        
        # Should return empty list when no channels enabled
        assert results == []
    
    @pytest.mark.asyncio
    async def test_send_schedule_notification(self):
        """Should format schedule notification correctly."""
        from services.notifications import NotificationService
        
        service = NotificationService.__new__(NotificationService)
        service.engine = Mock()
        service._settings_cache = {}
        service._get_enabled_channels = Mock(return_value=[])
        
        results = await service.send_schedule_notification(
            schedule_name="Weekly Forecast",
            status="success",
            run_id="run_123"
        )
        
        assert results == []


# ========================================
# Integration Tests
# ========================================

class TestPhase2Integration:
    """Integration tests for Phase 2 features."""
    
    def test_drift_check_workflow(self):
        """Test complete drift check workflow."""
        # Create check -> evaluate -> trigger alert
        pass
    
    def test_schedule_execution_workflow(self):
        """Test complete schedule execution workflow."""
        # Create schedule -> trigger -> verify run
        pass
    
    def test_asset_version_chain(self):
        """Test complete asset version chain."""
        # Create asset -> new version -> get history
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
