"""
Seed database with comprehensive demo data for ZeroStack demos.

Creates sample tables for:
- Data Explorer browsing
- Lineage analysis demos
- ML feature engineering examples
- Chat with data queries

Usage:
    cd backend
    python scripts/seed_demo_data.py
"""

import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv('../.env')

from sqlalchemy import create_engine, text
from core.config import settings


# Sample data generators
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Emma", "Oliver", "Ava", "Liam", "Sophia",
    "Noah", "Isabella", "Ethan", "Mia", "Lucas", "Charlotte", "Mason", "Amelia"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
]

COUNTRIES = [
    ("US", "United States"), ("UK", "United Kingdom"), ("CA", "Canada"),
    ("DE", "Germany"), ("FR", "France"), ("AU", "Australia"),
    ("JP", "Japan"), ("BR", "Brazil"), ("IN", "India"), ("MX", "Mexico")
]

PRODUCT_CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Food", "Health"]

PRODUCT_NAMES = {
    "Electronics": ["Laptop Pro", "Wireless Headphones", "Smart Watch", "Tablet", "Bluetooth Speaker", "Camera"],
    "Clothing": ["Cotton T-Shirt", "Denim Jeans", "Winter Jacket", "Running Shoes", "Dress Shirt", "Sneakers"],
    "Home & Garden": ["Coffee Maker", "Desk Lamp", "Plant Pot", "Throw Pillow", "Wall Clock", "Rug"],
    "Sports": ["Yoga Mat", "Dumbbell Set", "Tennis Racket", "Basketball", "Bicycle Helmet", "Fitness Tracker"],
    "Books": ["Mystery Novel", "Cookbook", "Biography", "Science Fiction", "Self-Help Guide", "History Book"],
    "Toys": ["Building Blocks", "Board Game", "Action Figure", "Puzzle Set", "RC Car", "Stuffed Animal"],
    "Food": ["Organic Coffee", "Chocolate Box", "Snack Pack", "Tea Collection", "Spice Set", "Honey Jar"],
    "Health": ["Vitamins", "First Aid Kit", "Essential Oils", "Protein Powder", "Face Cream", "Sunscreen"]
}

ORDER_STATUSES = ["completed", "completed", "completed", "completed", "shipped", "processing", "cancelled"]


