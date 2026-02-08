"""Tests for ml_development domain - recipes, models, runs, and monitoring."""
import pytest
from datetime import datetime
from uuid import uuid4

from domains.ml_development.models import (
    ModelFamily, RecipeLevel, RecipeStatus, ModelStatus, RunType, RunStatus,
    MLRecipe, MLRecipeCreate, MLRecipeUpdate,
    MLRecipeVersion, MLRecipeVersionCreate,
    MLModel, MLModelCreate, MLModelUpdate,
    MLRun, MLRunCreate,
    MLMonitorSnapshot, MLMonitorSnapshotCreate,
    MLSyntheticExample, MLSyntheticExampleCreate,
    RecipeListResponse, ModelListResponse, RunListResponse,
    MLChatMessage, MLChatRequest, MLChatResponse
)


class TestMLEnums:
    """Test ML enum values."""

    def test_model_family(self):
        """Test model family enum values."""
        assert ModelFamily.PRICING.value == "pricing"
        assert ModelFamily.NEXT_BEST_ACTION.value == "next_best_action"
        assert ModelFamily.LOCATION_SCORING.value == "location_scoring"
        assert ModelFamily.FORECASTING.value == "forecasting"

    def test_recipe_level(self):
        """Test recipe level enum values."""
        assert RecipeLevel.BASELINE.value == "baseline"
        assert RecipeLevel.INDUSTRY.value == "industry"
        assert RecipeLevel.CLIENT.value == "client"

    def test_recipe_status(self):
        """Test recipe status enum values."""
        assert RecipeStatus.DRAFT.value == "draft"
        assert RecipeStatus.APPROVED.value == "approved"
        assert RecipeStatus.ARCHIVED.value == "archived"

    def test_model_status(self):
        """Test model status enum values."""
        assert ModelStatus.DRAFT.value == "draft"
        assert ModelStatus.STAGING.value == "staging"
        assert ModelStatus.PRODUCTION.value == "production"
        assert ModelStatus.RETIRED.value == "retired"

    def test_run_type(self):
        """Test run type enum values."""
        assert RunType.TRAIN.value == "train"
        assert RunType.EVAL.value == "eval"
        assert RunType.BACKTEST.value == "backtest"

    def test_run_status(self):
        """Test run status enum values."""
        assert RunStatus.QUEUED.value == "queued"
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.SUCCEEDED.value == "succeeded"
        assert RunStatus.FAILED.value == "failed"


