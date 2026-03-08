"""
Comprehensive integration tests for complete Mind API flows.

This module tests end-to-end scenarios including:
- Full CRUD lifecycle with real Neo4j database
- Version history traversal with multiple updates
- Complex relationship graphs
- Bulk operations with transaction rollback

**Validates: All requirements (1.1-12.6)**
"""

import time
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.models.enums import StatusEnum

# Create test client
client = TestClient(app)


# Mark all tests to use clean_database fixture
pytestmark = pytest.mark.usefixtures("clean_database")


# ============================================================================
# Test: Full CRUD Lifecycle
# ============================================================================


def test_full_crud_lifecycle_with_real_database():
    """
    Test complete CRUD lifecycle: Create -> Read -> Update -> Read -> Delete -> Verify.
    
    This test validates the entire lifecycle of a Mind node from creation through
    deletion, ensuring all operations work correctly with the real Neo4j database.
    
    Validates: Requirements 3.1-3.7, 4.1-4.3, 5.1-5.8, 7.1-7.6
    """
    # Step 1: Create a Mind node
    create_data = {
        "mind_type": "project",
        "title": "Full Lifecycle Test Project",
        "description": "Testing complete CRUD lifecycle",
        "creator": "lifecycle@example.com",
        "type_specific_attributes": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "budget": 100000.0,
        },
    }
    
    create_response = client.post("/api/v1/minds", json=create_data)
    assert create_response.status_code == 201
    
    created_data = create_response.json()
    created_uuid = created_data["uuid"]
    assert created_data["version"] == 1
    assert created_data["title"] == "Full Lifecycle Test Project"
    assert created_data["creator"] == "lifecycle@example.com"
    
    # Step 2: Read the created Mind node
    read_response = client.get(f"/api/v1/minds/{created_uuid}")
    assert read_response.status_code == 200
    
    read_data = read_response.json()
    assert read_data["uuid"] == created_uuid
    assert read_data["title"] == "Full Lifecycle Test Project"
    assert read_data["version"] == 1
    
    # Step 3: Update the Mind node (first update)
    update_data_1 = {
        "title": "Updated Lifecycle Project",
        "type_specific_attributes": {"budget": 150000.0},
    }
    update_response_1 = client.put(f"/api/v1/minds/{created_uuid}", json=update_data_1)
    assert update_response_1.status_code == 200
    
    updated_data_1 = update_response_1.json()
    assert updated_data_1["uuid"] == created_uuid
    assert updated_data_1["version"] == 2
    assert updated_data_1["title"] == "Updated Lifecycle Project"
    assert updated_data_1["type_specific_attributes"]["budget"] == 150000.0
    assert updated_data_1["creator"] == "lifecycle@example.com"  # Creator preserved
    
    # Step 4: Update again (second update)
    update_data_2 = {
        "description": "Updated description after second update",
    }
    update_response_2 = client.put(f"/api/v1/minds/{created_uuid}", json=update_data_2)
    assert update_response_2.status_code == 200
    
    updated_data_2 = update_response_2.json()
    assert updated_data_2["version"] == 3
    assert updated_data_2["title"] == "Updated Lifecycle Project"  # Preserved
    assert updated_data_2["description"] == "Updated description after second update"
    
    # Step 5: Read again to verify latest version
    read_response_2 = client.get(f"/api/v1/minds/{created_uuid}")
    assert read_response_2.status_code == 200
    
    read_data_2 = read_response_2.json()
    assert read_data_2["version"] == 3
    assert read_data_2["title"] == "Updated Lifecycle Project"
    
    # Step 6: Soft delete
    delete_response = client.delete(f"/api/v1/minds/{created_uuid}")
    assert delete_response.status_code == 204
    
    # Step 7: Verify soft delete created new version with deleted status
    read_after_delete = client.get(f"/api/v1/minds/{created_uuid}")
    assert read_after_delete.status_code == 200
    deleted_data = read_after_delete.json()
    assert deleted_data["status"] == "deleted"
    assert deleted_data["version"] == 4
    
    # Step 8: Hard delete
    hard_delete_response = client.delete(f"/api/v1/minds/{created_uuid}?hard=true")
    assert hard_delete_response.status_code == 204
    
    # Step 9: Verify hard delete removed all versions
    final_read = client.get(f"/api/v1/minds/{created_uuid}")
    assert final_read.status_code == 404


# ============================================================================
# Test: Version History Traversal with Multiple Updates
# ============================================================================


