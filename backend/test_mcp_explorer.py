#!/usr/bin/env python3
"""
Test script for MCP Data Explorer.

This script tests:
1. Database configuration detection
2. Data Explorer service functions
3. HTTP bridge endpoints (requires FastAPI backend running)
4. MCP server tool handlers

Usage:
    python test_mcp_explorer.py
"""

import sys
import json
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domains.data_explorer.db_configs import get_database_configs
from domains.data_explorer.service import DataExplorerService
from domains.data_explorer.connection import test_connection


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"    {details}")


def test_database_configs():
    """Test database configuration detection."""
    print("\n" + "="*60)
    print("Testing Database Configuration")
    print("="*60)
    
    try:
        configs = get_database_configs()
        print_test(
            "Database config detection",
            len(configs) > 0,
            f"Found {len(configs)} database configuration(s)"
        )
        
        for config in configs:
            print(f"    - {config.id}: {config.database} @ {config.host}:{config.port}")
        
        return len(configs) > 0
    except Exception as e:
        print_test("Database config detection", False, f"Error: {e}")
        return False


def test_database_connection():
    """Test database connection."""
    print("\n" + "="*60)
    print("Testing Database Connection")
    print("="*60)
    
    try:
        result = test_connection("default")
        connected = result.get("connected", False)
        
        print_test(
            "Database connection",
            connected,
            f"Database: {result.get('database', 'unknown')}, "
            f"Host: {result.get('host', 'unknown')}:{result.get('port', 'unknown')}"
        )
        
        if connected:
            print(f"    Version: {result.get('version', 'unknown')[:50]}...")
        else:
            print(f"    Error: {result.get('error', 'unknown')}")
        
        return connected
    except Exception as e:
        print_test("Database connection", False, f"Error: {e}")
        return False


def test_data_explorer_service():
    """Test Data Explorer service methods."""
    print("\n" + "="*60)
    print("Testing Data Explorer Service")
    print("="*60)
    
    all_passed = True
    
    # Test list_schemas
    try:
        schemas = DataExplorerService.get_schemas(db_id="default")
        passed = len(schemas) > 0
        all_passed = all_passed and passed
        print_test(
            "list_schemas",
            passed,
            f"Found {len(schemas)} schema(s): {', '.join([s.name for s in schemas[:3]])}"
        )
    except Exception as e:
        print_test("list_schemas", False, f"Error: {e}")
        all_passed = False
    
    # Test list_tables
    try:
        tables = DataExplorerService.get_tables(schema="public", db_id="default")
        passed = True  # OK if empty
        all_passed = all_passed and passed
        print_test(
            "list_tables",
            passed,
            f"Found {len(tables)} table(s) in 'public' schema"
        )
        
        # If we have tables, use the first one for further tests
        if tables:
            test_table = tables[0].name
            print(f"    Using table '{test_table}' for further tests...")
            
            # Test get_columns
            try:
                columns = DataExplorerService.get_columns(
                    schema="public",
                    table=test_table,
                    db_id="default"
                )
                passed = len(columns) > 0
                all_passed = all_passed and passed
                print_test(
                    "get_table_info",
                    passed,
                    f"Found {len(columns)} column(s) in '{test_table}'"
                )
            except Exception as e:
                print_test("get_table_info", False, f"Error: {e}")
                all_passed = False
            
            # Test sample_rows
            try:
                result = DataExplorerService.get_table_rows(
                    schema="public",
                    table=test_table,
                    page=1,
                    page_size=5,
                    db_id="default"
                )
                passed = True  # OK even if no rows
                all_passed = all_passed and passed
                print_test(
                    "sample_rows",
                    passed,
                    f"Retrieved {len(result.rows)} row(s) from '{test_table}'"
                )
            except Exception as e:
                print_test("sample_rows", False, f"Error: {e}")
                all_passed = False
            
            # Test profile_table (only if table has data)
            try:
                profile = DataExplorerService.profile_table(
                    schema="public",
                    table=test_table,
                    max_distinct=10,
                    db_id="default"
                )
                passed = "column_profiles" in profile
                all_passed = all_passed and passed
                col_count = len(profile.get("column_profiles", {}))
                print_test(
                    "profile_table",
                    passed,
                    f"Profiled {col_count} column(s) in '{test_table}'"
                )
            except Exception as e:
                print_test("profile_table", False, f"Error: {e}")
                all_passed = False
    
    except Exception as e:
        print_test("list_tables", False, f"Error: {e}")
        all_passed = False
    
    # Test run_query (safe query)
    try:
        result = DataExplorerService.execute_query(
            sql="SELECT 1 as test_column",
            page=1,
            page_size=10,
            db_id="default"
        )
        passed = result.error is None and len(result.rows) == 1
        all_passed = all_passed and passed
        print_test(
            "run_query (safe)",
            passed,
            f"Executed query in {result.execution_time_ms:.2f}ms"
        )
    except Exception as e:
        print_test("run_query (safe)", False, f"Error: {e}")
        all_passed = False
    
    # Test run_query (unsafe query - should be blocked)
    try:
        result = DataExplorerService.execute_query(
            sql="DELETE FROM users",
            page=1,
            page_size=10,
            db_id="default"
        )
        passed = result.error is not None and "forbidden" in result.error.get("message", "").lower()
        all_passed = all_passed and passed
        print_test(
            "run_query (unsafe - should block)",
            passed,
            f"Correctly blocked unsafe query"
        )
    except Exception as e:
        print_test("run_query (unsafe)", False, f"Error: {e}")
        all_passed = False
    
    return all_passed