def random_date(start_year=2022, end_year=2024):
    """Generate a random date."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def create_demo_schema(engine):
    """Create demo schema and tables."""

    ddl = """
    -- Create demo schema
    CREATE SCHEMA IF NOT EXISTS demo;

    -- Customers table
    DROP TABLE IF EXISTS demo.order_items CASCADE;
    DROP TABLE IF EXISTS demo.orders CASCADE;
    DROP TABLE IF EXISTS demo.products CASCADE;
    DROP TABLE IF EXISTS demo.customers CASCADE;
    DROP TABLE IF EXISTS demo.customer_segments CASCADE;
    DROP TABLE IF EXISTS demo.sales_summary CASCADE;

    CREATE TABLE demo.customers (
        customer_id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        country_code VARCHAR(2),
        country_name VARCHAR(50),
        signup_date DATE NOT NULL,
        is_active BOOLEAN DEFAULT true,
        lifetime_value DECIMAL(12,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    );

    COMMENT ON TABLE demo.customers IS 'Customer master data with contact info and lifetime metrics';
    COMMENT ON COLUMN demo.customers.customer_id IS 'Unique customer identifier';
    COMMENT ON COLUMN demo.customers.lifetime_value IS 'Total revenue from this customer';

    -- Products table
    CREATE TABLE demo.products (
        product_id SERIAL PRIMARY KEY,
        product_name VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        cost_price DECIMAL(10,2) NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW()
    );

    COMMENT ON TABLE demo.products IS 'Product catalog with pricing and inventory';
    COMMENT ON COLUMN demo.products.unit_price IS 'Selling price per unit';
    COMMENT ON COLUMN demo.products.cost_price IS 'Cost to acquire/produce';

    -- Orders table
    CREATE TABLE demo.orders (
        order_id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES demo.customers(customer_id),
        order_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'processing',
        total_amount DECIMAL(12,2) NOT NULL,
        discount_amount DECIMAL(10,2) DEFAULT 0,
        shipping_country VARCHAR(2),
        created_at TIMESTAMP DEFAULT NOW()
    );

    COMMENT ON TABLE demo.orders IS 'Order headers with totals and status';

    -- Order Items table
    CREATE TABLE demo.order_items (
        item_id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES demo.orders(order_id),
        product_id INTEGER REFERENCES demo.products(product_id),
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        line_total DECIMAL(12,2) NOT NULL
    );

    COMMENT ON TABLE demo.order_items IS 'Individual line items within orders';

    -- Customer Segments (for ML demo)
    CREATE TABLE demo.customer_segments (
        segment_id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES demo.customers(customer_id),
        segment_name VARCHAR(50),
        rfm_score INTEGER,
        churn_risk DECIMAL(5,4),
        predicted_ltv DECIMAL(12,2),
        last_updated TIMESTAMP DEFAULT NOW()
    );

    COMMENT ON TABLE demo.customer_segments IS 'ML-derived customer segmentation and predictions';

    -- Sales Summary (aggregated view for reporting)
    CREATE TABLE demo.sales_summary (
        summary_id SERIAL PRIMARY KEY,
        report_date DATE NOT NULL,
        country_code VARCHAR(2),
        category VARCHAR(50),
        total_orders INTEGER,
        total_revenue DECIMAL(14,2),
        avg_order_value DECIMAL(10,2),
        unique_customers INTEGER
    );

    COMMENT ON TABLE demo.sales_summary IS 'Daily aggregated sales metrics by country and category';

    -- Create indexes for better query performance
    CREATE INDEX idx_customers_country ON demo.customers(country_code);
    CREATE INDEX idx_customers_signup ON demo.customers(signup_date);
    CREATE INDEX idx_orders_customer ON demo.orders(customer_id);
    CREATE INDEX idx_orders_date ON demo.orders(order_date);
    CREATE INDEX idx_order_items_order ON demo.order_items(order_id);
    CREATE INDEX idx_order_items_product ON demo.order_items(product_id);
    CREATE INDEX idx_products_category ON demo.products(category);
    """

    with engine.connect() as conn:
        for statement in ddl.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(text(statement))
                except Exception as e:
                    print(f"Warning: {e}")
        conn.commit()

    print("[OK] Created demo schema and tables")


def seed_products(engine, count=50):
    """Seed products table."""
    products = []

    for category, names in PRODUCT_NAMES.items():
        for name in names:
            base_price = random.uniform(10, 500)
            products.append({
                "product_name": name,
                "category": category,
                "unit_price": round(base_price, 2),
                "cost_price": round(base_price * random.uniform(0.4, 0.7), 2),
                "stock_quantity": random.randint(0, 500),
                "is_active": random.random() > 0.1
            })

    with engine.connect() as conn:
        for p in products:
            conn.execute(text("""
                INSERT INTO demo.products (product_name, category, unit_price, cost_price, stock_quantity, is_active)
                VALUES (:product_name, :category, :unit_price, :cost_price, :stock_quantity, :is_active)
            """), p)
        conn.commit()

    print(f"[OK] Seeded {len(products)} products")
    return len(products)


def seed_customers(engine, count=500):
    """Seed customers table."""
    emails_used = set()

    with engine.connect() as conn:
        for i in range(count):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)

            # Generate unique email
            base_email = f"{first.lower()}.{last.lower()}"
            email = f"{base_email}@example.com"
            counter = 1
            while email in emails_used:
                email = f"{base_email}{counter}@example.com"
                counter += 1
            emails_used.add(email)

            country = random.choice(COUNTRIES)
            signup = random_date(2020, 2024)

            conn.execute(text("""
                INSERT INTO demo.customers (first_name, last_name, email, country_code, country_name, signup_date, is_active)
                VALUES (:first_name, :last_name, :email, :country_code, :country_name, :signup_date, :is_active)
            """), {
                "first_name": first,
                "last_name": last,
                "email": email,
                "country_code": country[0],
                "country_name": country[1],
                "signup_date": signup.date(),
                "is_active": random.random() > 0.15
            })
        conn.commit()

    print(f"[OK] Seeded {count} customers")


def seed_orders(engine, order_count=2000):
    """Seed orders and order items."""

    with engine.connect() as conn:
        # Get customer and product IDs
        customers = [r[0] for r in conn.execute(text("SELECT customer_id FROM demo.customers")).fetchall()]
        products = [(r[0], r[1]) for r in conn.execute(text("SELECT product_id, unit_price FROM demo.products")).fetchall()]

        for i in range(order_count):
            customer_id = random.choice(customers)
            order_date = random_date(2022, 2024)
            status = random.choice(ORDER_STATUSES)

            # Get customer country for shipping
            country = conn.execute(text(
                "SELECT country_code FROM demo.customers WHERE customer_id = :cid"
            ), {"cid": customer_id}).fetchone()[0]

            # Create order with placeholder total
            result = conn.execute(text("""
                INSERT INTO demo.orders (customer_id, order_date, status, total_amount, discount_amount, shipping_country)
                VALUES (:customer_id, :order_date, :status, 0, :discount, :country)
                RETURNING order_id
            """), {
                "customer_id": customer_id,
                "order_date": order_date.date(),
                "status": status,
                "discount": round(random.uniform(0, 20), 2) if random.random() > 0.7 else 0,
                "country": country
            })
            order_id = result.fetchone()[0]

            # Add 1-5 items to order
            num_items = random.randint(1, 5)
            order_total = 0

            for _ in range(num_items):
                product_id, unit_price = random.choice(products)
                quantity = random.randint(1, 4)
                line_total = float(unit_price) * quantity
                order_total += line_total

                conn.execute(text("""
                    INSERT INTO demo.order_items (order_id, product_id, quantity, unit_price, line_total)
                    VALUES (:order_id, :product_id, :quantity, :unit_price, :line_total)
                """), {
                    "order_id": order_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": round(line_total, 2)
                })

            # Update order total
            conn.execute(text("""
                UPDATE demo.orders SET total_amount = :total WHERE order_id = :oid
            """), {"total": round(order_total, 2), "oid": order_id})

            if (i + 1) % 500 == 0:
                conn.commit()
                print(f"  ... created {i + 1} orders")

        conn.commit()

    print(f"[OK] Seeded {order_count} orders with items")


def update_customer_ltv(engine):
    """Calculate and update customer lifetime values."""

    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE demo.customers c
            SET lifetime_value = COALESCE((
                SELECT SUM(total_amount)
                FROM demo.orders o
                WHERE o.customer_id = c.customer_id
                AND o.status = 'completed'
            ), 0)
        """))
        conn.commit()

    print("[OK] Updated customer lifetime values")


