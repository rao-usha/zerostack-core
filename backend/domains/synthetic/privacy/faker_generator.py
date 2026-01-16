"""Faker-based PII generator for replacing sensitive data."""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import pandas as pd
import numpy as np
from faker import Faker

from .pii_detector import PIIType

logger = logging.getLogger(__name__)


@dataclass
class GeneratorConfig:
    """Configuration for a PII generator."""
    faker_method: str
    kwargs: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


class FakerPIIGenerator:
    """Generate fake PII data using Faker library.
    
    Replaces detected PII columns with realistic fake data that:
    - Maintains the same data type
    - Preserves approximate distribution characteristics
    - Uses locale-appropriate formats
    """
    
    # Mapping of PII types to Faker methods
    PII_GENERATORS: Dict[PIIType, GeneratorConfig] = {
        PIIType.EMAIL: GeneratorConfig("email"),
        PIIType.PHONE: GeneratorConfig("phone_number"),
        PIIType.SSN: GeneratorConfig("ssn"),
        PIIType.CREDIT_CARD: GeneratorConfig("credit_card_number"),
        PIIType.NAME: GeneratorConfig("name"),
        PIIType.FIRST_NAME: GeneratorConfig("first_name"),
        PIIType.LAST_NAME: GeneratorConfig("last_name"),
        PIIType.ADDRESS: GeneratorConfig("street_address"),
        PIIType.CITY: GeneratorConfig("city"),
        PIIType.STATE: GeneratorConfig("state"),
        PIIType.ZIP_CODE: GeneratorConfig("zipcode"),
        PIIType.DATE_OF_BIRTH: GeneratorConfig("date_of_birth"),
        PIIType.IP_ADDRESS: GeneratorConfig("ipv4"),
        PIIType.URL: GeneratorConfig("url"),
        PIIType.USERNAME: GeneratorConfig("user_name"),
    }
    
    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """Initialize the Faker generator.
        
        Args:
            locale: Locale for generating data (e.g., "en_US", "en_GB", "de_DE")
            seed: Random seed for reproducibility
        """
        self.faker = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
            self.faker.seed_instance(seed)
        
        self.locale = locale
    
    def generate_column(
        self,
        pii_type: PIIType,
        num_rows: int,
        preserve_nulls: Optional[pd.Series] = None,
    ) -> pd.Series:
        """Generate a column of fake PII data.
        
        Args:
            pii_type: Type of PII to generate
            num_rows: Number of rows to generate
            preserve_nulls: Optional series to match null pattern from
            
        Returns:
            Series of fake PII values
        """
        if pii_type not in self.PII_GENERATORS:
            raise ValueError(f"No generator configured for PII type: {pii_type}")
        
        config = self.PII_GENERATORS[pii_type]
        faker_method = getattr(self.faker, config.faker_method)
        
        # Generate values
        values = [faker_method(**config.kwargs) for _ in range(num_rows)]
        series = pd.Series(values)
        
        # Preserve null pattern if provided
        if preserve_nulls is not None and len(preserve_nulls) == num_rows:
            null_mask = preserve_nulls.isna()
            series[null_mask] = None
        
        return series
    
    def replace_pii_columns(
        self,
        df: pd.DataFrame,
        pii_columns: Dict[str, PIIType],
        preserve_null_pattern: bool = True,
    ) -> pd.DataFrame:
        """Replace PII columns in a dataframe with fake data.
        
        Args:
            df: Original dataframe
            pii_columns: Dict mapping column names to PII types
            preserve_null_pattern: Whether to preserve null positions
            
        Returns:
            DataFrame with PII columns replaced
        """
        result = df.copy()
        num_rows = len(df)
        
        for col_name, pii_type in pii_columns.items():
            if col_name not in df.columns:
                logger.warning(f"Column '{col_name}' not found in dataframe, skipping")
                continue
            
            try:
                preserve_nulls = df[col_name] if preserve_null_pattern else None
                result[col_name] = self.generate_column(
                    pii_type,
                    num_rows,
                    preserve_nulls=preserve_nulls,
                )
                logger.info(f"Replaced PII column '{col_name}' with fake {pii_type.value} data")
            except Exception as e:
                logger.error(f"Failed to replace column '{col_name}': {e}")
                raise
        
        return result
    
    def generate_fake_record(self, pii_types: List[PIIType]) -> Dict[str, Any]:
        """Generate a single fake record with multiple PII fields.
        
        Args:
            pii_types: List of PII types to generate
            
        Returns:
            Dict with fake values for each type
        """
        record = {}
        for pii_type in pii_types:
            if pii_type in self.PII_GENERATORS:
                config = self.PII_GENERATORS[pii_type]
                faker_method = getattr(self.faker, config.faker_method)
                record[pii_type.value] = faker_method(**config.kwargs)
        return record
    
    def get_available_generators(self) -> List[str]:
        """Get list of available PII generators."""
        return [pii_type.value for pii_type in self.PII_GENERATORS.keys()]
    
    @classmethod
    def get_generator_info(cls) -> Dict[str, Dict[str, str]]:
        """Get information about available generators."""
        return {
            pii_type.value: {
                "faker_method": config.faker_method,
                "description": f"Generates fake {pii_type.value.replace('_', ' ')} values",
            }
            for pii_type, config in cls.PII_GENERATORS.items()
        }