def test_http_bridge():
    """Test HTTP bridge endpoints."""
    print("\n" + "="*60)
    print("Testing HTTP Bridge Endpoints")
    print("="*60)
    print("Note: FastAPI backend must be running on port 8000")
    print("Start with: uvicorn main:app --port 8000")
    print("="*60)
    
    try:
        import requests
    except ImportError:
        print_test("HTTP bridge", False, "requests library not installed")
        print("    Install with: pip install requests")
        return False
    
    base_url = "http://localhost:8000/api/v1/data-explorer"
    all_passed = True
    
    # Test list_connections
    try:
        response = requests.post(
            f"{base_url}/tool/list_connections",
            json={},
            timeout=5
        )
        passed = response.status_code == 200 and response.json().get("success", False)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json().get("data", [])
            print_test(
                "POST /tool/list_connections",
                passed,
                f"Found {len(data)} connection(s)"
            )
        else:
            print_test("POST /tool/list_connections", False, f"Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print_test("POST /tool/list_connections", False, f"Connection error: {e}")
        print("    Make sure FastAPI backend is running!")
        return False
    
    # Test list_schemas
    try:
        response = requests.post(
            f"{base_url}/tool/list_schemas",
            json={"connection_id": "default"},
            timeout=5
        )
        passed = response.status_code == 200 and response.json().get("success", False)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json().get("data", [])
            print_test(
                "POST /tool/list_schemas",
                passed,
                f"Found {len(data)} schema(s)"
            )
        else:
            print_test("POST /tool/list_schemas", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test("POST /tool/list_schemas", False, f"Error: {e}")
        all_passed = False
    
    # Test list_tables
    try:
        response = requests.post(
            f"{base_url}/tool/list_tables",
            json={"connection_id": "default", "schema": "public"},
            timeout=5
        )
        passed = response.status_code == 200 and response.json().get("success", False)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json().get("data", [])
            print_test(
                "POST /tool/list_tables",
                passed,
                f"Found {len(data)} table(s)"
            )
        else:
            print_test("POST /tool/list_tables", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test("POST /tool/list_tables", False, f"Error: {e}")
        all_passed = False
    
    # Test run_query
    try:
        response = requests.post(
            f"{base_url}/tool/run_query",
            json={
                "connection_id": "default",
                "sql": "SELECT 1 as test_value",
                "page": 1,
                "page_size": 10
            },
            timeout=5
        )
        passed = response.status_code == 200 and response.json().get("success", False)
        all_passed = all_passed and passed
        
        if passed:
            data = response.json().get("data", {})
            print_test(
                "POST /tool/run_query",
                passed,
                f"Query executed in {data.get('execution_time_ms', 0):.2f}ms"
            )
        else:
            print_test("POST /tool/run_query", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test("POST /tool/run_query", False, f"Error: {e}")
        all_passed = False
    
    return all_passed


def test_mcp_server_tools():
    """Test MCP server tool handlers."""
    print("\n" + "="*60)
    print("Testing MCP Server Tool Handlers")
    print("="*60)
    
    try:
        # Import MCP server handlers
        from mcp_server import (
            handle_list_connections,
            handle_list_schemas,
            handle_list_tables,
            handle_get_table_info,
            handle_sample_rows,
            handle_profile_table,
            handle_run_query
        )
    except ImportError as e:
        print_test("MCP server imports", False, f"Error: {e}")
        return False
    
    all_passed = True
    
    # Test handle_list_connections
    try:
        result = handle_list_connections()
        passed = isinstance(result, list) and len(result) > 0
        all_passed = all_passed and passed
        print_test(
            "handle_list_connections",
            passed,
            f"Returned {len(result)} connection(s)"
        )
    except Exception as e:
        print_test("handle_list_connections", False, f"Error: {e}")
        all_passed = False
    
    # Test handle_list_schemas
    try:
        result = handle_list_schemas("default")
        passed = isinstance(result, list)
        all_passed = all_passed and passed
        print_test(
            "handle_list_schemas",
            passed,
            f"Returned {len(result)} schema(s)"
        )
    except Exception as e:
        print_test("handle_list_schemas", False, f"Error: {e}")
        all_passed = False
    
    # Test handle_list_tables
    try:
        result = handle_list_tables("default", "public")
        passed = isinstance(result, list)
        all_passed = all_passed and passed
        print_test(
            "handle_list_tables",
            passed,
            f"Returned {len(result)} table(s)"
        )
    except Exception as e:
        print_test("handle_list_tables", False, f"Error: {e}")
        all_passed = False
    
    # Test handle_run_query
    try:
        result = handle_run_query("default", "SELECT 1 as test", 1, 10)
        passed = isinstance(result, dict) and not result.get("error")
        all_passed = all_passed and passed
        print_test(
            "handle_run_query",
            passed,
            f"Query executed successfully"
        )
    except Exception as e:
        print_test("handle_run_query", False, f"Error: {e}")
        all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MCP DATA EXPLORER TEST SUITE")
    print("="*60)
    
    results = {
        "Database Configuration": test_database_configs(),
        "Database Connection": test_database_connection(),
        "Data Explorer Service": test_data_explorer_service(),
        "HTTP Bridge": test_http_bridge(),
        "MCP Server Tools": test_mcp_server_tools()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nThe MCP Data Explorer is working correctly!")
        print("\nNext steps:")
        print("1. Start the MCP server: python mcp_server.py")
        print("2. Configure Claude Desktop (see MCP_DATA_EXPLORER_SETUP.md)")
        print("3. Or use HTTP bridge with xAI, Gemini, ChatGPT")
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease review the errors above and:")
        print("1. Check database configuration in .env file")
        print("2. Ensure Postgres is running and accessible")
        print("3. Verify FastAPI backend is running for HTTP bridge tests")
        print("4. See MCP_DATA_EXPLORER_SETUP.md for troubleshooting")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

