"""Tests for drift history and trending functionality."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestDriftHistoryRecording:
    """Tests for recording drift history."""

    def test_record_history_on_check(self):
        """History should be recorded when a drift check is performed."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            detector = DriftDetector(engine=mock_engine)

            # Mock the check lookup
            with patch.object(detector, '_get_check') as mock_get_check, \
                 patch.object(detector, '_update_check_status'), \
                 patch.object(detector, '_record_history') as mock_record:

                mock_get_check.return_value = {
                    'id': 'check_123',
                    'name': 'Test Check',
                    'metric': 'accuracy',
                    'threshold': 0.1,
                    'comparison': 'percentage_both',
                    'baseline_value': 0.9
                }

                result = detector.check_drift('check_123', 0.85)

                # History should be recorded
                mock_record.assert_called_once()
                call_kwargs = mock_record.call_args[1]
                assert call_kwargs['check_id'] == 'check_123'
                assert call_kwargs['value'] == 0.85
                assert call_kwargs['source'] == 'manual'

    def test_record_history_with_run_context(self):
        """History should include run_id when checking run metrics."""
        from services.drift_detector import DriftDetector, DriftCheckResult

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            detector = DriftDetector(engine=mock_engine)

            with patch.object(detector, '_get_run') as mock_get_run, \
                 patch.object(detector, '_get_checks_for_recipe') as mock_get_checks, \
                 patch.object(detector, 'check_drift') as mock_check, \
                 patch.object(detector, '_record_history') as mock_record, \
                 patch.object(detector, '_create_alert'):

                mock_get_run.return_value = {
                    'id': 'run_abc',
                    'recipe_id': 'recipe_xyz'
                }

                mock_get_checks.return_value = [{
                    'id': 'check_1',
                    'metric': 'accuracy',
                    'baseline_value': 0.9
                }]

                mock_check.return_value = DriftCheckResult(
                    check_id='check_1',
                    check_name='Test',
                    metric='accuracy',
                    is_breached=False,
                    baseline_value=0.9,
                    current_value=0.92,
                    change_percent=2.2,
                    severity=None,
                    message='OK'
                )

                detector.check_run_metrics('run_abc', {'accuracy': 0.92})

                # History should be recorded with run context
                mock_record.assert_called()
                call_kwargs = mock_record.call_args[1]
                assert call_kwargs['run_id'] == 'run_abc'
                assert call_kwargs['source'] == 'run'


class TestDriftHistoryRetrieval:
    """Tests for retrieving drift history."""

    def test_get_history_basic(self):
        """Should retrieve history records for a check."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            # Mock query result
            mock_row = MagicMock()
            mock_row._mapping = {
                'id': 'hist_1',
                'drift_check_id': 'check_1',
                'value': 0.95,
                'baseline_value': 0.9,
                'change_percent': 5.5,
                'is_breached': False,
                'severity': None,
                'run_id': 'run_1',
                'source': 'run',
                'recorded_at': datetime.now()
            }
            mock_conn.execute.return_value = [mock_row]

            detector = DriftDetector(engine=mock_engine)
            history = detector.get_history('check_1', limit=10)

            assert len(history) == 1
            assert history[0]['value'] == 0.95

    def test_get_history_with_time_filters(self):
        """Should filter history by time range."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value = []

            detector = DriftDetector(engine=mock_engine)

            start = datetime.now() - timedelta(days=7)
            end = datetime.now()

            detector.get_history('check_1', start_time=start, end_time=end)

            # Verify the query included time filters
            call_args = mock_conn.execute.call_args
            query_str = str(call_args[0][0])
            assert 'start_time' in query_str or ':start_time' in str(call_args[1])


class TestTrendStatistics:
    """Tests for trend statistics calculation."""

    def test_get_trend_stats_empty(self):
        """Should handle empty history gracefully."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            # Return empty result
            mock_result = MagicMock()
            mock_result.__getitem__ = lambda self, i: [0, 0, None, None, None, None, None, None, None][i]
            mock_conn.execute.return_value.fetchone.return_value = mock_result

            detector = DriftDetector(engine=mock_engine)
            stats = detector.get_trend_stats('check_1', days=30)

            assert stats['total_checks'] == 0
            assert stats['breach_count'] == 0
            assert stats['breach_rate'] == 0.0
            assert stats['avg_value'] is None

    def test_get_trend_stats_with_data(self):
        """Should calculate statistics correctly."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            # Mock result with data
            now = datetime.now()
            mock_result = [
                10,    # total_checks
                2,     # breach_count
                0.92,  # avg_value
                0.85,  # min_value
                0.98,  # max_value
                0.03,  # stddev_value
                3.5,   # avg_change_percent
                now - timedelta(days=7),   # first_check
                now    # last_check
            ]

            mock_row = MagicMock()
            mock_row.__getitem__ = lambda self, i: mock_result[i]
            mock_conn.execute.return_value.fetchone.return_value = mock_row

            detector = DriftDetector(engine=mock_engine)
            stats = detector.get_trend_stats('check_1', days=30)

            assert stats['total_checks'] == 10
            assert stats['breach_count'] == 2
            assert stats['breach_rate'] == 20.0  # 2/10 * 100
            assert stats['avg_value'] == 0.92
            assert stats['min_value'] == 0.85
            assert stats['max_value'] == 0.98