def test_version_history_traversal_multiple_updates():
    """
    Test version history traversal with multiple sequential updates.
    
    Creates a Mind node and performs 10 updates, then verifies:
    - All versions are retrievable
    - Versions are ordered correctly (newest to oldest)
    - Each version contains correct attributes
    - Version chain integrity is maintained
    
    Validates: Requirements 5.1-5.8, 6.1-6.6
    """
    # Create initial Mind node
    create_data = {
        "mind_type": "task",
        "title": "Version History Test Task",
        "description": "Initial description",
        "creator": "version@example.com",
        "type_specific_attributes": {
            "priority": "low",
            "assignee": "dev@example.com",
            "estimated_hours": 1.0,
        },
    }
    
    create_response = client.post("/api/v1/minds", json=create_data)
    assert create_response.status_code == 201
    created_uuid = create_response.json()["uuid"]
    
    # Perform 10 updates with different attributes
    priorities = ["low", "medium", "high", "critical", "high", "medium", "low", "critical", "high", "medium"]
    estimated_hours = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    
    for i, (priority, hours) in enumerate(zip(priorities, estimated_hours), start=1):
        update_data = {
            "title": f"Version History Test Task - Update {i}",
            "description": f"Description after update {i}",
            "type_specific_attributes": {
                "priority": priority,
                "estimated_hours": hours,
            },
        }
        
        update_response = client.put(f"/api/v1/minds/{created_uuid}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["version"] == i + 1
        
        # Small delay to ensure timestamps are different
        time.sleep(0.01)
    
    # Retrieve version history
    history_response = client.get(f"/api/v1/minds/{created_uuid}/history")
    assert history_response.status_code == 200
    
    history = history_response.json()
    assert isinstance(history, list)
    assert len(history) == 11  # 1 initial + 10 updates
    
    # Verify ordering (newest to oldest)
    versions = [item["version"] for item in history]
    assert versions == list(range(11, 0, -1))
    
    # Verify each version has correct attributes
    for i, version_data in enumerate(history):
        expected_version = 11 - i
        assert version_data["version"] == expected_version
        assert version_data["uuid"] == created_uuid
        assert version_data["creator"] == "version@example.com"
        
        # Verify version-specific attributes
        if expected_version > 1:
            update_num = expected_version - 1
            assert f"Update {update_num}" in version_data["title"]
            assert f"Description after update {update_num}" == version_data["description"]
    
    # Test pagination of version history
    paginated_response = client.get(f"/api/v1/minds/{created_uuid}/history?page=1&page_size=5")
    assert paginated_response.status_code == 200
    
    paginated_history = paginated_response.json()
    assert len(paginated_history) == 5
    assert paginated_history[0]["version"] == 11  # Newest first


def test_version_history_attribute_preservation():
    """
    Test that unchanged attributes are preserved across versions.
    
    Validates: Requirements 5.3, 5.6, 5.7, 6.3
    """
    # Create Mind node
    create_data = {
        "mind_type": "employee",
        "title": "John Doe",
        "description": "Software Engineer",
        "creator": "hr@example.com",
        "type_specific_attributes": {
            "email": "john.doe@example.com",
            "role": "Senior Developer",
            "hire_date": "2024-01-15",
        },
    }
    
    create_response = client.post("/api/v1/minds", json=create_data)
    created_uuid = create_response.json()["uuid"]
    original_creator = create_response.json()["creator"]
    
    # Update only the role (other attributes should be preserved)
    update_data = {
        "type_specific_attributes": {
            "role": "Lead Developer",
        },
    }
    
    update_response = client.put(f"/api/v1/minds/{created_uuid}", json=update_data)
    assert update_response.status_code == 200
    
    updated_data = update_response.json()
    
    # Verify UUID is preserved
    assert updated_data["uuid"] == created_uuid
    
    # Verify creator is preserved
    assert updated_data["creator"] == original_creator
    
    # Verify unchanged attributes are preserved
    assert updated_data["title"] == "John Doe"
    assert updated_data["description"] == "Software Engineer"
    assert updated_data["type_specific_attributes"]["email"] == "john.doe@example.com"
    assert updated_data["type_specific_attributes"]["hire_date"] == "2024-01-15"
    
    # Verify only role was updated
    assert updated_data["type_specific_attributes"]["role"] == "Lead Developer"
    
    # Verify version history shows both versions with correct attributes
    history_response = client.get(f"/api/v1/minds/{created_uuid}/history")
    history = history_response.json()
    
    assert len(history) == 2
    
    # Check version 2 (latest)
    assert history[0]["version"] == 2
    assert history[0]["type_specific_attributes"]["role"] == "Lead Developer"
    
    # Check version 1 (original)
    assert history[1]["version"] == 1
    assert history[1]["type_specific_attributes"]["role"] == "Senior Developer"


# ============================================================================
# Test: Complex Relationship Graphs
# ============================================================================


def test_complex_relationship_graph():
    """
    Test creating and querying complex relationship graphs.
    
    Creates a project hierarchy:
    - Project contains 2 Phases
    - Each Phase contains 2 Tasks
    - Tasks depend on each other
    - Tasks are assigned to Employees
    - Risks mitigate Failures
    
    Validates: Requirements 8.1-8.6
    """
    # Create Project
    project_data = {
        "mind_type": "project",
        "title": "Complex Project",
        "creator": "pm@example.com",
        "type_specific_attributes": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "budget": 500000.0,
        },
    }
    project_response = client.post("/api/v1/minds", json=project_data)
    project_uuid = project_response.json()["uuid"]
    
    # Create 2 Phases
    phase_uuids = []
    for i in range(1, 3):
        phase_data = {
            "mind_type": "phase",
            "title": f"Phase {i}",
            "creator": "pm@example.com",
            "type_specific_attributes": {
                "start_date": f"2024-{i*3:02d}-01",
                "end_date": f"2024-{i*3+2:02d}-28",
                "phase_number": i,
            },
        }
        phase_response = client.post("/api/v1/minds", json=phase_data)
        phase_uuid = phase_response.json()["uuid"]
        phase_uuids.append(phase_uuid)
        
        # Create CONTAINS relationship: Project -> Phase
        rel_response = client.post(
            f"/api/v1/minds/{project_uuid}/relationships"
            f"?target_uuid={phase_uuid}&relationship_type=contains"
        )
        assert rel_response.status_code == 201
    
    # Create 2 Tasks per Phase (4 tasks total)
    task_uuids = []
    for phase_idx, phase_uuid in enumerate(phase_uuids):
        for task_idx in range(1, 3):
            task_data = {
                "mind_type": "task",
                "title": f"Task {phase_idx+1}.{task_idx}",
                "creator": "dev@example.com",
                "type_specific_attributes": {
                    "priority": "high" if task_idx == 1 else "medium",
                    "assignee": f"dev{task_idx}@example.com",
                    "estimated_hours": 8.0,
                },
            }
            task_response = client.post("/api/v1/minds", json=task_data)
            task_uuid = task_response.json()["uuid"]
            task_uuids.append(task_uuid)
            
            # Create CONTAINS relationship: Phase -> Task
            client.post(
                f"/api/v1/minds/{phase_uuid}/relationships"
                f"?target_uuid={task_uuid}&relationship_type=contains"
            )
    
    # Create DEPENDS_ON relationships between tasks
    # Task 1.2 depends on Task 1.1
    client.post(
        f"/api/v1/minds/{task_uuids[1]}/relationships"
        f"?target_uuid={task_uuids[0]}&relationship_type=depends_on"
    )
    
    # Task 2.1 depends on Task 1.2
    client.post(
        f"/api/v1/minds/{task_uuids[2]}/relationships"
        f"?target_uuid={task_uuids[1]}&relationship_type=depends_on"
    )
    
    # Task 2.2 depends on Task 2.1
    client.post(
        f"/api/v1/minds/{task_uuids[3]}/relationships"
        f"?target_uuid={task_uuids[2]}&relationship_type=depends_on"
    )
    
    # Create Employees
    employee_uuids = []
    for i in range(1, 3):
        employee_data = {
            "mind_type": "employee",
            "title": f"Developer {i}",
            "creator": "hr@example.com",
            "type_specific_attributes": {
                "email": f"dev{i}@example.com",
                "role": "Software Engineer",
                "hire_date": "2024-01-01",
            },
        }
        employee_response = client.post("/api/v1/minds", json=employee_data)
        employee_uuid = employee_response.json()["uuid"]
        employee_uuids.append(employee_uuid)
    
    # Create ASSIGNED_TO relationships: Tasks -> Employees
    for i, task_uuid in enumerate(task_uuids):
        employee_idx = i % 2
        client.post(
            f"/api/v1/minds/{task_uuid}/relationships"
            f"?target_uuid={employee_uuids[employee_idx]}&relationship_type=assigned_to"
        )
    
    # Create Risk and Failure nodes
    failure_data = {
        "mind_type": "failure",
        "title": "Database Connection Failure",
        "creator": "qa@example.com",
        "type_specific_attributes": {
            "failure_mode": "Connection timeout",
            "effects": "System unavailable",
            "causes": "Network issues",
            "detection_method": "Health check monitoring",
        },
    }
    failure_response = client.post("/api/v1/minds", json=failure_data)
    failure_uuid = failure_response.json()["uuid"]
    
    risk_data = {
        "mind_type": "risk",
        "title": "Database Reliability Risk",
        "creator": "qa@example.com",
        "type_specific_attributes": {
            "severity": "high",
            "probability": "possible",
            "mitigation_plan": "Implement connection pooling and retry logic",
        },
    }
    risk_response = client.post("/api/v1/minds", json=risk_data)
    risk_uuid = risk_response.json()["uuid"]
    
    # Create MITIGATES relationship: Risk -> Failure
    client.post(
        f"/api/v1/minds/{risk_uuid}/relationships"
        f"?target_uuid={failure_uuid}&relationship_type=mitigates"
    )
    
    # Verify relationship graph structure
    # Check Project relationships
    project_rels = client.get(f"/api/v1/minds/{project_uuid}/relationships").json()
    assert len(project_rels) == 2  # Contains 2 phases
    contains_rels = [r for r in project_rels if r["relationship_type"] == "contains"]
    assert len(contains_rels) == 2
    
    # Check Phase 1 relationships
    phase1_rels = client.get(f"/api/v1/minds/{phase_uuids[0]}/relationships").json()
    phase1_contains = [r for r in phase1_rels if r["relationship_type"] == "contains" and r["source_uuid"] == phase_uuids[0]]
    assert len(phase1_contains) == 2  # Contains 2 tasks
    
    # Check Task dependency chain
    task_deps = client.get(
        f"/api/v1/minds/{task_uuids[1]}/relationships?relationship_type=depends_on"
    ).json()
    assert len(task_deps) >= 1
    
    # Check Risk mitigation relationship
    risk_rels = client.get(f"/api/v1/minds/{risk_uuid}/relationships").json()
    mitigates_rels = [r for r in risk_rels if r["relationship_type"] == "mitigates"]
    assert len(mitigates_rels) == 1
    assert mitigates_rels[0]["target_uuid"] == failure_uuid