def seed_customer_segments(engine):
    """Create ML-derived customer segments."""

    with engine.connect() as conn:
        # Get customers with their order stats
        customers = conn.execute(text("""
            SELECT
                c.customer_id,
                c.lifetime_value,
                COUNT(o.order_id) as order_count,
                MAX(o.order_date) as last_order
            FROM demo.customers c
            LEFT JOIN demo.orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id, c.lifetime_value
        """)).fetchall()

        segments = ["Champions", "Loyal", "Potential", "New", "At Risk", "Dormant"]

        for cust in customers:
            customer_id, ltv, order_count, last_order = cust

            # Simple segmentation logic
            if ltv and ltv > 1000 and order_count and order_count > 5:
                segment = "Champions"
                rfm = random.randint(8, 10)
                churn_risk = random.uniform(0.01, 0.1)
            elif ltv and ltv > 500:
                segment = "Loyal"
                rfm = random.randint(6, 8)
                churn_risk = random.uniform(0.05, 0.2)
            elif order_count and order_count > 2:
                segment = "Potential"
                rfm = random.randint(4, 6)
                churn_risk = random.uniform(0.1, 0.3)
            elif order_count and order_count > 0:
                segment = "New"
                rfm = random.randint(3, 5)
                churn_risk = random.uniform(0.2, 0.4)
            else:
                segment = random.choice(["At Risk", "Dormant"])
                rfm = random.randint(1, 3)
                churn_risk = random.uniform(0.5, 0.9)

            predicted_ltv = float(ltv or 0) * random.uniform(1.1, 2.0)

            conn.execute(text("""
                INSERT INTO demo.customer_segments (customer_id, segment_name, rfm_score, churn_risk, predicted_ltv)
                VALUES (:cid, :segment, :rfm, :churn, :ltv)
            """), {
                "cid": customer_id,
                "segment": segment,
                "rfm": rfm,
                "churn": round(churn_risk, 4),
                "ltv": round(predicted_ltv, 2)
            })

        conn.commit()

    print(f"[OK] Created customer segments for {len(customers)} customers")


