"""
Unit tests for Mind relationship types.

This module contains unit tests specifically for validating that each
relationship type defined in Requirement 8.2 can be created successfully.

**Validates: Requirement 8.2**
"""

import pytest

from src.schemas.minds import MindCreate
from src.services.mind_service import MindService


class TestRelationshipTypes:
    """Test suite for validating all supported relationship types."""

    @pytest.mark.asyncio
    async def test_contains_relationship_type(self, clean_database):
        """
        Test that 'contains' relationship type can be created.

        Validates: Requirement 8.2 - contains relationship type
        """
        service = MindService()

        # Create source and target nodes
        source_data = MindCreate(
            mind_type="project",
            title="Parent Project",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        source = await service.create_mind(source_data)

        target_data = MindCreate(
            mind_type="phase",
            title="Child Phase",
            creator="test@example.com",
            type_specific_attributes={
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "phase_number": 1,
            },
        )
        target = await service.create_mind(target_data)

        # Create 'contains' relationship
        relationship = await service.create_relationship(
            source.uuid, target.uuid, "contains"
        )

        # Verify relationship was created with correct type
        assert relationship.relationship_type == "contains"
        assert relationship.source_uuid == source.uuid
        assert relationship.target_uuid == target.uuid
        assert relationship.created_at is not None

    @pytest.mark.asyncio
    async def test_depends_on_relationship_type(self, clean_database):
        """
        Test that 'depends_on' relationship type can be created.

        Validates: Requirement 8.2 - depends_on relationship type
        """
        service = MindService()

        # Create source and target nodes
        source_data = MindCreate(
            mind_type="task",
            title="Dependent Task",
            creator="test@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        source = await service.create_mind(source_data)

        target_data = MindCreate(
            mind_type="task",
            title="Prerequisite Task",
            creator="test@example.com",
            type_specific_attributes={
                "priority": "high",
                "assignee": "dev@example.com",
            },
        )
        target = await service.create_mind(target_data)

        # Create 'depends_on' relationship
        relationship = await service.create_relationship(
            source.uuid, target.uuid, "depends_on"
        )

        # Verify relationship was created with correct type
        assert relationship.relationship_type == "depends_on"
        assert relationship.source_uuid == source.uuid
        assert relationship.target_uuid == target.uuid
        assert relationship.created_at is not None

    @pytest.mark.asyncio
    async def test_assigned_to_relationship_type(self, clean_database):
        """
        Test that 'assigned_to' relationship type can be created.

        Validates: Requirement 8.2 - assigned_to relationship type
        """
        service = MindService()

        # Create source and target nodes
        source_data = MindCreate(
            mind_type="task",
            title="Assigned Task",
            creator="test@example.com",
            type_specific_attributes={
                "priority": "medium",
                "assignee": "dev@example.com",
            },
        )
        source = await service.create_mind(source_data)

        target_data = MindCreate(
            mind_type="resource",
            title="John Doe",
            creator="test@example.com",
            type_specific_attributes={
                "email": "john.doe@example.com",
                "resource_type": "PERSON",
                "efficiency": 1.0,
                "daily_rate": 800.0,
            },
        )
        target = await service.create_mind(target_data)

        # Create 'assigned_to' relationship
        relationship = await service.create_relationship(
            source.uuid, target.uuid, "assigned_to"
        )

        # Verify relationship was created with correct type
        assert relationship.relationship_type == "assigned_to"
        assert relationship.source_uuid == source.uuid
        assert relationship.target_uuid == target.uuid
        assert relationship.created_at is not None

    @pytest.mark.asyncio
    async def test_relates_to_relationship_type(self, clean_database):
        """
        Test that 'relates_to' relationship type can be created.

        Validates: Requirement 8.2 - relates_to relationship type
        """
        service = MindService()

        # Create source and target nodes
        source_data = MindCreate(
            mind_type="design_output",
            title="API Design Document",
            creator="test@example.com",
            type_specific_attributes={
                "output_type": "documentation",
                "verification_status": "verified",
                "content": "API design specifications",
            },
        )
        source = await service.create_mind(source_data)

        target_data = MindCreate(
            mind_type="design_input",
            title="Requirements Document",
            creator="test@example.com",
            type_specific_attributes={
                "source": "stakeholder",
                "input_type": "requirements",
                "content": "System requirements",
            },
        )
        target = await service.create_mind(target_data)

        # Create 'relates_to' relationship
        relationship = await service.create_relationship(
            source.uuid, target.uuid, "relates_to"
        )

        # Verify relationship was created with correct type
        assert relationship.relationship_type == "relates_to"
        assert relationship.source_uuid == source.uuid
        assert relationship.target_uuid == target.uuid
        assert relationship.created_at is not None

    @pytest.mark.asyncio
    async def test_implements_relationship_type(self, clean_database):
        """
        Test that 'implements' relationship type can be created.

        Validates: Requirement 8.2 - implements relationship type
        """
        service = MindService()

        # Create source and target nodes
        source_data = MindCreate(
            mind_type="acceptance_criteria",
            title="Login Success Criteria",
            creator="test@example.com",
            type_specific_attributes={
                "criteria_text": "User can login with valid credentials",
                "verification_method": "automated test",
                "verification_status": "verified",
            },
        )
        source = await service.create_mind(source_data)

        target_data = MindCreate(
            mind_type="user_story",
            title="User Login Story",
            creator="test@example.com",
            type_specific_attributes={
                "as_a": "registered user",
                "i_want": "to login to the system",
                "so_that": "I can access my account",
                "acceptance_criteria_ids": [],
            },
        )
        target = await service.create_mind(target_data)

        # Create 'implements' relationship
        relationship = await service.create_relationship(
            source.uuid, target.uuid, "implements"
        )

        # Verify relationship was created with correct type
        assert relationship.relationship_type == "implements"
        assert relationship.source_uuid == source.uuid
        assert relationship.target_uuid == target.uuid
        assert relationship.created_at is not None

    @pytest.mark.asyncio
    async def test_mitigates_relationship_type(self, clean_database):
        """
        Test that 'mitigates' relationship type can be created.

        Validates: Requirement 8.2 - mitigates relationship type
        """
        service = MindService()

        # Create source and target nodes
        source_data = MindCreate(
            mind_type="risk",
            title="Security Risk Mitigation",
            creator="test@example.com",
            type_specific_attributes={
                "severity": "high",
                "probability": "unlikely",
                "mitigation_plan": "Implement encryption and access controls",
            },
        )
        source = await service.create_mind(source_data)

        target_data = MindCreate(
            mind_type="failure",
            title="Data Breach Failure",
            creator="test@example.com",
            type_specific_attributes={
                "failure_mode": "unauthorized access",
                "effects": "data exposure",
                "causes": "weak authentication",
                "detection_method": "security monitoring",
            },
        )
        target = await service.create_mind(target_data)

        # Create 'mitigates' relationship
        relationship = await service.create_relationship(
            source.uuid, target.uuid, "mitigates"
        )

        # Verify relationship was created with correct type
        assert relationship.relationship_type == "mitigates"
        assert relationship.source_uuid == source.uuid
        assert relationship.target_uuid == target.uuid
        assert relationship.created_at is not None

    @pytest.mark.asyncio
    async def test_all_relationship_types_in_sequence(self, clean_database):
        """
        Test that all 6 relationship types can be created in sequence.

        This comprehensive test validates that all relationship types defined
        in Requirement 8.2 are supported and can be created successfully.

        Validates: Requirement 8.2 - all relationship types
        """
        service = MindService()

        # Create nodes for testing all relationship types
        nodes = []
        for i in range(7):
            node_data = MindCreate(
                mind_type="knowledge",
                title=f"Test Node {i}",
                creator="test@example.com",
                type_specific_attributes={
                    "category": "Test",
                    "tags": ["test"],
                    "content": f"Content for node {i}",
                },
            )
            node = await service.create_mind(node_data)
            nodes.append(node)

        # Define all 6 relationship types from Requirement 8.2
        relationship_types = [
            "contains",
            "depends_on",
            "assigned_to",
            "relates_to",
            "implements",
            "mitigates",
        ]

        # Create one relationship of each type
        created_relationships = []
        for i, rel_type in enumerate(relationship_types):
            relationship = await service.create_relationship(
                nodes[i].uuid, nodes[i + 1].uuid, rel_type
            )
            created_relationships.append(relationship)

            # Verify each relationship was created correctly
            assert relationship.relationship_type == rel_type
            assert relationship.source_uuid == nodes[i].uuid
            assert relationship.target_uuid == nodes[i + 1].uuid
            assert relationship.created_at is not None

        # Verify all 6 relationship types were created
        assert len(created_relationships) == 6
        created_types = {rel.relationship_type for rel in created_relationships}
        assert created_types == set(relationship_types)