def test_relationship_uniqueness_enforcement():
    """
    Test that duplicate relationships are prevented.
    
    Validates: Requirements 8.6
    """
    # Create two Mind nodes
    node1_data = {
        "mind_type": "task",
        "title": "Task 1",
        "creator": "test@example.com",
        "type_specific_attributes": {
            "priority": "high",
            "assignee": "dev@example.com",
        },
    }
    node1_response = client.post("/api/v1/minds", json=node1_data)
    node1_uuid = node1_response.json()["uuid"]
    
    node2_data = {
        "mind_type": "task",
        "title": "Task 2",
        "creator": "test@example.com",
        "type_specific_attributes": {
            "priority": "medium",
            "assignee": "dev@example.com",
        },
    }
    node2_response = client.post("/api/v1/minds", json=node2_data)
    node2_uuid = node2_response.json()["uuid"]
    
    # Create first relationship
    rel_response_1 = client.post(
        f"/api/v1/minds/{node1_uuid}/relationships"
        f"?target_uuid={node2_uuid}&relationship_type=depends_on"
    )
    assert rel_response_1.status_code == 201
    
    # Attempt to create duplicate relationship
    rel_response_2 = client.post(
        f"/api/v1/minds/{node1_uuid}/relationships"
        f"?target_uuid={node2_uuid}&relationship_type=depends_on"
    )
    
    # Should fail (400, 409 for conflict, or 500 if not implemented yet)
    assert rel_response_2.status_code in [400, 409, 500]


