"""Recipe compatibility checker - assess if data meets recipe requirements."""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import table_scans, recipe_compatibility
from .models import (
    TableScanDetail, ColumnScan, RequirementCheck, 
    RecipeCompatibilityResponse, TableCompatibilityResponse
)

logger = logging.getLogger(__name__)


# ============================================================================
# RECIPE REQUIREMENTS DEFINITIONS
# ============================================================================

RECIPE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "recipe_forecasting_base": {
        "name": "M5 Sales Forecasting",
        "description": "LightGBM-based time series forecasting",
        "requirements": [
            {
                "id": "date_column",
                "name": "Date Column",
                "description": "A date or timestamp column for time series",
                "type": "date",
                "required": True,
                "match_patterns": ["date", "timestamp", "time", "day", "dt"]
            },
            {
                "id": "target_numeric",
                "name": "Target Variable",
                "description": "Numeric column to forecast (e.g., sales, demand)",
                "type": "numeric",
                "required": True,
                "match_patterns": ["sales", "demand", "quantity", "count", "revenue", "value", "amount"]
            },
            {
                "id": "group_columns",
                "name": "Group Columns",
                "description": "Columns to group by (e.g., item_id, store_id)",
                "type": "categorical",
                "required": False,
                "match_patterns": ["item", "product", "sku", "store", "location", "category", "id"]
            },
            {
                "id": "price_column",
                "name": "Price Column",
                "description": "Price column for price-based features",
                "type": "numeric",
                "required": False,
                "match_patterns": ["price", "cost", "sell_price", "unit_price"]
            },
            {
                "id": "sufficient_history",
                "name": "Sufficient History",
                "description": "At least 90 days of historical data",
                "type": "date_range",
                "required": True,
                "min_days": 90
            },
            {
                "id": "sufficient_rows",
                "name": "Sufficient Rows",
                "description": "At least 1000 rows for training",
                "type": "row_count",
                "required": True,
                "min_rows": 1000
            }
        ],
        "min_compatibility_score": 60
    },
    
    "recipe_classification_base": {
        "name": "Classification Model",
        "description": "Binary or multi-class classification",
        "requirements": [
            {
                "id": "target_column",
                "name": "Target Column",
                "description": "Column to predict (categorical/boolean)",
                "type": "categorical_or_boolean",
                "required": True,
                "match_patterns": ["target", "label", "class", "outcome", "result", "status"]
            },
            {
                "id": "feature_columns",
                "name": "Feature Columns",
                "description": "At least 3 non-target columns",
                "type": "min_columns",
                "required": True,
                "min_count": 3
            },
            {
                "id": "sufficient_rows",
                "name": "Sufficient Rows",
                "description": "At least 500 rows for training",
                "type": "row_count",
                "required": True,
                "min_rows": 500
            }
        ],
        "min_compatibility_score": 70
    },
    
    "recipe_anomaly_detection": {
        "name": "Anomaly Detection",
        "description": "Detect outliers and anomalies in data",
        "requirements": [
            {
                "id": "numeric_columns",
                "name": "Numeric Columns",
                "description": "At least 2 numeric columns for analysis",
                "type": "min_numeric",
                "required": True,
                "min_count": 2
            },
            {
                "id": "sufficient_rows",
                "name": "Sufficient Rows",
                "description": "At least 100 rows",
                "type": "row_count",
                "required": True,
                "min_rows": 100
            }
        ],
        "min_compatibility_score": 50
    }
}


