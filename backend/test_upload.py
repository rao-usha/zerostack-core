"""
Quick test script for the CSV upload endpoint.

Run: python test_upload.py
Requires: requests, pandas
"""
import requests
import io
import pandas as pd

# Create sample PE due diligence data
sample_data = pd.DataFrame({
    'date': ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
    'revenue': [1500000, 1650000, 1720000, 1800000, 1950000, 2100000],
    'gross_margin': [0.42, 0.43, 0.44, 0.43, 0.45, 0.46],
    'headcount': [45, 48, 52, 55, 58, 62],
    'customer_count': [120, 128, 135, 142, 155, 168],
    'churn_rate': [0.02, 0.018, 0.022, 0.015, 0.019, 0.016],
    'arr': [18000000, 19800000, 20640000, 21600000, 23400000, 25200000],
    'sales_lead': ['John Smith', 'Jane Doe', 'John Smith', 'Jane Doe', 'Mike Johnson', 'Jane Doe'],
    'region': ['North', 'South', 'North', 'West', 'East', 'South'],
    'contact_email': ['john@acme.com', 'jane@acme.com', 'john@acme.com', 'jane@acme.com', 'mike@acme.com', 'jane@acme.com'],
})

# Save to CSV buffer
csv_buffer = io.StringIO()
sample_data.to_csv(csv_buffer, index=False)
csv_content = csv_buffer.getvalue().encode()

# Test the endpoint
API_URL = "http://localhost:8000/api/v1/ingest/upload"

print("Testing CSV upload endpoint...")
print(f"URL: {API_URL}")
print(f"File size: {len(csv_content)} bytes")
print("-" * 50)

try:
    response = requests.post(
        API_URL,
        files={"file": ("sample_financials.csv", csv_content, "text/csv")},
        timeout=30,
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"\nSummary: {result['summary']}")
        print(f"\nQuality Score: {result['overall_quality_score']}/100")
        print(f"\nDetected Categories: {', '.join(result['detected_data_categories'])}")

        print(f"\n--- Column Analysis ---")
        for sheet in result['sheets']:
            print(f"\nSheet: {sheet['sheet_name']} ({sheet['row_count']} rows)")
            for col in sheet['columns']:
                flags = f" ⚠️ {', '.join(col['quality_flags'])}" if col['quality_flags'] else ""
                print(f"  • {col['name']}: {col['inferred_type']} (nulls: {col['null_percent']}%){flags}")

        if result['potential_issues']:
            print(f"\n--- Potential Issues ---")
            for issue in result['potential_issues']:
                print(f"  ⚠️ {issue}")

        if result['recommendations']:
            print(f"\n--- Recommendations ---")
            for rec in result['recommendations']:
                print(f"  💡 {rec}")

    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Connection failed. Make sure the backend is running:")
    print("   cd backend && uvicorn main:app --reload --port 8000")
except Exception as e:
    print(f"❌ Error: {e}")
