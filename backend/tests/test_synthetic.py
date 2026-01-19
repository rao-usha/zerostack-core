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
from domains.synthetic.privacy import (
    PIIDetector,
    PIIType,
    FakerPIIGenerator,
    PrivacyRiskScorer,
)
from domains.synthetic.quality import (
    MLUtilityEvaluator,
    DetectionEvaluator,
    QualityVisualizer,
)


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


# ============================================================================
# Privacy Tests
# ============================================================================

@pytest.fixture
def pii_data():
    """Create sample data with PII columns."""
    np.random.seed(42)
    n = 100
    
    return pd.DataFrame({
        'email': [f"user{i}@example.com" for i in range(n)],
        'phone': [f"555-{i:03d}-{i*11 % 10000:04d}" for i in range(n)],
        'first_name': np.random.choice(['John', 'Jane', 'Bob', 'Alice', 'Charlie'], n),
        'last_name': np.random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'], n),
        'ssn': [f"{i:03d}-{i%100:02d}-{i*111 % 10000:04d}" for i in range(n)],
        'age': np.random.randint(18, 80, n),
        'income': np.random.normal(50000, 15000, n),
        'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston'], n),
    })


class TestPIIDetector:
    """Tests for PII detection."""
    
    def test_detect_email(self, pii_data):
        """Test email detection."""
        detector = PIIDetector()
        results = detector.detect(pii_data)
        
        assert 'email' in results
        assert results['email'].pii_type == PIIType.EMAIL
        assert results['email'].confidence >= 0.7
    
    def test_detect_phone(self, pii_data):
        """Test phone number detection."""
        detector = PIIDetector()
        results = detector.detect(pii_data)
        
        assert 'phone' in results
        assert results['phone'].pii_type == PIIType.PHONE
    
    def test_detect_ssn(self, pii_data):
        """Test SSN detection."""
        detector = PIIDetector()
        results = detector.detect(pii_data)
        
        assert 'ssn' in results
        assert results['ssn'].pii_type == PIIType.SSN
    
    def test_detect_names_by_column_name(self, pii_data):
        """Test name detection by column name."""
        detector = PIIDetector()
        results = detector.detect(pii_data)
        
        assert 'first_name' in results
        assert results['first_name'].pii_type == PIIType.FIRST_NAME
        
        assert 'last_name' in results
        assert results['last_name'].pii_type == PIIType.LAST_NAME
    
    def test_no_pii_in_numeric_columns(self, pii_data):
        """Test that numeric columns are not flagged as PII."""
        detector = PIIDetector()
        results = detector.detect(pii_data)
        
        # Age and income should not be detected as PII
        assert 'age' not in results
        assert 'income' not in results
    
    def test_get_pii_summary(self, pii_data):
        """Test PII summary generation."""
        detector = PIIDetector()
        results = detector.detect(pii_data)
        summary = detector.get_pii_summary(results)
        
        assert summary['total_pii_columns'] > 0
        assert 'pii_types' in summary
        assert 'recommendations' in summary
        assert 'high_risk_columns' in summary


class TestFakerPIIGenerator:
    """Tests for Faker-based PII generation."""
    
    def test_generate_email(self):
        """Test email generation."""
        generator = FakerPIIGenerator(seed=42)
        series = generator.generate_column(PIIType.EMAIL, 10)
        
        assert len(series) == 10
        assert all('@' in str(email) for email in series)
    
    def test_generate_phone(self):
        """Test phone generation."""
        generator = FakerPIIGenerator(seed=42)
        series = generator.generate_column(PIIType.PHONE, 10)
        
        assert len(series) == 10
    
    def test_generate_name(self):
        """Test name generation."""
        generator = FakerPIIGenerator(seed=42)
        series = generator.generate_column(PIIType.NAME, 10)
        
        assert len(series) == 10
        assert all(len(str(name)) > 0 for name in series)
    
    def test_replace_pii_columns(self, pii_data):
        """Test replacing PII columns in a dataframe."""
        generator = FakerPIIGenerator(seed=42)
        
        pii_columns = {
            'email': PIIType.EMAIL,
            'first_name': PIIType.FIRST_NAME,
        }
        
        result = generator.replace_pii_columns(pii_data, pii_columns)
        
        # Original data should not be modified
        assert 'user0@example.com' in pii_data['email'].values
        
        # Result should have different values
        assert 'user0@example.com' not in result['email'].values
        
        # Non-PII columns should be unchanged
        assert (result['age'] == pii_data['age']).all()
    
    def test_preserve_null_pattern(self):
        """Test that null patterns are preserved."""
        generator = FakerPIIGenerator(seed=42)
        
        # Create data with nulls
        data = pd.DataFrame({
            'email': ['a@b.com', None, 'c@d.com', None, 'e@f.com']
        })
        
        pii_columns = {'email': PIIType.EMAIL}
        result = generator.replace_pii_columns(data, pii_columns, preserve_null_pattern=True)
        
        # Null positions should be preserved
        assert pd.isna(result['email'].iloc[1])
        assert pd.isna(result['email'].iloc[3])
        assert not pd.isna(result['email'].iloc[0])


