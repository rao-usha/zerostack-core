"""Test to ensure no duplicate table definitions exist."""

import sys
from pathlib import Path

# Add parent directory to path to import the check script
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.check_duplicate_tables import find_table_definitions, check_for_duplicates


def test_no_duplicate_table_definitions():
    """
    Test that there are no duplicate __tablename__ definitions.
    
    This test ensures that each table is defined only once across the codebase,
    preventing SQLAlchemy errors at import time.
    """
    # Find all table definitions
    table_definitions = find_table_definitions()
    
    # Check for duplicates
    has_duplicates = check_for_duplicates(table_definitions)
    
    # Fail the test if duplicates are found
    assert not has_duplicates, (
        "Duplicate table definitions found! "
        "Run 'python scripts/check_duplicate_tables.py' for details."
    )


def test_tables_are_defined():
    """Sanity check that we actually found some table definitions."""
    table_definitions = find_table_definitions()
    
    assert len(table_definitions) > 0, (
        "No table definitions found! This might indicate a problem with the scanner."
    )
    
    # We should have at least these core tables
    expected_tables = {
        'ai_analysis_results',
        'analysis_jobs',
        'prompt_recipes',
        'data_dictionary_entries',
        'dictionary_entries',  # New semantics table
    }
    
    found_tables = set(table_definitions.keys())
    missing = expected_tables - found_tables
    
    if missing:
        print(f"Warning: Expected tables not found: {missing}")
        print(f"Found tables: {sorted(found_tables)}")
    
    # At least some expected tables should exist
    assert len(expected_tables & found_tables) > 0, (
        "None of the expected core tables were found!"
    )