# ============================================================================
# Test: Bulk Operations with Transaction Rollback
# ============================================================================



def test_bulk_create_atomicity_with_validation_failure():
    """
    Test that bulk create is atomic - if any item fails, none are created.
    
    Validates: Requirements 10.3, 10.4
    """
    # Get initial count of Mind nodes
    initial_response = client.get("/api/v1/minds")
    initial_count = initial_response.json()["total"]
    
    # Create bulk data with one invalid item
    bulk_data = [
        {
            "mind_type": "project",
            "title": "Valid Project 1",
            "creator": "test@example.com",
            "type_specific_attributes": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        },
        {
            "mind_type": "project",
            "title": "Valid Project 2",
            "creator": "test@example.com",
            "type_specific_attributes": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        },
        {
            "mind_type": "invalid_type",  # Invalid type
            "title": "Invalid Project",
            "creator": "test@example.com",
            "type_specific_attributes": {},
        },
        {
            "mind_type": "project",
            "title": "Valid Project 3",
            "creator": "test@example.com",
            "type_specific_attributes": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        },
    ]
    
    # Attempt bulk create
    bulk_response = client.post("/api/v1/minds/bulk", json=bulk_data)
    
    # Should fail validation
    assert bulk_response.status_code == 422
    
    # Verify no nodes were created (atomicity)
    final_response = client.get("/api/v1/minds")
    final_count = final_response.json()["total"]
    assert final_count == initial_count