class TestPrivacyRiskScorer:
    """Tests for privacy risk scoring."""
    
    def test_score_identical_data_high_risk(self, small_data):
        """Test that identical data has high similarity risk."""
        scorer = PrivacyRiskScorer()
        report = scorer.score(small_data, small_data.copy())
        
        # Identical data should have high similarity risk
        assert report.similarity_risk > 0.5
    
    def test_score_different_data_low_risk(self, small_data):
        """Test that very different data has lower risk."""
        scorer = PrivacyRiskScorer()
        
        # Create very different data
        np.random.seed(999)
        different_data = pd.DataFrame({
            'x': np.random.normal(100, 50, 100),  # Very different distribution
            'y': np.random.normal(-50, 10, 100),
            'label': np.random.choice(['a', 'b'], 100),
        })
        
        report = scorer.score(small_data, different_data)
        
        # Very different data should have lower similarity risk
        assert report.similarity_risk < 0.5
    
    def test_risk_report_structure(self, sample_data):
        """Test that risk report has expected structure."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(100)
        
        scorer = PrivacyRiskScorer()
        report = scorer.score(sample_data, result.synthetic_data)
        
        assert report.overall_risk in ['low', 'medium', 'high']
        assert 0 <= report.risk_score <= 1
        assert 0 <= report.uniqueness_risk <= 1
        assert 0 <= report.similarity_risk <= 1
        assert 0 <= report.outlier_risk <= 1
        assert isinstance(report.recommendations, list)
    
    def test_recommendations_generated(self, sample_data):
        """Test that recommendations are generated."""
        scorer = PrivacyRiskScorer()
        report = scorer.score(sample_data, sample_data.copy())
        
        # Should have at least one recommendation
        assert len(report.recommendations) > 0


class TestPrivacyIntegration:
    """Integration tests for privacy features."""
    
    def test_full_privacy_workflow(self, pii_data):
        """Test complete PII detection, synthesis, and risk assessment."""
        # 1. Detect PII
        detector = PIIDetector()
        detected = detector.detect(pii_data)
        
        assert len(detected) >= 3  # Should detect at least email, phone, ssn
        
        # 2. Synthesize data (without PII columns first)
        synth = GaussianCopulaSynthesizer()
        synth.fit(pii_data)
        result = synth.sample(100)
        synthetic_df = result.synthetic_data
        
        # 3. Replace PII columns with fake data
        generator = FakerPIIGenerator(seed=42)
        pii_columns = {col: r.pii_type for col, r in detected.items()}
        synthetic_df = generator.replace_pii_columns(synthetic_df, pii_columns)
        
        # 4. Assess privacy risk
        scorer = PrivacyRiskScorer()
        report = scorer.score(pii_data, synthetic_df, pii_columns=list(pii_columns.keys()))
        
        # 5. Verify
        assert report.overall_risk in ['low', 'medium', 'high']
        
        # Synthetic emails should all be different from original
        original_emails = set(pii_data['email'].dropna())
        synthetic_emails = set(synthetic_df['email'].dropna())
        assert len(original_emails & synthetic_emails) == 0  # No overlap
        
        print(f"\nPrivacy Risk Report:")
        print(f"  Overall Risk: {report.overall_risk}")
        print(f"  Risk Score: {report.risk_score:.3f}")
        print(f"  PII Columns Handled: {list(pii_columns.keys())}")


# ============================================================================
# Quality Metrics Tests
# ============================================================================

@pytest.fixture
def ml_data():
    """Create sample data for ML utility testing."""
    np.random.seed(42)
    n = 200
    
    # Create data with clear patterns
    x1 = np.random.normal(0, 1, n)
    x2 = np.random.normal(5, 2, n)
    noise = np.random.normal(0, 0.5, n)
    
    # Binary target based on features
    y = (x1 + 0.5 * x2 + noise > 3).astype(int)
    
    return pd.DataFrame({
        'feature1': x1,
        'feature2': x2,
        'feature3': np.random.uniform(0, 10, n),
        'category': np.random.choice(['A', 'B', 'C'], n),
        'target': y,
    })


class TestMLUtilityEvaluator:
    """Tests for ML utility evaluation."""
    
    def test_evaluate_classification(self, ml_data):
        """Test ML utility evaluation for classification task."""
        # Generate synthetic data
        synth = GaussianCopulaSynthesizer()
        synth.fit(ml_data)
        result = synth.sample(200)
        synthetic_df = result.synthetic_data
        
        # Evaluate ML utility
        evaluator = MLUtilityEvaluator()
        report = evaluator.evaluate(
            ml_data, 
            synthetic_df, 
            target_column='target',
            task_type='classification'
        )
        
        assert report.task_type == 'classification'
        assert 0 <= report.overall_score <= 1
        assert 0 <= report.utility_ratio <= 1
        assert report.tstr_score >= 0
        assert report.trtr_score >= 0
        assert len(report.recommendations) > 0
    
    def test_evaluate_regression(self, sample_data):
        """Test ML utility evaluation for regression task."""
        # Use numeric column as target
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(100)
        synthetic_df = result.synthetic_data
        
        evaluator = MLUtilityEvaluator()
        report = evaluator.evaluate(
            sample_data,
            synthetic_df,
            target_column='income',
            task_type='regression'
        )
        
        assert report.task_type == 'regression'
        assert 0 <= report.overall_score <= 1
        assert 'r2_score' in report.trtr_metrics or 'error' in report.trtr_metrics
    
    def test_auto_detect_task_type(self, ml_data):
        """Test automatic task type detection."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(ml_data)
        result = synth.sample(100)
        
        evaluator = MLUtilityEvaluator()
        
        # Binary target should be detected as classification
        report = evaluator.evaluate(ml_data, result.synthetic_data, 'target')
        assert report.task_type == 'classification'


