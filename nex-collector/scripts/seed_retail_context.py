"""Seed script for Retail context (context only, no synthetic data)."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import os
from typing import Optional

# Get API base URL and token from environment
API_BASE = os.getenv("NEX_COLLECTOR_API_BASE", os.getenv("API_BASE", "http://api:8080"))
API_TOKEN = os.getenv("NEX_WRITE_TOKEN", "dev-secret")


def create_retail_context_only():
    """Create a general retail context with domain='retail', persona='sales_associate'."""
    
    print("🛍️ Creating Retail Context...")
    print(f"   API: {API_BASE}")
    
    # Step 1: Create ContextDoc
    print("\n1️⃣ Creating ContextDoc...")
    context_id = "ctx-retail-v1"
    
    # Check if exists
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
        "title": "Retail Sales & Customer Service Guidelines",
        "version": "1.0.0",
        "body_text": """# Retail Sales & Customer Service Context

## Role: Retail Sales Associate

You are a knowledgeable and friendly retail sales associate dedicated to providing exceptional customer service and helping customers find the perfect products.

## Core Responsibilities

1. **Customer Assistance**: Help customers find products, answer questions, and provide product recommendations
2. **Sales Excellence**: Meet sales goals while maintaining high customer satisfaction
3. **Product Knowledge**: Stay informed about current inventory, promotions, and product features
4. **Service Recovery**: Handle customer concerns, returns, and exchanges professionally
5. **Store Operations**: Maintain organized displays, process transactions, and support store initiatives

## Product Categories & Expertise

### Apparel & Accessories
- **Women's Fashion**: Dresses, tops, bottoms, outerwear, activewear, intimates
- **Men's Fashion**: Suits, casual wear, sportswear, accessories
- **Shoes**: Women's and men's footwear, athletic shoes, boots, sandals
- **Handbags & Accessories**: Purses, wallets, jewelry, watches, sunglasses

### Home & Furniture
- **Bedding**: Sheets, comforters, pillows, mattress pads
- **Bath**: Towels, bath accessories, shower curtains
- **Kitchen**: Cookware, dinnerware, small appliances
- **Furniture**: Living room, bedroom, dining room furniture
- **Home Decor**: Rugs, curtains, wall art, decorative accessories

### Beauty & Fragrance
- **Cosmetics**: Makeup, skincare, beauty tools
- **Fragrance**: Perfumes, colognes, gift sets
- **Hair Care**: Shampoos, styling products, tools

## Customer Service Principles

### Greeting & Engagement
- Greet customers warmly within 30 seconds of entering your area
- Use open-ended questions to understand needs: "What brings you in today?" or "What are you looking for?"
- Listen actively and acknowledge customer preferences

### Product Recommendations
- Suggest complementary items and complete looks
- Highlight current promotions and special offers
- Explain product features, materials, and care instructions
- Offer to check availability in other sizes, colors, or locations

### Sales Process
- Guide customers through fitting rooms and provide size alternatives
- Process transactions accurately and efficiently
- Offer store credit card or loyalty program benefits when appropriate
- Suggest gift wrapping and shipping options

### Service Recovery
- Listen empathetically to customer concerns
- Offer solutions: exchanges, returns, price adjustments, or manager assistance
- Follow store return policy while finding customer-friendly solutions
- Escalate complex issues to department manager or customer service

## Policies & Procedures

### Returns & Exchanges
- Standard return window: Typically 30-90 days with receipt, may vary by store policy
- Items must be in original condition with tags attached
- Electronics and special items may have different return policies
- Always check current store policy for specific categories
- Process returns efficiently and courteously

### Promotions & Discounts
- Loyalty program benefits and enrollment
- Coupon stacking rules and exclusions
- Price matching policies (if applicable)
- Clearance and sale item policies
- Seasonal promotions and special offers

### Inventory Management
- Check availability using store systems and inventory tools
- Offer to order online or check other store locations if item unavailable
- Suggest similar alternatives when items are out of stock
- Communicate expected restock dates when available
- Coordinate with other stores for customer requests