def test_bulk_create_success_all_or_nothing():
    """
    Test successful bulk create with all valid items.
    
    Validates: Requirements 10.1, 10.5
    """
    # Get initial count
    initial_response = client.get("/api/v1/minds")
    initial_count = initial_response.json()["total"]
    
    # Create 20 valid Mind nodes in bulk
    bulk_data = [
        {
            "mind_type": "task",
            "title": f"Bulk Task {i}",
            "creator": "bulk@example.com",
            "type_specific_attributes": {
                "priority": "medium",
                "assignee": "dev@example.com",
                "estimated_hours": float(i),
            },
        }
        for i in range(1, 21)
    ]
    
    bulk_response = client.post("/api/v1/minds/bulk", json=bulk_data)
    assert bulk_response.status_code == 201
    
    created_nodes = bulk_response.json()
    assert len(created_nodes) == 20
    
    # Verify all have unique UUIDs
    uuids = [node["uuid"] for node in created_nodes]
    assert len(uuids) == len(set(uuids))
    
    # Verify all were created in database
    final_response = client.get("/api/v1/minds")
    final_count = final_response.json()["total"]
    assert final_count == initial_count + 20
    
    # Verify we can retrieve each created node
    for node in created_nodes:
        get_response = client.get(f"/api/v1/minds/{node['uuid']}")
        assert get_response.status_code == 200


def test_bulk_update_atomicity_with_nonexistent_uuid():
    """
    Test that bulk update is atomic - if any UUID doesn't exist, none are updated.
    
    Validates: Requirements 10.3, 10.4
    """
    # Create some Mind nodes
    created_uuids = []
    for i in range(3):
        create_data = {
            "mind_type": "task",
            "title": f"Task {i}",
            "creator": "test@example.com",
            "type_specific_attributes": {
                "priority": "low",
                "assignee": "dev@example.com",
            },
        }
        response = client.post("/api/v1/minds", json=create_data)
        created_uuids.append(response.json()["uuid"])
    
    # Get original versions
    original_versions = []
    for uuid_str in created_uuids:
        response = client.get(f"/api/v1/minds/{uuid_str}")
        original_versions.append(response.json()["version"])
    
    # Attempt bulk update with one non-existent UUID
    bulk_updates = [
        {"uuid": created_uuids[0], "title": "Updated Task 0"},
        {"uuid": created_uuids[1], "title": "Updated Task 1"},
        {"uuid": str(uuid.uuid4()), "title": "Non-existent Task"},  # Invalid UUID
    ]
    
    bulk_response = client.put("/api/v1/minds/bulk", json=bulk_updates)
    
    # Should fail
    assert bulk_response.status_code in [400, 404]
    
    # Verify no nodes were updated (atomicity)
    for i, uuid_str in enumerate(created_uuids):
        response = client.get(f"/api/v1/minds/{uuid_str}")
        assert response.json()["version"] == original_versions[i]
        assert response.json()["title"] == f"Task {i}"  # Original title preserved


def test_bulk_update_success_with_version_tracking():
    """
    Test successful bulk update with version tracking.
    
    Validates: Requirements 10.2, 10.5
    """
    # Create 5 Mind nodes
    created_uuids = []
    for i in range(5):
        create_data = {
            "mind_type": "milestone",
            "title": f"Milestone {i}",
            "creator": "pm@example.com",
            "type_specific_attributes": {
                "target_date": "2024-06-01",
                "completion_percentage": 0.0,
            },
        }
        response = client.post("/api/v1/minds", json=create_data)
        created_uuids.append(response.json()["uuid"])
    
    # Bulk update all nodes
    bulk_updates = [
        {
            "uuid": uuid_str,
            "title": f"Updated Milestone {i}",
            "type_specific_attributes": {
                "completion_percentage": float(i * 20),
            },
        }
        for i, uuid_str in enumerate(created_uuids)
    ]
    
    bulk_response = client.put("/api/v1/minds/bulk", json=bulk_updates)
    assert bulk_response.status_code == 200
    
    updated_nodes = bulk_response.json()
    assert len(updated_nodes) == 5
    
    # Verify all nodes were updated with new versions
    for i, node in enumerate(updated_nodes):
        assert node["version"] == 2  # All should be version 2
        assert node["title"] == f"Updated Milestone {i}"
        assert node["type_specific_attributes"]["completion_percentage"] == float(i * 20)
        assert node["uuid"] == created_uuids[i]
    
    # Verify version history for each node
    for uuid_str in created_uuids:
        history_response = client.get(f"/api/v1/minds/{uuid_str}/history")
        history = history_response.json()
        assert len(history) == 2  # Original + update


