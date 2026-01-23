# PowerShell Script to Auto-Document All Nexdata Tables
# This will generate AI-powered column documentation for all undocumented tables

$ErrorActionPreference = "Continue"
$API_BASE = "http://localhost:8000"

# Category mapping for better documentation context
$CATEGORIES = @{
    # Family Office
    'family_offices' = 'Family Office'
    'family_office_contacts' = 'Family Office'
    'family_office_interactions' = 'Family Office'
    'co_investments' = 'Family Office'
    'portfolio_companies' = 'Family Office'
    'impact_analysis' = 'Family Office'
    'investor_themes' = 'Family Office'
    
    # Limited Partners
    'lp_fund' = 'Limited Partners (LP)'
    'lp_key_contact' = 'Limited Partners (LP)'
    'lp_document' = 'Limited Partners (LP)'
    'lp_document_text_section' = 'Limited Partners (LP)'
    'lp_strategy_snapshot' = 'Limited Partners (LP)'
    'lp_strategy_thematic_tag' = 'Limited Partners (LP)'
    'lp_asset_class_target_allocation' = 'Limited Partners (LP)'
    'lp_asset_class_projection' = 'Limited Partners (LP)'
    'lp_manager_or_vehicle_exposure' = 'Limited Partners (LP)'
    
    # Economic Indicators
    'bea_gdp_industry' = 'U.S. Economic Indicators'
    'bea_regional' = 'U.S. Economic Indicators'
    'bls_cps_unemployment' = 'U.S. Economic Indicators'
    'bls_ppi_producer_prices' = 'U.S. Economic Indicators'
    'fred_economic_indicators' = 'U.S. Economic Indicators'
    'fred_industrial_production' = 'U.S. Economic Indicators'
    'fred_interest_rates' = 'U.S. Economic Indicators'
    'fred_monetary_aggregates' = 'U.S. Economic Indicators'
    'treasury_auctions' = 'U.S. Economic Indicators'
    'treasury_daily_balance' = 'U.S. Economic Indicators'
    'treasury_debt_outstanding' = 'U.S. Economic Indicators'
    'treasury_interest_rates' = 'U.S. Economic Indicators'
    'treasury_monthly_statement' = 'U.S. Economic Indicators'
    'us_trade_exports_hs' = 'U.S. Economic Indicators'
    'us_trade_exports_state' = 'U.S. Economic Indicators'
    'us_trade_imports_hs' = 'U.S. Economic Indicators'
    'us_trade_port_trade' = 'U.S. Economic Indicators'
    
    # International
    'intl_oecd_alfs' = 'International Economics'
    'intl_oecd_batis' = 'International Economics'
    'intl_oecd_kei' = 'International Economics'
    'intl_oecd_mei' = 'International Economics'
    'intl_oecd_tax' = 'International Economics'
    'intl_worldbank_countries' = 'International Economics'
    'intl_worldbank_wdi' = 'International Economics'
    
    # Census
    'acs5_2020_b01001' = 'Census & Demographics'
    'census_variable_metadata' = 'Census & Demographics'
    
    # SEC
    'sec_10k' = 'SEC Filings & Financials'
    'sec_10q' = 'SEC Filings & Financials'
    'sec_8k' = 'SEC Filings & Financials'
    'sec_balance_sheet' = 'SEC Filings & Financials'
    'sec_cash_flow_statement' = 'SEC Filings & Financials'
    'sec_income_statement' = 'SEC Filings & Financials'
    'sec_financial_facts' = 'SEC Filings & Financials'
    'sec_filing_sections' = 'SEC Filings & Financials'
    'sec_form_adv' = 'SEC Filings & Financials'
    'sec_form_adv_personnel' = 'SEC Filings & Financials'
    
    # Financial
    'fdic_bank_financials' = 'Financial & Banking'
    'fdic_failed_banks' = 'Financial & Banking'
    'fdic_institutions' = 'Financial & Banking'
    'cftc_cot_disaggregated_combined' = 'Commodities & Futures'
    'cftc_cot_legacy_combined' = 'Commodities & Futures'
    'cftc_cot_tff_combined' = 'Commodities & Futures'
    
    # Real Estate
    'realestate_fhfa_hpi' = 'Real Estate'
    'realestate_hud_permits' = 'Real Estate'
    'realestate_osm_buildings' = 'Real Estate'
    'realestate_redfin' = 'Real Estate'
    
    # Healthcare
    'cms_drug_pricing' = 'Healthcare & Medicare'
    'cms_hospital_cost_reports' = 'Healthcare & Medicare'
    'cms_medicare_utilization' = 'Healthcare & Medicare'
    
    # Government
    'fema_disaster_declarations' = 'Government & Public Services'
    'fema_hma_projects' = 'Government & Public Services'
    'fema_pa_projects' = 'Government & Public Services'
    'fbi_crime_estimates_national' = 'Government & Public Services'
    'fcc_broadband_coverage' = 'Government & Public Services'
    'fcc_broadband_summary' = 'Government & Public Services'
    'bts_border_crossing' = 'Government & Public Services'
    
    # Tax
    'irs_soi_county_income' = 'Tax & Revenue'
    'irs_soi_migration' = 'Tax & Revenue'
    'irs_soi_zip_income' = 'Tax & Revenue'
    
    # M5
    'm5_calendar' = 'Retail & Competition'
    'm5_items' = 'Retail & Competition'
    'm5_sales' = 'Retail & Competition'
    
    # Location
    'locations' = 'Location & Geography'
    'location_metadata' = 'Location & Geography'
    'geojson_boundaries' = 'Location & Geography'
    
    # Alternative Data
    'foot_traffic_observations' = 'Alternative Data'
    'prediction_markets' = 'Alternative Data'
    'market_observations' = 'Alternative Data'
    'market_categories' = 'Alternative Data'
    'market_alerts' = 'Alternative Data'
    'data_commons_observations' = 'Alternative Data'
    
    # Infrastructure
    'dataset_registry' = 'Data Infrastructure'
    'dataset_versions' = 'Data Infrastructure'
    'ingestion_jobs' = 'Data Infrastructure'
    'ingestion_schedules' = 'Data Infrastructure'
    'ingestion_templates' = 'Data Infrastructure'
    'source_rate_limits' = 'Data Infrastructure'
    'data_quality_reports' = 'Data Infrastructure'
    'data_quality_results' = 'Data Infrastructure'
    'data_quality_rules' = 'Data Infrastructure'
    'lineage_edges' = 'Data Infrastructure'
    'lineage_events' = 'Data Infrastructure'
    'lineage_nodes' = 'Data Infrastructure'
    'job_chains' = 'Data Infrastructure'
    'job_chain_executions' = 'Data Infrastructure'
    'job_dependencies' = 'Data Infrastructure'
    'template_executions' = 'Data Infrastructure'
    'agentic_collection_jobs' = 'Data Infrastructure'
    'foot_traffic_collection_jobs' = 'Data Infrastructure'
    'prediction_market_jobs' = 'Data Infrastructure'
    'webhooks' = 'Data Infrastructure'
    'webhook_deliveries' = 'Data Infrastructure'
}

