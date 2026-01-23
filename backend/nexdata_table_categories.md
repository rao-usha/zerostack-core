# Nexdata Tables - Complete Categorization

## 💼 Family Office (7 tables)
- `family_offices` - Family office entities and profiles
- `family_office_contacts` - Contact information for FO staff
- `family_office_interactions` - Interaction history and notes
- `co_investments` - Co-investment opportunities and participation
- `portfolio_companies` - Portfolio company information
- `impact_analysis` - ESG and impact metrics
- `investor_themes` - Investment themes and preferences

## 🤝 Limited Partners (LP) (10 tables)
- `lp_fund` - LP fund commitments and details
- `lp_key_contact` - Key contacts at LP organizations
- `lp_document` - LP-related documents and reports
- `lp_document_text_section` - Extracted text from LP documents
- `lp_strategy_snapshot` - Strategy allocation snapshots
- `lp_strategy_thematic_tag` - Thematic tags for strategies
- `lp_asset_class_target_allocation` - Target allocations by asset class
- `lp_asset_class_projection` - Projected allocations over time
- `lp_manager_or_vehicle_exposure` - Manager and vehicle exposures

## 📊 U.S. Economic Indicators (23 tables)
### Bureau of Economic Analysis (BEA)
- `bea_nipa` - National Income and Product Accounts
- `bea_gdp_industry` - GDP by industry
- `bea_regional` - Regional economic data

### Bureau of Labor Statistics (BLS)
- `bls_ces_employment` - Current Employment Statistics
- `bls_cpi_consumer_prices` - Consumer Price Index
- `bls_cps_unemployment` - Current Population Survey unemployment
- `bls_jolts_openings` - Job Openings and Labor Turnover
- `bls_ppi_producer_prices` - Producer Price Index

### Federal Reserve Economic Data (FRED)
- `fred_economic_indicators` - General economic indicators
- `fred_industrial_production` - Industrial production index
- `fred_interest_rates` - Interest rate data
- `fred_monetary_aggregates` - Money supply data

### U.S. Treasury
- `treasury_auctions` - Treasury auction results
- `treasury_daily_balance` - Daily Treasury balance
- `treasury_debt_outstanding` - Outstanding Treasury debt
- `treasury_interest_rates` - Treasury interest rates
- `treasury_monthly_statement` - Monthly Treasury statements

### International Trade
- `us_trade_exports_hs` - Exports by HS code
- `us_trade_exports_state` - Exports by state
- `us_trade_imports_hs` - Imports by HS code
- `us_trade_port_trade` - Port-level trade data

## 🌍 International Economics (7 tables)
### OECD
- `intl_oecd_alfs` - Labour Force Statistics
- `intl_oecd_batis` - Bilateral Trade in Services
- `intl_oecd_kei` - Key Economic Indicators
- `intl_oecd_mei` - Main Economic Indicators
- `intl_oecd_tax` - Tax statistics

### World Bank
- `intl_worldbank_countries` - Country metadata
- `intl_worldbank_wdi` - World Development Indicators

## 👥 Census & Demographics (5 tables)
- `acs5_2020_b01001` - American Community Survey 2020
- `acs5_2021_b01001` - American Community Survey 2021
- `acs5_2022_b01001` - American Community Survey 2022
- `acs5_2023_b01001` - American Community Survey 2023
- `census_variable_metadata` - Census variable definitions

## 🏛️ SEC Filings & Financials (13 tables)
- `sec_10k` - Annual reports (10-K)
- `sec_10q` - Quarterly reports (10-Q)
- `sec_8k` - Current reports (8-K)
- `sec_balance_sheet` - Balance sheet data
- `sec_cash_flow_statement` - Cash flow statements
- `sec_income_statement` - Income statements
- `sec_financial_facts` - XBRL financial facts
- `sec_filing_sections` - Filing text sections
- `sec_form_adv` - Investment adviser registrations
- `sec_form_adv_personnel` - Adviser personnel

## 🏦 Financial & Banking (7 tables)
### FDIC
- `fdic_bank_financials` - Bank financial statements
- `fdic_failed_banks` - Failed bank list
- `fdic_institutions` - Active institutions

### CFTC (Commodities & Futures)
- `cftc_cot_disaggregated_combined` - Disaggregated COT reports
- `cftc_cot_legacy_combined` - Legacy COT reports
- `cftc_cot_tff_combined` - Traders in Financial Futures

## 🏠 Real Estate (5 tables)
- `realestate_fhfa_hpi` - FHFA House Price Index
- `realestate_hud_permits` - HUD building permits
- `realestate_osm_buildings` - OpenStreetMap building data
- `realestate_redfin` - Redfin market data

## 🏥 Healthcare & Medicare (3 tables)
- `cms_drug_pricing` - Medicare drug prices
- `cms_hospital_cost_reports` - Hospital cost reports
- `cms_medicare_utilization` - Medicare utilization data

## 🏛️ Government & Public Services (7 tables)
### FEMA
- `fema_disaster_declarations` - Disaster declarations
- `fema_hma_projects` - Hazard Mitigation Assistance projects
- `fema_pa_projects` - Public Assistance projects

### Other Federal Agencies
- `fbi_crime_estimates_national` - FBI crime statistics
- `fcc_broadband_coverage` - FCC broadband coverage
- `fcc_broadband_summary` - FCC broadband summary
- `bts_border_crossing` - Border crossing data

## 💰 Tax & Revenue (3 tables)
- `irs_soi_county_income` - County-level income statistics
- `irs_soi_migration` - Migration patterns
- `irs_soi_zip_income` - ZIP code income statistics

## 🏪 Retail & Competition (4 tables)
- `m5_calendar` - M5 calendar
- `m5_items` - M5 item catalog
- `m5_prices` - M5 pricing data
- `m5_sales` - M5 sales transactions

## 📍 Location & Geography (3 tables)
- `locations` - Location entities
- `location_metadata` - Location metadata
- `geojson_boundaries` - Geographic boundaries (GeoJSON)

## 📡 Alternative Data (6 tables)
- `foot_traffic_observations` - Foot traffic metrics
- `prediction_markets` - Prediction market data
- `market_observations` - Market observation data
- `market_categories` - Market categories
- `market_alerts` - Market alerts
- `data_commons_observations` - Data Commons observations

## 🔧 Data Infrastructure (23 tables)
### Data Management
- `dataset_registry` - Dataset catalog
- `dataset_versions` - Dataset version tracking
- `ingestion_jobs` - Data ingestion jobs
- `ingestion_schedules` - Ingestion schedules
- `ingestion_templates` - Ingestion templates
- `source_rate_limits` - API rate limit tracking

### Data Quality
- `data_quality_reports` - Quality assessment reports
- `data_quality_results` - Quality test results
- `data_quality_rules` - Quality validation rules

### Lineage & Orchestration
- `lineage_edges` - Data lineage edges
- `lineage_events` - Lineage events
- `lineage_nodes` - Data lineage nodes
- `job_chains` - Job chain definitions
- `job_chain_executions` - Chain execution history
- `job_dependencies` - Job dependencies
- `template_executions` - Template execution logs

### Agentic & Automation
- `agentic_collection_jobs` - AI agent collection jobs
- `foot_traffic_collection_jobs` - Foot traffic collection
- `prediction_market_jobs` - Prediction market scraping

### Integration
- `webhooks` - Webhook configurations
- `webhook_deliveries` - Webhook delivery logs

---

**Total: 116 tables across 14 categories**
