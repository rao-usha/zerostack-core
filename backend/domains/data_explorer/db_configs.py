"""
Multiple database configurations for Data Explorer.

Automatically detects all EXPLORER*_DB_* environment variables.
"""
import os
import re
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Configuration for a single database connection."""
    id: str
    name: str
    host: str
    port: int
    user: str
    password: str
    database: str
    description: str = ""


def get_database_configs() -> List[DatabaseConfig]:
    """
    Get all configured databases for Data Explorer.
    
    Automatically scans environment for:
    - EXPLORER_DB_* (primary database)
    - EXPLORER2_DB_*, EXPLORER3_DB_*, etc.
    - EXPLORER_DB_2_*, EXPLORER_DB_3_*, etc.
    
    Returns:
        List of database configurations
    """
    configs = []
    detected_dbs = set()
    
    # Scan all environment variables for EXPLORER patterns
    for key in os.environ.keys():
        # Match patterns like EXPLORER_DB_HOST, EXPLORER2_DB_HOST, EXPLORER_DB_2_HOST
        if key.startswith('EXPLORER') and '_DB_HOST' in key:
            # Extract the database identifier
            match = re.match(r'EXPLORER(\d*)_DB(?:_(\d+))?_HOST', key)
            if match:
                num1 = match.group(1) or ''
                num2 = match.group(2) or ''
                
                # Determine prefix for this database
                if num2:
                    prefix = f'EXPLORER_DB_{num2}'
                    db_id = f'db{num2}'
                    db_num = int(num2)
                elif num1:
                    prefix = f'EXPLORER{num1}_DB'
                    db_id = f'db{num1}'
                    db_num = int(num1)
                else:
                    prefix = 'EXPLORER_DB'
                    db_id = 'default'
                    db_num = 0
                
                if db_id in detected_dbs:
                    continue
                detected_dbs.add(db_id)
                
                # Get all config values for this database
                host = os.getenv(f'{prefix}_HOST')
                port_str = os.getenv(f'{prefix}_PORT', '5432')
                user = os.getenv(f'{prefix}_USER', 'postgres')
                password = os.getenv(f'{prefix}_PASSWORD', '')
                database = os.getenv(f'{prefix}_NAME', 'postgres')
                
                if host:  # Only add if host is configured
                    try:
                        port = int(port_str)
                    except:
                        port = 5432
                    
                    configs.append(DatabaseConfig(
                        id=db_id,
                        name=database,
                        host=host,
                        port=port,
                        user=user,
                        password=password,
                        database=database,
                        description=f"{host}:{port}"
                    ))
    
    # Sort by database number (default first, then by number)
    def sort_key(config):
        if config.id == 'default':
            return (0, '')
        match = re.match(r'db(\d+)', config.id)
        if match:
            return (1, int(match.group(1)))
        return (2, config.id)
    
    configs.sort(key=sort_key)
    
    return configs


def get_database_config_by_id(db_id: str) -> DatabaseConfig:
    """Get a specific database configuration by ID."""
    configs = get_database_configs()
    for config in configs:
        if config.id == db_id:
            return config
    raise ValueError(f"Database configuration '{db_id}' not found")

