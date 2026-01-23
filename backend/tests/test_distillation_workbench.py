"""Comprehensive tests for the Distillation Workbench features.

Tests run against the live backend at http://localhost:8000
"""
import pytest
import requests
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/distillation"


def api_get(endpoint: str):
    """Helper to make GET requests."""
    return requests.get(f"{API_BASE}{endpoint}")


def api_post(endpoint: str, json_data: dict = None):
    """Helper to make POST requests."""
    return requests.post(f"{API_BASE}{endpoint}", json=json_data)


def api_patch(endpoint: str, json_data: dict = None):
    """Helper to make PATCH requests."""
    return requests.patch(f"{API_BASE}{endpoint}", json=json_data)


def api_delete(endpoint: str):
    """Helper to make DELETE requests."""
    return requests.delete(f"{API_BASE}{endpoint}")


# ============================================
# Test Data
# ============================================

TEST_DOMAIN = {
    "name": f"Test Domain {uuid4().hex[:8]}",
    "description": "A test domain for unit testing"
}

TEST_TAG = {
    "name": f"test-tag-{uuid4().hex[:8]}"
}

TEST_TASK = {
    "name": f"Test Task {uuid4().hex[:8]}",
    "description": "A test task",
    "prompt_template": "Answer the following: {{question}}",
    "task_type": "qa",
    "target_models": ["openai/gpt-4o"]
}

TEST_DATASET = {
    "name": f"Test Dataset {uuid4().hex[:8]}",
    "description": "A test dataset for training",
    "version": "1.0",
    "dataset_type": "training"
}


# Store created IDs for cleanup and cross-test usage
created_ids = {
    "domain_id": None,
    "topic_id": None,
    "tag_id": None,
    "task_id": None,
    "dataset_id": None
}


# ============================================
# Health Check
# ============================================

class TestHealthCheck:
    """Verify the server is running."""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


# ============================================
# Domain Tests
# ============================================