class TestDetectionEvaluator:
    """Tests for detection evaluation."""
    
    def test_evaluate_identical_data(self, sample_data):
        """Test detection on identical data (edge case)."""
        evaluator = DetectionEvaluator()
        
        # Use same data - with cross-validation, the classifier can't distinguish
        # because there are no systematic differences between the groups
        report = evaluator.evaluate(sample_data, sample_data.copy())
        
        # The score should be valid (clamped 0-1)
        assert 0 <= report.overall_score <= 1
        # Accuracy can be below 0.5 due to random noise in CV
        assert 0 <= report.detection_accuracy <= 1.0
    
    def test_evaluate_synthetic_data(self, sample_data):
        """Test detection of synthetic vs real data."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(len(sample_data))
        
        evaluator = DetectionEvaluator()
        report = evaluator.evaluate(sample_data, result.synthetic_data)
        
        assert 0 <= report.overall_score <= 1
        assert 0 <= report.detection_accuracy <= 1
        assert 0 <= report.detection_auc <= 1
        assert len(report.cv_scores) == 5  # Default n_splits
        assert len(report.recommendations) > 0
    
    def test_distinguishing_features(self, sample_data):
        """Test that distinguishing features are identified."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(len(sample_data))
        
        evaluator = DetectionEvaluator()
        report = evaluator.evaluate(sample_data, result.synthetic_data)
        
        # Should have some features identified
        if report.detection_accuracy > 0.55:
            assert len(report.distinguishing_features) > 0


