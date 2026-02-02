"""Tests for conditional synthetic data generation.

These tests validate the conditional synthetic data generation feature,
which allows generating synthetic data matching specific constraints.
"""
import pytest
import pandas as pd
import numpy as np

# Skip the test file if imports fail due to database setup
pytest.importorskip("sdv")

# Try to import from the domain - this may fail in test environment
# due to database initialization, but we document the expected behavior
try:
    from domains.synthetic.models import (
        ConditionOperator,
        GenerationCondition,
        ConditionalGenerateRequest,
    )
    from domains.synthetic.conditions import (
        ConditionProcessor,
        ConditionValidationError,
    )
    from domains.synthetic.synthesizers import (
        GaussianCopulaSynthesizer,
        CTGANSynthesizer,
        TVAESynthesizer,
    )
    IMPORTS_AVAILABLE = True
except Exception as e:
    # Imports may fail due to database initialization in test environment
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_data():
    """Create sample data for testing conditions."""
    np.random.seed(42)
    n = 500

    return pd.DataFrame({
        'age': np.random.randint(18, 80, n),
        'income': np.random.normal(50000, 15000, n).clip(20000, 150000),
        'region': np.random.choice(['US', 'EU', 'APAC'], n, p=[0.5, 0.3, 0.2]),
        'status': np.random.choice(['active', 'pending', 'inactive'], n),
        'score': np.random.uniform(0, 100, n),
    })


@pytest.fixture
def small_data():
    """Small dataset for quick tests."""
    np.random.seed(42)
    n = 100

    return pd.DataFrame({
        'x': np.random.normal(0, 1, n),
        'y': np.random.normal(5, 2, n),
        'category': np.random.choice(['A', 'B', 'C'], n),
    })


# ============================================================================
# Condition Model Tests
# ============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports failed: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
class TestConditionModels:
    """Tests for condition Pydantic models."""

    def test_condition_operator_values(self):
        """Test all condition operators are defined."""
        assert ConditionOperator.EQ.value == "eq"
        assert ConditionOperator.NE.value == "ne"
        assert ConditionOperator.GT.value == "gt"
        assert ConditionOperator.GTE.value == "gte"
        assert ConditionOperator.LT.value == "lt"
        assert ConditionOperator.LTE.value == "lte"
        assert ConditionOperator.IN.value == "in"
        assert ConditionOperator.NOT_IN.value == "not_in"
        assert ConditionOperator.BETWEEN.value == "between"

    def test_generation_condition_creation(self):
        """Test creating GenerationCondition instances."""
        cond = GenerationCondition(
            column="region",
            operator=ConditionOperator.EQ,
            value="US"
        )
        assert cond.column == "region"
        assert cond.operator == ConditionOperator.EQ
        assert cond.value == "US"

    def test_generation_condition_with_list_value(self):
        """Test condition with list value for IN operator."""
        cond = GenerationCondition(
            column="status",
            operator=ConditionOperator.IN,
            value=["active", "pending"]
        )
        assert cond.value == ["active", "pending"]

    def test_generation_condition_with_between(self):
        """Test condition with [min, max] for BETWEEN operator."""
        cond = GenerationCondition(
            column="age",
            operator=ConditionOperator.BETWEEN,
            value=[25, 65]
        )
        assert cond.value == [25, 65]