def seed_sales_summary(engine):
    """Create aggregated sales summary."""

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO demo.sales_summary (report_date, country_code, category, total_orders, total_revenue, avg_order_value, unique_customers)
            SELECT
                o.order_date as report_date,
                o.shipping_country as country_code,
                p.category,
                COUNT(DISTINCT o.order_id) as total_orders,
                SUM(oi.line_total) as total_revenue,
                AVG(o.total_amount) as avg_order_value,
                COUNT(DISTINCT o.customer_id) as unique_customers
            FROM demo.orders o
            JOIN demo.order_items oi ON o.order_id = oi.order_id
            JOIN demo.products p ON oi.product_id = p.product_id
            WHERE o.status = 'completed'
            GROUP BY o.order_date, o.shipping_country, p.category
        """))
        conn.commit()

        result = conn.execute(text("SELECT COUNT(*) FROM demo.sales_summary")).fetchone()
        print(f"[OK] Created {result[0]} sales summary records")


def print_stats(engine):
    """Print summary statistics."""

    with engine.connect() as conn:
        stats = {
            "Customers": conn.execute(text("SELECT COUNT(*) FROM demo.customers")).fetchone()[0],
            "Products": conn.execute(text("SELECT COUNT(*) FROM demo.products")).fetchone()[0],
            "Orders": conn.execute(text("SELECT COUNT(*) FROM demo.orders")).fetchone()[0],
            "Order Items": conn.execute(text("SELECT COUNT(*) FROM demo.order_items")).fetchone()[0],
            "Customer Segments": conn.execute(text("SELECT COUNT(*) FROM demo.customer_segments")).fetchone()[0],
            "Sales Summary": conn.execute(text("SELECT COUNT(*) FROM demo.sales_summary")).fetchone()[0],
        }

        total_revenue = conn.execute(text(
            "SELECT SUM(total_amount) FROM demo.orders WHERE status = 'completed'"
        )).fetchone()[0]

        print("\n" + "="*50)
        print("DEMO DATA SUMMARY")
        print("="*50)
        for table, count in stats.items():
            print(f"  {table:20} {count:>10,}")
        print(f"  {'Total Revenue':20} ${total_revenue:>10,.2f}")
        print("="*50)


def main():
    print("\n[*] ZeroStack Demo Data Seeder")
    print("="*50 + "\n")

    engine = create_engine(settings.database_url)

    print("[*] Creating schema and tables...")
    create_demo_schema(engine)

    print("\n[*] Seeding data...")
    seed_products(engine)
    seed_customers(engine, count=500)
    seed_orders(engine, order_count=2000)

    print("\n[*] Calculating derived data...")
    update_customer_ltv(engine)
    seed_customer_segments(engine)
    seed_sales_summary(engine)

    print_stats(engine)

    print("\n[OK] Demo data seeded successfully!")
    print("\nTry these in Data Explorer (http://localhost:3000/explorer):")
    print("  - Browse schema 'demo' to see all tables")
    print("  - Run: SELECT * FROM demo.customers LIMIT 10")
    print("  - Run: SELECT * FROM demo.sales_summary WHERE country_code = 'US'")
    print("\nTry Lineage Demo (http://localhost:3000/lineage-full-demo):")
    print("  - The pre-loaded queries will work with this data!")


if __name__ == "__main__":
    main()
