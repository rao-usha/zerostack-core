"""Tests for synthetic data generation."""
import pytest
import pandas as pd
import numpy as np

from domains.synthetic.synthesizers import (
    BaseSynthesizer,
    GaussianCopulaSynthesizer,
    CTGANSynthesizer,
    TVAESynthesizer,
)
from domains.synthetic.evaluator import SyntheticDataEvaluator


# ============================================================================
# Test Data
# ============================================================================

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n = 500
    
    return pd.DataFrame({
        'age': np.random.randint(18, 80, n),
        'income': np.random.normal(50000, 15000, n).clip(20000, 150000),
        'category': np.random.choice(['A', 'B', 'C'], n, p=[0.5, 0.3, 0.2]),
        'score': np.random.uniform(0, 100, n),
    })


@pytest.fixture
def small_data():
    """Small dataset for quick tests."""
    np.random.seed(42)
    n = 100
    
    return pd.DataFrame({
        'x': np.random.normal(0, 1, n),
        'y': np.random.normal(5, 2, n),
        'label': np.random.choice(['yes', 'no'], n),
    })


# ============================================================================
# Synthesizer Tests
# ============================================================================

class TestGaussianCopulaSynthesizer:
    """Tests for Gaussian Copula synthesizer."""
    
    def test_get_info(self):
        """Test synthesizer info."""
        info = GaussianCopulaSynthesizer.get_info()
        
        assert info['id'] == 'gaussian_copula'
        assert info['name'] == 'Gaussian Copula'
        assert info['gpu_required'] == False
        assert 'best_for' in info
    
    def test_fit_and_sample(self, small_data):
        """Test basic fit and sample workflow."""
        synth = GaussianCopulaSynthesizer()
        
        # Initially not fitted
        assert not synth.is_fitted
        
        # Fit
        synth.fit(small_data)
        assert synth.is_fitted
        
        # Sample
        result = synth.sample(50)
        synthetic_df = result.synthetic_data
        
        assert len(synthetic_df) == 50
        assert list(synthetic_df.columns) == list(small_data.columns)
    
    def test_sample_without_fit_raises(self, small_data):
        """Test that sampling without fitting raises error."""
        synth = GaussianCopulaSynthesizer()
        
        with pytest.raises(RuntimeError):
            synth.sample(100)
    
    def test_preserves_column_types(self, small_data):
        """Test that column types are preserved."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(small_data)
        
        result = synth.sample(100)
        synthetic_df = result.synthetic_data
        
        # Check numeric columns are numeric
        assert pd.api.types.is_numeric_dtype(synthetic_df['x'])
        assert pd.api.types.is_numeric_dtype(synthetic_df['y'])
    
    def test_with_config(self, small_data):
        """Test with custom configuration."""
        config = {
            'enforce_min_max': True,
            'enforce_rounding': False,
        }
        synth = GaussianCopulaSynthesizer(config=config)
        synth.fit(small_data)
        
        result = synth.sample(50)
        assert len(result.synthetic_data) == 50


class TestCTGANSynthesizer:
    """Tests for CTGAN synthesizer."""
    
    def test_get_info(self):
        """Test synthesizer info."""
        info = CTGANSynthesizer.get_info()
        
        assert info['id'] == 'ctgan'
        assert info['name'] == 'CTGAN'
        assert info['quality'] == 'excellent'
    
    @pytest.mark.slow
    def test_fit_and_sample(self, small_data):
        """Test CTGAN fit and sample (slow - marked for optional skip)."""
        config = {'epochs': 5, 'batch_size': 50}  # Minimal config for speed
        synth = CTGANSynthesizer(config=config)
        
        synth.fit(small_data)
        result = synth.sample(50)
        
        assert len(result.synthetic_data) == 50


class TestTVAESynthesizer:
    """Tests for TVAE synthesizer."""
    
    def test_get_info(self):
        """Test synthesizer info."""
        info = TVAESynthesizer.get_info()
        
        assert info['id'] == 'tvae'
        assert info['name'] == 'TVAE'
    
    @pytest.mark.slow
    def test_fit_and_sample(self, small_data):
        """Test TVAE fit and sample (slow - marked for optional skip)."""
        config = {'epochs': 5, 'batch_size': 50}
        synth = TVAESynthesizer(config=config)
        
        synth.fit(small_data)
        result = synth.sample(50)
        
        assert len(result.synthetic_data) == 50


# ============================================================================
# Evaluator Tests
# ============================================================================

class TestSyntheticDataEvaluator:
    """Tests for quality evaluator."""
    
    def test_evaluate_identical_data(self, small_data):
        """Test evaluation of identical data (should be perfect score)."""
        evaluator = SyntheticDataEvaluator()
        
        # Evaluate real data against itself
        report = evaluator.evaluate(small_data, small_data.copy())
        
        # Should have near-perfect scores
        assert report.overall_score >= 0.95
        assert report.statistical_fidelity_score >= 0.95
    
    def test_evaluate_different_data(self, small_data):
        """Test evaluation of different data."""
        evaluator = SyntheticDataEvaluator()
        
        # Create different data
        np.random.seed(999)
        different_data = pd.DataFrame({
            'x': np.random.normal(10, 5, 100),  # Different distribution
            'y': np.random.normal(0, 1, 100),
            'label': np.random.choice(['yes', 'no'], 100, p=[0.9, 0.1]),  # Different balance
        })
        
        report = evaluator.evaluate(small_data, different_data)
        
        # Should have lower scores
        assert report.overall_score < 0.8
    
    def test_evaluate_generates_recommendations(self, small_data):
        """Test that evaluation generates recommendations."""
        evaluator = SyntheticDataEvaluator()
        
        # Create synthetic with some issues
        synth = GaussianCopulaSynthesizer()
        synth.fit(small_data)
        result = synth.sample(100)
        
        report = evaluator.evaluate(small_data, result.synthetic_data)
        
        # Should have recommendations
        assert isinstance(report.recommendations, list)
        assert len(report.recommendations) > 0
    
    def test_column_scores(self, small_data):
        """Test that column-level scores are generated."""
        evaluator = SyntheticDataEvaluator()
        
        synth = GaussianCopulaSynthesizer()
        synth.fit(small_data)
        result = synth.sample(100)
        
        report = evaluator.evaluate(small_data, result.synthetic_data)
        
        # Should have score for each column
        assert len(report.column_scores) == len(small_data.columns)
        
        for col_score in report.column_scores:
            assert col_score.column_name in small_data.columns
            assert 0 <= col_score.score <= 1
            assert col_score.rating in ['excellent', 'good', 'fair', 'poor', 'unknown']


# ============================================================================
# Integration Tests
# ============================================================================

class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_full_workflow(self, sample_data):
        """Test complete synthesis and evaluation workflow."""
        # 1. Initialize synthesizer
        synth = GaussianCopulaSynthesizer()
        
        # 2. Fit to data
        synth.fit(sample_data)
        
        # 3. Generate synthetic data
        result = synth.sample(len(sample_data))
        synthetic_df = result.synthetic_data
        
        # 4. Evaluate quality
        evaluator = SyntheticDataEvaluator()
        report = evaluator.evaluate(sample_data, synthetic_df)
        
        # 5. Assertions
        assert len(synthetic_df) == len(sample_data)
        assert report.overall_score > 0.6  # Reasonable quality
        assert report.statistical_fidelity_score > 0.6
        
        print(f"\nQuality Report:")
        print(f"  Overall Score: {report.overall_score:.3f}")
        print(f"  Statistical Fidelity: {report.statistical_fidelity_score:.3f}")
        print(f"  Correlation Score: {report.correlation_score:.3f}")
        print(f"  Recommendations: {report.recommendations}")