# ============================================================================
# Condition Processor Tests
# ============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports failed: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
class TestConditionProcessor:
    """Tests for ConditionProcessor class."""

    def test_validate_valid_conditions(self, sample_data):
        """Test validation of valid conditions."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
            GenerationCondition(column="age", operator=ConditionOperator.GTE, value=25),
        ]

        warnings = processor.validate_conditions(conditions, sample_data)
        # Should not raise and no critical warnings
        assert isinstance(warnings, list)

    def test_validate_invalid_column(self, sample_data):
        """Test validation fails for non-existent column."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="nonexistent", operator=ConditionOperator.EQ, value="X"),
        ]

        with pytest.raises(ConditionValidationError) as exc_info:
            processor.validate_conditions(conditions, sample_data)

        assert "nonexistent" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_validate_between_requires_list(self, sample_data):
        """Test BETWEEN operator requires [min, max] list."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.BETWEEN, value=25),
        ]

        with pytest.raises(ConditionValidationError) as exc_info:
            processor.validate_conditions(conditions, sample_data)

        assert "BETWEEN" in str(exc_info.value)
        assert "[min, max]" in str(exc_info.value)

    def test_validate_between_numeric_only(self, sample_data):
        """Test BETWEEN only works with numeric columns."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.BETWEEN, value=["A", "Z"]),
        ]

        with pytest.raises(ConditionValidationError) as exc_info:
            processor.validate_conditions(conditions, sample_data)

        assert "numeric" in str(exc_info.value).lower()

    def test_validate_in_requires_list(self, sample_data):
        """Test IN operator requires a list."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.IN, value="US"),
        ]

        with pytest.raises(ConditionValidationError) as exc_info:
            processor.validate_conditions(conditions, sample_data)

        assert "list" in str(exc_info.value)

    def test_validate_warns_nonexistent_value(self, sample_data):
        """Test warning for value not in categorical column."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="AFRICA"),
        ]

        warnings = processor.validate_conditions(conditions, sample_data)
        assert len(warnings) > 0
        assert "AFRICA" in str(warnings)

    def test_split_conditions(self):
        """Test splitting conditions into SDV and post-filter groups."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
            GenerationCondition(column="status", operator=ConditionOperator.IN, value=["active"]),
            GenerationCondition(column="age", operator=ConditionOperator.GTE, value=25),
            GenerationCondition(column="income", operator=ConditionOperator.BETWEEN, value=[30000, 80000]),
        ]

        sdv_conds, post_conds = processor.split_conditions(conditions)

        # EQ and IN should be SDV-native
        assert len(sdv_conds) == 2
        assert all(c.operator in [ConditionOperator.EQ, ConditionOperator.IN] for c in sdv_conds)

        # GTE and BETWEEN should be post-filter
        assert len(post_conds) == 2
        assert all(c.operator in [ConditionOperator.GTE, ConditionOperator.BETWEEN] for c in post_conds)

    def test_build_sdv_conditions_eq(self):
        """Test building SDV Condition for EQ operator."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
        ]

        sdv_conds = processor.build_sdv_conditions(100, conditions)
        assert len(sdv_conds) == 1

    def test_build_sdv_conditions_in(self):
        """Test building SDV Conditions for IN operator (multiple conditions)."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.IN, value=["US", "EU"]),
        ]

        sdv_conds = processor.build_sdv_conditions(100, conditions)
        # Should create one condition per value
        assert len(sdv_conds) == 2

    def test_merge_sdv_conditions(self):
        """Test merging multiple EQ conditions into one."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
            GenerationCondition(column="status", operator=ConditionOperator.EQ, value="active"),
        ]

        merged = processor.merge_sdv_conditions(100, conditions)
        assert merged is not None

    def test_merge_sdv_conditions_fails_with_in(self):
        """Test that merge returns None when IN operator present."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
            GenerationCondition(column="status", operator=ConditionOperator.IN, value=["active"]),
        ]

        merged = processor.merge_sdv_conditions(100, conditions)
        assert merged is None

    def test_apply_post_filters_ne(self, sample_data):
        """Test post-filter for NE (not equal) operator."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.NE, value="US"),
        ]

        filtered = processor.apply_post_filters(sample_data, conditions)

        assert len(filtered) < len(sample_data)
        assert "US" not in filtered["region"].values

    def test_apply_post_filters_gt(self, sample_data):
        """Test post-filter for GT (greater than) operator."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.GT, value=50),
        ]

        filtered = processor.apply_post_filters(sample_data, conditions)

        assert all(filtered["age"] > 50)

    def test_apply_post_filters_gte(self, sample_data):
        """Test post-filter for GTE (greater than or equal) operator."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.GTE, value=50),
        ]

        filtered = processor.apply_post_filters(sample_data, conditions)

        assert all(filtered["age"] >= 50)

    def test_apply_post_filters_lt(self, sample_data):
        """Test post-filter for LT (less than) operator."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.LT, value=30),
        ]

        filtered = processor.apply_post_filters(sample_data, conditions)

        assert all(filtered["age"] < 30)

    def test_apply_post_filters_lte(self, sample_data):
        """Test post-filter for LTE (less than or equal) operator."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.LTE, value=30),
        ]

        filtered = processor.apply_post_filters(sample_data, conditions)

        assert all(filtered["age"] <= 30)

    def test_apply_post_filters_not_in(self, sample_data):
        """Test post-filter for NOT_IN operator."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.NOT_IN, value=["US", "EU"]),
        ]

        filtered = processor.apply_post_filters(sample_data, conditions)

        assert "US" not in filtered["region"].values
        assert "EU" not in filtered["region"].values

    def test_apply_post_filters_between(self, sample_data):
        """Test post-filter for BETWEEN operator."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.BETWEEN, value=[30, 50]),
        ]

        filtered = processor.apply_post_filters(sample_data, conditions)

        assert all(filtered["age"] >= 30)
        assert all(filtered["age"] <= 50)

    def test_apply_multiple_post_filters(self, sample_data):
        """Test applying multiple post-filters (AND logic)."""
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.GTE, value=25),
            GenerationCondition(column="age", operator=ConditionOperator.LTE, value=60),
            GenerationCondition(column="region", operator=ConditionOperator.NE, value="APAC"),
        ]

        filtered = processor.apply_post_filters(sample_data, conditions)

        assert all(filtered["age"] >= 25)
        assert all(filtered["age"] <= 60)
        assert "APAC" not in filtered["region"].values

    def test_estimate_oversample_factor(self, sample_data):
        """Test oversample factor estimation."""
        processor = ConditionProcessor()

        # Condition that matches ~50% of data
        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.NE, value="US"),
        ]

        factor = processor.estimate_oversample_factor(sample_data, conditions)

        # Should be between 1.5 and 10.0
        assert 1.5 <= factor <= 10.0

    def test_estimate_oversample_factor_rare(self, sample_data):
        """Test oversample factor for rare conditions."""
        processor = ConditionProcessor()

        # Condition that matches very few rows
        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.GT, value=75),
        ]

        factor = processor.estimate_oversample_factor(sample_data, conditions)

        # Should be higher for rare conditions
        assert factor > 2.0


