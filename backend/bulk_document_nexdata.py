"""
Bulk documentation script for all undocumented nexdata tables.
This will generate AI-powered column documentation for all tables.
"""
import asyncio
import sys
from sqlalchemy import create_engine, text
from sqlmodel import Session
import httpx

# Database connections (Docker internal)
NEX_DB = "postgresql+psycopg://nex:nex@db:5432/nex"
NEXDATA_DB = "postgresql+psycopg://nexdata:nexdata@host.docker.internal:5433/nexdata"

# API endpoint
API_BASE = "http://localhost:8000"

# Category mapping
CATEGORIES = {
    # Family Office
    'family_offices': 'Family Office',
    'family_office_contacts': 'Family Office',
    'family_office_interactions': 'Family Office',
    'co_investments': 'Family Office',
    'portfolio_companies': 'Family Office',
    'impact_analysis': 'Family Office',
    'investor_themes': 'Family Office',
    
    # Limited Partners
    'lp_fund': 'Limited Partners (LP)',
    'lp_key_contact': 'Limited Partners (LP)',
    'lp_document': 'Limited Partners (LP)',
    'lp_document_text_section': 'Limited Partners (LP)',
    'lp_strategy_snapshot': 'Limited Partners (LP)',
    'lp_strategy_thematic_tag': 'Limited Partners (LP)',
    'lp_asset_class_target_allocation': 'Limited Partners (LP)',
    'lp_asset_class_projection': 'Limited Partners (LP)',
    'lp_manager_or_vehicle_exposure': 'Limited Partners (LP)',
    
    # Economic Indicators
    'bea_gdp_industry': 'U.S. Economic Indicators',
    'bea_regional': 'U.S. Economic Indicators',
    'bls_cps_unemployment': 'U.S. Economic Indicators',
    'bls_ppi_producer_prices': 'U.S. Economic Indicators',
    'fred_economic_indicators': 'U.S. Economic Indicators',
    'fred_industrial_production': 'U.S. Economic Indicators',
    'fred_interest_rates': 'U.S. Economic Indicators',
    'fred_monetary_aggregates': 'U.S. Economic Indicators',
    'treasury_auctions': 'U.S. Economic Indicators',
    'treasury_daily_balance': 'U.S. Economic Indicators',
    'treasury_debt_outstanding': 'U.S. Economic Indicators',
    'treasury_interest_rates': 'U.S. Economic Indicators',
    'treasury_monthly_statement': 'U.S. Economic Indicators',
    'us_trade_exports_hs': 'U.S. Economic Indicators',
    'us_trade_exports_state': 'U.S. Economic Indicators',
    'us_trade_imports_hs': 'U.S. Economic Indicators',
    'us_trade_port_trade': 'U.S. Economic Indicators',
    
    # International
    'intl_oecd_alfs': 'International Economics',
    'intl_oecd_batis': 'International Economics',
    'intl_oecd_kei': 'International Economics',
    'intl_oecd_mei': 'International Economics',
    'intl_oecd_tax': 'International Economics',
    'intl_worldbank_countries': 'International Economics',
    'intl_worldbank_wdi': 'International Economics',
    
    # Census
    'acs5_2020_b01001': 'Census & Demographics',
    'census_variable_metadata': 'Census & Demographics',
    
    # SEC
    'sec_10k': 'SEC Filings & Financials',
    'sec_10q': 'SEC Filings & Financials',
    'sec_8k': 'SEC Filings & Financials',
    'sec_balance_sheet': 'SEC Filings & Financials',
    'sec_cash_flow_statement': 'SEC Filings & Financials',
    'sec_income_statement': 'SEC Filings & Financials',
    'sec_financial_facts': 'SEC Filings & Financials',
    'sec_filing_sections': 'SEC Filings & Financials',
    'sec_form_adv': 'SEC Filings & Financials',
    'sec_form_adv_personnel': 'SEC Filings & Financials',
    
    # Financial
    'fdic_bank_financials': 'Financial & Banking',
    'fdic_failed_banks': 'Financial & Banking',
    'fdic_institutions': 'Financial & Banking',
    'cftc_cot_disaggregated_combined': 'Commodities & Futures',
    'cftc_cot_legacy_combined': 'Commodities & Futures',
    'cftc_cot_tff_combined': 'Commodities & Futures',
    
    # Real Estate
    'realestate_fhfa_hpi': 'Real Estate',
    'realestate_hud_permits': 'Real Estate',
    'realestate_osm_buildings': 'Real Estate',
    'realestate_redfin': 'Real Estate',
    
    # Healthcare
    'cms_drug_pricing': 'Healthcare & Medicare',
    'cms_hospital_cost_reports': 'Healthcare & Medicare',
    'cms_medicare_utilization': 'Healthcare & Medicare',
    
    # Government
    'fema_disaster_declarations': 'Government & Public Services',
    'fema_hma_projects': 'Government & Public Services',
    'fema_pa_projects': 'Government & Public Services',
    'fbi_crime_estimates_national': 'Government & Public Services',
    'fcc_broadband_coverage': 'Government & Public Services',
    'fcc_broadband_summary': 'Government & Public Services',
    'bts_border_crossing': 'Government & Public Services',
    
    # Tax
    'irs_soi_county_income': 'Tax & Revenue',
    'irs_soi_migration': 'Tax & Revenue',
    'irs_soi_zip_income': 'Tax & Revenue',
    
    # M5
    'm5_calendar': 'Retail & Competition',
    'm5_items': 'Retail & Competition',
    'm5_sales': 'Retail & Competition',
    
    # Location
    'locations': 'Location & Geography',
    'location_metadata': 'Location & Geography',
    'geojson_boundaries': 'Location & Geography',
    
    # Alternative Data
    'foot_traffic_observations': 'Alternative Data',
    'prediction_markets': 'Alternative Data',
    'market_observations': 'Alternative Data',
    'market_categories': 'Alternative Data',
    'market_alerts': 'Alternative Data',
    'data_commons_observations': 'Alternative Data',
    
    # Infrastructure
    'dataset_registry': 'Data Infrastructure',
    'dataset_versions': 'Data Infrastructure',
    'ingestion_jobs': 'Data Infrastructure',
    'ingestion_schedules': 'Data Infrastructure',
    'ingestion_templates': 'Data Infrastructure',
    'source_rate_limits': 'Data Infrastructure',
    'data_quality_reports': 'Data Infrastructure',
    'data_quality_results': 'Data Infrastructure',
    'data_quality_rules': 'Data Infrastructure',
    'lineage_edges': 'Data Infrastructure',
    'lineage_events': 'Data Infrastructure',
    'lineage_nodes': 'Data Infrastructure',
    'job_chains': 'Data Infrastructure',
    'job_chain_executions': 'Data Infrastructure',
    'job_dependencies': 'Data Infrastructure',
    'template_executions': 'Data Infrastructure',
    'agentic_collection_jobs': 'Data Infrastructure',
    'foot_traffic_collection_jobs': 'Data Infrastructure',
    'prediction_market_jobs': 'Data Infrastructure',
    'webhooks': 'Data Infrastructure',
    'webhook_deliveries': 'Data Infrastructure',
}


