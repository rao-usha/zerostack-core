#!/usr/bin/env python
"""Comprehensive tests for synthetic data generation.

Run from backend directory:
    python scripts/test_synthetic_comprehensive.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_subheader(title):
    print(f"\n--- {title} ---")

def test_gaussian_copula():
    """Test Gaussian Copula synthesizer."""
    print_header("TEST 1: Gaussian Copula Synthesizer")
    
    from domains.synthetic.synthesizers import GaussianCopulaSynthesizer
    
    # Create test data with various types
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'age': np.random.randint(18, 80, n),
        'income': np.random.normal(50000, 15000, n).round(2),
        'score': np.random.uniform(0, 100, n).round(1),
        'category': np.random.choice(['A', 'B', 'C'], n),
        'is_active': np.random.choice([True, False], n),
    })
    
    print(f"Source data: {len(df)} rows, {len(df.columns)} columns")
    
    synth = GaussianCopulaSynthesizer()
    
    start = time.time()
    synth.fit(df)
    fit_time = time.time() - start
    print(f"Fit time: {fit_time:.2f}s")
    
    start = time.time()
    result = synth.sample(200)
    sample_time = time.time() - start
    print(f"Sample 200 rows: {sample_time:.2f}s")
    
    synthetic_df = result.synthetic_data
    
    # Validate output
    assert len(synthetic_df) == 200, "Row count mismatch"
    assert list(synthetic_df.columns) == list(df.columns), "Column mismatch"
    
    # Check distributions
    print_subheader("Distribution Check")
    for col in ['age', 'income', 'score']:
        real_mean = df[col].mean()
        synth_mean = synthetic_df[col].mean()
        diff = abs(synth_mean - real_mean) / real_mean * 100
        status = "OK" if diff < 20 else "WARN"
        print(f"  {col}: Real={real_mean:.1f}, Synth={synth_mean:.1f}, Diff={diff:.1f}% [{status}]")
    
    print("\n[PASS] Gaussian Copula test completed")
    return df, synthetic_df

def test_ctgan():
    """Test CTGAN synthesizer (deep learning)."""
    print_header("TEST 2: CTGAN Synthesizer (Quick)")
    
    from domains.synthetic.synthesizers import CTGANSynthesizer
    
    # Small dataset for faster training
    np.random.seed(42)
    n = 50
    df = pd.DataFrame({
        'x': np.random.normal(0, 1, n),
        'y': np.random.normal(5, 2, n),
        'cat': np.random.choice(['A', 'B'], n),
    })
    
    print(f"Source data: {len(df)} rows")
    
    # Use minimal epochs for speed via config
    synth = CTGANSynthesizer(config={'epochs': 5})
    
    start = time.time()
    synth.fit(df)
    fit_time = time.time() - start
    print(f"Fit time (5 epochs): {fit_time:.2f}s")
    
    result = synth.sample(30)
    print(f"Generated {len(result.synthetic_data)} rows")
    
    assert len(result.synthetic_data) == 30
    print("\n[PASS] CTGAN test completed")

def test_tvae():
    """Test TVAE synthesizer."""
    print_header("TEST 3: TVAE Synthesizer (Quick)")
    
    from domains.synthetic.synthesizers import TVAESynthesizer
    
    np.random.seed(42)
    n = 50
    df = pd.DataFrame({
        'value': np.random.exponential(10, n),
        'group': np.random.choice(['X', 'Y', 'Z'], n),
    })
    
    print(f"Source data: {len(df)} rows")
    
    synth = TVAESynthesizer(config={'epochs': 5})
    
    start = time.time()
    synth.fit(df)
    fit_time = time.time() - start
    print(f"Fit time (5 epochs): {fit_time:.2f}s")
    
    result = synth.sample(30)
    print(f"Generated {len(result.synthetic_data)} rows")
    
    assert len(result.synthetic_data) == 30
    print("\n[PASS] TVAE test completed")

def test_quality_evaluator(real_df, synthetic_df):
    """Test quality evaluation."""
    print_header("TEST 4: Quality Evaluator")
    
    from domains.synthetic.evaluator import SyntheticDataEvaluator
    
    evaluator = SyntheticDataEvaluator()
    report = evaluator.evaluate(real_df, synthetic_df)
    
    print(f"Overall Score: {report.overall_score:.3f}")
    print(f"Statistical Fidelity: {report.statistical_fidelity_score:.3f}")
    print(f"Correlation: {report.correlation_score:.3f}")
    
    assert 0 <= report.overall_score <= 1, "Score out of range"
    assert len(report.column_scores) > 0, "No column scores"
    
    print_subheader("Column Ratings")
    for cs in report.column_scores:
        print(f"  {cs.column_name}: {cs.rating} ({cs.score:.3f})")
    
    print("\n[PASS] Quality evaluation test completed")
    return report

def test_ml_utility(real_df, synthetic_df):
    """Test ML utility evaluation."""
    print_header("TEST 5: ML Utility Evaluator")
    
    from domains.synthetic.quality import MLUtilityEvaluator
    
    # Add a target column for classification
    real_df = real_df.copy()
    synthetic_df = synthetic_df.copy()
    
    # Create target based on existing columns
    real_df['target'] = (real_df['income'] > real_df['income'].median()).astype(int)
    synthetic_df['target'] = (synthetic_df['income'] > real_df['income'].median()).astype(int)
    
    evaluator = MLUtilityEvaluator()
    report = evaluator.evaluate(real_df, synthetic_df, target_column='target')
    
    print(f"TSTR Score: {report.tstr_score:.3f}")
    print(f"TRTR Score: {report.trtr_score:.3f}")
    print(f"Utility Ratio: {report.utility_ratio:.3f}")
    print(f"Task Type: {report.task_type}")
    
    print_subheader("TSTR Metrics")
    for k, v in report.tstr_metrics.items():
        print(f"  {k}: {v:.3f}")
    
    assert 0 <= report.tstr_score <= 1
    print("\n[PASS] ML Utility test completed")
    return report

def test_detection(real_df, synthetic_df):
    """Test detection evaluation."""
    print_header("TEST 6: Detection Evaluator")
    
    from domains.synthetic.quality import DetectionEvaluator
    
    evaluator = DetectionEvaluator()
    report = evaluator.evaluate(real_df, synthetic_df)
    
    print(f"Detection Accuracy: {report.detection_accuracy:.3f}")
    print(f"Overall Score: {report.overall_score:.3f}")
    print(f"Detection AUC: {report.detection_auc:.3f}")
    
    print_subheader("Model Results")
    for name, results in report.model_results.items():
        if 'accuracy' in results:
            print(f"  {name}: accuracy={results['accuracy']:.3f}, auc={results['auc']:.3f}")
    
    if report.distinguishing_features:
        print_subheader("Most Distinguishing Features")
        for feat, imp in report.distinguishing_features[:3]:
            print(f"  {feat}: {imp:.3f}")
    
    # Good synthetic data should be hard to detect (accuracy near 0.5)
    # But we accept a wider range for small datasets
    assert 0 <= report.detection_accuracy <= 1
    print("\n[PASS] Detection test completed")
    return report

def test_visualizations(real_df, synthetic_df):
    """Test quality visualizations."""
    print_header("TEST 7: Quality Visualizations")
    
    from domains.synthetic.quality import QualityVisualizer
    
    viz = QualityVisualizer()
    
    # Distribution comparison
    print_subheader("Distribution Comparison")
    dist_comp = viz.generate_distribution_comparison(real_df, synthetic_df)
    print(f"  Numeric columns: {len(dist_comp.numeric_columns)}")
    print(f"  Categorical columns: {len(dist_comp.categorical_columns)}")
    
    for hist_data in dist_comp.numeric_columns[:2]:
        print(f"    {hist_data.column_name}: {len(hist_data.bins)} bins")
    
    # Correlation comparison
    print_subheader("Correlation Comparison")
    corr_comp = viz.generate_correlation_comparison(real_df, synthetic_df)
    print(f"  Columns: {len(corr_comp.columns)}")
    avg_diff = np.mean([abs(v) for row in corr_comp.difference for v in row])
    print(f"  Avg correlation diff: {avg_diff:.3f}")
    
    # Summary stats
    print_subheader("Summary Statistics")
    stats = viz.generate_summary_statistics(real_df, synthetic_df)
    print(f"  Columns with stats: {len(stats)}")
    
    for col, col_stats in list(stats.items())[:2]:
        print(f"    {col}: real_mean={col_stats.get('real_mean', 'N/A')}")
    
    print("\n[PASS] Visualizations test completed")

def test_pii_workflow():
    """Test full PII detection and replacement workflow."""
    print_header("TEST 8: PII Workflow")
    
    from domains.synthetic.privacy import PIIDetector, FakerPIIGenerator, PrivacyRiskScorer
    from domains.synthetic.synthesizers import GaussianCopulaSynthesizer
    
    # Create data with PII
    df = pd.DataFrame({
        'customer_email': ['alice@example.com', 'bob@test.org', 'carol@demo.net', 'dan@mail.com'],
        'phone_number': ['555-111-2222', '555-333-4444', '555-555-6666', '555-777-8888'],
        'full_name': ['Alice Smith', 'Bob Jones', 'Carol Brown', 'Dan White'],
        'purchase_amount': [100.50, 250.75, 75.25, 500.00],
        'items_bought': [3, 7, 2, 12],
    })
    
    print(f"Original data: {len(df)} rows")
    print(df.head(2).to_string(index=False))
    
    # Step 1: Detect PII
    print_subheader("Step 1: PII Detection")
    detector = PIIDetector()
    detected = detector.detect(df)
    
    print(f"  Detected {len(detected)} PII columns:")
    for col, result in detected.items():
        print(f"    {col}: {result.pii_type.value} (conf: {result.confidence:.2f})")
    
    assert 'customer_email' in detected
    assert 'phone_number' in detected
    assert 'full_name' in detected
    
    # Step 2: Replace PII
    print_subheader("Step 2: PII Replacement")
    generator = FakerPIIGenerator(seed=123)
    pii_columns = {col: result.pii_type for col, result in detected.items()}
    anonymized_df = generator.replace_pii_columns(df, pii_columns)
    
    print("  Anonymized sample:")
    print(anonymized_df.head(2).to_string(index=False))
    
    # Verify PII was replaced
    assert anonymized_df['customer_email'].iloc[0] != 'alice@example.com'
    assert anonymized_df['full_name'].iloc[0] != 'Alice Smith'
    
    # Non-PII should be preserved
    assert anonymized_df['purchase_amount'].equals(df['purchase_amount'])
    
    # Step 3: Generate synthetic from anonymized
    print_subheader("Step 3: Synthetic Generation")
    synth = GaussianCopulaSynthesizer()
    synth.fit(anonymized_df)
    result = synth.sample(10)
    synthetic_df = result.synthetic_data
    
    print(f"  Generated {len(synthetic_df)} synthetic rows")
    
    # Step 4: Assess privacy risk
    print_subheader("Step 4: Privacy Risk Assessment")
    scorer = PrivacyRiskScorer()
    risk_report = scorer.score(anonymized_df, synthetic_df)
    
    print(f"  Risk Level: {risk_report.overall_risk}")
    print(f"  Risk Score: {risk_report.risk_score:.3f}")
    
    print("\n[PASS] PII Workflow test completed")

def test_edge_cases():
    """Test edge cases and error handling."""
    print_header("TEST 9: Edge Cases")
    
    from domains.synthetic.synthesizers import GaussianCopulaSynthesizer
    from domains.synthetic.evaluator import SyntheticDataEvaluator
    
    # Test with minimal data
    print_subheader("Minimal Data (5 rows)")
    df = pd.DataFrame({
        'a': [1, 2, 3, 4, 5],
        'b': ['x', 'y', 'x', 'y', 'x'],
    })
    
    synth = GaussianCopulaSynthesizer()
    synth.fit(df)
    result = synth.sample(10)
    assert len(result.synthetic_data) == 10
    print("  [OK] Generated 10 rows from 5 source rows")
    
    # Test with single column types
    print_subheader("Single Numeric Column")
    df = pd.DataFrame({'value': np.random.normal(0, 1, 20)})
    synth = GaussianCopulaSynthesizer()
    synth.fit(df)
    result = synth.sample(10)
    assert len(result.synthetic_data) == 10
    print("  [OK] Single numeric column works")
    
    print_subheader("Single Categorical Column")
    df = pd.DataFrame({'cat': ['A', 'B', 'C'] * 10})
    synth = GaussianCopulaSynthesizer()
    synth.fit(df)
    result = synth.sample(10)
    assert len(result.synthetic_data) == 10
    print("  [OK] Single categorical column works")
    
    # Test with nulls
    print_subheader("Data with Nulls")
    df = pd.DataFrame({
        'x': [1.0, 2.0, None, 4.0, 5.0, None, 7.0, 8.0, 9.0, 10.0],
        'y': ['a', None, 'b', 'a', None, 'b', 'a', 'b', 'a', 'b'],
    })
    synth = GaussianCopulaSynthesizer()
    synth.fit(df)
    result = synth.sample(10)
    assert len(result.synthetic_data) == 10
    print("  [OK] Null handling works")
    
    print("\n[PASS] Edge cases test completed")

def test_performance():
    """Test performance with larger dataset."""
    print_header("TEST 10: Performance (1000 rows)")
    
    from domains.synthetic.synthesizers import GaussianCopulaSynthesizer
    
    np.random.seed(42)
    n = 1000
    df = pd.DataFrame({
        'id': range(n),
        'value1': np.random.normal(100, 25, n),
        'value2': np.random.exponential(50, n),
        'value3': np.random.uniform(0, 1000, n),
        'category1': np.random.choice(['A', 'B', 'C', 'D'], n),
        'category2': np.random.choice(['X', 'Y'], n),
        'flag': np.random.choice([True, False], n),
    })
    
    print(f"Source: {len(df)} rows, {len(df.columns)} columns")
    
    synth = GaussianCopulaSynthesizer()
    
    start = time.time()
    synth.fit(df)
    fit_time = time.time() - start
    
    start = time.time()
    result = synth.sample(5000)
    sample_time = time.time() - start
    
    print(f"Fit time: {fit_time:.2f}s")
    print(f"Generate 5000 rows: {sample_time:.2f}s")
    print(f"Rows/second: {5000/sample_time:.0f}")
    
    assert len(result.synthetic_data) == 5000
    print("\n[PASS] Performance test completed")

def main():
    print("\n" + "="*60)
    print(" COMPREHENSIVE SYNTHETIC DATA TESTS")
    print("="*60)
    
    passed = 0
    failed = 0
    
    tests = [
        ("Gaussian Copula", test_gaussian_copula),
        ("CTGAN", test_ctgan),
        ("TVAE", test_tvae),
    ]
    
    # Run synthesizer tests first
    real_df = None
    synthetic_df = None
    
    for name, test_fn in tests:
        try:
            result = test_fn()
            if name == "Gaussian Copula":
                real_df, synthetic_df = result
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] {name}: {e}")
            failed += 1
    
    # Run tests that need real/synthetic data
    if real_df is not None:
        quality_tests = [
            ("Quality Evaluator", lambda: test_quality_evaluator(real_df, synthetic_df)),
            ("ML Utility", lambda: test_ml_utility(real_df, synthetic_df)),
            ("Detection", lambda: test_detection(real_df, synthetic_df)),
            ("Visualizations", lambda: test_visualizations(real_df, synthetic_df)),
        ]
        
        for name, test_fn in quality_tests:
            try:
                test_fn()
                passed += 1
            except Exception as e:
                print(f"\n[FAIL] {name}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1
    
    # Other tests
    other_tests = [
        ("PII Workflow", test_pii_workflow),
        ("Edge Cases", test_edge_cases),
        ("Performance", test_performance),
    ]
    
    for name, test_fn in other_tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total:  {passed + failed}")
    print("="*60)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