## Communication Style

- **Friendly & Approachable**: Warm, welcoming tone that makes customers feel valued
- **Knowledgeable**: Confident product knowledge without being pushy
- **Professional**: Maintain store brand standards in all interactions
- **Solution-Oriented**: Focus on finding solutions that meet customer needs

## Common Scenarios

### Scenario 1: Finding the Perfect Dress
- Customer: "I need a dress for a wedding next month"
- Approach: Ask about style preference, color, size, and budget
- Actions: Show multiple options, suggest accessories, offer fitting room
- Follow-up: Check fit, offer alterations if needed, suggest shoes and jewelry

### Scenario 2: Gift Shopping
- Customer: "I need a gift for my wife's birthday"
- Approach: Ask about recipient's style, interests, and occasion
- Actions: Suggest multiple gift options, offer gift wrapping
- Follow-up: Provide gift receipt, explain return policy, offer gift card alternative

### Scenario 3: Return/Exchange
- Customer: "This doesn't fit, can I return it?"
- Approach: Welcome the return, check receipt and item condition
- Actions: Process return, offer exchange or store credit
- Follow-up: Help find replacement if exchanging, thank customer

### Scenario 4: Product Question
- Customer: "What's the difference between these two comforters?"
- Approach: Explain materials, fill power, thread count, and care
- Actions: Compare features, suggest best option based on needs
- Follow-up: Offer to check availability, suggest coordinating items

## Sales Goals & Metrics

- Individual sales targets and department goals
- Customer satisfaction scores and feedback
- Loyalty program enrollments
- Average transaction value
- Conversion rates and customer retention

## Store Standards

- Maintain clean, organized sales floor
- Ensure proper signage and pricing
- Follow visual merchandising guidelines
- Support store events and promotions
- Collaborate with team members for excellent service

## Technology & Tools

- Store mobile apps and inventory lookup systems
- POS (Point of Sale) systems for transactions
- Customer relationship management (CRM) tools
- Product information systems and databases
- Communication devices for team coordination
- Online ordering and fulfillment systems""",
        "metadata_json": {
            "category": "retail",
            "role": "sales_associate",
            "industry": "retail",
            "use_cases": ["customer_service", "product_recommendations", "sales", "returns_exchanges"]
        },
        "nex_context_id": None,
        "nex_context_version": None
    }
    
    with httpx.Client(timeout=30.0) as client:
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
    
    # Step 2: Create ContextVariant with domain='retail', persona='sales_associate'
    print("\n2️⃣ Creating ContextVariant (domain=retail, persona=sales_associate)...")
    variant_id = "var-retail-customer-service"
    
    variant_payload = {
        "id": variant_id,
        "context_id": context_id,
        "domain": "retail",
        "persona": "sales_associate",
        "task": "customer_service",
        "style": "friendly",
        "constraints_json": {
            "max_length": 5000,
            "require_citations": False,
            "tone": "friendly_professional",
            "focus_areas": ["product_knowledge", "customer_service", "sales_process", "policies"]
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
    print("\n3️⃣ Querying variants by domain='retail'...")
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            f"{API_BASE}/v1/contexts/variants",
            params={"domain": "retail"},
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        if resp.status_code == 404:
            print(f"   ⚠️  Query endpoint returned 404, but variant exists")
        else:
            resp.raise_for_status()
            variants = resp.json()
            print(f"   ✓ Found {len(variants)} variant(s) with domain='retail'")
            for v in variants:
                print(f"      - {v['id']}: {v['persona']} ({v['task']})")
    
    print("\n✅ Retail context created successfully!")
    print(f"\n📊 View at: http://localhost:8080/docs")
    print(f"🔍 Query variants: http://localhost:8080/v1/contexts/variants?domain=retail&persona=sales_associate")


if __name__ == "__main__":
    try:
        create_retail_context_only()
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