class TestMLRecipeModels:
    """Test ML recipe models."""

    def test_recipe_create_minimal(self):
        """Test creating recipe with minimal fields."""
        recipe = MLRecipeCreate(
            name="Price Optimizer",
            model_family=ModelFamily.PRICING,
            level=RecipeLevel.BASELINE
        )
        assert recipe.name == "Price Optimizer"
        assert recipe.model_family == ModelFamily.PRICING
        assert recipe.tags == []

    def test_recipe_create_full(self):
        """Test creating recipe with all fields."""
        recipe = MLRecipeCreate(
            name="Retail Demand Forecasting",
            model_family=ModelFamily.FORECASTING,
            level=RecipeLevel.INDUSTRY,
            parent_id="recipe_baseline_001",
            tags=["retail", "demand", "time-series"],
            manifest={
                "features": ["date", "store_id", "product_id", "sales"],
                "target": "sales",
                "algorithm": "lightgbm"
            }
        )
        assert recipe.parent_id == "recipe_baseline_001"
        assert "retail" in recipe.tags
        assert recipe.manifest["algorithm"] == "lightgbm"

    def test_recipe_update(self):
        """Test recipe update model."""
        update = MLRecipeUpdate(
            name="Updated Recipe",
            status=RecipeStatus.APPROVED,
            tags=["production", "validated"]
        )
        assert update.status == RecipeStatus.APPROVED
        assert "production" in update.tags

    def test_ml_recipe_response(self):
        """Test ML recipe response model."""
        recipe = MLRecipe(
            id="recipe_abc123",
            name="Pricing Model",
            model_family=ModelFamily.PRICING,
            level=RecipeLevel.CLIENT,
            status=RecipeStatus.APPROVED,
            parent_id="recipe_industry_001",
            tags=["pricing", "retail"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert recipe.id == "recipe_abc123"
        assert recipe.status == RecipeStatus.APPROVED


class TestMLRecipeVersionModels:
    """Test ML recipe version models."""

    def test_recipe_version_create(self):
        """Test creating a recipe version."""
        version = MLRecipeVersionCreate(
            recipe_id="recipe_abc123",
            manifest_json={
                "features": ["price", "quantity", "discount"],
                "target": "revenue",
                "pipeline": ["preprocessing", "training", "evaluation"]
            },
            change_note="Added discount feature",
            created_by="user123"
        )
        assert version.recipe_id == "recipe_abc123"
        assert "discount" in version.manifest_json["features"]

    def test_recipe_version_response(self):
        """Test recipe version response model."""
        version = MLRecipeVersion(
            version_id="ver_xyz789",
            recipe_id="recipe_abc123",
            version_number="1.2.0",
            manifest_json={"features": [], "target": "sales"},
            diff_from_prev={"features": {"added": ["new_feature"]}},
            created_by="user123",
            created_at=datetime.utcnow(),
            change_note="Added new feature"
        )
        assert version.version_number == "1.2.0"
        assert version.diff_from_prev is not None


class TestMLModelModels:
    """Test ML model models."""

    def test_model_create(self):
        """Test creating an ML model."""
        model = MLModelCreate(
            name="Production Price Model v1",
            recipe_id="recipe_abc123",
            recipe_version_id="ver_xyz789",
            owner="data_team"
        )
        assert model.name == "Production Price Model v1"
        assert model.owner == "data_team"

    def test_model_update(self):
        """Test model update model."""
        update = MLModelUpdate(
            name="Updated Model Name",
            status=ModelStatus.PRODUCTION,
            owner="ml_ops"
        )
        assert update.status == ModelStatus.PRODUCTION

    def test_model_response(self):
        """Test ML model response model."""
        model = MLModel(
            id="model_prod123",
            name="Sales Forecasting Model",
            model_family=ModelFamily.FORECASTING,
            recipe_id="recipe_forecast_001",
            recipe_version_id="ver_001",
            status=ModelStatus.PRODUCTION,
            owner="forecasting_team",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        assert model.status == ModelStatus.PRODUCTION
        assert model.model_family == ModelFamily.FORECASTING


class TestMLRunModels:
    """Test ML run models."""

    def test_run_create(self):
        """Test creating an ML run."""
        run = MLRunCreate(
            recipe_id="recipe_abc123",
            recipe_version_id="ver_xyz789",
            run_type=RunType.TRAIN,
            model_id="model_prod123"
        )
        assert run.run_type == RunType.TRAIN
        assert run.model_id == "model_prod123"

    def test_run_response(self):
        """Test ML run response model."""
        run = MLRun(
            id="run_train_001",
            model_id="model_prod123",
            recipe_id="recipe_abc123",
            recipe_version_id="ver_xyz789",
            run_type=RunType.TRAIN,
            status=RunStatus.SUCCEEDED,
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            metrics_json={
                "accuracy": 0.95,
                "f1_score": 0.93,
                "auc_roc": 0.97
            },
            artifacts_json={
                "model_path": "s3://models/model_prod123.pkl",
                "feature_importance": "s3://models/importance.json"
            },
            logs_text="Training completed successfully."
        )
        assert run.status == RunStatus.SUCCEEDED
        assert run.metrics_json["accuracy"] == 0.95

    def test_run_response_failed(self):
        """Test failed run response."""
        run = MLRun(
            id="run_failed_001",
            recipe_id="recipe_abc123",
            recipe_version_id="ver_xyz789",
            run_type=RunType.EVAL,
            status=RunStatus.FAILED,
            logs_text="Error: Out of memory"
        )
        assert run.status == RunStatus.FAILED


class TestMLMonitoringModels:
    """Test ML monitoring models."""

    def test_monitor_snapshot_create(self):
        """Test creating a monitoring snapshot."""
        snapshot = MLMonitorSnapshotCreate(
            model_id="model_prod123",
            performance_metrics_json={
                "accuracy": 0.94,
                "latency_p95": 120
            },
            drift_metrics_json={
                "feature_drift": {"price": 0.05, "quantity": 0.02},
                "prediction_drift": 0.03
            },
            data_freshness_json={
                "last_data_update": "2024-01-15T10:00:00Z",
                "data_lag_hours": 2
            },
            alerts_json={
                "active_alerts": [],
                "resolved_alerts": ["high_latency_resolved"]
            }
        )
        assert snapshot.performance_metrics_json["accuracy"] == 0.94
        assert "price" in snapshot.drift_metrics_json["feature_drift"]

    def test_monitor_snapshot_response(self):
        """Test monitoring snapshot response model."""
        snapshot = MLMonitorSnapshot(
            id="snap_mon_001",
            model_id="model_prod123",
            captured_at=datetime.utcnow(),
            performance_metrics_json={"accuracy": 0.93},
            drift_metrics_json={"overall_drift": 0.08},
            data_freshness_json={"hours_since_update": 4},
            alerts_json={"active": ["drift_warning"]}
        )
        assert "drift_warning" in snapshot.alerts_json["active"]


class TestMLSyntheticExampleModels:
    """Test ML synthetic example models."""

    def test_synthetic_example_create(self):
        """Test creating a synthetic example."""
        example = MLSyntheticExampleCreate(
            recipe_id="recipe_abc123",
            dataset_schema_json={
                "columns": [
                    {"name": "price", "type": "float"},
                    {"name": "quantity", "type": "int"},
                    {"name": "category", "type": "string"}
                ]
            },
            sample_rows_json=[
                {"price": 10.99, "quantity": 5, "category": "electronics"},
                {"price": 25.00, "quantity": 2, "category": "clothing"}
            ],
            example_run_json={
                "metrics": {"accuracy": 0.92},
                "predictions": [10.5, 24.5]
            }
        )
        assert len(example.sample_rows_json) == 2
        assert example.dataset_schema_json["columns"][0]["name"] == "price"

    def test_synthetic_example_response(self):
        """Test synthetic example response model."""
        example = MLSyntheticExample(
            id="example_abc123",
            recipe_id="recipe_abc123",
            dataset_schema_json={"columns": []},
            sample_rows_json=[],
            example_run_json={},
            created_at=datetime.utcnow()
        )
        assert example.id == "example_abc123"


class TestListResponses:
    """Test list response models."""

    def test_recipe_list_response(self):
        """Test recipe list response."""
        response = RecipeListResponse(recipes=[], total=0)
        assert response.total == 0

    def test_model_list_response(self):
        """Test model list response."""
        response = ModelListResponse(models=[], total=0)
        assert response.total == 0

    def test_run_list_response(self):
        """Test run list response."""
        response = RunListResponse(runs=[], total=0)
        assert response.total == 0


class TestMLChatModels:
    """Test ML chat assistant models."""

    def test_chat_message(self):
        """Test chat message model."""
        message = MLChatMessage(
            role="user",
            content="How do I build a pricing model?",
            timestamp=datetime.utcnow()
        )
        assert message.role == "user"

    def test_chat_request(self):
        """Test chat request model."""
        request = MLChatRequest(
            message="What features should I use for demand forecasting?",
            provider="openai",
            model="gpt-4o",
            context={"industry": "retail"},
            recipe_id="recipe_forecast_001"
        )
        assert request.provider == "openai"
        assert request.recipe_id == "recipe_forecast_001"

    def test_chat_request_defaults(self):
        """Test chat request default values."""
        request = MLChatRequest(message="Help me build a model")
        assert request.provider == "openai"
        assert request.model == "gpt-4o"
        assert request.context is None

    def test_chat_response(self):
        """Test chat response model."""
        response = MLChatResponse(
            message="For demand forecasting, consider using...",
            suggested_changes={"add_features": ["seasonality", "promotions"]},
            timestamp=datetime.utcnow()
        )
        assert "demand forecasting" in response.message
        assert response.suggested_changes is not None


class TestRouterImports:
    """Test that router and services import correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.ml_development.router import router
        assert router is not None
        assert router.prefix == "/ml-development"

    def test_service_imports(self):
        """Verify services can be imported."""
        from domains.ml_development.service import (
            MLRecipeService, MLRecipeVersionService, MLModelService,
            MLRunService, MLMonitorService, MLSyntheticExampleService
        )
        assert MLRecipeService is not None
        assert MLRecipeVersionService is not None
        assert MLModelService is not None
        assert MLRunService is not None
        assert MLMonitorService is not None
        assert MLSyntheticExampleService is not None

    def test_state_machine_imports(self):
        """Verify state machine can be imported."""
        from domains.ml_development.state_machine import RunStateMachine, RunState, FailureType
        assert RunStateMachine is not None
        assert RunState is not None
        assert FailureType is not None

    def test_promotion_service_imports(self):
        """Verify promotion service can be imported."""
        from domains.ml_development.promotion_service import get_promotion_service
        assert get_promotion_service is not None


class TestRunStateMachine:
    """Test run state machine logic."""

    def test_valid_run_state_transitions(self):
        """Test valid run state transitions."""
        from domains.ml_development.state_machine import RunStateMachine, RunState

        sm = RunStateMachine.__new__(RunStateMachine)  # Create without DB init

        # Queued -> Scheduled
        assert sm.can_transition(RunState.QUEUED, RunState.SCHEDULED) is True

        # Scheduled -> Running
        assert sm.can_transition(RunState.SCHEDULED, RunState.RUNNING) is True

        # Running -> Succeeded
        assert sm.can_transition(RunState.RUNNING, RunState.SUCCEEDED) is True

        # Running -> Failed
        assert sm.can_transition(RunState.RUNNING, RunState.FAILED) is True

    def test_invalid_run_state_transitions(self):
        """Test invalid run state transitions."""
        from domains.ml_development.state_machine import RunStateMachine, RunState

        sm = RunStateMachine.__new__(RunStateMachine)

        # Cannot go from queued directly to running
        assert sm.can_transition(RunState.QUEUED, RunState.RUNNING) is False

        # Cannot go from succeeded back to running
        assert sm.can_transition(RunState.SUCCEEDED, RunState.RUNNING) is False

        # Failed is terminal
        assert sm.can_transition(RunState.FAILED, RunState.RUNNING) is False

    def test_failure_classification(self):
        """Test failure type classification."""
        from domains.ml_development.state_machine import RunStateMachine, FailureType

        sm = RunStateMachine.__new__(RunStateMachine)

        # Infrastructure errors
        assert sm.classify_failure("Connection refused") == FailureType.INFRA
        assert sm.classify_failure("Out of memory error") == FailureType.INFRA
        assert sm.classify_failure("CUDA error detected") == FailureType.INFRA

        # Timeout errors
        assert sm.classify_failure("Request timed out") == FailureType.TIMEOUT

        # Model errors (default)
        assert sm.classify_failure("Invalid model weights") == FailureType.MODEL

        # Unknown
        assert sm.classify_failure("") == FailureType.UNKNOWN
        assert sm.classify_failure(None) == FailureType.UNKNOWN

    def test_retry_logic(self):
        """Test retry decision logic."""
        from domains.ml_development.state_machine import RunStateMachine, FailureType

        sm = RunStateMachine.__new__(RunStateMachine)

        # Infra failures should retry if under max
        assert sm.should_retry(FailureType.INFRA, retry_count=0, max_retries=2) is True
        assert sm.should_retry(FailureType.INFRA, retry_count=1, max_retries=2) is True
        assert sm.should_retry(FailureType.INFRA, retry_count=2, max_retries=2) is False

        # Timeout should retry
        assert sm.should_retry(FailureType.TIMEOUT, retry_count=0, max_retries=2) is True

        # Model errors should not retry
        assert sm.should_retry(FailureType.MODEL, retry_count=0, max_retries=2) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