async def get_undocumented_tables():
    """Get list of tables that don't have dictionary entries."""
    nexdata_engine = create_engine(NEXDATA_DB)
    nex_engine = create_engine(NEX_DB)
    
    # Get all tables from nexdata
    with nexdata_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """))
        all_tables = [row[0] for row in result]
    
    # Get documented tables
    with nex_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT table_name 
            FROM data_dictionary_entries 
            WHERE database_name = 'default'
        """))
        documented_tables = {row[0] for row in result}
    
    # Return undocumented
    undocumented = [t for t in all_tables if t not in documented_tables]
    print(f"Found {len(undocumented)} undocumented tables out of {len(all_tables)} total")
    return undocumented


async def document_table(table_name: str, category: str):
    """Trigger documentation for a single table."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{API_BASE}/api/v1/data-explorer/analyze",
                json={
                    "db_id": "db2",  # nexdata database
                    "schema": "public",
                    "tables": [table_name],
                    "analysis_types": ["column_documentation"],
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "context": f"This is part of the {category} data category."
                }
            )
            if response.status_code == 200:
                print(f"✓ {table_name} ({category})")
                return True
            else:
                print(f"✗ {table_name}: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ {table_name}: {str(e)}")
            return False


async def main():
    print("🚀 Starting bulk documentation of nexdata tables...\n")
    
    # Get undocumented tables
    undocumented = await get_undocumented_tables()
    
    if not undocumented:
        print("✅ All tables are already documented!")
        return
    
    print(f"\n📝 Documenting {len(undocumented)} tables...\n")
    
    # Process in batches of 5 to avoid overwhelming the API
    batch_size = 5
    success_count = 0
    
    for i in range(0, len(undocumented), batch_size):
        batch = undocumented[i:i+batch_size]
        print(f"\n--- Batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, len(undocumented))}/{len(undocumented)}) ---")
        
        tasks = []
        for table_name in batch:
            category = CATEGORIES.get(table_name, 'Uncategorized')
            tasks.append(document_table(table_name, category))
        
        results = await asyncio.gather(*tasks)
        success_count += sum(results)
        
        # Brief pause between batches
        if i + batch_size < len(undocumented):
            await asyncio.sleep(2)
    
    print(f"\n✅ Complete! Documented {success_count}/{len(undocumented)} tables")


if __name__ == "__main__":
    asyncio.run(main())
