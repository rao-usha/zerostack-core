#!/usr/bin/env python
"""Demo script for synthetic data generation.

Run from backend directory:
    python scripts/demo_synthetic.py
"""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

def main():
    print("=" * 60)
    print("SYNTHETIC DATA GENERATION DEMO")
    print("=" * 60)
    
    # Load sample data
    sample_file = "../example_data/sample_sales_data.csv"
    if not os.path.exists(sample_file):
        sample_file = "example_data/sample_sales_data.csv"
    
    print(f"\n1. Loading sample data from {sample_file}...")
    df = pd.read_csv(sample_file)
    print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"   Columns: {list(df.columns)}")
    
    # Show sample
    print("\n   Sample rows:")
    print(df.head(3).to_string(index=False))
    
    # Initialize synthesizer
    print("\n2. Initializing Gaussian Copula synthesizer...")
    from domains.synthetic.synthesizers import GaussianCopulaSynthesizer
    
    synth = GaussianCopulaSynthesizer()
    print(f"   Synthesizer: {synth.name}")
    
    # Fit
    print("\n3. Fitting synthesizer to data...")
    synth.fit(df)
    print("   Fitting complete!")
    
    # Generate
    num_rows = 50
    print(f"\n4. Generating {num_rows} synthetic rows...")
    result = synth.sample(num_rows)
    synthetic_df = result.synthetic_data
    print(f"   Generated {len(synthetic_df)} rows in {result.sample_time_seconds:.2f}s")
    
    # Show synthetic sample
    print("\n   Synthetic sample:")
    print(synthetic_df.head(3).to_string(index=False))
    
    # Quality evaluation
    print("\n5. Evaluating quality...")
    from domains.synthetic.evaluator import SyntheticDataEvaluator
    
    evaluator = SyntheticDataEvaluator()
    report = evaluator.evaluate(df, synthetic_df)
    
    print(f"\n   QUALITY REPORT")
    print(f"   -----------------------------")
    print(f"   Overall Score:     {report.overall_score:.3f}")
    print(f"   Statistical Score: {report.statistical_fidelity_score:.3f}")
    print(f"   Correlation Score: {report.correlation_score:.3f}")
    
    print(f"\n   Column Scores:")
    for cs in report.column_scores:
        print(f"     {cs.column_name:20} {cs.rating:10} ({cs.score:.3f})")
    
    print(f"\n   Recommendations:")
    for rec in report.recommendations:
        print(f"     • {rec}")
    
    # Compare distributions
    print("\n6. Distribution comparison...")
    print("\n   Numeric columns - Mean comparison:")
    for col in df.select_dtypes(include=[np.number]).columns:
        real_mean = df[col].mean()
        synth_mean = synthetic_df[col].mean()
        diff_pct = abs(synth_mean - real_mean) / real_mean * 100 if real_mean != 0 else 0
        print(f"     {col:15} Real: {real_mean:>12.2f}  Synth: {synth_mean:>12.2f}  Diff: {diff_pct:>5.1f}%")
    
    print("\n   Categorical columns - Value counts:")
    for col in df.select_dtypes(include=['object']).columns:
        if col == 'date':
            continue
        print(f"\n     {col}:")
        real_counts = df[col].value_counts(normalize=True)
        synth_counts = synthetic_df[col].value_counts(normalize=True)
        for val in real_counts.index:
            real_pct = real_counts.get(val, 0) * 100
            synth_pct = synth_counts.get(val, 0) * 100
            print(f"       {val:15} Real: {real_pct:>5.1f}%  Synth: {synth_pct:>5.1f}%")
    
    # PII Detection demo
    print("\n7. PII Detection demo...")
    
    # Create sample data with PII
    pii_df = pd.DataFrame({
        'email': ['john@example.com', 'jane@test.org', 'bob@company.net'],
        'phone': ['555-123-4567', '555-987-6543', '555-456-7890'],
        'name': ['John Smith', 'Jane Doe', 'Bob Johnson'],
        'ssn': ['123-45-6789', '987-65-4321', '456-78-9012'],
        'age': [30, 25, 45],
        'income': [50000, 75000, 100000],
    })
    
    from domains.synthetic.privacy import PIIDetector
    
    detector = PIIDetector()
    detected = detector.detect(pii_df)
    
    print("\n   Detected PII columns:")
    for col, result in detected.items():
        print(f"     {col:15} Type: {result.pii_type.value:15} Confidence: {result.confidence:.2f}")
    
    # PII replacement
    print("\n8. PII Replacement demo...")
    from domains.synthetic.privacy import FakerPIIGenerator
    
    generator = FakerPIIGenerator(seed=42)
    pii_columns = {col: result.pii_type for col, result in detected.items()}
    anonymized_df = generator.replace_pii_columns(pii_df, pii_columns)
    
    print("\n   Original data:")
    print(pii_df.to_string(index=False))
    
    print("\n   Anonymized data (PII replaced with fake):")
    print(anonymized_df.to_string(index=False))
    
    # Privacy risk demo
    print("\n9. Privacy Risk Assessment...")
    from domains.synthetic.privacy import PrivacyRiskScorer
    
    scorer = PrivacyRiskScorer()
    # Use the sales data for this demo
    risk_report = scorer.score(df, synthetic_df)
    
    print(f"\n   Risk Level: {risk_report.overall_risk.upper()}")
    print(f"   Risk Score: {risk_report.risk_score:.3f}")
    print(f"   Uniqueness Risk: {risk_report.uniqueness_risk:.3f}")
    print(f"   Similarity Risk: {risk_report.similarity_risk:.3f}")
    print(f"   Outlier Risk: {risk_report.outlier_risk:.3f}")
    
    if risk_report.recommendations:
        print(f"\n   Recommendations:")
        for rec in risk_report.recommendations[:2]:
            print(f"     * {rec}")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    
    return synthetic_df


if __name__ == "__main__":
    synthetic_df = main()