class ConsistentPIIGenerator(FakerPIIGenerator):
    """PII generator that maintains consistency for related fields.
    
    For example, generates consistent first_name + last_name + email
    where the email uses the generated name.
    """
    
    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        super().__init__(locale, seed)
        self._identity_cache: Dict[int, Dict[str, Any]] = {}
    
    def generate_consistent_identity(self, row_index: int) -> Dict[str, Any]:
        """Generate a consistent identity for a row.
        
        Returns the same identity if called multiple times with same row_index.
        """
        if row_index in self._identity_cache:
            return self._identity_cache[row_index]
        
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        
        identity = {
            PIIType.FIRST_NAME: first_name,
            PIIType.LAST_NAME: last_name,
            PIIType.NAME: f"{first_name} {last_name}",
            PIIType.EMAIL: f"{first_name.lower()}.{last_name.lower()}@{self.faker.free_email_domain()}",
            PIIType.USERNAME: f"{first_name.lower()}{last_name.lower()}{self.faker.random_int(1, 999)}",
            PIIType.PHONE: self.faker.phone_number(),
            PIIType.ADDRESS: self.faker.street_address(),
            PIIType.CITY: self.faker.city(),
            PIIType.STATE: self.faker.state(),
            PIIType.ZIP_CODE: self.faker.zipcode(),
            PIIType.DATE_OF_BIRTH: self.faker.date_of_birth(),
            PIIType.SSN: self.faker.ssn(),
        }
        
        self._identity_cache[row_index] = identity
        return identity
    
    def replace_pii_columns_consistent(
        self,
        df: pd.DataFrame,
        pii_columns: Dict[str, PIIType],
    ) -> pd.DataFrame:
        """Replace PII columns with consistent fake identities.
        
        All name-related fields will be consistent for each row.
        """
        result = df.copy()
        num_rows = len(df)
        
        # Clear cache for fresh generation
        self._identity_cache.clear()
        
        # Generate identities for all rows
        for i in range(num_rows):
            self.generate_consistent_identity(i)
        
        # Replace columns
        for col_name, pii_type in pii_columns.items():
            if col_name not in df.columns:
                continue
            
            values = []
            for i in range(num_rows):
                identity = self._identity_cache[i]
                if pii_type in identity:
                    values.append(identity[pii_type])
                else:
                    # Fallback to regular generation
                    config = self.PII_GENERATORS[pii_type]
                    faker_method = getattr(self.faker, config.faker_method)
                    values.append(faker_method(**config.kwargs))
            
            # Preserve nulls
            null_mask = df[col_name].isna()
            series = pd.Series(values)
            series[null_mask] = None
            result[col_name] = series
        
        return result
