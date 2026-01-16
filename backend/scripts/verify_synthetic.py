#!/usr/bin/env python
"""Verify synthetic data module is complete."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=== SYNTHETIC DATA MODULE VERIFICATION ===")
    print()
    
    passed = 0
    failed = 0

    # 1. Check all imports
    print("1. Checking imports...")
    try:
        from domains.synthetic.synthesizers import GaussianCopulaSynthesizer, CTGANSynthesizer, TVAESynthesizer
        print("   [OK] Synthesizers: GaussianCopula, CTGAN, TVAE")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Synthesizers: {e}")
        failed += 1

    try:
        from domains.synthetic.evaluator import SyntheticDataEvaluator
        print("   [OK] Evaluator")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Evaluator: {e}")
        failed += 1

    try:
        from domains.synthetic.privacy import PIIDetector, FakerPIIGenerator, PrivacyRiskScorer
        print("   [OK] Privacy: PIIDetector, FakerPIIGenerator, PrivacyRiskScorer")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Privacy: {e}")
        failed += 1

    try:
        from domains.synthetic.quality import MLUtilityEvaluator, DetectionEvaluator, QualityVisualizer
        print("   [OK] Quality: MLUtility, Detection, Visualizer")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Quality: {e}")
        failed += 1

    try:
        from domains.synthetic.models import SyntheticGenerateRequest, SyntheticDatasetResponse, QualityReportResponse
        print("   [OK] Models: SyntheticGenerateRequest, SyntheticDatasetResponse, QualityReportResponse")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Models: {e}")
        failed += 1

    try:
        from domains.synthetic.db_models import synthetic_jobs, synthetic_datasets, synthetic_quality_reports
        print("   [OK] DB Models")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] DB Models: {e}")
        failed += 1

    try:
        from domains.synthetic.service import SyntheticDataService
        print("   [OK] Service")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Service: {e}")
        failed += 1

    # 2. Test synthesis
    print()
    print("2. Testing synthesis pipeline...")
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    df = pd.DataFrame({
        "num1": np.random.normal(100, 20, 50),
        "num2": np.random.exponential(10, 50),
        "cat": np.random.choice(["A", "B", "C"], 50),
    })

    try:
        synth = GaussianCopulaSynthesizer()
        synth.fit(df)
        result = synth.sample(100)
        print(f"   [OK] Generated {len(result.synthetic_data)} rows")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Synthesis: {e}")
        failed += 1

    # 3. Test quality evaluation
    print()
    print("3. Testing quality evaluation...")
    try:
        evaluator = SyntheticDataEvaluator()
        report = evaluator.evaluate(df, result.synthetic_data)
        print(f"   [OK] Quality score: {report.overall_score:.3f}")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Quality evaluation: {e}")
        failed += 1

    # 4. Test privacy
    print()
    print("4. Testing privacy features...")
    try:
        pii_df = pd.DataFrame({"email": ["a@b.com"], "name": ["John"]})
        detector = PIIDetector()
        detected = detector.detect(pii_df)
        print(f"   [OK] Detected {len(detected)} PII columns")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] PII detection: {e}")
        failed += 1

    try:
        gen = FakerPIIGenerator(seed=42)
        pii_cols = {col: r.pii_type for col, r in detected.items()}
        anon = gen.replace_pii_columns(pii_df, pii_cols)
        email_col = anon["email"].iloc[0]
        print(f"   [OK] PII replaced: {email_col}")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] PII replacement: {e}")
        failed += 1

    try:
        scorer = PrivacyRiskScorer()
        risk = scorer.score(df, result.synthetic_data)
        print(f"   [OK] Risk level: {risk.overall_risk}")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Privacy risk: {e}")
        failed += 1

    # 5. Test quality metrics
    print()
    print("5. Testing quality metrics...")
    try:
        det = DetectionEvaluator()
        det_report = det.evaluate(df, result.synthetic_data)
        print(f"   [OK] Detection accuracy: {det_report.detection_accuracy:.3f}")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Detection: {e}")
        failed += 1

    try:
        viz = QualityVisualizer()
        dist = viz.generate_distribution_comparison(df, result.synthetic_data)
        print(f"   [OK] Distributions: {len(dist.numeric_columns)} numeric, {len(dist.categorical_columns)} categorical")
        passed += 1
    except Exception as e:
        print(f"   [FAIL] Visualizations: {e}")
        failed += 1

    # 6. Check files exist
    print()
    print("6. Checking module files...")
    files = [
        "domains/synthetic/__init__.py",
        "domains/synthetic/router.py",
        "domains/synthetic/service.py",
        "domains/synthetic/models.py",
        "domains/synthetic/db_models.py",
        "domains/synthetic/evaluator.py",
        "domains/synthetic/synthesizers/__init__.py",
        "domains/synthetic/synthesizers/copula.py",
        "domains/synthetic/synthesizers/ctgan.py",
        "domains/synthetic/synthesizers/tvae.py",
        "domains/synthetic/privacy/__init__.py",
        "domains/synthetic/privacy/pii_detector.py",
        "domains/synthetic/privacy/faker_generator.py",
        "domains/synthetic/privacy/risk_scorer.py",
        "domains/synthetic/quality/__init__.py",
        "domains/synthetic/quality/ml_utility.py",
        "domains/synthetic/quality/detection.py",
        "domains/synthetic/quality/visualizations.py",
    ]
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print(f"   [WARN] Missing: {missing}")
        failed += 1
    else:
        print(f"   [OK] All {len(files)} module files present")
        passed += 1

    # Summary
    print()
    print("=" * 50)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed == 0:
        print("\n=== ALL VERIFICATIONS PASSED ===")
        return 0
    else:
        print("\n=== SOME VERIFICATIONS FAILED ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())