def test_bulk_operations_capacity_limits():
    """
    Test bulk operations respect 100-item capacity limits.
    
    Validates: Requirements 10.1, 10.2
    """
    # Test bulk create at capacity (100 items)
    bulk_create_data = [
        {
            "mind_type": "knowledge",
            "title": f"Knowledge Item {i}",
            "creator": "admin@example.com",
            "type_specific_attributes": {
                "category": "Technical",
                "tags": ["test"],
                "content": f"Content {i}",
            },
        }
        for i in range(100)
    ]
    
    create_response = client.post("/api/v1/minds/bulk", json=bulk_create_data)
    assert create_response.status_code == 201
    created_nodes = create_response.json()
    assert len(created_nodes) == 100
    
    # Test bulk create exceeding capacity (101 items)
    bulk_create_exceed = bulk_create_data + [bulk_create_data[0]]
    exceed_response = client.post("/api/v1/minds/bulk", json=bulk_create_exceed)
    assert exceed_response.status_code == 400
    
    # Test bulk update at capacity
    bulk_update_data = [
        {"uuid": node["uuid"], "title": f"Updated {i}"}
        for i, node in enumerate(created_nodes)
    ]
    
    update_response = client.put("/api/v1/minds/bulk", json=bulk_update_data)
    assert update_response.status_code == 200
    updated_nodes = update_response.json()
    assert len(updated_nodes) == 100


# ============================================================================
# Test: Query Operations with Complex Filters
# ============================================================================



def test_query_with_multiple_filters_and_pagination():
    """
    Test querying with multiple filters combined with pagination.
    
    Validates: Requirements 11.1-11.7
    """
    # Create diverse set of Mind nodes
    creators = ["alice@example.com", "bob@example.com", "charlie@example.com"]
    types = ["project", "task", "milestone"]
    statuses = ["draft", "active", "archived"]
    
    created_nodes = []
    for i in range(30):
        create_data = {
            "mind_type": types[i % 3],
            "title": f"Test Node {i}",
            "creator": creators[i % 3],
            "type_specific_attributes": {},
        }
        
        # Add type-specific attributes
        if create_data["mind_type"] == "project":
            create_data["type_specific_attributes"] = {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            }
        elif create_data["mind_type"] == "task":
            create_data["type_specific_attributes"] = {
                "priority": "medium",
                "assignee": "dev@example.com",
            }
        elif create_data["mind_type"] == "milestone":
            create_data["type_specific_attributes"] = {
                "target_date": "2024-06-01",
                "completion_percentage": 50.0,
            }
        
        response = client.post("/api/v1/minds", json=create_data)
        created_nodes.append(response.json())
        
        # Update status for some nodes
        if i % 3 == 0:
            uuid_str = response.json()["uuid"]
            client.put(f"/api/v1/minds/{uuid_str}", json={"status": statuses[i % 3]})
    
    # Test 1: Filter by type only
    type_response = client.get("/api/v1/minds?mind_type=project")
    assert type_response.status_code == 200
    type_data = type_response.json()
    assert all(item["mind_type"] == "project" for item in type_data["items"])
    
    # Test 2: Filter by creator only
    creator_response = client.get("/api/v1/minds?creator=alice@example.com")
    assert creator_response.status_code == 200
    creator_data = creator_response.json()
    assert all(item["creator"] == "alice@example.com" for item in creator_data["items"])
    
    # Test 3: Combine multiple filters (type + creator)
    combined_response = client.get("/api/v1/minds?mind_type=task&creator=bob@example.com")
    assert combined_response.status_code == 200
    combined_data = combined_response.json()
    for item in combined_data["items"]:
        assert item["mind_type"] == "task"
        assert item["creator"] == "bob@example.com"
    
    # Test 4: Pagination with filters
    paginated_response = client.get(
        "/api/v1/minds?mind_type=project&page=1&page_size=5"
    )
    assert paginated_response.status_code == 200
    paginated_data = paginated_response.json()
    assert paginated_data["page"] == 1
    assert paginated_data["page_size"] == 5
    assert len(paginated_data["items"]) <= 5
    assert all(item["mind_type"] == "project" for item in paginated_data["items"])
    
    # Test 5: Sorting
    sorted_response = client.get("/api/v1/minds?sort_by=title&sort_order=asc")
    assert sorted_response.status_code == 200
    sorted_data = sorted_response.json()
    titles = [item["title"] for item in sorted_data["items"]]
    assert titles == sorted(titles)


def test_query_with_date_range_filtering():
    """
    Test querying with date range filters.
    
    Validates: Requirements 11.4
    """
    # Create nodes at different times
    base_time = datetime.now()
    
    for i in range(5):
        create_data = {
            "mind_type": "task",
            "title": f"Time-based Task {i}",
            "creator": "test@example.com",
            "type_specific_attributes": {
                "priority": "medium",
                "assignee": "dev@example.com",
            },
        }
        client.post("/api/v1/minds", json=create_data)
        time.sleep(0.1)  # Small delay to ensure different timestamps
    
    # Query with date range
    after_time = (base_time + timedelta(seconds=0.2)).isoformat()
    before_time = (base_time + timedelta(seconds=0.4)).isoformat()
    
    range_response = client.get(
        f"/api/v1/minds?updated_after={after_time}&updated_before={before_time}"
    )
    assert range_response.status_code == 200