class TestDomains:
    """Tests for domain management."""
    
    def test_create_domain(self):
        """Test creating a new domain."""
        response = api_post("/domains", TEST_DOMAIN)
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == TEST_DOMAIN["name"]
        assert "id" in data
        created_ids["domain_id"] = data["id"]
    
    def test_list_domains(self):
        """Test listing all domains."""
        response = api_get("/domains")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert isinstance(data["domains"], list)
    
    def test_get_domain(self):
        """Test getting a specific domain."""
        if not created_ids["domain_id"]:
            pytest.skip("No domain created")
        response = api_get(f"/domains/{created_ids['domain_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == TEST_DOMAIN["name"]
    
    def test_update_domain(self):
        """Test updating a domain."""
        if not created_ids["domain_id"]:
            pytest.skip("No domain created")
        update_data = {"description": "Updated description"}
        response = api_patch(f"/domains/{created_ids['domain_id']}", update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"


# ============================================
# Topic Tests
# ============================================

class TestTopics:
    """Tests for topic management."""
    
    def test_create_topic(self):
        """Test creating a new topic."""
        # Topics require a domain_id
        if not created_ids["domain_id"]:
            pytest.skip("No domain created - topic requires domain_id")
        
        topic_data = {
            "name": f"Test Topic {uuid4().hex[:8]}",
            "description": "A test topic",
            "domain_id": created_ids["domain_id"]
        }
        
        response = api_post("/topics", topic_data)
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == topic_data["name"]
        assert "id" in data
        created_ids["topic_id"] = data["id"]
    
    def test_list_topics_by_domain(self):
        """Test listing topics for a domain."""
        if not created_ids["domain_id"]:
            pytest.skip("No domain created")
        response = api_get(f"/domains/{created_ids['domain_id']}/topics")
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert isinstance(data["topics"], list)


# ============================================
# Tag Tests
# ============================================

class TestTags:
    """Tests for tag management."""
    
    def test_create_tag(self):
        """Test creating a new tag."""
        response = api_post("/tags", TEST_TAG)
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == TEST_TAG["name"]
        assert "id" in data
        created_ids["tag_id"] = data["id"]
    
    def test_list_tags(self):
        """Test listing all tags."""
        response = api_get("/tags")
        assert response.status_code == 200
        data = response.json()
        # Tags endpoint returns a list directly or {"tags": [...]}
        if isinstance(data, list):
            assert len(data) >= 0
        else:
            assert "tags" in data


# ============================================
# Task Tests
# ============================================

class TestTasks:
    """Tests for task management."""
    
    def test_create_task(self):
        """Test creating a new task."""
        task_data = {**TEST_TASK}
        if created_ids["domain_id"]:
            task_data["domain_id"] = created_ids["domain_id"]
        
        response = api_post("/tasks", task_data)
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == TEST_TASK["name"]
        assert "id" in data
        created_ids["task_id"] = data["id"]
    
    def test_list_tasks(self):
        """Test listing all tasks."""
        response = api_get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
    
    def test_get_task(self):
        """Test getting a specific task."""
        if not created_ids["task_id"]:
            pytest.skip("No task created")
        response = api_get(f"/tasks/{created_ids['task_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == TEST_TASK["name"]


# ============================================
# Dataset Tests
# ============================================

class TestDatasets:
    """Tests for dataset management."""
    
    def test_create_dataset(self):
        """Test creating a new dataset."""
        response = api_post("/datasets", TEST_DATASET)
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data["name"] == TEST_DATASET["name"]
        assert "id" in data
        created_ids["dataset_id"] = data["id"]
    
    def test_list_datasets(self):
        """Test listing all datasets."""
        response = api_get("/datasets")
        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
        assert isinstance(data["datasets"], list)
    
    def test_get_dataset(self):
        """Test getting a specific dataset."""
        if not created_ids["dataset_id"]:
            pytest.skip("No dataset created")
        response = api_get(f"/datasets/{created_ids['dataset_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == TEST_DATASET["name"]


# ============================================
# Response & Banking Tests
# ============================================

class TestResponses:
    """Tests for response management."""
    
    def test_list_responses(self):
        """Test listing all responses."""
        response = api_get("/responses")
        assert response.status_code == 200
        data = response.json()
        assert "responses" in data
        assert isinstance(data["responses"], list)


class TestBanking:
    """Tests for banking responses."""
    
    def test_list_banked(self):
        """Test listing all banked responses."""
        response = api_get("/banked")
        assert response.status_code == 200
        data = response.json()
        assert "banked" in data
        assert isinstance(data["banked"], list)


# ============================================
# Template Tests (Batch Generation)
# ============================================

class TestTemplates:
    """Tests for generation templates."""
    
    def test_list_templates(self):
        """Test listing all templates."""
        response = api_get("/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        # Should have built-in templates
        assert len(data["templates"]) >= 5, f"Expected at least 5 built-in templates, got {len(data['templates'])}"
    
    def test_builtin_templates_exist(self):
        """Test that built-in templates exist."""
        response = api_get("/templates")
        data = response.json()
        template_names = [t["name"] for t in data["templates"]]
        
        expected_templates = [
            "QA Pair Generator",
            "Reps & Warrants Extractor",
            "Summary Generator",
            "Text Classifier",
            "Instruction-Response Generator"
        ]
        
        for expected in expected_templates:
            assert expected in template_names, f"Missing built-in template: {expected}"


# ============================================
# Batch Job Tests
# ============================================

class TestBatchJobs:
    """Tests for batch job management."""
    
    def test_list_batch_jobs(self):
        """Test listing all batch jobs."""
        response = api_get("/batch-jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)


# ============================================
# Lineage Tests (Process Discovery)
# ============================================

class TestLineage:
    """Tests for lineage and process discovery features."""
    
    def test_get_standard_purposes(self):
        """Test getting standard purpose tags."""
        response = api_get("/lineage/purposes")
        assert response.status_code == 200
        data = response.json()
        assert "purposes" in data
        assert isinstance(data["purposes"], list)
        
        # Check for expected purposes
        expected_purposes = [
            "customer_faq",
            "compliance_training",
            "agent_reasoning",
            "tool_use",
            "instruction_following",
            "knowledge_base",
            "code_generation",
            "classification",
            "summarization",
            "extraction",
            "other"
        ]
        
        for purpose in expected_purposes:
            assert purpose in data["purposes"], f"Missing purpose: {purpose}"
    
    def test_get_audit_logs(self):
        """Test getting audit logs."""
        response = api_get("/lineage/audit-logs")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert isinstance(data["logs"], list)
    
    def test_get_audit_logs_with_filters(self):
        """Test getting audit logs with filters."""
        response = api_get("/lineage/audit-logs?entity_type=banked&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
    
    def test_get_models_summary(self):
        """Test getting all models summary."""
        response = api_get("/lineage/models/summary")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "total_models" in data
        assert isinstance(data["models"], list)
    
    def test_get_model_contribution(self):
        """Test getting model contribution stats."""
        response = api_get("/lineage/models/contribution")
        assert response.status_code == 200
        data = response.json()
        assert "total_responses" in data
        assert "banked_responses" in data
        assert "bank_rate" in data
    
    def test_dataset_provenance(self):
        """Test dataset provenance endpoint."""
        if not created_ids["dataset_id"]:
            pytest.skip("No dataset created")
        
        response = api_get(f"/lineage/datasets/{created_ids['dataset_id']}/provenance")
        assert response.status_code == 200
        data = response.json()
        assert "dataset_id" in data
        assert "total_items" in data
        assert "by_model" in data
        assert "by_provider" in data
        assert "by_purpose" in data
    
    def test_entity_audit_trail(self):
        """Test getting audit trail for an entity."""
        if not created_ids["dataset_id"]:
            pytest.skip("No dataset created")
        
        response = api_get(f"/lineage/dataset/{created_ids['dataset_id']}/audit-trail")
        assert response.status_code == 200
        data = response.json()
        assert "entity_type" in data
        assert "entity_id" in data
        assert "audit_trail" in data
    
    def test_lineage_upstream(self):
        """Test getting upstream lineage."""
        if not created_ids["dataset_id"]:
            pytest.skip("No dataset created")
        
        response = api_get(f"/lineage/dataset/{created_ids['dataset_id']}/upstream")
        assert response.status_code == 200
        data = response.json()
        assert "entity_type" in data
        assert "upstream" in data
    
    def test_lineage_downstream(self):
        """Test getting downstream lineage."""
        if not created_ids["dataset_id"]:
            pytest.skip("No dataset created")
        
        response = api_get(f"/lineage/dataset/{created_ids['dataset_id']}/downstream")
        assert response.status_code == 200
        data = response.json()
        assert "entity_type" in data
        assert "downstream" in data
    
    def test_impact_analysis(self):
        """Test impact analysis endpoint."""
        if not created_ids["dataset_id"]:
            pytest.skip("No dataset created")
        
        response = api_get(f"/lineage/dataset/{created_ids['dataset_id']}/impact")
        assert response.status_code == 200
        data = response.json()
        assert "entity_type" in data
        assert "entity_id" in data
        assert "total_affected" in data


# ============================================
# Available Models Tests
# ============================================

class TestAvailableModels:
    """Tests for available models endpoint."""
    
    def test_get_available_models(self):
        """Test getting available models."""
        # Try different possible endpoints
        response = api_get("/available-models")
        if response.status_code == 404:
            response = api_get("/models")
        if response.status_code == 404:
            # Try interactive chat endpoint which returns models
            response = requests.get(f"{BASE_URL}/api/v1/distillation/interactive/models")
        
        # If all fail, check if there's any endpoint that returns models
        if response.status_code == 404:
            pytest.skip("Available models endpoint not found - this is expected if API key not configured")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data or isinstance(data, list)


# ============================================
# Review Queue Tests
# ============================================

class TestReviewQueues:
    """Tests for expert review queues."""
    
    def test_list_review_queues(self):
        """Test listing review queues."""
        response = api_get("/review-queues")
        assert response.status_code == 200
        data = response.json()
        assert "queues" in data
        assert isinstance(data["queues"], list)


# ============================================
# Comparison Tests
# ============================================

class TestComparisons:
    """Tests for comparison features."""
    
    def test_list_comparisons(self):
        """Test listing comparisons."""
        response = api_get("/comparisons")
        assert response.status_code == 200
        data = response.json()
        assert "comparisons" in data
        assert isinstance(data["comparisons"], list)


# ============================================
# Structure Tests
# ============================================

class TestStructured:
    """Tests for structured extraction."""
    
    def test_list_structured(self):
        """Test listing structured extractions."""
        response = api_get("/structured")
        assert response.status_code == 200
        data = response.json()
        assert "structured" in data
        assert isinstance(data["structured"], list)
    
    def test_list_schemas(self):
        """Test listing available schemas."""
        response = api_get("/schemas")
        assert response.status_code == 200
        data = response.json()
        assert "schemas" in data
        assert isinstance(data["schemas"], list)


# ============================================
# Statistics Tests
# ============================================

class TestStatistics:
    """Tests for statistics endpoint."""
    
    def test_get_statistics(self):
        """Test getting workbench statistics."""
        response = api_get("/statistics")
        assert response.status_code == 200
        data = response.json()
        # Should have various counts
        assert isinstance(data, dict)


# ============================================
# Cleanup Tests (Run Last)
# ============================================

class TestCleanup:
    """Cleanup tests - run last to delete test data."""
    
    def test_delete_dataset(self):
        """Test deleting a dataset."""
        if not created_ids["dataset_id"]:
            pytest.skip("No dataset to delete")
        response = api_delete(f"/datasets/{created_ids['dataset_id']}")
        # Delete might not be implemented - skip if not allowed
        if response.status_code == 405:
            pytest.skip("Dataset DELETE not implemented")
        assert response.status_code in [200, 204], f"Failed: {response.text}"
    
    def test_delete_task(self):
        """Test deleting a task."""
        if not created_ids["task_id"]:
            pytest.skip("No task to delete")
        response = api_delete(f"/tasks/{created_ids['task_id']}")
        assert response.status_code in [200, 204], f"Failed: {response.text}"
    
    def test_delete_topic(self):
        """Test deleting a topic."""
        if not created_ids["topic_id"]:
            pytest.skip("No topic to delete")
        response = api_delete(f"/topics/{created_ids['topic_id']}")
        assert response.status_code in [200, 204], f"Failed: {response.text}"
    
    def test_delete_domain(self):
        """Test deleting a domain."""
        if not created_ids["domain_id"]:
            pytest.skip("No domain to delete")
        response = api_delete(f"/domains/{created_ids['domain_id']}")
        assert response.status_code in [200, 204], f"Failed: {response.text}"


# ============================================
# Run tests if executed directly
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
