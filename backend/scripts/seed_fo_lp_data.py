"""
Seed script for Family Office (FO) and Limited Partner (LP) data.

Creates and populates tables with realistic sample data for development/demo.

Usage:
    python scripts/seed_fo_lp_data.py [--drop-existing]
"""
import os
import sys
import argparse
from datetime import date, datetime, timedelta
import random

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
from core.config import settings


def get_connection():
    """Get a database connection."""
    # Try to use EXPLORER_DB settings first, fall back to main database
    host = os.getenv("EXPLORER_DB_HOST", "localhost")
    port = os.getenv("EXPLORER_DB_PORT", "5432")
    user = os.getenv("EXPLORER_DB_USER", "nex")
    password = os.getenv("EXPLORER_DB_PASSWORD", "nex")
    database = os.getenv("EXPLORER_DB_NAME", "nex")

    conn_string = f"host={host} port={port} user={user} password={password} dbname={database}"
    return psycopg.connect(conn_string)


# ========================================
# Table Creation DDL
# ========================================

FO_TABLES_DDL = """
-- Family Offices main table
CREATE TABLE IF NOT EXISTS family_offices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    aum NUMERIC(20, 2),
    aum_currency VARCHAR(10) DEFAULT 'USD',
    headquarters VARCHAR(255),
    family_name VARCHAR(255),
    office_type VARCHAR(100),
    investment_focus TEXT,
    status VARCHAR(50) DEFAULT 'active',
    description TEXT,
    founded_year INTEGER,
    website VARCHAR(500),
    linkedin VARCHAR(500),
    investment_horizon VARCHAR(100),
    min_investment NUMERIC(20, 2),
    max_investment NUMERIC(20, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Family Office Contacts
CREATE TABLE IF NOT EXISTS family_office_contacts (
    id SERIAL PRIMARY KEY,
    family_office_id INTEGER REFERENCES family_offices(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Family Office Interactions
CREATE TABLE IF NOT EXISTS family_office_interactions (
    id SERIAL PRIMARY KEY,
    family_office_id INTEGER REFERENCES family_offices(id) ON DELETE CASCADE,
    interaction_type VARCHAR(100),
    interaction_date DATE,
    subject VARCHAR(500),
    notes TEXT,
    outcome VARCHAR(255),
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Co-investments
CREATE TABLE IF NOT EXISTS co_investments (
    id SERIAL PRIMARY KEY,
    family_office_id INTEGER REFERENCES family_offices(id) ON DELETE CASCADE,
    deal_name VARCHAR(255),
    deal_type VARCHAR(100),
    sector VARCHAR(100),
    investment_amount NUMERIC(20, 2),
    investment_currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50),
    close_date DATE,
    description TEXT,
    lead_investor VARCHAR(255),
    co_investors TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Portfolio Companies
CREATE TABLE IF NOT EXISTS portfolio_companies (
    id SERIAL PRIMARY KEY,
    family_office_id INTEGER REFERENCES family_offices(id) ON DELETE CASCADE,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    location VARCHAR(255),
    investment_date DATE,
    investment_amount NUMERIC(20, 2),
    ownership_percentage NUMERIC(5, 2),
    current_valuation NUMERIC(20, 2),
    status VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Investor Themes
CREATE TABLE IF NOT EXISTS investor_themes (
    id SERIAL PRIMARY KEY,
    family_office_id INTEGER REFERENCES family_offices(id) ON DELETE CASCADE,
    theme_name VARCHAR(255),
    theme_category VARCHAR(100),
    allocation_target NUMERIC(5, 2),
    priority VARCHAR(50),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Impact Analysis
CREATE TABLE IF NOT EXISTS impact_analysis (
    id SERIAL PRIMARY KEY,
    family_office_id INTEGER REFERENCES family_offices(id) ON DELETE CASCADE,
    analysis_date DATE,
    esg_score NUMERIC(5, 2),
    environmental_score NUMERIC(5, 2),
    social_score NUMERIC(5, 2),
    governance_score NUMERIC(5, 2),
    impact_focus_areas TEXT,
    carbon_footprint NUMERIC(12, 2),
    diversity_metrics TEXT,
    reporting_framework VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

LP_TABLES_DDL = """
-- LP Fund
CREATE TABLE IF NOT EXISTS lp_fund (
    id SERIAL PRIMARY KEY,
    fund_name VARCHAR(255) NOT NULL,
    lp_name VARCHAR(255),
    commitment NUMERIC(20, 2),
    commitment_currency VARCHAR(10) DEFAULT 'USD',
    vintage_year INTEGER,
    strategy VARCHAR(255),
    fund_type VARCHAR(100),
    status VARCHAR(50),
    description TEXT,
    aum NUMERIC(20, 2),
    headquarters VARCHAR(255),
    website VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LP Key Contact
CREATE TABLE IF NOT EXISTS lp_key_contact (
    id SERIAL PRIMARY KEY,
    fund_id INTEGER REFERENCES lp_fund(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LP Document
CREATE TABLE IF NOT EXISTS lp_document (
    id SERIAL PRIMARY KEY,
    fund_id INTEGER REFERENCES lp_fund(id) ON DELETE CASCADE,
    document_type VARCHAR(100),
    document_name VARCHAR(500),
    document_date DATE,
    source_url VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LP Document Text Section
CREATE TABLE IF NOT EXISTS lp_document_text_section (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES lp_document(id) ON DELETE CASCADE,
    section_name VARCHAR(255),
    section_text TEXT,
    page_number INTEGER,
    section_order INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LP Strategy Snapshot
CREATE TABLE IF NOT EXISTS lp_strategy_snapshot (
    id SERIAL PRIMARY KEY,
    fund_id INTEGER REFERENCES lp_fund(id) ON DELETE CASCADE,
    snapshot_date DATE,
    strategy_name VARCHAR(255),
    allocation_percentage NUMERIC(5, 2),
    target_return NUMERIC(5, 2),
    risk_tolerance VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LP Strategy Thematic Tag
CREATE TABLE IF NOT EXISTS lp_strategy_thematic_tag (
    id SERIAL PRIMARY KEY,
    strategy_snapshot_id INTEGER REFERENCES lp_strategy_snapshot(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    tag_category VARCHAR(100),
    weight NUMERIC(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LP Asset Class Target Allocation
CREATE TABLE IF NOT EXISTS lp_asset_class_target_allocation (
    id SERIAL PRIMARY KEY,
    fund_id INTEGER REFERENCES lp_fund(id) ON DELETE CASCADE,
    asset_class VARCHAR(100),
    target_allocation NUMERIC(5, 2),
    current_allocation NUMERIC(5, 2),
    min_allocation NUMERIC(5, 2),
    max_allocation NUMERIC(5, 2),
    as_of_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LP Asset Class Projection
CREATE TABLE IF NOT EXISTS lp_asset_class_projection (
    id SERIAL PRIMARY KEY,
    fund_id INTEGER REFERENCES lp_fund(id) ON DELETE CASCADE,
    asset_class VARCHAR(100),
    projection_date DATE,
    projected_allocation NUMERIC(5, 2),
    confidence_level VARCHAR(50),
    scenario VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LP Manager or Vehicle Exposure
CREATE TABLE IF NOT EXISTS lp_manager_or_vehicle_exposure (
    id SERIAL PRIMARY KEY,
    fund_id INTEGER REFERENCES lp_fund(id) ON DELETE CASCADE,
    manager_name VARCHAR(255),
    vehicle_name VARCHAR(255),
    exposure_amount NUMERIC(20, 2),
    exposure_percentage NUMERIC(5, 2),
    asset_class VARCHAR(100),
    strategy VARCHAR(100),
    vintage_year INTEGER,
    as_of_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""


# ========================================
# Sample Data
# ========================================

FAMILY_OFFICES = [
    {
        "name": "Walton Family Holdings",
        "family_name": "Walton",
        "aum": 250000000000,
        "headquarters": "Bentonville, AR",
        "office_type": "Single Family Office",
        "investment_focus": "Retail, Technology, Real Estate, Impact Investing",
        "founded_year": 1992,
        "status": "active",
        "investment_horizon": "Long-term (10+ years)",
        "min_investment": 50000000,
        "max_investment": 5000000000,
    },
    {
        "name": "Pritzker Group",
        "family_name": "Pritzker",
        "aum": 15000000000,
        "headquarters": "Chicago, IL",
        "office_type": "Single Family Office",
        "investment_focus": "Private Equity, Venture Capital, Real Estate",
        "founded_year": 1996,
        "status": "active",
        "investment_horizon": "Medium-term (5-10 years)",
        "min_investment": 25000000,
        "max_investment": 500000000,
    },
    {
        "name": "Bezos Expeditions",
        "family_name": "Bezos",
        "aum": 180000000000,
        "headquarters": "Seattle, WA",
        "office_type": "Single Family Office",
        "investment_focus": "Space, Technology, Media, Climate Tech",
        "founded_year": 2005,
        "status": "active",
        "investment_horizon": "Long-term (10+ years)",
        "min_investment": 10000000,
        "max_investment": 10000000000,
    },
    {
        "name": "Emerson Collective",
        "family_name": "Jobs/Powell Jobs",
        "aum": 35000000000,
        "headquarters": "Palo Alto, CA",
        "office_type": "Single Family Office",
        "investment_focus": "Education, Immigration Reform, Environment, Media",
        "founded_year": 2004,
        "status": "active",
        "investment_horizon": "Long-term (10+ years)",
        "min_investment": 5000000,
        "max_investment": 1000000000,
    },
    {
        "name": "Cascade Investment",
        "family_name": "Gates",
        "aum": 75000000000,
        "headquarters": "Kirkland, WA",
        "office_type": "Single Family Office",
        "investment_focus": "Public Equities, Private Equity, Real Estate, Agriculture",
        "founded_year": 1995,
        "status": "active",
        "investment_horizon": "Long-term (10+ years)",
        "min_investment": 100000000,
        "max_investment": 5000000000,
    },
    {
        "name": "MSD Capital",
        "family_name": "Dell",
        "aum": 50000000000,
        "headquarters": "New York, NY",
        "office_type": "Single Family Office",
        "investment_focus": "Technology, Real Estate, Credit, Public Equities",
        "founded_year": 1998,
        "status": "active",
        "investment_horizon": "Medium-term (5-10 years)",
        "min_investment": 50000000,
        "max_investment": 2000000000,
    },
    {
        "name": "Mousse Partners",
        "family_name": "Arnault",
        "aum": 45000000000,
        "headquarters": "Paris, France",
        "office_type": "Single Family Office",
        "investment_focus": "Luxury, Consumer, Technology",
        "founded_year": 2000,
        "status": "active",
        "investment_horizon": "Long-term (10+ years)",
        "min_investment": 20000000,
        "max_investment": 1000000000,
    },
    {
        "name": "Soros Fund Management",
        "family_name": "Soros",
        "aum": 28000000000,
        "headquarters": "New York, NY",
        "office_type": "Single Family Office",
        "investment_focus": "Global Macro, Public Equities, Emerging Markets",
        "founded_year": 1969,
        "status": "active",
        "investment_horizon": "Medium-term (3-7 years)",
        "min_investment": 25000000,
        "max_investment": 500000000,
    },
    {
        "name": "Koch Industries Capital",
        "family_name": "Koch",
        "aum": 125000000000,
        "headquarters": "Wichita, KS",
        "office_type": "Single Family Office",
        "investment_focus": "Energy, Manufacturing, Technology, Commodities",
        "founded_year": 1983,
        "status": "active",
        "investment_horizon": "Long-term (10+ years)",
        "min_investment": 100000000,
        "max_investment": 10000000000,
    },
    {
        "name": "Pershing Square Capital",
        "family_name": "Ackman",
        "aum": 18000000000,
        "headquarters": "New York, NY",
        "office_type": "Single Family Office",
        "investment_focus": "Activist Investing, Public Equities",
        "founded_year": 2004,
        "status": "active",
        "investment_horizon": "Medium-term (3-5 years)",
        "min_investment": 50000000,
        "max_investment": 2000000000,
    },
]

LP_FUNDS = [
    {
        "fund_name": "CalPERS Private Equity",
        "lp_name": "California Public Employees' Retirement System",
        "commitment": 50000000000,
        "vintage_year": 2020,
        "strategy": "Diversified Private Equity",
        "fund_type": "Public Pension",
        "status": "active",
        "headquarters": "Sacramento, CA",
        "aum": 500000000000,
    },
    {
        "fund_name": "Ontario Teachers' PE Program",
        "lp_name": "Ontario Teachers' Pension Plan",
        "commitment": 35000000000,
        "vintage_year": 2019,
        "strategy": "Direct & Co-Investment",
        "fund_type": "Public Pension",
        "status": "active",
        "headquarters": "Toronto, Canada",
        "aum": 250000000000,
    },
    {
        "fund_name": "Yale Endowment Alternatives",
        "lp_name": "Yale University Endowment",
        "commitment": 20000000000,
        "vintage_year": 2021,
        "strategy": "Venture Capital & Buyouts",
        "fund_type": "Endowment",
        "status": "active",
        "headquarters": "New Haven, CT",
        "aum": 42000000000,
    },
    {
        "fund_name": "Harvard Management Company",
        "lp_name": "Harvard University Endowment",
        "commitment": 18000000000,
        "vintage_year": 2020,
        "strategy": "Multi-Strategy",
        "fund_type": "Endowment",
        "status": "active",
        "headquarters": "Boston, MA",
        "aum": 53000000000,
    },
    {
        "fund_name": "CPP Investment Board",
        "lp_name": "Canada Pension Plan",
        "commitment": 75000000000,
        "vintage_year": 2022,
        "strategy": "Global Private Equity",
        "fund_type": "Sovereign Wealth Fund",
        "status": "active",
        "headquarters": "Toronto, Canada",
        "aum": 570000000000,
    },
    {
        "fund_name": "GIC Private Equity",
        "lp_name": "Government of Singapore Investment Corp",
        "commitment": 60000000000,
        "vintage_year": 2021,
        "strategy": "Global Multi-Asset",
        "fund_type": "Sovereign Wealth Fund",
        "status": "active",
        "headquarters": "Singapore",
        "aum": 700000000000,
    },
    {
        "fund_name": "ADIA Alternatives",
        "lp_name": "Abu Dhabi Investment Authority",
        "commitment": 80000000000,
        "vintage_year": 2020,
        "strategy": "Private Equity & Infrastructure",
        "fund_type": "Sovereign Wealth Fund",
        "status": "active",
        "headquarters": "Abu Dhabi, UAE",
        "aum": 850000000000,
    },
    {
        "fund_name": "Texas Teachers PE",
        "lp_name": "Teacher Retirement System of Texas",
        "commitment": 25000000000,
        "vintage_year": 2021,
        "strategy": "Buyouts & Growth Equity",
        "fund_type": "Public Pension",
        "status": "active",
        "headquarters": "Austin, TX",
        "aum": 200000000000,
    },
]

SECTORS = ["Technology", "Healthcare", "Financial Services", "Consumer", "Industrial", "Energy", "Real Estate", "Infrastructure"]
DEAL_TYPES = ["Buyout", "Growth Equity", "Venture Capital", "Real Estate", "Infrastructure", "Credit", "Co-Investment"]
INTERACTION_TYPES = ["Meeting", "Call", "Email", "Conference", "Site Visit", "Due Diligence"]
ASSET_CLASSES = ["Private Equity", "Venture Capital", "Real Estate", "Infrastructure", "Credit", "Public Equities", "Fixed Income", "Hedge Funds"]
THEMES = ["Climate Tech", "Digital Health", "Fintech", "AI/ML", "Clean Energy", "Enterprise SaaS", "Cybersecurity", "Biotech"]


def create_tables(conn):
    """Create all FO/LP tables."""
    print("Creating FO tables...")
    with conn.cursor() as cur:
        cur.execute(FO_TABLES_DDL)
    conn.commit()

    print("Creating LP tables...")
    with conn.cursor() as cur:
        cur.execute(LP_TABLES_DDL)
    conn.commit()

    print("Tables created successfully.")


def drop_tables(conn):
    """Drop all FO/LP tables."""
    print("Dropping existing tables...")
    drop_sql = """
    DROP TABLE IF EXISTS impact_analysis CASCADE;
    DROP TABLE IF EXISTS investor_themes CASCADE;
    DROP TABLE IF EXISTS portfolio_companies CASCADE;
    DROP TABLE IF EXISTS co_investments CASCADE;
    DROP TABLE IF EXISTS family_office_interactions CASCADE;
    DROP TABLE IF EXISTS family_office_contacts CASCADE;
    DROP TABLE IF EXISTS family_offices CASCADE;

    DROP TABLE IF EXISTS lp_manager_or_vehicle_exposure CASCADE;
    DROP TABLE IF EXISTS lp_asset_class_projection CASCADE;
    DROP TABLE IF EXISTS lp_asset_class_target_allocation CASCADE;
    DROP TABLE IF EXISTS lp_strategy_thematic_tag CASCADE;
    DROP TABLE IF EXISTS lp_strategy_snapshot CASCADE;
    DROP TABLE IF EXISTS lp_document_text_section CASCADE;
    DROP TABLE IF EXISTS lp_document CASCADE;
    DROP TABLE IF EXISTS lp_key_contact CASCADE;
    DROP TABLE IF EXISTS lp_fund CASCADE;
    """
    with conn.cursor() as cur:
        cur.execute(drop_sql)
    conn.commit()
    print("Tables dropped.")


def seed_family_offices(conn):
    """Seed family office data."""
    print("Seeding family offices...")

    with conn.cursor() as cur:
        for fo in FAMILY_OFFICES:
            cur.execute("""
                INSERT INTO family_offices (name, family_name, aum, aum_currency, headquarters,
                    office_type, investment_focus, founded_year, status, investment_horizon,
                    min_investment, max_investment, description, website)
                VALUES (%s, %s, %s, 'USD', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                fo["name"], fo["family_name"], fo["aum"], fo["headquarters"],
                fo["office_type"], fo["investment_focus"], fo["founded_year"],
                fo["status"], fo["investment_horizon"], fo["min_investment"],
                fo["max_investment"],
                f"{fo['name']} is a {fo['office_type'].lower()} focused on {fo['investment_focus']}.",
                f"https://www.{fo['name'].lower().replace(' ', '')}.com"
            ))
            fo_id = cur.fetchone()[0]

            # Add contacts
            titles = ["Chief Investment Officer", "Managing Director", "Partner", "Investment Director", "Head of Private Equity"]
            for i, title in enumerate(random.sample(titles, min(3, len(titles)))):
                cur.execute("""
                    INSERT INTO family_office_contacts (family_office_id, name, title, email, phone, role, is_primary)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    fo_id,
                    f"{random.choice(['John', 'Sarah', 'Michael', 'Emily', 'David'])} {random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Davis'])}",
                    title,
                    f"{title.lower().replace(' ', '.')}@{fo['name'].lower().replace(' ', '')}.com",
                    f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                    "Investment",
                    i == 0
                ))

            # Add interactions
            for j in range(random.randint(3, 8)):
                interaction_date = date.today() - timedelta(days=random.randint(1, 365))
                cur.execute("""
                    INSERT INTO family_office_interactions (family_office_id, interaction_type, interaction_date,
                        subject, notes, outcome, follow_up_required, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    fo_id,
                    random.choice(INTERACTION_TYPES),
                    interaction_date,
                    f"Discussion on {random.choice(SECTORS)} investment opportunities",
                    f"Discussed potential co-investment in {random.choice(SECTORS)} sector. Strong interest shown.",
                    random.choice(["Positive", "Follow-up needed", "On hold", "Moved forward"]),
                    random.choice([True, False]),
                    "System"
                ))

            # Add co-investments
            for k in range(random.randint(2, 5)):
                cur.execute("""
                    INSERT INTO co_investments (family_office_id, deal_name, deal_type, sector,
                        investment_amount, status, close_date, lead_investor, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    fo_id,
                    f"{random.choice(['Project', 'Deal', 'Investment'])} {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon'])}-{random.randint(1,99):02d}",
                    random.choice(DEAL_TYPES),
                    random.choice(SECTORS),
                    random.randint(10, 500) * 1000000,
                    random.choice(["Active", "Closed", "In Due Diligence", "Monitoring"]),
                    date.today() - timedelta(days=random.randint(1, 730)),
                    random.choice(["KKR", "Blackstone", "Carlyle", "Apollo", "TPG"]),
                    f"Co-investment opportunity in the {random.choice(SECTORS)} sector."
                ))

            # Add portfolio companies
            for m in range(random.randint(3, 8)):
                cur.execute("""
                    INSERT INTO portfolio_companies (family_office_id, company_name, sector, location,
                        investment_date, investment_amount, ownership_percentage, current_valuation, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    fo_id,
                    f"{random.choice(['Tech', 'Bio', 'Fin', 'Health', 'Green'])}{random.choice(['Corp', 'Labs', 'Systems', 'Solutions', 'Dynamics'])}",
                    random.choice(SECTORS),
                    random.choice(["New York", "San Francisco", "Boston", "Chicago", "Austin", "Seattle", "London", "Singapore"]),
                    date.today() - timedelta(days=random.randint(365, 2000)),
                    random.randint(5, 200) * 1000000,
                    round(random.uniform(5, 30), 2),
                    random.randint(50, 2000) * 1000000,
                    random.choice(["Active", "Exited", "In Process"])
                ))

            # Add investor themes
            for theme in random.sample(THEMES, min(4, len(THEMES))):
                cur.execute("""
                    INSERT INTO investor_themes (family_office_id, theme_name, theme_category,
                        allocation_target, priority, description, active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    fo_id,
                    theme,
                    random.choice(["Sector", "Strategy", "Impact", "Geographic"]),
                    round(random.uniform(5, 25), 2),
                    random.choice(["High", "Medium", "Low"]),
                    f"Investment focus on {theme} opportunities.",
                    True
                ))

            # Add impact analysis
            cur.execute("""
                INSERT INTO impact_analysis (family_office_id, analysis_date, esg_score,
                    environmental_score, social_score, governance_score, impact_focus_areas,
                    carbon_footprint, reporting_framework)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                fo_id,
                date.today() - timedelta(days=random.randint(1, 90)),
                round(random.uniform(60, 95), 2),
                round(random.uniform(55, 95), 2),
                round(random.uniform(60, 95), 2),
                round(random.uniform(65, 98), 2),
                ", ".join(random.sample(["Climate", "Diversity", "Education", "Healthcare Access", "Financial Inclusion"], 3)),
                round(random.uniform(1000, 50000), 2),
                random.choice(["SASB", "GRI", "TCFD", "UN PRI"])
            ))

    conn.commit()
    print(f"Seeded {len(FAMILY_OFFICES)} family offices with related data.")


def seed_lp_funds(conn):
    """Seed LP fund data."""
    print("Seeding LP funds...")

    with conn.cursor() as cur:
        for lp in LP_FUNDS:
            cur.execute("""
                INSERT INTO lp_fund (fund_name, lp_name, commitment, commitment_currency,
                    vintage_year, strategy, fund_type, status, headquarters, aum, description)
                VALUES (%s, %s, %s, 'USD', %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                lp["fund_name"], lp["lp_name"], lp["commitment"], lp["vintage_year"],
                lp["strategy"], lp["fund_type"], lp["status"], lp["headquarters"],
                lp["aum"], f"{lp['lp_name']} is a {lp['fund_type'].lower()} with {lp['strategy'].lower()} strategy."
            ))
            fund_id = cur.fetchone()[0]

            # Add key contacts
            for i in range(random.randint(2, 4)):
                cur.execute("""
                    INSERT INTO lp_key_contact (fund_id, name, title, email, phone, role, is_primary)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    fund_id,
                    f"{random.choice(['James', 'Jennifer', 'Robert', 'Lisa', 'William'])} {random.choice(['Anderson', 'Taylor', 'Thomas', 'Jackson', 'White'])}",
                    random.choice(["Portfolio Manager", "Senior Investment Officer", "Managing Director", "Investment Analyst"]),
                    f"contact{i}@example.com",
                    f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                    "Investment",
                    i == 0
                ))

            # Add documents
            doc_types = ["Annual Report", "Quarterly Update", "Investment Policy", "Due Diligence Report"]
            for doc_type in random.sample(doc_types, min(3, len(doc_types))):
                cur.execute("""
                    INSERT INTO lp_document (fund_id, document_type, document_name, document_date)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (
                    fund_id,
                    doc_type,
                    f"{lp['fund_name']} - {doc_type} {random.randint(2022, 2025)}",
                    date.today() - timedelta(days=random.randint(30, 365))
                ))
                doc_id = cur.fetchone()[0]

                # Add text sections
                sections = ["Executive Summary", "Performance", "Holdings", "Outlook"]
                for idx, section in enumerate(sections):
                    cur.execute("""
                        INSERT INTO lp_document_text_section (document_id, section_name, section_text, page_number, section_order)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        doc_id, section,
                        f"This section contains the {section.lower()} for {lp['fund_name']}. Performance has been strong with returns exceeding benchmarks.",
                        idx + 1, idx + 1
                    ))

            # Add strategy snapshots
            for _ in range(random.randint(2, 4)):
                cur.execute("""
                    INSERT INTO lp_strategy_snapshot (fund_id, snapshot_date, strategy_name,
                        allocation_percentage, target_return, risk_tolerance)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    fund_id,
                    date.today() - timedelta(days=random.randint(30, 365)),
                    random.choice(["Core", "Value-Add", "Opportunistic", "Growth"]),
                    round(random.uniform(10, 40), 2),
                    round(random.uniform(8, 25), 2),
                    random.choice(["Low", "Medium", "High"])
                ))
                snapshot_id = cur.fetchone()[0]

                # Add thematic tags
                for tag in random.sample(THEMES, min(3, len(THEMES))):
                    cur.execute("""
                        INSERT INTO lp_strategy_thematic_tag (strategy_snapshot_id, tag_name, tag_category, weight)
                        VALUES (%s, %s, %s, %s)
                    """, (snapshot_id, tag, random.choice(["Sector", "Theme"]), round(random.uniform(0.1, 0.5), 2)))

            # Add asset class allocations
            for asset_class in random.sample(ASSET_CLASSES, min(5, len(ASSET_CLASSES))):
                target = round(random.uniform(5, 30), 2)
                cur.execute("""
                    INSERT INTO lp_asset_class_target_allocation (fund_id, asset_class, target_allocation,
                        current_allocation, min_allocation, max_allocation, as_of_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    fund_id, asset_class, target,
                    round(target + random.uniform(-5, 5), 2),
                    round(target - 10, 2),
                    round(target + 10, 2),
                    date.today() - timedelta(days=random.randint(1, 90))
                ))

            # Add manager exposures
            managers = ["Blackstone", "KKR", "Carlyle", "Apollo", "TPG", "Warburg Pincus", "Advent", "Bain Capital"]
            for manager in random.sample(managers, min(4, len(managers))):
                cur.execute("""
                    INSERT INTO lp_manager_or_vehicle_exposure (fund_id, manager_name, vehicle_name,
                        exposure_amount, exposure_percentage, asset_class, strategy, vintage_year, as_of_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    fund_id,
                    manager,
                    f"{manager} Fund {random.choice(['VII', 'VIII', 'IX', 'X'])}",
                    random.randint(100, 2000) * 1000000,
                    round(random.uniform(1, 10), 2),
                    random.choice(ASSET_CLASSES[:4]),
                    random.choice(["Buyout", "Growth", "Venture"]),
                    random.randint(2018, 2023),
                    date.today() - timedelta(days=random.randint(1, 90))
                ))

    conn.commit()
    print(f"Seeded {len(LP_FUNDS)} LP funds with related data.")


def main():
    parser = argparse.ArgumentParser(description="Seed FO/LP data")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing tables first")
    args = parser.parse_args()

    print("Connecting to database...")
    conn = get_connection()

    try:
        if args.drop_existing:
            drop_tables(conn)

        create_tables(conn)
        seed_family_offices(conn)
        seed_lp_funds(conn)

        print("\n=== Seed Complete ===")
        print("Data seeded successfully!")

        # Print counts
        with conn.cursor() as cur:
            tables = [
                "family_offices", "family_office_contacts", "family_office_interactions",
                "co_investments", "portfolio_companies", "investor_themes", "impact_analysis",
                "lp_fund", "lp_key_contact", "lp_document", "lp_document_text_section",
                "lp_strategy_snapshot", "lp_strategy_thematic_tag", "lp_asset_class_target_allocation",
                "lp_manager_or_vehicle_exposure"
            ]
            print("\nRow counts:")
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table}: {count}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