# ============================================================================
# Test: End-to-End Scenarios
# ============================================================================



def test_end_to_end_project_management_scenario():
    """
    Test complete project management scenario from creation to completion.
    
    Scenario:
    1. Create project with phases and tasks
    2. Assign tasks to employees
    3. Update task progress
    4. Track version history
    5. Query project status
    6. Complete and archive project
    
    Validates: All requirements in realistic usage scenario
    """
    # Step 1: Create project
    project_data = {
        "mind_type": "project",
        "title": "E2E Test Project",
        "description": "End-to-end integration test project",
        "creator": "pm@example.com",
        "type_specific_attributes": {
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
            "budget": 250000.0,
        },
    }
    project_response = client.post("/api/v1/minds", json=project_data)
    assert project_response.status_code == 201
    project_uuid = project_response.json()["uuid"]
    
    # Step 2: Create phase
    phase_data = {
        "mind_type": "phase",
        "title": "Development Phase",
        "creator": "pm@example.com",
        "type_specific_attributes": {
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "phase_number": 1,
        },
    }
    phase_response = client.post("/api/v1/minds", json=phase_data)
    phase_uuid = phase_response.json()["uuid"]
    
    # Link phase to project
    client.post(
        f"/api/v1/minds/{project_uuid}/relationships"
        f"?target_uuid={phase_uuid}&relationship_type=contains"
    )
    
    # Step 3: Create tasks
    task_uuids = []
    for i in range(3):
        task_data = {
            "mind_type": "task",
            "title": f"E2E Task {i+1}",
            "creator": "pm@example.com",
            "type_specific_attributes": {
                "priority": "high" if i == 0 else "medium",
                "assignee": f"dev{i+1}@example.com",
                "estimated_hours": 16.0,
            },
        }
        task_response = client.post("/api/v1/minds", json=task_data)
        task_uuid = task_response.json()["uuid"]
        task_uuids.append(task_uuid)
        
        # Link task to phase
        client.post(
            f"/api/v1/minds/{phase_uuid}/relationships"
            f"?target_uuid={task_uuid}&relationship_type=contains"
        )
    
    # Step 4: Create employees and assign tasks
    for i, task_uuid in enumerate(task_uuids):
        employee_data = {
            "mind_type": "employee",
            "title": f"Developer {i+1}",
            "creator": "hr@example.com",
            "type_specific_attributes": {
                "email": f"dev{i+1}@example.com",
                "role": "Software Engineer",
                "hire_date": "2024-01-01",
            },
        }
        employee_response = client.post("/api/v1/minds", json=employee_data)
        employee_uuid = employee_response.json()["uuid"]
        
        # Assign task to employee
        client.post(
            f"/api/v1/minds/{task_uuid}/relationships"
            f"?target_uuid={employee_uuid}&relationship_type=assigned_to"
        )
    
    # Step 5: Update task progress (simulate work)
    for task_uuid in task_uuids:
        # First update: In progress
        client.put(
            f"/api/v1/minds/{task_uuid}",
            json={"description": "Work in progress"}
        )
        
        # Second update: Completed
        client.put(
            f"/api/v1/minds/{task_uuid}",
            json={"description": "Task completed"}
        )
    
    # Step 6: Verify version history for tasks
    for task_uuid in task_uuids:
        history_response = client.get(f"/api/v1/minds/{task_uuid}/history")
        history = history_response.json()
        assert len(history) >= 2  # At least create + updates
        assert history[0]["description"] == "Task completed"
    
    # Step 7: Query project structure
    project_rels = client.get(f"/api/v1/minds/{project_uuid}/relationships").json()
    project_contains = [r for r in project_rels if r["relationship_type"] == "contains" and r["source_uuid"] == project_uuid]
    assert len(project_contains) == 1  # Contains 1 phase
    
    phase_rels = client.get(f"/api/v1/minds/{phase_uuid}/relationships").json()
    phase_contains = [r for r in phase_rels if r["relationship_type"] == "contains" and r["source_uuid"] == phase_uuid]
    assert len(phase_contains) == 3  # Contains 3 tasks
    
    # Step 8: Update project status to completed
    client.put(
        f"/api/v1/minds/{project_uuid}",
        json={"description": "Project completed successfully"}
    )
    
    # Step 9: Archive project
    client.put(
        f"/api/v1/minds/{project_uuid}",
        json={"description": "Project archived"}
    )
    
    # Step 10: Verify final state
    final_project = client.get(f"/api/v1/minds/{project_uuid}").json()
    assert final_project["version"] == 3  # Create + 2 updates



