"""Condition processing for conditional synthetic data generation."""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Tuple, Optional, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .models import GenerationCondition

logger = logging.getLogger(__name__)

# Operator string values for comparison (avoid runtime import of ConditionOperator)
OP_EQ = "eq"
OP_NE = "ne"
OP_GT = "gt"
OP_GTE = "gte"
OP_LT = "lt"
OP_LTE = "lte"
OP_IN = "in"
OP_NOT_IN = "not_in"
OP_BETWEEN = "between"


class ConditionValidationError(Exception):
    """Raised when a condition is invalid."""
    pass


class ConditionProcessor:
    """Process and validate generation conditions.

    Handles:
    - Validation of conditions against column metadata
    - Splitting conditions into SDV-native (exact) and post-filter (range)
    - Building SDV Condition objects
    - Applying post-filters after generation
    """

    # Operators that SDV can handle natively (exact value matching)
    SDV_NATIVE_OPERATORS = {OP_EQ, OP_IN}

    # Operators that require post-filtering
    POST_FILTER_OPERATORS = {OP_NE, OP_GT, OP_GTE, OP_LT, OP_LTE, OP_NOT_IN, OP_BETWEEN}

    def _get_operator_value(self, operator) -> str:
        """Get the string value of an operator (handles both Enum and string)."""
        if hasattr(operator, 'value'):
            return operator.value
        return str(operator)

    def validate_conditions(
        self,
        conditions: List[GenerationCondition],
        df: pd.DataFrame,
    ) -> List[str]:
        """Validate conditions against source data.

        Args:
            conditions: List of conditions to validate
            df: Source DataFrame to validate against

        Returns:
            List of warning messages (empty if all valid)

        Raises:
            ConditionValidationError: If a condition is invalid
        """
        warnings = []
        columns = set(df.columns)
        dtypes = {col: str(df[col].dtype) for col in df.columns}

        for cond in conditions:
            # Check column exists
            if cond.column not in columns:
                raise ConditionValidationError(
                    f"Column '{cond.column}' not found in source data. "
                    f"Available columns: {sorted(columns)}"
                )

            col_dtype = dtypes[cond.column]
            is_numeric = any(t in col_dtype for t in ['int', 'float', 'Int', 'Float'])
            is_categorical = col_dtype in ['object', 'category', 'bool']

            op_value = self._get_operator_value(cond.operator)

            # Validate operator/value combinations
            if op_value == OP_BETWEEN:
                if not isinstance(cond.value, (list, tuple)) or len(cond.value) != 2:
                    raise ConditionValidationError(
                        f"BETWEEN operator requires [min, max] list, got: {cond.value}"
                    )
                if not is_numeric:
                    raise ConditionValidationError(
                        f"BETWEEN operator only valid for numeric columns, "
                        f"'{cond.column}' is {col_dtype}"
                    )

            elif op_value in (OP_IN, OP_NOT_IN):
                if not isinstance(cond.value, (list, tuple)):
                    raise ConditionValidationError(
                        f"{op_value} operator requires a list, got: {type(cond.value)}"
                    )

            elif op_value in (OP_GT, OP_GTE, OP_LT, OP_LTE):
                if not is_numeric:
                    warnings.append(
                        f"Comparison operator '{op_value}' on non-numeric column "
                        f"'{cond.column}' ({col_dtype}) may not work as expected"
                    )

            # Check if condition value exists in categorical column
            if op_value == OP_EQ and is_categorical:
                unique_vals = set(df[cond.column].dropna().unique())
                if cond.value not in unique_vals:
                    warnings.append(
                        f"Value '{cond.value}' not found in column '{cond.column}'. "
                        f"Available values: {sorted(str(v) for v in list(unique_vals)[:10])}"
                    )

        return warnings

    def split_conditions(
        self,
        conditions: List[GenerationCondition],
    ) -> Tuple[List[GenerationCondition], List[GenerationCondition]]:
        """Split conditions into SDV-native and post-filter groups.

        SDV can natively handle exact value conditions (eq, in).
        Range conditions (gt, gte, lt, lte, between, ne, not_in) need post-filtering.

        Args:
            conditions: List of all conditions

        Returns:
            Tuple of (sdv_conditions, post_filter_conditions)
        """
        sdv_conditions = []
        post_filter_conditions = []

        for cond in conditions:
            op_value = self._get_operator_value(cond.operator)
            if op_value in self.SDV_NATIVE_OPERATORS:
                sdv_conditions.append(cond)
            else:
                post_filter_conditions.append(cond)

        return sdv_conditions, post_filter_conditions

    def build_sdv_conditions(
        self,
        num_rows: int,
        conditions: List[GenerationCondition],
    ) -> List[Any]:
        """Build SDV Condition objects from exact-value conditions.

        When multiple conditions exist, they are combined to ensure all
        conditions are satisfied together. For example, if we have:
        - region EQ "US"
        - status IN ["active", "pending"]

        We create conditions that combine them:
        - Condition(column_values={"region": "US", "status": "active"})
        - Condition(column_values={"region": "US", "status": "pending"})

        Args:
            num_rows: Number of rows to request per condition
            conditions: List of exact-value conditions

        Returns:
            List of SDV Condition objects
        """
        from sdv.sampling import Condition
        import itertools

        if not conditions:
            return []

        # Separate EQ conditions (single value) from IN conditions (multiple values)
        eq_values = {}  # column -> value
        in_values = {}  # column -> [values]

        for cond in conditions:
            op_value = self._get_operator_value(cond.operator)

            if op_value == OP_EQ:
                eq_values[cond.column] = cond.value
            elif op_value == OP_IN:
                in_values[cond.column] = cond.value

        # If no IN conditions, just return a single condition with all EQ values
        if not in_values:
            if eq_values:
                return [Condition(num_rows=num_rows, column_values=eq_values)]
            return []

        # Generate all combinations of IN values
        in_columns = list(in_values.keys())
        in_value_lists = [in_values[col] for col in in_columns]
        combinations = list(itertools.product(*in_value_lists))

        # Calculate rows per combination
        rows_per_combo = max(1, num_rows // len(combinations))
        extra_rows = num_rows % len(combinations)

        sdv_conditions = []
        for i, combo in enumerate(combinations):
            # Start with all EQ values
            column_values = eq_values.copy()

            # Add this combination's IN values
            for col, val in zip(in_columns, combo):
                column_values[col] = val

            # Calculate rows for this combo
            rows = rows_per_combo + (1 if i < extra_rows else 0)

            if rows > 0:
                sdv_conditions.append(Condition(
                    num_rows=rows,
                    column_values=column_values
                ))

        return sdv_conditions

    def merge_sdv_conditions(
        self,
        num_rows: int,
        conditions: List[GenerationCondition],
    ) -> Optional[Any]:
        """Merge multiple EQ conditions into a single SDV Condition.

        When multiple exact-value conditions are specified, we can combine them
        into a single condition for more efficient sampling.

        Args:
            num_rows: Number of rows to generate
            conditions: List of exact-value conditions (EQ only)

        Returns:
            Single merged SDV Condition, or None if conditions include IN
        """
        from sdv.sampling import Condition

        # Check if we can merge (all EQ conditions)
        if not all(self._get_operator_value(c.operator) == OP_EQ for c in conditions):
            return None

        column_values = {c.column: c.value for c in conditions}
        return Condition(num_rows=num_rows, column_values=column_values)

    def apply_post_filters(
        self,
        df: pd.DataFrame,
        conditions: List[GenerationCondition],
    ) -> pd.DataFrame:
        """Apply post-generation filters for range conditions.

        Args:
            df: Generated synthetic DataFrame
            conditions: List of range/comparison conditions

        Returns:
            Filtered DataFrame
        """
        if not conditions:
            return df

        mask = pd.Series([True] * len(df), index=df.index)

        for cond in conditions:
            col = cond.column
            if col not in df.columns:
                logger.warning(f"Column '{col}' not in generated data, skipping filter")
                continue

            op_value = self._get_operator_value(cond.operator)

            if op_value == OP_NE:
                mask &= df[col] != cond.value

            elif op_value == OP_GT:
                mask &= df[col] > cond.value

            elif op_value == OP_GTE:
                mask &= df[col] >= cond.value

            elif op_value == OP_LT:
                mask &= df[col] < cond.value

            elif op_value == OP_LTE:
                mask &= df[col] <= cond.value

            elif op_value == OP_NOT_IN:
                mask &= ~df[col].isin(cond.value)

            elif op_value == OP_BETWEEN:
                min_val, max_val = cond.value
                mask &= (df[col] >= min_val) & (df[col] <= max_val)

        filtered_df = df[mask].reset_index(drop=True)

        logger.info(
            f"Post-filter: {len(df)} rows -> {len(filtered_df)} rows "
            f"({len(conditions)} conditions)"
        )

        return filtered_df

    def estimate_oversample_factor(
        self,
        df: pd.DataFrame,
        conditions: List[GenerationCondition],
    ) -> float:
        """Estimate oversample factor based on condition selectivity.

        Analyzes the source data to estimate what fraction of rows would
        match the conditions, then returns an appropriate oversample factor.

        Args:
            df: Source DataFrame
            conditions: Range conditions to analyze

        Returns:
            Recommended oversample factor (1.0 to 10.0)
        """
        if not conditions:
            return 1.0

        # Apply conditions to source data to estimate selectivity
        mask = pd.Series([True] * len(df), index=df.index)

        for cond in conditions:
            col = cond.column
            if col not in df.columns:
                continue

            op_value = self._get_operator_value(cond.operator)

            try:
                if op_value == OP_NE:
                    mask &= df[col] != cond.value
                elif op_value == OP_GT:
                    mask &= df[col] > cond.value
                elif op_value == OP_GTE:
                    mask &= df[col] >= cond.value
                elif op_value == OP_LT:
                    mask &= df[col] < cond.value
                elif op_value == OP_LTE:
                    mask &= df[col] <= cond.value
                elif op_value == OP_NOT_IN:
                    mask &= ~df[col].isin(cond.value)
                elif op_value == OP_BETWEEN:
                    min_val, max_val = cond.value
                    mask &= (df[col] >= min_val) & (df[col] <= max_val)
            except Exception as e:
                logger.warning(f"Could not estimate selectivity for {cond}: {e}")

        matching_rows = mask.sum()
        total_rows = len(df)

        if matching_rows == 0:
            logger.warning("No rows in source data match the conditions")
            return 10.0  # Maximum oversample

        selectivity = matching_rows / total_rows

        # Calculate oversample factor: we want 1/selectivity but capped
        oversample = min(10.0, max(1.5, 1.0 / selectivity * 1.2))

        logger.info(
            f"Estimated selectivity: {selectivity:.2%} "
            f"({matching_rows}/{total_rows} rows), "
            f"oversample factor: {oversample:.1f}"
        )

        return oversample