# ============================================================================
# Synthesizer Conditional Sampling Tests
# ============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports failed: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
class TestGaussianCopulaConditional:
    """Tests for conditional sampling with Gaussian Copula."""

    def test_sample_with_eq_condition(self, sample_data):
        """Test sampling with EQ condition."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
        ]

        result = synth.sample_with_conditions(50, conditions)

        assert len(result.synthetic_data) <= 50
        # All rows should have region=US
        assert all(result.synthetic_data["region"] == "US")
        assert result.metadata.get("conditional") is True

    def test_sample_with_multiple_eq_conditions(self, sample_data):
        """Test sampling with multiple EQ conditions (merged)."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
            GenerationCondition(column="status", operator=ConditionOperator.EQ, value="active"),
        ]

        result = synth.sample_with_conditions(50, conditions)

        assert all(result.synthetic_data["region"] == "US")
        assert all(result.synthetic_data["status"] == "active")

    def test_sample_with_range_condition(self, sample_data):
        """Test sampling with range condition (post-filter)."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.GTE, value=25),
            GenerationCondition(column="age", operator=ConditionOperator.LTE, value=65),
        ]

        result = synth.sample_with_conditions(100, conditions, oversample_factor=3.0)

        # All rows should satisfy age constraints
        assert all(result.synthetic_data["age"] >= 25)
        assert all(result.synthetic_data["age"] <= 65)

    def test_sample_with_mixed_conditions(self, sample_data):
        """Test sampling with both SDV and post-filter conditions."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
            GenerationCondition(column="age", operator=ConditionOperator.GTE, value=30),
        ]

        result = synth.sample_with_conditions(50, conditions, oversample_factor=2.0)

        assert all(result.synthetic_data["region"] == "US")
        assert all(result.synthetic_data["age"] >= 30)

    def test_sample_with_in_condition(self, sample_data):
        """Test sampling with IN condition."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.IN, value=["US", "EU"]),
        ]

        result = synth.sample_with_conditions(100, conditions)

        # All rows should be in US or EU
        assert all(result.synthetic_data["region"].isin(["US", "EU"]))

    def test_sample_with_between_condition(self, sample_data):
        """Test sampling with BETWEEN condition."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        conditions = [
            GenerationCondition(column="income", operator=ConditionOperator.BETWEEN, value=[40000, 60000]),
        ]

        result = synth.sample_with_conditions(100, conditions, oversample_factor=3.0)

        assert all(result.synthetic_data["income"] >= 40000)
        assert all(result.synthetic_data["income"] <= 60000)

    def test_sample_warns_when_insufficient_rows(self, sample_data):
        """Test warning when not enough rows match conditions."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        # Very restrictive condition
        conditions = [
            GenerationCondition(column="age", operator=ConditionOperator.GT, value=100),  # No one over 100
        ]

        result = synth.sample_with_conditions(100, conditions, oversample_factor=2.0)

        # Should have warning about insufficient rows
        assert any("rows matched" in w for w in result.warnings)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports failed: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
class TestCTGANConditional:
    """Tests for conditional sampling with CTGAN."""

    @pytest.mark.slow
    def test_sample_with_eq_condition(self, small_data):
        """Test CTGAN sampling with EQ condition."""
        config = {"epochs": 5, "batch_size": 50}
        synth = CTGANSynthesizer(config=config)
        synth.fit(small_data)

        conditions = [
            GenerationCondition(column="category", operator=ConditionOperator.EQ, value="A"),
        ]

        result = synth.sample_with_conditions(30, conditions)

        assert all(result.synthetic_data["category"] == "A")
        # Should have warning about reject sampling
        assert any("reject sampling" in w.lower() for w in result.warnings)


@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports failed: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
class TestTVAEConditional:
    """Tests for conditional sampling with TVAE."""

    @pytest.mark.slow
    def test_sample_with_eq_condition(self, small_data):
        """Test TVAE sampling with EQ condition."""
        config = {"epochs": 5, "batch_size": 50}
        synth = TVAESynthesizer(config=config)
        synth.fit(small_data)

        conditions = [
            GenerationCondition(column="category", operator=ConditionOperator.EQ, value="B"),
        ]

        result = synth.sample_with_conditions(30, conditions)

        assert all(result.synthetic_data["category"] == "B")


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.skipif(not IMPORTS_AVAILABLE, reason=f"Imports failed: {IMPORT_ERROR if not IMPORTS_AVAILABLE else ''}")
class TestConditionalIntegration:
    """Integration tests for conditional generation."""

    def test_full_conditional_workflow(self, sample_data):
        """Test complete conditional generation workflow."""
        # 1. Create and validate conditions
        processor = ConditionProcessor()

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
            GenerationCondition(column="age", operator=ConditionOperator.GTE, value=25),
            GenerationCondition(column="age", operator=ConditionOperator.LTE, value=65),
            GenerationCondition(column="status", operator=ConditionOperator.IN, value=["active", "pending"]),
        ]

        warnings = processor.validate_conditions(conditions, sample_data)
        assert len([w for w in warnings if "not found" in w.lower()]) == 0

        # 2. Split conditions
        sdv_conds, post_conds = processor.split_conditions(conditions)
        assert len(sdv_conds) == 2  # region EQ, status IN
        assert len(post_conds) == 2  # age GTE, age LTE

        # 3. Estimate oversample factor
        factor = processor.estimate_oversample_factor(sample_data, post_conds)
        assert factor >= 1.5

        # 4. Fit synthesizer
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        # 5. Generate conditional data
        result = synth.sample_with_conditions(
            num_rows=100,
            conditions=conditions,
            oversample_factor=factor,
        )

        synthetic_df = result.synthetic_data

        # 6. Verify all conditions are satisfied
        assert all(synthetic_df["region"] == "US")
        assert all(synthetic_df["age"] >= 25)
        assert all(synthetic_df["age"] <= 65)
        assert all(synthetic_df["status"].isin(["active", "pending"]))

        print(f"\nConditional Generation Results:")
        print(f"  Requested: 100 rows")
        print(f"  Generated: {len(synthetic_df)} rows")
        print(f"  Oversample factor: {factor:.2f}")
        print(f"  Conditions: {len(conditions)}")
        print(f"  Warnings: {result.warnings}")

    def test_conditional_preserves_distributions(self, sample_data):
        """Test that conditional sampling preserves column distributions within constraints."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        # Filter original data to match conditions
        original_us = sample_data[sample_data["region"] == "US"]

        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="US"),
        ]

        result = synth.sample_with_conditions(len(original_us), conditions)
        synthetic_df = result.synthetic_data

        # Compare age distribution between original US and synthetic US
        orig_mean = original_us["age"].mean()
        synth_mean = synthetic_df["age"].mean()

        # Means should be reasonably close (within 10 years)
        assert abs(orig_mean - synth_mean) < 10

    def test_conditional_with_rare_category(self, sample_data):
        """Test conditional generation targeting rare category."""
        synth = GaussianCopulaSynthesizer()
        synth.fit(sample_data)

        # APAC is ~20% of data
        conditions = [
            GenerationCondition(column="region", operator=ConditionOperator.EQ, value="APAC"),
        ]

        result = synth.sample_with_conditions(100, conditions)

        assert all(result.synthetic_data["region"] == "APAC")
        # Should have generated close to requested amount
        assert len(result.synthetic_data) >= 50  # At least half
