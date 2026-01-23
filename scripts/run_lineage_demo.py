#!/usr/bin/env python3
"""
Lineage Demo Runner

This script:
1. Creates synthetic data in the database
2. Runs demo queries through the lineage tracker
3. Populates the lineage system with realistic examples
4. Generates a summary report

Usage:
    python scripts/run_lineage_demo.py
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import psycopg2
from psycopg2 import sql
import json
from datetime import datetime
from uuid import uuid4

# Import lineage modules
from domains.lineage.sql_parser import parse_sql_lineage
from domains.lineage.column_lineage import extract_column_lineage
from domains.lineage.ml_tracker import analyze_ml_query

# Import demo queries
from lineage_demo_queries import DEMO_QUERIES, QUERY_CATEGORIES


# Database connection (read from env or use defaults)
DB_CONFIG = {
    'host': os.getenv('EXPLORER_DB_HOST', 'localhost'),
    'port': int(os.getenv('EXPLORER_DB_PORT', '5433')),
    'database': os.getenv('EXPLORER_DB_NAME', 'nexdata'),
    'user': os.getenv('EXPLORER_DB_USER', 'nexdata'),
    'password': os.getenv('EXPLORER_DB_PASSWORD', 'nexdata_dev_password')
}


class LineageDemoRunner:
    """Runs the lineage demonstration"""
    
    def __init__(self):
        self.conn = None
        self.results = {
            'queries_run': 0,
            'lineage_detected': 0,
            'ml_queries_found': 0,
            'column_transformations': 0,
            'pipeline_stages': 0,
            'errors': []
        }
    
    def connect_db(self):
        """Connect to database"""
        print("🔌 Connecting to database...")
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print(f"✅ Connected to {DB_CONFIG['database']} on {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def load_sample_data(self):
        """Load synthetic data from SQL file"""
        print("\n📊 Loading synthetic data...")
        
        sql_file = Path(__file__).parent / "create_lineage_demo_data.sql"
        if not sql_file.exists():
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        try:
            with open(sql_file, 'r') as f:
                sql_script = f.read()
            
            cursor = self.conn.cursor()
            cursor.execute(sql_script)
            self.conn.commit()
            cursor.close()
            
            print("✅ Synthetic data loaded successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to load data: {e}")
            self.results['errors'].append(f"Data loading: {str(e)}")
            return False
    
    def run_demo_query(self, query_key: str, query_info: dict):
        """Run a single demo query and analyze lineage"""
        print(f"\n{'='*60}")
        print(f"📝 Query: {query_info['name']}")
        print(f"{'='*60}")
        
        sql = query_info['sql'].strip()
        print(f"\nSQL:\n{sql[:200]}{'...' if len(sql) > 200 else ''}\n")
        
        self.results['queries_run'] += 1
        
        # Parse table-level lineage
        print("🔍 Analyzing table-level lineage...")
        try:
            lineage = parse_sql_lineage(sql)
            
            if lineage.source_tables:
                self.results['lineage_detected'] += 1
                print(f"✓ Source Tables: {[t.full_name for t in lineage.source_tables]}")
                
                if lineage.target_table:
                    print(f"✓ Target Table: {lineage.target_table.full_name}")
                    self.results['pipeline_stages'] += 1
                
                if lineage.join_type:
                    print(f"✓ JOIN Type: {lineage.join_type}")
                
                if lineage.has_aggregation:
                    print("✓ Has Aggregation: Yes")
                
                if lineage.has_filter:
                    print("✓ Has Filter: Yes")
            else:
                print("⚠️  No source tables detected")
        except Exception as e:
            print(f"❌ Table lineage error: {e}")
            self.results['errors'].append(f"{query_key} (table): {str(e)}")
        
        # Parse column-level lineage
        print("\n🔗 Analyzing column-level lineage...")
        try:
            col_lineage = extract_column_lineage(sql)
            
            if col_lineage.transformations:
                self.results['column_transformations'] += len(col_lineage.transformations)
                print(f"✓ Column Transformations Found: {len(col_lineage.transformations)}")
                
                # Show first 3 transformations
                for i, trans in enumerate(col_lineage.transformations[:3]):
                    print(f"  {i+1}. {trans.source_full_name} → {trans.target_column} ({trans.transformation_type})")
                
                if len(col_lineage.transformations) > 3:
                    print(f"  ... and {len(col_lineage.transformations) - 3} more")
            else:
                print("⚠️  No column transformations detected")
        except Exception as e:
            print(f"❌ Column lineage error: {e}")
            self.results['errors'].append(f"{query_key} (column): {str(e)}")
        
        # Analyze ML relevance
        print("\n🤖 Analyzing ML query patterns...")
        try:
            ml_analysis = analyze_ml_query(sql)
            
            if ml_analysis and ml_analysis.is_ml_related:
                self.results['ml_queries_found'] += 1
                print(f"✓ ML Query Detected! Confidence: {ml_analysis.confidence_score:.1%}")
                print(f"  Query Type: {ml_analysis.query_type}")
                print(f"  Features: {len(ml_analysis.features_extracted)}")
                print(f"  Patterns: {', '.join(ml_analysis.detected_patterns[:2])}")
            else:
                print("⚠️  Not detected as ML-related")
        except Exception as e:
            print(f"❌ ML analysis error: {e}")
            self.results['errors'].append(f"{query_key} (ML): {str(e)}")
        
        # Show what this demonstrates
        print(f"\n💡 Demonstrates: {', '.join(query_info.get('demonstrates', []))}")
    
    def run_all_queries(self):
        """Run all demo queries"""
        print("\n" + "="*60)
        print("🚀 RUNNING LINEAGE DEMO QUERIES")
        print("="*60)
        
        for category, query_keys in QUERY_CATEGORIES.items():
            print(f"\n\n{'#'*60}")
            print(f"# Category: {category.upper()}")
            print(f"{'#'*60}")
            
            for query_key in query_keys:
                if query_key in DEMO_QUERIES:
                    self.run_demo_query(query_key, DEMO_QUERIES[query_key])
    
    def print_summary(self):
        """Print summary report"""
        print("\n" + "="*60)
        print("📊 LINEAGE DEMO SUMMARY")
        print("="*60)
        
        print(f"\n✅ Queries Run: {self.results['queries_run']}")
        print(f"✅ Lineage Detected: {self.results['lineage_detected']}")
        print(f"✅ Column Transformations: {self.results['column_transformations']}")
        print(f"✅ Pipeline Stages: {self.results['pipeline_stages']}")
        print(f"✅ ML Queries Found: {self.results['ml_queries_found']}")
        
        if self.results['errors']:
            print(f"\n⚠️  Errors Encountered: {len(self.results['errors'])}")
            for error in self.results['errors'][:5]:
                print(f"  - {error}")
            if len(self.results['errors']) > 5:
                print(f"  ... and {len(self.results['errors']) - 5} more")
        
        print("\n" + "="*60)
        print("🎉 DEMO COMPLETE!")
        print("="*60)
        print("\nNext Steps:")
        print("1. Go to Data Explorer: http://localhost:3000/data-explorer")
        print("2. Select database: 'nexdata (demo data)'")
        print("3. Run any of the demo queries")
        print("4. See automatic lineage below query results!")
        print("\nTry these example queries:")
        print("- Simple JOIN: inner_join")
        print("- ML Features: ml_features_customer")
        print("- Window Functions: window_functions")
        print("- Pipeline: pipeline_stage_1, pipeline_stage_2, pipeline_stage_3")
        print("="*60)
    
    def run(self):
        """Main runner"""
        print("="*60)
        print("🔬 LINEAGE SYSTEM DEMO")
        print("="*60)
        print("\nThis demo will:")
        print("1. Load synthetic data into the database")
        print("2. Run sample queries through lineage parser")
        print("3. Demonstrate all lineage features")
        print("4. Generate a summary report")
        
        # Connect
        if not self.connect_db():
            return False
        
        # Load data
        response = input("\n⚠️  This will create/overwrite demo tables. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled by user")
            return False
        
        if not self.load_sample_data():
            return False
        
        # Run demo queries
        self.run_all_queries()
        
        # Print summary
        self.print_summary()
        
        # Close connection
        if self.conn:
            self.conn.close()
        
        return True


if __name__ == "__main__":
    runner = LineageDemoRunner()
    success = runner.run()
    sys.exit(0 if success else 1)
