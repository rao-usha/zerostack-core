"""
Data Explorer database connection utility.

This module provides read-only access to Postgres databases for exploration.
Supports multiple database configurations.
"""
import os
from typing import Optional
from contextlib import contextmanager
import psycopg
from .db_configs import DatabaseConfig, get_database_config_by_id


class ExplorerDBConfig:
    """Configuration for the Explorer database connection (legacy)."""
    
    def __init__(self):
        self.host = os.getenv("EXPLORER_DB_HOST", "localhost")
        self.port = int(os.getenv("EXPLORER_DB_PORT", "5432"))
        self.user = os.getenv("EXPLORER_DB_USER", "nex")
        self.password = os.getenv("EXPLORER_DB_PASSWORD", "nex")
        self.database = os.getenv("EXPLORER_DB_NAME", "nex")
        
    def get_connection_string(self) -> str:
        """Build psycopg connection string."""
        return f"host={self.host} port={self.port} user={self.user} password={self.password} dbname={self.database}"
    
    def validate(self) -> bool:
        """Validate that required config is present."""
        return bool(self.password and self.database)


# Global config instance (for backward compatibility)
config = ExplorerDBConfig()


@contextmanager
def get_explorer_connection(db_id: str = "default"):
    """
    Context manager for getting a read-only database connection.
    
    Args:
        db_id: Database configuration ID (default: "default")
    
    Usage:
        with get_explorer_connection("db2") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM table")
                results = cur.fetchall()
    
    Yields:
        psycopg.Connection: Database connection
    
    Raises:
        psycopg.Error: If connection fails
    """
    conn = None
    try:
        # Get the database configuration
        db_config = get_database_config_by_id(db_id)
        
        # Build connection string
        conn_string = f"host={db_config.host} port={db_config.port} user={db_config.user} password={db_config.password} dbname={db_config.database}"
        
        conn = psycopg.connect(conn_string)
        # Set session to read-only for safety
        with conn.cursor() as cur:
            cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        yield conn
    finally:
        if conn:
            conn.close()


def test_connection(db_id: str = "default") -> dict:
    """
    Test the database connection.
    
    Args:
        db_id: Database configuration ID
    
    Returns:
        dict: Connection status and info
    """
    try:
        db_config = get_database_config_by_id(db_id)
        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                cur.execute("SELECT current_database()")
                db_name = cur.fetchone()[0]
                
            return {
                "connected": True,
                "database": db_name,
                "version": version,
                "host": db_config.host,
                "port": db_config.port
            }
    except Exception as e:
        try:
            db_config = get_database_config_by_id(db_id)
            return {
                "connected": False,
                "error": str(e),
                "host": db_config.host,
                "port": db_config.port
            }
        except:
            return {
                "connected": False,
                "error": str(e),
                "host": "unknown",
                "port": 0
            }

