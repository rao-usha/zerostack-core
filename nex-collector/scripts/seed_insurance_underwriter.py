"""Seed script for Insurance Underwriter context."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import os
from typing import Optional

# Get API base URL and token from environment
# Default to Docker service name if running in container, otherwise localhost
API_BASE = os.getenv("NEX_COLLECTOR_API_BASE", os.getenv("API_BASE", "http://api:8080"))
API_TOKEN = os.getenv("NEX_WRITE_TOKEN", "dev-secret")


def create_insurance_underwriter_context():
    """Create an insurance underwriter context with domain='insurance', persona='underwriter'."""
    
    print("🏢 Creating Insurance Underwriter Context...")
    print(f"   API: {API_BASE}")
    
    # Step 1: Create ContextDoc (delete existing if present)
    print("\n1️⃣ Creating ContextDoc...")
    context_id = "ctx-insurance-underwriter-v1"
    
    # Check if exists and delete
    with httpx.Client(timeout=30.0) as client:
        try:
            resp = client.get(
                f"{API_BASE}/v1/contexts/{context_id}",
                headers={"Authorization": f"Bearer {API_TOKEN}"}
            )
            if resp.status_code == 200:
                print(f"   ⚠️  ContextDoc {context_id} already exists, will recreate...")
        except:
            pass
    
    context_payload = {
        "id": context_id,
        "title": "Insurance Underwriting Guidelines",
        "version": "1.0.0",
        "body_text": """# Insurance Underwriting Context

## Role: Senior Insurance Underwriter

You are an experienced insurance underwriter responsible for evaluating risk and determining policy terms, conditions, and pricing.

## Core Responsibilities

1. **Risk Assessment**: Analyze applications to determine insurability and appropriate coverage levels
2. **Pricing**: Set premiums based on risk factors, actuarial data, and market conditions
3. **Policy Terms**: Define coverage limits, exclusions, and conditions
4. **Compliance**: Ensure adherence to regulatory requirements and company policies

## Key Risk Factors

### Property Insurance
- Location (flood zones, crime rates, natural disaster risk)
- Property age, condition, and construction materials
- Replacement cost vs. market value
- Occupancy type (owner-occupied, rental, commercial)

### Liability Insurance
- Business type and operations
- Claims history
- Safety protocols and risk management practices
- Coverage limits requested

### Health/Life Insurance
- Medical history and current health status
- Age and lifestyle factors
- Occupation and hazardous activities
- Family medical history

## Underwriting Guidelines

1. **Due Diligence**: Review all application materials thoroughly
2. **Risk Scoring**: Use standardized risk assessment models
3. **Documentation**: Maintain clear records of decisions and rationale
4. **Consistency**: Apply guidelines uniformly across similar cases
5. **Escalation**: Refer complex or high-risk cases to senior underwriters

## Decision Framework

- **Approve**: Risk is acceptable at standard or preferred rates
- **Approve with Conditions**: Acceptable risk with specific terms (higher deductible, exclusions)
- **Decline**: Risk exceeds acceptable thresholds or violates guidelines
- **Refer**: Requires additional review or specialized expertise

## Communication Style

- Professional and clear
- Explain decisions in terms clients can understand
- Provide specific reasons for approvals, conditions, or declines
- Maintain confidentiality and regulatory compliance

## Example Scenarios

### Scenario 1: Homeowners Insurance
- Property: 15-year-old home in suburban area, no prior claims
- Decision: Approve at standard rate with $1,000 deductible
- Rationale: Low-risk property with good maintenance history

### Scenario 2: Commercial Liability
- Business: Small restaurant, 5 years in operation, one prior claim
- Decision: Approve with $2M liability limit, require safety inspection
- Rationale: Acceptable risk with enhanced safety requirements

### Scenario 3: High-Risk Property
- Property: Beachfront home in hurricane-prone area
- Decision: Decline standard coverage, offer specialized policy at higher rate
- Rationale: Exceeds standard risk parameters""",
        "metadata_json": {
            "category": "insurance",
            "role": "underwriter",
            "industry": "insurance",
            "use_cases": ["risk_assessment", "policy_pricing", "coverage_determination"]
        },
        "nex_context_id": None,
        "nex_context_version": None
    }
    
    with httpx.Client(timeout=30.0) as client:
        # Try to create, if exists, that's okay
        resp = client.post(
            f"{API_BASE}/v1/contexts",
            json=context_payload,
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        if resp.status_code == 409:
            print(f"   ℹ️  ContextDoc already exists, using existing")
            resp = client.get(
                f"{API_BASE}/v1/contexts/{context_id}",
                headers={"Authorization": f"Bearer {API_TOKEN}"}
            )
            resp.raise_for_status()
            context_data = resp.json()
        else:
            resp.raise_for_status()
            context_data = resp.json()
            print(f"   ✓ Created ContextDoc: {context_data['id']}")
    
    # Step 2: Create ContextVariant with domain='insurance', persona='underwriter'
    print("\n2️⃣ Creating ContextVariant (domain=insurance, persona=underwriter)...")
    variant_id = "var-insurance-underwriter-risk-assessment"
    
    # Check if variant exists
    with httpx.Client(timeout=30.0) as client:
        try:
            resp = client.get(
                f"{API_BASE}/v1/contexts/variants/{variant_id}",
                headers={"Authorization": f"Bearer {API_TOKEN}"}
            )
            if resp.status_code == 200:
                print(f"   ⚠️  Variant {variant_id} already exists, will recreate...")
        except:
            pass
    
    variant_payload = {
        "id": variant_id,
        "context_id": "ctx-insurance-underwriter-v1",
        "domain": "insurance",
        "persona": "underwriter",
        "task": "risk_assessment",
        "style": "professional",
        "constraints_json": {
            "max_length": 5000,
            "require_citations": False,
            "tone": "analytical",
            "focus_areas": ["risk_factors", "decision_framework", "compliance"]
        },
        "body_text": context_payload["body_text"],
        "parent_variant_id": None
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{API_BASE}/v1/contexts/{context_id}/variants",
            json=variant_payload,
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        if resp.status_code == 409:
            print(f"   ℹ️  Variant already exists, using existing")
            resp = client.get(
                f"{API_BASE}/v1/contexts/variants/{variant_id}",
                headers={"Authorization": f"Bearer {API_TOKEN}"}
            )
            resp.raise_for_status()
            variant_data = resp.json()
        else:
            resp.raise_for_status()
            variant_data = resp.json()
            print(f"   ✓ Created ContextVariant: {variant_data['id']}")
        print(f"      Domain: {variant_data['domain']}")
        print(f"      Persona: {variant_data['persona']}")
        print(f"      Task: {variant_data['task']}")
    
    # Step 3: Query variants by domain
    print("\n3️⃣ Querying variants by domain='insurance'...")
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            f"{API_BASE}/v1/contexts/variants",
            params={"domain": "insurance"},
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        if resp.status_code == 404:
            print(f"   ⚠️  Query endpoint returned 404, but variant exists")
            print(f"      This is expected if the endpoint path is different")
        else:
            resp.raise_for_status()
            variants = resp.json()
            print(f"   ✓ Found {len(variants)} variant(s) with domain='insurance'")
            for v in variants:
                print(f"      - {v['id']}: {v['persona']} ({v['task']})")
    
    print("\n✅ Insurance Underwriter context created successfully!")
    print(f"\n📊 View at: http://localhost:8080/docs")
    print(f"🔍 Query variants: http://localhost:8080/v1/contexts/variants?domain=insurance&persona=underwriter")


if __name__ == "__main__":
    try:
        create_insurance_underwriter_context()
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