class RecipeCompatibilityChecker:
    """
    Checks if table data meets recipe requirements.
    
    Analyzes scanned table data and determines:
    - Which requirements are met
    - Which are missing or partial
    - Overall compatibility score
    - Recommendations for improvement
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_compatibility(
        self, 
        table_scan: TableScanDetail,
        recipe_id: str
    ) -> RecipeCompatibilityResponse:
        """
        Check if a table is compatible with a recipe.
        
        Args:
            table_scan: Detailed table scan data
            recipe_id: Recipe ID to check against
            
        Returns:
            Compatibility assessment
        """
        if recipe_id not in RECIPE_REQUIREMENTS:
            raise ValueError(f"Unknown recipe: {recipe_id}")
        
        recipe = RECIPE_REQUIREMENTS[recipe_id]
        requirements = recipe["requirements"]
        
        met: List[RequirementCheck] = []
        missing: List[RequirementCheck] = []
        partial: List[RequirementCheck] = []
        recommendations: List[str] = []
        
        for req in requirements:
            check = self._check_requirement(req, table_scan)
            
            if check.status == "met":
                met.append(check)
            elif check.status == "partial":
                partial.append(check)
                if check.notes:
                    recommendations.append(check.notes)
            else:
                missing.append(check)
                if req["required"]:
                    recommendations.append(f"Missing required: {req['name']} - {req['description']}")
        
        # Calculate score
        total_reqs = len(requirements)
        required_reqs = [r for r in requirements if r["required"]]
        required_met = len([m for m in met if any(r["id"] == m.requirement for r in required_reqs)])
        
        # Score: required requirements weighted more
        required_score = (required_met / len(required_reqs)) * 70 if required_reqs else 70
        optional_score = (len(met) / total_reqs) * 30
        score = required_score + optional_score
        
        # Determine status
        if score >= 90 and not missing:
            status = "ready"
        elif score >= recipe["min_compatibility_score"]:
            status = "partial"
        else:
            status = "incompatible"
        
        # Quality estimate
        if score >= 90:
            quality = "excellent"
        elif score >= 75:
            quality = "good"
        elif score >= 50:
            quality = "fair"
        else:
            quality = "poor"
        
        return RecipeCompatibilityResponse(
            table_scan_id=table_scan.id,
            recipe_id=recipe_id,
            recipe_name=recipe["name"],
            compatibility_score=round(score, 1),
            status=status,
            requirements_met=met,
            requirements_missing=missing,
            requirements_partial=partial,
            recommendations=recommendations,
            can_run=status != "incompatible",
            estimated_quality=quality
        )
    
    def _check_requirement(
        self, 
        req: dict, 
        table: TableScanDetail
    ) -> RequirementCheck:
        """Check a single requirement against table data."""
        req_type = req["type"]
        req_id = req["id"]
        patterns = req.get("match_patterns", [])
        
        # DATE COLUMN
        if req_type == "date":
            if table.date_column:
                return RequirementCheck(
                    requirement=req_id,
                    status="met",
                    column=table.date_column,
                    notes=None
                )
            # Try to find by pattern
            for col in table.columns:
                if col.is_date or any(p in col.name.lower() for p in patterns):
                    return RequirementCheck(
                        requirement=req_id,
                        status="met",
                        column=col.name,
                        notes="Detected date column by name pattern"
                    )
            return RequirementCheck(
                requirement=req_id,
                status="missing",
                column=None,
                notes="No date/timestamp column found"
            )
        
        # NUMERIC TARGET
        elif req_type == "numeric":
            for col in table.columns:
                if col.is_numeric and any(p in col.name.lower() for p in patterns):
                    if col.nulls_pct > 20:
                        return RequirementCheck(
                            requirement=req_id,
                            status="partial",
                            column=col.name,
                            notes=f"Column {col.name} has {col.nulls_pct:.1f}% nulls - consider imputation"
                        )
                    return RequirementCheck(
                        requirement=req_id,
                        status="met",
                        column=col.name,
                        notes=None
                    )
            # Any numeric column as fallback
            numeric_cols = [c for c in table.columns if c.is_numeric]
            if numeric_cols:
                return RequirementCheck(
                    requirement=req_id,
                    status="partial",
                    column=numeric_cols[0].name,
                    notes=f"No exact match found. Using {numeric_cols[0].name} - verify this is the target"
                )
            return RequirementCheck(
                requirement=req_id,
                status="missing",
                column=None,
                notes="No numeric columns found"
            )
        
        # CATEGORICAL COLUMNS
        elif req_type == "categorical":
            matches = []
            for col in table.columns:
                if col.is_categorical or (col.is_text and col.cardinality < 1000):
                    if any(p in col.name.lower() for p in patterns):
                        matches.append(col.name)
            if matches:
                return RequirementCheck(
                    requirement=req_id,
                    status="met",
                    column=", ".join(matches),
                    notes=None
                )
            return RequirementCheck(
                requirement=req_id,
                status="missing",
                column=None,
                notes="No matching categorical columns found"
            )
        
        # DATE RANGE CHECK
        elif req_type == "date_range":
            min_days = req.get("min_days", 90)
            if table.date_span_days and table.date_span_days >= min_days:
                return RequirementCheck(
                    requirement=req_id,
                    status="met",
                    column=table.date_column,
                    notes=f"{table.date_span_days} days of history"
                )
            elif table.date_span_days:
                return RequirementCheck(
                    requirement=req_id,
                    status="partial",
                    column=table.date_column,
                    notes=f"Only {table.date_span_days} days of history (need {min_days}+)"
                )
            return RequirementCheck(
                requirement=req_id,
                status="missing",
                column=None,
                notes="Cannot determine date range"
            )
        
        # ROW COUNT CHECK
        elif req_type == "row_count":
            min_rows = req.get("min_rows", 1000)
            if table.row_count and table.row_count >= min_rows:
                return RequirementCheck(
                    requirement=req_id,
                    status="met",
                    column=None,
                    notes=f"{table.row_count:,} rows"
                )
            elif table.row_count:
                return RequirementCheck(
                    requirement=req_id,
                    status="partial",
                    column=None,
                    notes=f"Only {table.row_count:,} rows (need {min_rows:,}+)"
                )
            return RequirementCheck(
                requirement=req_id,
                status="missing",
                column=None,
                notes="Cannot determine row count"
            )
        
        # MIN COLUMNS CHECK
        elif req_type == "min_columns":
            min_count = req.get("min_count", 3)
            if table.column_count and table.column_count >= min_count:
                return RequirementCheck(
                    requirement=req_id,
                    status="met",
                    column=None,
                    notes=f"{table.column_count} columns"
                )
            return RequirementCheck(
                requirement=req_id,
                status="missing",
                column=None,
                notes=f"Only {table.column_count} columns (need {min_count}+)"
            )
        
        # MIN NUMERIC CHECK
        elif req_type == "min_numeric":
            min_count = req.get("min_count", 2)
            numeric_cols = [c for c in table.columns if c.is_numeric]
            if len(numeric_cols) >= min_count:
                return RequirementCheck(
                    requirement=req_id,
                    status="met",
                    column=", ".join(c.name for c in numeric_cols[:5]),
                    notes=f"{len(numeric_cols)} numeric columns"
                )
            return RequirementCheck(
                requirement=req_id,
                status="missing",
                column=None,
                notes=f"Only {len(numeric_cols)} numeric columns (need {min_count}+)"
            )
        
        # CATEGORICAL OR BOOLEAN
        elif req_type == "categorical_or_boolean":
            for col in table.columns:
                if any(p in col.name.lower() for p in patterns):
                    if col.is_boolean or col.is_categorical:
                        return RequirementCheck(
                            requirement=req_id,
                            status="met",
                            column=col.name,
                            notes=None
                        )
            # Check for low-cardinality columns
            for col in table.columns:
                if col.cardinality and col.cardinality < 20:
                    if any(p in col.name.lower() for p in patterns):
                        return RequirementCheck(
                            requirement=req_id,
                            status="met",
                            column=col.name,
                            notes=f"{col.cardinality} unique values"
                        )
            return RequirementCheck(
                requirement=req_id,
                status="missing",
                column=None,
                notes="No suitable target column found"
            )
        
        # DEFAULT
        return RequirementCheck(
            requirement=req_id,
            status="missing",
            column=None,
            notes=f"Unknown requirement type: {req_type}"
        )
    
    async def check_all_recipes(
        self, 
        table_scan: TableScanDetail
    ) -> TableCompatibilityResponse:
        """Check compatibility against all available recipes."""
        results = []
        
        for recipe_id in RECIPE_REQUIREMENTS:
            try:
                result = await self.check_compatibility(table_scan, recipe_id)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to check {recipe_id}: {e}")
        
        # Sort by compatibility score
        results.sort(key=lambda r: r.compatibility_score, reverse=True)
        
        return TableCompatibilityResponse(
            table_scan_id=table_scan.id,
            table_name=table_scan.full_name,
            recipes=results
        )
    
    def get_available_recipes(self) -> List[dict]:
        """Get list of available recipes with descriptions."""
        return [
            {
                "id": recipe_id,
                "name": recipe["name"],
                "description": recipe["description"],
                "requirements_count": len(recipe["requirements"]),
                "required_count": len([r for r in recipe["requirements"] if r["required"]])
            }
            for recipe_id, recipe in RECIPE_REQUIREMENTS.items()
        ]