class TestTrendData:
    """Tests for time-bucketed trend data."""

    def test_get_trend_data_empty(self):
        """Should return empty list when no data."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value = []

            detector = DriftDetector(engine=mock_engine)
            data = detector.get_trend_data('check_1', days=30, bucket_hours=24)

            assert data == []

    def test_get_trend_data_buckets(self):
        """Should return bucketed data for visualization."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            # Mock bucket results
            now = datetime.now()
            bucket1 = [now - timedelta(days=1), 5, 1, 0.91, 0.88, 0.95, 2.5]
            bucket2 = [now, 3, 0, 0.93, 0.92, 0.94, 1.2]

            mock_rows = [
                MagicMock(__getitem__=lambda self, i, b=bucket1: b[i]),
                MagicMock(__getitem__=lambda self, i, b=bucket2: b[i])
            ]
            mock_conn.execute.return_value = mock_rows

            detector = DriftDetector(engine=mock_engine)
            data = detector.get_trend_data('check_1', days=7, bucket_hours=24)

            assert len(data) == 2
            assert data[0]['check_count'] == 5
            assert data[0]['breach_count'] == 1
            assert data[1]['check_count'] == 3
            assert data[1]['breach_count'] == 0


class TestHistoryEndpointModels:
    """Tests for the Pydantic models used in history endpoints."""

    def test_drift_history_record_model(self):
        """DriftHistoryRecord should validate correctly."""
        from domains.drift.router import DriftHistoryRecord

        record = DriftHistoryRecord(
            id='hist_123',
            drift_check_id='check_456',
            value=0.95,
            baseline_value=0.90,
            change_percent=5.5,
            is_breached=False,
            severity=None,
            run_id='run_789',
            source='run',
            recorded_at=datetime.now()
        )

        assert record.id == 'hist_123'
        assert record.value == 0.95
        assert record.source == 'run'

    def test_trend_stats_response_model(self):
        """TrendStatsResponse should validate correctly."""
        from domains.drift.router import TrendStatsResponse

        stats = TrendStatsResponse(
            total_checks=100,
            breach_count=5,
            breach_rate=5.0,
            avg_value=0.92,
            min_value=0.85,
            max_value=0.98,
            stddev_value=0.03,
            avg_change_percent=2.5,
            first_check='2026-01-01T00:00:00',
            last_check='2026-01-31T00:00:00',
            days_analyzed=30
        )

        assert stats.total_checks == 100
        assert stats.breach_rate == 5.0

    def test_trend_bucket_model(self):
        """TrendBucket should validate correctly."""
        from domains.drift.router import TrendBucket

        bucket = TrendBucket(
            timestamp='2026-01-15T00:00:00',
            check_count=10,
            breach_count=2,
            avg_value=0.91,
            min_value=0.88,
            max_value=0.95,
            avg_change_percent=3.0
        )

        assert bucket.check_count == 10
        assert bucket.breach_count == 2


class TestRecordHistoryMethod:
    """Tests for the _record_history internal method."""

    def test_record_history_success(self):
        """Should insert history record into database."""
        from services.drift_detector import DriftDetector, Severity

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            detector = DriftDetector(engine=mock_engine)

            detector._record_history(
                check_id='check_1',
                value=0.85,
                baseline_value=0.9,
                change_percent=-5.5,
                is_breached=True,
                severity=Severity.WARNING,
                run_id='run_abc',
                source='run'
            )

            # Verify insert was called
            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args
            # Parameters are passed as second positional arg to execute(text(query), params)
            params = call_args[0][1]
            assert params['check_id'] == 'check_1'
            assert params['value'] == 0.85
            assert params['severity'] == 'warning'

    def test_record_history_error_does_not_raise(self):
        """Recording history failure should not raise exception."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_engine.begin.return_value.__enter__.side_effect = Exception("DB error")

            detector = DriftDetector(engine=mock_engine)

            # Should not raise
            detector._record_history(
                check_id='check_1',
                value=0.85,
                baseline_value=0.9,
                change_percent=-5.5,
                is_breached=True,
                severity=None,
                source='manual'
            )

    def test_record_history_with_none_severity(self):
        """Should handle None severity correctly."""
        from services.drift_detector import DriftDetector

        with patch('services.drift_detector.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine
            mock_conn = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_conn

            detector = DriftDetector(engine=mock_engine)

            detector._record_history(
                check_id='check_1',
                value=0.92,
                baseline_value=0.9,
                change_percent=2.2,
                is_breached=False,
                severity=None,
                source='manual'
            )

            call_args = mock_conn.execute.call_args
            # Parameters are passed as second positional arg to execute(text(query), params)
            params = call_args[0][1]
            assert params['severity'] is None