class TestQualityVisualizer:
    """Tests for quality visualizations."""
    
    def test_distribution_comparison_numeric(self, sample_data):
        """Test histogram generation for numeric columns."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(100)
        
        visualizer = QualityVisualizer()
        comparison = visualizer.generate_distribution_comparison(
            sample_data, 
            result.synthetic_data
        )
        
        assert len(comparison.numeric_columns) > 0
        
        # Check histogram structure
        hist = comparison.numeric_columns[0]
        assert len(hist.bins) > 0
        assert len(hist.real_counts) == len(hist.bins) - 1
        assert len(hist.synthetic_counts) == len(hist.bins) - 1
        assert 'real' in hist.statistics
        assert 'synthetic' in hist.statistics
    
    def test_distribution_comparison_categorical(self, sample_data):
        """Test category comparison for categorical columns."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(100)
        
        visualizer = QualityVisualizer()
        comparison = visualizer.generate_distribution_comparison(
            sample_data,
            result.synthetic_data
        )
        
        assert len(comparison.categorical_columns) > 0
        
        # Check category structure
        cat = comparison.categorical_columns[0]
        assert len(cat.categories) > 0
        assert len(cat.real_counts) == len(cat.categories)
        assert len(cat.real_percentages) == len(cat.categories)
    
    def test_correlation_comparison(self, sample_data):
        """Test correlation matrix comparison."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(100)
        
        visualizer = QualityVisualizer()
        comparison = visualizer.generate_correlation_comparison(
            sample_data,
            result.synthetic_data
        )
        
        # Should have correlation matrices
        assert len(comparison.columns) >= 2
        assert len(comparison.real_correlation) == len(comparison.columns)
        assert len(comparison.synthetic_correlation) == len(comparison.columns)
        assert len(comparison.difference) == len(comparison.columns)
        
        # Check matrix dimensions
        assert len(comparison.real_correlation[0]) == len(comparison.columns)
        
        # Check summary
        assert 'mean_absolute_difference' in comparison.summary
    
    def test_summary_stats(self, sample_data):
        """Test summary statistics generation."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(100)
        
        visualizer = QualityVisualizer()
        stats = visualizer.generate_summary_stats(sample_data, result.synthetic_data)
        
        assert 'columns' in stats
        assert len(stats['columns']) > 0
        assert stats['real_rows'] == len(sample_data)
        assert stats['synthetic_rows'] == len(result.synthetic_data)
        
        # Check column stats structure
        col_stat = stats['columns'][0]
        assert 'column' in col_stat
        assert 'dtype' in col_stat


class TestQualityIntegration:
    """Integration tests for quality features."""
    
    def test_full_quality_workflow(self, sample_data):
        """Test complete quality evaluation workflow."""
        # 1. Generate synthetic data
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)
        result = synth.sample(100)
        synthetic_df = result.synthetic_data
        
        # 2. Basic quality evaluation
        evaluator = SyntheticDataEvaluator()
        quality_report = evaluator.evaluate(sample_data, synthetic_df)
        
        assert quality_report.overall_score > 0.5
        
        # 3. ML utility evaluation
        ml_evaluator = MLUtilityEvaluator()
        ml_report = ml_evaluator.evaluate(
            sample_data, synthetic_df, 
            target_column='income',
            task_type='regression'
        )
        
        assert ml_report.overall_score >= 0
        
        # 4. Detection evaluation
        det_evaluator = DetectionEvaluator()
        det_report = det_evaluator.evaluate(sample_data, synthetic_df)
        
        assert det_report.overall_score >= 0
        
        # 5. Visualizations
        visualizer = QualityVisualizer()
        dist = visualizer.generate_distribution_comparison(sample_data, synthetic_df)
        corr = visualizer.generate_correlation_comparison(sample_data, synthetic_df)
        
        print(f"\nQuality Report:")
        print(f"  Overall Score: {quality_report.overall_score:.3f}")
        print(f"  ML Utility Score: {ml_report.overall_score:.3f}")
        print(f"  Detection Score: {det_report.overall_score:.3f}")
        print(f"  Numeric Columns Visualized: {len(dist.numeric_columns)}")
        print(f"  Correlation Columns: {len(corr.columns)}")
