#!/usr/bin/env python
"""Generate sample synthetic data output."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import json

def main():
    print("=== Synthetic Data Generation Demo ===")
    print()

    # Load sample data
    df = pd.read_csv("../example_data/sample_sales_data.csv")
    print(f"Source: {len(df)} rows from sample_sales_data.csv")
    print(f"Columns: {list(df.columns)}")
    print()

    # Generate synthetic
    from domains.synthetic.synthesizers import GaussianCopulaSynthesizer
    synth = GaussianCopulaSynthesizer()
    synth.fit(df)
    result = synth.sample(100)
    synthetic_df = result.synthetic_data

    print(f"Generated: {len(synthetic_df)} synthetic rows")
    print()

    # Save outputs
    synthetic_df.to_csv("../example_data/synthetic_sales_data.csv", index=False)
    print("Saved: example_data/synthetic_sales_data.csv")

    # Quality evaluation
    from domains.synthetic.evaluator import SyntheticDataEvaluator
    evaluator = SyntheticDataEvaluator()
    report = evaluator.evaluate(df, synthetic_df)

    quality_summary = {
        "overall_score": report.overall_score,
        "statistical_fidelity": report.statistical_fidelity_score,
        "correlation_preservation": report.correlation_score,
        "column_scores": {
            cs.column_name: {"score": cs.score, "rating": cs.rating} 
            for cs in report.column_scores
        },
        "recommendations": report.recommendations,
    }

    with open("../example_data/synthetic_quality_report.json", "w") as f:
        json.dump(quality_summary, f, indent=2)
    print("Saved: example_data/synthetic_quality_report.json")
    print()

    # Show comparison
    print("=== Distribution Comparison ===")
    header = f"{'Column':20} {'Real Mean':>12} {'Synth Mean':>12} {'Diff %':>8}"
    print(header)
    print("-" * len(header))
    for col in df.select_dtypes(include=[np.number]).columns:
        real_mean = df[col].mean()
        synth_mean = synthetic_df[col].mean()
        diff = abs(synth_mean - real_mean) / real_mean * 100 if real_mean != 0 else 0
        print(f"{col:20} {real_mean:>12.2f} {synth_mean:>12.2f} {diff:>7.1f}%")
    print()

    print("=== Quality Scores ===")
    print(f"Overall Score:     {report.overall_score:.3f}")
    print(f"Statistical Score: {report.statistical_fidelity_score:.3f}")
    print(f"Correlation Score: {report.correlation_score:.3f}")
    print()
    
    # Show sample rows
    print("=== Sample Synthetic Rows ===")
    print(synthetic_df.head(5).to_string(index=False))
    print()

    print("Done!")

if __name__ == "__main__":
    main()