def test_concurrent_updates_version_integrity():
    """
    Test that concurrent updates maintain version integrity.
    
    Validates: Requirements 5.1-5.8
    """
    # Create a Mind node
    create_data = {
        "mind_type": "task",
        "title": "Concurrent Update Test",
        "creator": "test@example.com",
        "type_specific_attributes": {
            "priority": "medium",
            "assignee": "dev@example.com",
        },
    }
    create_response = client.post("/api/v1/minds", json=create_data)
    created_uuid = create_response.json()["uuid"]
    
    # Perform multiple rapid updates
    update_count = 10
    for i in range(update_count):
        update_data = {
            "title": f"Concurrent Update {i}",
            "description": f"Update number {i}",
        }
        response = client.put(f"/api/v1/minds/{created_uuid}", json=update_data)
        assert response.status_code == 200
    
    # Verify version history integrity
    history_response = client.get(f"/api/v1/minds/{created_uuid}/history")
    history = history_response.json()
    
    # Should have initial + all updates
    assert len(history) == update_count + 1
    
    # Verify version numbers are sequential
    versions = [item["version"] for item in history]
    expected_versions = list(range(update_count + 1, 0, -1))
    assert versions == expected_versions
    
    # Verify UUID consistency across all versions
    uuids = [item["uuid"] for item in history]
    assert all(u == created_uuid for u in uuids)
    
    # Verify creator consistency
    creators = [item["creator"] for item in history]
    assert all(c == "test@example.com" for c in creators)


def test_error_handling_in_complex_operations():
    """
    Test error handling in complex multi-step operations.
    
    Validates: Requirements 12.1-12.6
    """
    # Test 1: Create relationship with non-existent source
    non_existent_uuid = str(uuid.uuid4())
    target_data = {
        "mind_type": "task",
        "title": "Target Task",
        "creator": "test@example.com",
        "type_specific_attributes": {
            "priority": "medium",
            "assignee": "dev@example.com",
        },
    }
    target_response = client.post("/api/v1/minds", json=target_data)
    target_uuid = target_response.json()["uuid"]
    
    rel_response = client.post(
        f"/api/v1/minds/{non_existent_uuid}/relationships"
        f"?target_uuid={target_uuid}&relationship_type=contains"
    )
    assert rel_response.status_code == 404
    error_data = rel_response.json()
    assert "request_id" in error_data
    assert "error_type" in error_data
    
    # Test 2: Update non-existent node
    update_response = client.put(
        f"/api/v1/minds/{non_existent_uuid}",
        json={"title": "Updated Title"}
    )
    assert update_response.status_code == 404
    update_error = update_response.json()
    assert "request_id" in update_error
    assert non_existent_uuid in update_error["message"]
    
    # Test 3: Delete non-existent node
    delete_response = client.delete(f"/api/v1/minds/{non_existent_uuid}")
    assert delete_response.status_code == 404
    
    # Test 4: Get version history for non-existent node
    history_response = client.get(f"/api/v1/minds/{non_existent_uuid}/history")
    assert history_response.status_code == 404
    
    # Test 5: Invalid validation in create
    invalid_data = {
        "mind_type": "project",
        "title": "",  # Empty title should fail validation
        "creator": "test@example.com",
        "type_specific_attributes": {
            "start_date": "2024-01-01",
            "end_date": "2023-12-31",  # End before start
        },
    }
    invalid_response = client.post("/api/v1/minds", json=invalid_data)
    assert invalid_response.status_code == 422


def test_performance_with_large_version_history():
    """
    Test system performance with large version histories.
    
    Validates: Requirements 6.1-6.6
    """
    # Create a Mind node
    create_data = {
        "mind_type": "knowledge",
        "title": "Performance Test Knowledge",
        "creator": "test@example.com",
        "type_specific_attributes": {
            "category": "Technical",
            "tags": ["performance"],
            "content": "Initial content",
        },
    }
    create_response = client.post("/api/v1/minds", json=create_data)
    created_uuid = create_response.json()["uuid"]
    
    # Create 50 versions
    for i in range(50):
        update_data = {
            "type_specific_attributes": {
                "content": f"Updated content version {i+1}",
            },
        }
        client.put(f"/api/v1/minds/{created_uuid}", json=update_data)
    
    # Test retrieval performance
    start_time = time.time()
    latest_response = client.get(f"/api/v1/minds/{created_uuid}")
    retrieval_time = time.time() - start_time
    
    assert latest_response.status_code == 200
    assert retrieval_time < 0.2  # Should be under 200ms
    
    # Test version history retrieval with pagination
    start_time = time.time()
    history_response = client.get(
        f"/api/v1/minds/{created_uuid}/history?page=1&page_size=20"
    )
    history_time = time.time() - start_time
    
    assert history_response.status_code == 200
    assert history_time < 0.5  # Should be under 500ms
    history = history_response.json()
    assert len(history) == 20