Write-Host "Starting Auto-Documentation of Nexdata Tables" -ForegroundColor Cyan
Write-Host ("=" * 60)
Write-Host ""

# Step 1: Get all tables from nexdata
Write-Host "Fetching table list from nexdata..." -ForegroundColor Yellow
try {
    $tablesUri = "$API_BASE/api/v1/data-explorer/tables?db_id=default&schema=public"
    $allTablesResponse = Invoke-RestMethod -Uri $tablesUri -Method Get
    $allTables = $allTablesResponse | Select-Object -ExpandProperty name | Sort-Object
    Write-Host "   Found $($allTables.Count) total tables" -ForegroundColor Green
} catch {
    Write-Host "Failed to fetch tables: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Get documented tables
Write-Host "Checking which tables are already documented..." -ForegroundColor Yellow
try {
    $dictUri = "$API_BASE/api/v1/data-dictionary/?database_name=default"
    $documentedResponse = Invoke-RestMethod -Uri $dictUri -Method Get
    $documentedTables = $documentedResponse | Select-Object -ExpandProperty table_name -Unique
    Write-Host "   Already documented: $($documentedTables.Count) tables" -ForegroundColor Green
} catch {
    Write-Host "   Could not fetch documented tables, assuming none" -ForegroundColor Yellow
    $documentedTables = @()
}

# Step 3: Find undocumented tables
$undocumentedTables = $allTables | Where-Object { $_ -notin $documentedTables }
Write-Host "   Need to document: $($undocumentedTables.Count) tables" -ForegroundColor Cyan
Write-Host ""

if ($undocumentedTables.Count -eq 0) {
    Write-Host "All tables are already documented!" -ForegroundColor Green
    exit 0
}

# Step 4: Document each table
$successCount = 0
$failCount = 0
$totalTables = $undocumentedTables.Count
$currentTable = 0

Write-Host "Starting documentation process..." -ForegroundColor Cyan
Write-Host "   This will take approximately $([Math]::Round($totalTables * 0.5)) minutes" -ForegroundColor Gray
Write-Host ""

foreach ($tableName in $undocumentedTables) {
    $currentTable++
    $category = if ($CATEGORIES.ContainsKey($tableName)) { $CATEGORIES[$tableName] } else { "Uncategorized" }
    
    Write-Host "[$currentTable/$totalTables] $tableName" -NoNewline -ForegroundColor White
    Write-Host " ($category)" -ForegroundColor Gray
    
    try {
        $payload = @{
            db_id = "default"
            tables = @(@{
                schema = "public"
                table = $tableName
            })
            analysis_types = @("column_documentation")
            provider = "openai"
            model = "gpt-4o-mini"
            context = "This table is part of the $category data category."
        } | ConvertTo-Json -Depth 5
        
        $analyzeUri = "$API_BASE/api/v1/data-explorer/analyze"
        $response = Invoke-RestMethod -Uri $analyzeUri `
                                      -Method Post `
                                      -Body $payload `
                                      -ContentType "application/json" `
                                      -TimeoutSec 180
        
        Write-Host "            [SUCCESS]" -ForegroundColor Green
        $successCount++
        
        # Small delay to avoid overwhelming API
        Start-Sleep -Milliseconds 500
        
    } catch {
        Write-Host "            [FAILED] $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
}

# Summary
Write-Host ""
Write-Host ("=" * 60)
Write-Host "Documentation Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Successful: $successCount tables" -ForegroundColor Green
Write-Host "   Failed: $failCount tables" -ForegroundColor Red
Write-Host "   Total Processed: $totalTables tables" -ForegroundColor White
Write-Host ""
Write-Host "View your documented tables in the Data Dictionary UI!" -ForegroundColor Yellow
Write-Host "   http://localhost:3000/data-dictionary" -ForegroundColor Cyan
Write-Host ""
