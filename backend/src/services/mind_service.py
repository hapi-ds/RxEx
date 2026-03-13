"""
Mind service layer for CRUD operations.

This module implements the MindService class that handles business logic for
Mind node operations including creation, retrieval, updates, deletion, version
history, relationships, and queries.

**Validates: Requirements 3.1-3.7**
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from ..exceptions import MindNotFoundError
from ..models.mind import BaseMind
from ..models.mind_types import (
    AcceptanceCriteria,
    Company,
    Department,
    Email,
    Failure,
    Knowledge,
    Project,
    Risk,
    Task,
    Resource,
    Account,
    ScheduleHistory,
    ScheduledTask,
    Requirement,
)
from ..schemas.mind_generic import (
    MindBulkUpdate,
    MindCreate,
    MindQueryFilters,
    MindResponse,
    MindUpdate,
    QueryResult,
)


class MindService:
    """
    Service class for Mind node operations.

    This class implements business logic for creating, retrieving, updating,
    and deleting Mind nodes. It handles version history tracking, relationship
    management, and query operations.

    **Validates: Requirements 3.1-3.7**
    """

    # Mapping of mind_type strings to their corresponding model classes
    MIND_TYPE_MAP = {
        "project": Project,
        "task": Task,
        "company": Company,
        "department": Department,
        "resource": Resource,  # Replaces "employee" - use resource_type=ResourceType.PERSON
        "email": Email,
        "knowledge": Knowledge,
        "requirement": Requirement,  # Consolidated type - use requirement_type field
        "acceptance_criteria": AcceptanceCriteria,
        "risk": Risk,
        "failure": Failure,
        "account": Account,
        "journalentry": Journalentry,
        "booking": Booking,
        "sprint": Sprint,
        "schedulehistory": ScheduleHistory,
        "scheduledtask": ScheduledTask,
    }

    async def create_mind(self, mind_data: MindCreate) -> MindResponse:
        """
        Create a new Mind node in Neo4j.

        This method generates a UUID for the new Mind node, initializes version
        to 1, sets timestamps, and stores the node in Neo4j using neontology.
        It returns the complete node data including all base and type-specific
        attributes.

        Args:
            mind_data: MindCreate schema containing node creation data

        Returns:
            MindResponse: Complete node data including generated UUID

        Raises:
            ValueError: If mind_type is not supported or validation fails

        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.7**
        """
        # Get the appropriate model class for the mind_type
        model_class = self.MIND_TYPE_MAP.get(mind_data.mind_type)
        if model_class is None:
            raise ValueError(f"Unsupported mind_type: {mind_data.mind_type}")

        # Generate UUID for the new Mind node (Requirement 3.2)
        node_uuid = uuid4()

        # Initialize version to 1 (Requirement 3.3)
        version = 1

        # Set timestamp to current time (Requirement 3.4)
        updated_at = datetime.now(timezone.utc)

        # Prepare node data with base attributes
        node_data = {
            "uuid": node_uuid,
            "title": mind_data.title,
            "version": version,
            "updated_at": updated_at,
            "creator": mind_data.creator,  # Requirement 3.5
            "description": mind_data.description,
            "status": mind_data.status,
            "tags": mind_data.tags,
        }

        # Add type-specific attributes if provided
        if mind_data.type_specific_attributes:
            node_data.update(mind_data.type_specific_attributes)

        # Create and save the Mind node using neontology
        mind_node = model_class(**node_data)
        mind_node.create()  # create() modifies the node in place and returns self

        # Return complete node data (Requirement 3.7)
        return MindResponse(
            uuid=mind_node.uuid,
            mind_type=mind_data.mind_type,
            __primarylabel__=mind_data.mind_type.capitalize(),  # Capitalize for frontend compatibility
            title=mind_node.title,
            version=mind_node.version,
            created_at=mind_node.created_at,
            updated_at=mind_node.updated_at,
            creator=mind_node.creator,
            status=mind_node.status,
            description=mind_node.description,
            tags=mind_node.tags,
            type_specific_attributes=self._extract_type_specific_attributes(
                mind_node, mind_data.mind_type
            ),
        )

    def _extract_type_specific_attributes(
        self, mind_node: BaseMind, mind_type: str
    ) -> dict[str, Any]:
        """
        Extract type-specific attributes from a Mind node.

        This helper method extracts all attributes that are specific to the
        derived Mind type, excluding the base Mind attributes.

        Args:
            mind_node: The Mind node instance
            mind_type: The type of Mind node

        Returns:
            Dictionary of type-specific attributes
        """
        # Base attributes that should be excluded
        base_attributes = {
            "uuid",
            "title",
            "version",
            "updated_at",
            "creator",
            "status",
            "description",
            "element_id",
            "id",
        }

        # Extract all attributes from the node
        type_specific = {}
        for key, value in mind_node.model_dump().items():
            if key not in base_attributes:
                # Convert datetime and date objects to ISO format strings
                if isinstance(value, datetime):
                    type_specific[key] = value.isoformat()
                elif hasattr(value, "isoformat"):  # date objects
                    type_specific[key] = value.isoformat()
                else:
                    type_specific[key] = value

        return type_specific

    async def get_mind(self, uuid: UUID) -> MindResponse:
        """
        Retrieve a Mind node by UUID from Neo4j.

        This method queries Neo4j for the latest version of a Mind node with the
        specified UUID. The latest version is identified as the node with the highest
        version number for that UUID. It returns all base and type-specific attributes.
        It raises MindNotFoundError if the UUID does not exist in the database.

        Args:
            uuid: UUID of the Mind node to retrieve

        Returns:
            MindResponse: Complete node data including all attributes for the latest version

        Raises:
            MindNotFoundError: If the UUID does not exist in the database

        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # Try each model class to find which one has this UUID
        # Since we support version history, we need to find the latest version
        mind_node = None
        mind_type = None

        for type_name, model_class in self.MIND_TYPE_MAP.items():
            node = model_class.match(str(uuid))
            if node is not None:
                # Found a node, but we need the latest version
                # If there are multiple versions, match() returns the first one found
                # We need to query for all versions and get the latest
                from neontology import GraphConnection

                gc = GraphConnection()

                # Query for all nodes with this UUID, get the one with highest version
                cypher = """
                MATCH (n)
                WHERE n.uuid = $uuid
                RETURN n
                ORDER BY n.version DESC
                LIMIT 1
                """

                results = gc.engine.evaluate_query(cypher, {"uuid": str(uuid)})

                if results and results.records_raw:
                    record = results.records_raw[0]
                    result = record["n"]

                    # Convert to dict and instantiate the correct model class
                    node_data = dict(result)

                    # Convert Neo4j datetime/date objects to Python datetime/date
                    for key, value in node_data.items():
                        if hasattr(value, "to_native"):  # Neo4j DateTime/Date objects
                            node_data[key] = value.to_native()

                    mind_node = model_class(**node_data)
                    mind_type = type_name
                    break

        # If node not found in any type, raise MindNotFoundError (Requirement 4.3)
        if mind_node is None or mind_type is None:
            raise MindNotFoundError(str(uuid))

        # Return all base and type-specific attributes (Requirements 4.1, 4.2)
        return MindResponse(
            uuid=mind_node.uuid,
            mind_type=mind_type,
            __primarylabel__=mind_type.capitalize(),  # Capitalize for frontend compatibility
            title=mind_node.title,
            version=mind_node.version,
            created_at=mind_node.created_at,
            updated_at=mind_node.updated_at,
            creator=mind_node.creator,
            status=mind_node.status,
            description=mind_node.description,
            tags=mind_node.tags,
            type_specific_attributes=self._extract_type_specific_attributes(mind_node, mind_type),
        )

    async def update_mind(self, uuid: UUID, mind_data: MindUpdate) -> MindResponse:
        """
        Update a Mind node by creating a new version with version tracking.

        This method implements the version history pattern by:
        1. Fetching the current Mind node version
        2. Creating a new Mind node with incremented version number
        3. Copying unchanged attributes from the previous version
        4. Creating a PREVIOUS relationship to the prior version
        5. Setting new timestamp while preserving creator and UUID

        Args:
            uuid: UUID of the Mind node to update
            mind_data: MindUpdate schema containing updated attributes

        Returns:
            MindResponse: Complete data for the new version

        Raises:
            MindNotFoundError: If the UUID does not exist in the database

        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**
        """
        # Fetch current Mind node version (Requirement 5.1)
        current_response = await self.get_mind(uuid)

        # Get the model class for this mind type
        model_class = self.MIND_TYPE_MAP.get(current_response.mind_type)
        if model_class is None:
            raise ValueError(f"Unsupported mind_type: {current_response.mind_type}")

        # Fetch the actual node object to create relationship
        current_node = model_class.match(str(uuid))
        if current_node is None:
            raise MindNotFoundError(str(uuid))

        # Create new version number (Requirement 5.2)
        new_version = current_response.version + 1

        # Set new timestamp (Requirement 5.5)
        new_updated_at = datetime.now(timezone.utc)

        # Prepare node data starting with unchanged attributes (Requirement 5.3)
        node_data = {
            "uuid": current_response.uuid,  # Preserve UUID (Requirement 5.7)
            "title": mind_data.title if mind_data.title is not None else current_response.title,
            "version": new_version,
            "updated_at": new_updated_at,
            "creator": current_response.creator,  # Preserve creator (Requirement 5.6)
            "status": mind_data.status if mind_data.status is not None else current_response.status,
            "description": mind_data.description
            if mind_data.description is not None
            else current_response.description,
        }

        # Handle type-specific attributes (Requirement 5.3)
        # Start with current type-specific attributes
        type_specific = current_response.type_specific_attributes.copy()

        # Update with any new type-specific attributes provided
        if mind_data.type_specific_attributes is not None:
            type_specific.update(mind_data.type_specific_attributes)

        # Add type-specific attributes to node data
        node_data.update(type_specific)

        # Create the new Mind node version
        new_mind_node = model_class(**node_data)
        new_mind_node.create()

        # Create PREVIOUS relationship to prior version (Requirement 5.4)
        # We need to use Cypher directly because neontology has issues with UUID serialization in relationships
        from neontology import GraphConnection

        gc = GraphConnection()

        # Create relationship using Cypher query
        # Match nodes by UUID and version (don't rely on label since derived types may not have Mind label)
        cypher = """
        MATCH (new_node {uuid: $uuid, version: $new_version})
        MATCH (old_node {uuid: $uuid, version: $old_version})
        MERGE (new_node)-[r:PREVIOUS]->(old_node)
        RETURN count(r) as rel_count
        """

        result = gc.engine.evaluate_query(
            cypher,
            {
                "uuid": str(current_response.uuid),
                "new_version": new_version,
                "old_version": current_response.version,
            },
        )

        # Verify the relationship was created
        if not result or not result.records_raw or result.records_raw[0]["rel_count"] == 0:
            raise ValueError(
                f"Failed to create PREVIOUS relationship for UUID {current_response.uuid}"
            )

        # Return complete node data for the new version
        return MindResponse(
            uuid=new_mind_node.uuid,
            mind_type=current_response.mind_type,
            __primarylabel__=current_response.mind_type.capitalize(),  # Capitalize for frontend compatibility
            title=new_mind_node.title,
            version=new_mind_node.version,
            created_at=new_mind_node.created_at,
            updated_at=new_mind_node.updated_at,
            creator=new_mind_node.creator,
            status=new_mind_node.status,
            description=new_mind_node.description,
            tags=new_mind_node.tags,
            type_specific_attributes=self._extract_type_specific_attributes(
                new_mind_node, current_response.mind_type
            ),
        )

    async def get_version_history(
        self, uuid: UUID, page: int = 1, page_size: int = 100
    ) -> list[MindResponse]:
        """
        Retrieve the version history of a Mind node.

        This method traverses PREVIOUS relationships from the latest version to
        retrieve the complete version history. It returns an ordered list from
        newest to oldest, including all attributes for each version. Supports
        pagination for histories exceeding 100 versions.

        Args:
            uuid: UUID of the Mind node
            page: Page number (1-indexed)
            page_size: Number of versions per page (max 100)

        Returns:
            List of MindResponse objects ordered from newest to oldest

        Raises:
            MindNotFoundError: If the UUID does not exist in the database

        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6**
        """
        # First verify the UUID exists by getting the latest version
        latest_response = await self.get_mind(uuid)

        # Get the model class for this mind type
        model_class = self.MIND_TYPE_MAP.get(latest_response.mind_type)
        if model_class is None:
            raise ValueError(f"Unsupported mind_type: {latest_response.mind_type}")

        # Use Cypher to traverse PREVIOUS relationships (Requirement 6.1)
        from neontology import GraphConnection

        gc = GraphConnection()

        # Calculate pagination offset
        skip = (page - 1) * page_size

        # Query for all versions following PREVIOUS relationships
        # Order by version DESC to get newest to oldest (Requirement 6.2)
        # Don't rely on Mind label since derived types may not have it
        cypher = """
        MATCH (latest {uuid: $uuid})
        WHERE NOT EXISTS((latest)<-[:PREVIOUS]-())
        MATCH path = (latest)-[:PREVIOUS*0..]->(older)
        WITH older
        ORDER BY older.version DESC
        SKIP $skip
        LIMIT $limit
        RETURN older as n
        """

        results = gc.engine.evaluate_query(
            cypher, {"uuid": str(uuid), "skip": skip, "limit": page_size}
        )

        # Convert results to MindResponse objects
        version_history = []

        if results and results.records_raw:
            for record in results.records_raw:
                node_data = dict(record["n"])

                # Convert Neo4j datetime/date objects to Python datetime/date
                for key, value in node_data.items():
                    if hasattr(value, "to_native"):  # Neo4j DateTime/Date objects
                        node_data[key] = value.to_native()

                # Instantiate the model class
                mind_node = model_class(**node_data)

                # Create MindResponse with all attributes (Requirements 6.3, 6.4)
                version_history.append(
                    MindResponse(
                        uuid=mind_node.uuid,
                        mind_type=latest_response.mind_type,
                        __primarylabel__=latest_response.mind_type,  # Add __primarylabel__ for frontend compatibility
                        title=mind_node.title,
                        version=mind_node.version,
                        created_at=mind_node.created_at,
                        updated_at=mind_node.updated_at,
                        creator=mind_node.creator,
                        status=mind_node.status,
                        description=mind_node.description,
                        tags=mind_node.tags,
                        type_specific_attributes=self._extract_type_specific_attributes(
                            mind_node, latest_response.mind_type
                        ),
                    )
                )

        # Return ordered list from newest to oldest (Requirement 6.2)
        # If no versions found (shouldn't happen since we verified UUID exists),
        # return single-item list with current version (Requirement 6.5)
        if not version_history:
            version_history = [latest_response]

        return version_history

    async def delete_mind(self, uuid: UUID, hard_delete: bool = False) -> bool:
        """
        Delete a Mind node using soft or hard delete.

        Soft delete (default): Creates a new version with status set to "deleted"
        following all version history rules (increments version, creates PREVIOUS
        relationship, preserves UUID and creator).

        Hard delete: Removes all versions of the Mind node and all associated
        PREVIOUS relationships from the database. Requires explicit confirmation
        via hard_delete=True parameter.

        Args:
            uuid: UUID of the Mind node to delete
            hard_delete: If True, performs hard delete; if False (default), performs soft delete

        Returns:
            bool: True if deletion was successful

        Raises:
            MindNotFoundError: If the UUID does not exist in the database

        **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6**
        """
        # Verify the UUID exists
        await self.get_mind(uuid)

        if hard_delete:
            # Hard delete: Remove all versions and PREVIOUS relationships (Requirements 7.3, 7.4)
            from neontology import GraphConnection

            gc = GraphConnection()

            # Delete all nodes with this UUID and their PREVIOUS relationships
            cypher = """
            MATCH (n {uuid: $uuid})
            OPTIONAL MATCH (n)-[r:PREVIOUS]-()
            DELETE r, n
            RETURN count(n) as deleted_count
            """

            result = gc.engine.evaluate_query(cypher, {"uuid": str(uuid)})

            # Verify deletion occurred
            if result and result.records_raw and result.records_raw[0]["deleted_count"] > 0:
                return True
            else:
                raise ValueError(f"Failed to hard delete Mind node with UUID {uuid}")

        else:
            # Soft delete: Create new version with status="deleted" (Requirements 7.1, 7.2)
            # Use update_mind to create a new version following version history rules
            from ..models.enums import StatusEnum
            from ..schemas.mind_generic import MindUpdate

            update_data = MindUpdate(status=StatusEnum.DELETED)
            await self.update_mind(uuid, update_data)

            return True

    async def create_relationship(
        self, source_uuid: UUID, target_uuid: UUID, relationship_type: str
    ):
        """
        Create a typed relationship between two Mind nodes.

        This method validates that both source and target UUIDs exist in the
        database, then creates a typed relationship between them. It prevents
        duplicate relationships by checking if the same relationship already
        exists. Supported relationship types: contains, depends_on, assigned_to,
        relates_to, implements, mitigates.

        Args:
            source_uuid: UUID of the source Mind node
            target_uuid: UUID of the target Mind node
            relationship_type: Type of relationship to create

        Returns:
            RelationshipResponse: Complete relationship data including type, source, target, and timestamp

        Raises:
            MindNotFoundError: If either source or target UUID does not exist
            MindRelationshipError: If relationship creation fails or duplicate exists
            ValueError: If relationship_type is not supported

        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.6**
        """
        from ..exceptions import MindRelationshipError
        from ..schemas.mind_generic import RelationshipResponse

        # Validate relationship type (Requirement 8.2)
        valid_types = {
            "contains",
            "depends_on",
            "assigned_to",
            "relates_to",
            "implements",
            "mitigates",
        }
        if relationship_type not in valid_types:
            raise ValueError(
                f"Invalid relationship_type: {relationship_type}. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )

        # Validate that both source and target UUIDs exist (Requirement 8.3)
        try:
            await self.get_mind(source_uuid)
        except MindNotFoundError:
            raise MindNotFoundError(str(source_uuid))

        try:
            await self.get_mind(target_uuid)
        except MindNotFoundError:
            raise MindNotFoundError(str(target_uuid))

        # Check for duplicate relationships (Requirement 8.6)
        from neontology import GraphConnection

        gc = GraphConnection()

        # Convert relationship_type to uppercase for Neo4j relationship type
        rel_type_upper = relationship_type.upper()

        # Check if relationship already exists
        check_cypher = f"""
        MATCH (source {{uuid: $source_uuid}})
        MATCH (target {{uuid: $target_uuid}})
        MATCH (source)-[r:{rel_type_upper}]->(target)
        RETURN count(r) as rel_count
        """

        check_result = gc.engine.evaluate_query(
            check_cypher,
            {"source_uuid": str(source_uuid), "target_uuid": str(target_uuid)},
        )

        if (
            check_result
            and check_result.records_raw
            and check_result.records_raw[0]["rel_count"] > 0
        ):
            raise MindRelationshipError(
                f"Relationship already exists: {source_uuid} -{relationship_type}-> {target_uuid}"
            )

        # Create the relationship (Requirement 8.4)
        created_at = datetime.now(timezone.utc)

        create_cypher = f"""
        MATCH (source {{uuid: $source_uuid}})
        MATCH (target {{uuid: $target_uuid}})
        CREATE (source)-[r:{rel_type_upper} {{created_at: $created_at}}]->(target)
        RETURN count(r) as rel_count
        """

        create_result = gc.engine.evaluate_query(
            create_cypher,
            {
                "source_uuid": str(source_uuid),
                "target_uuid": str(target_uuid),
                "created_at": created_at,
            },
        )

        # Verify the relationship was created
        if (
            not create_result
            or not create_result.records_raw
            or create_result.records_raw[0]["rel_count"] == 0
        ):
            raise MindRelationshipError(
                f"Failed to create relationship: {source_uuid} -{relationship_type}-> {target_uuid}"
            )

        # Return relationship response
        return RelationshipResponse(
            relationship_type=relationship_type,
            source_uuid=source_uuid,
            target_uuid=target_uuid,
            created_at=created_at,
            properties={},
        )

    async def get_relationships(
        self,
        uuid: UUID,
        relationship_type: Optional[str] = None,
        direction: Optional[str] = "both",
    ) -> list:
        """
        Query relationships for a Mind node by UUID.

        This method retrieves relationships involving the specified Mind node,
        with optional filtering by relationship type and direction. It validates
        that the UUID exists and returns relationship data including type, source,
        target, created_at, and properties.

        Args:
            uuid: UUID of the Mind node to query relationships for
            relationship_type: Optional filter for specific relationship type
            direction: Direction filter - "outgoing", "incoming", or "both" (default)

        Returns:
            list[RelationshipResponse]: List of relationships matching the criteria

        Raises:
            MindNotFoundError: If the UUID does not exist in the database
            ValueError: If relationship_type or direction is invalid

        **Validates: Requirements 8.5**
        """
        from ..exceptions import MindNotFoundError
        from ..schemas.mind_generic import RelationshipResponse

        # Validate direction parameter
        valid_directions = {"outgoing", "incoming", "both"}
        if direction not in valid_directions:
            raise ValueError(
                f"Invalid direction: {direction}. "
                f"Must be one of: {', '.join(sorted(valid_directions))}"
            )

        # Validate relationship type if provided
        valid_types = {
            "contains",
            "depends_on",
            "assigned_to",
            "relates_to",
            "implements",
            "mitigates",
        }
        if relationship_type is not None and relationship_type not in valid_types:
            raise ValueError(
                f"Invalid relationship_type: {relationship_type}. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )

        # Validate that the UUID exists (Requirement 8.5)
        try:
            await self.get_mind(uuid)
        except MindNotFoundError:
            raise MindNotFoundError(str(uuid))

        # Query relationships based on direction
        from neontology import GraphConnection

        gc = GraphConnection()

        # Build Cypher query based on direction and optional type filter
        if direction == "outgoing":
            # Query outgoing relationships (uuid is source)
            if relationship_type:
                rel_type_upper = relationship_type.upper()
                cypher = f"""
                MATCH (source {{uuid: $uuid}})-[r:{rel_type_upper}]->(target)
                RETURN type(r) as rel_type, source.uuid as source_uuid,
                       target.uuid as target_uuid, r.created_at as created_at,
                       properties(r) as props
                ORDER BY r.created_at DESC
                """
            else:
                cypher = """
                MATCH (source {uuid: $uuid})-[r]->(target)
                WHERE type(r) IN ['CONTAINS', 'DEPENDS_ON', 'ASSIGNED_TO', 'RELATES_TO', 'IMPLEMENTS', 'MITIGATES']
                RETURN type(r) as rel_type, source.uuid as source_uuid,
                       target.uuid as target_uuid, r.created_at as created_at,
                       properties(r) as props
                ORDER BY r.created_at DESC
                """
        elif direction == "incoming":
            # Query incoming relationships (uuid is target)
            if relationship_type:
                rel_type_upper = relationship_type.upper()
                cypher = f"""
                MATCH (source)-[r:{rel_type_upper}]->(target {{uuid: $uuid}})
                RETURN type(r) as rel_type, source.uuid as source_uuid,
                       target.uuid as target_uuid, r.created_at as created_at,
                       properties(r) as props
                ORDER BY r.created_at DESC
                """
            else:
                cypher = """
                MATCH (source)-[r]->(target {uuid: $uuid})
                WHERE type(r) IN ['CONTAINS', 'DEPENDS_ON', 'ASSIGNED_TO', 'RELATES_TO', 'IMPLEMENTS', 'MITIGATES']
                RETURN type(r) as rel_type, source.uuid as source_uuid,
                       target.uuid as target_uuid, r.created_at as created_at,
                       properties(r) as props
                ORDER BY r.created_at DESC
                """
        else:  # direction == "both"
            # Query both outgoing and incoming relationships
            if relationship_type:
                rel_type_upper = relationship_type.upper()
                cypher = f"""
                MATCH (source {{uuid: $uuid}})-[r:{rel_type_upper}]->(target)
                RETURN type(r) as rel_type, source.uuid as source_uuid,
                       target.uuid as target_uuid, r.created_at as created_at,
                       properties(r) as props
                UNION
                MATCH (source)-[r:{rel_type_upper}]->(target {{uuid: $uuid}})
                RETURN type(r) as rel_type, source.uuid as source_uuid,
                       target.uuid as target_uuid, r.created_at as created_at,
                       properties(r) as props
                ORDER BY created_at DESC
                """
            else:
                cypher = """
                MATCH (source {uuid: $uuid})-[r]->(target)
                WHERE type(r) IN ['CONTAINS', 'DEPENDS_ON', 'ASSIGNED_TO', 'RELATES_TO', 'IMPLEMENTS', 'MITIGATES']
                RETURN type(r) as rel_type, source.uuid as source_uuid,
                       target.uuid as target_uuid, r.created_at as created_at,
                       properties(r) as props
                UNION
                MATCH (source)-[r]->(target {uuid: $uuid})
                WHERE type(r) IN ['CONTAINS', 'DEPENDS_ON', 'ASSIGNED_TO', 'RELATES_TO', 'IMPLEMENTS', 'MITIGATES']
                RETURN type(r) as rel_type, source.uuid as source_uuid,
                       target.uuid as target_uuid, r.created_at as created_at,
                       properties(r) as props
                ORDER BY created_at DESC
                """

        # Execute query
        result = gc.engine.evaluate_query(cypher, {"uuid": str(uuid)})

        # Convert results to RelationshipResponse objects
        relationships = []
        if result and result.records_raw:
            for record in result.records_raw:
                # Convert Neo4j relationship type to lowercase with underscores
                rel_type_neo4j = record["rel_type"]
                rel_type_normalized = rel_type_neo4j.lower()

                # Convert Neo4j DateTime to Python datetime
                created_at = record["created_at"]
                if hasattr(created_at, "to_native"):
                    created_at = created_at.to_native()

                # Extract properties (excluding created_at which is already a field)
                props = record.get("props", {})
                # Remove created_at from properties dict if present
                properties = {k: v for k, v in props.items() if k != "created_at"}

                relationships.append(
                    RelationshipResponse(
                        relationship_type=rel_type_normalized,
                        source_uuid=UUID(record["source_uuid"]),
                        target_uuid=UUID(record["target_uuid"]),
                        created_at=created_at,
                        properties=properties,
                    )
                )

        return relationships

    async def list_all_relationships(self) -> list:
        """
        List all relationships across all Mind nodes.

        This method retrieves all relationships in the database, returning
        relationship data including type, source, target, created_at, and properties.

        Returns:
            list[RelationshipResponse]: List of all relationships

        **Validates: Requirements 1.2, 8.5**
        """
        from ..schemas.mind_generic import RelationshipResponse
        from neontology import GraphConnection

        gc = GraphConnection()

        # Query all relationships of the supported types
        cypher = """
        MATCH (source)-[r]->(target)
        WHERE type(r) IN ['CONTAINS', 'DEPENDS_ON', 'ASSIGNED_TO', 'RELATES_TO', 'IMPLEMENTS', 'MITIGATES']
        AND source.uuid IS NOT NULL AND target.uuid IS NOT NULL
        RETURN type(r) as rel_type, source.uuid as source_uuid,
               target.uuid as target_uuid, r.created_at as created_at,
               properties(r) as props
        ORDER BY r.created_at DESC
        """

        # Execute query
        result = gc.engine.evaluate_query(cypher, {})

        # Convert results to RelationshipResponse objects
        relationships = []
        if result and result.records_raw:
            for record in result.records_raw:
                # Convert Neo4j relationship type to lowercase with underscores
                rel_type_neo4j = record["rel_type"]
                rel_type_normalized = rel_type_neo4j.lower()

                # Convert Neo4j DateTime to Python datetime
                created_at = record["created_at"]
                if hasattr(created_at, "to_native"):
                    created_at = created_at.to_native()

                # Extract properties (excluding created_at which is already a field)
                props = record.get("props", {})
                # Remove created_at from properties dict if present
                properties = {k: v for k, v in props.items() if k != "created_at"}

                relationships.append(
                    RelationshipResponse(
                        relationship_type=rel_type_normalized,
                        source_uuid=UUID(record["source_uuid"]),
                        target_uuid=UUID(record["target_uuid"]),
                        created_at=created_at,
                        properties=properties,
                    )
                )

        return relationships

    async def query_minds(self, filters: "MindQueryFilters") -> "QueryResult":
        """
        Query Mind nodes with filtering, sorting, and pagination.

        This method builds a dynamic Cypher query based on the provided filters,
        supporting filtering by mind_type, statuses, creator, tags, date ranges,
        and title search. Multiple filters are combined with AND logic. Multiple
        statuses use OR logic. Multiple tags use AND logic (Mind must have ALL tags).
        Results are sorted by the specified field and paginated. Only the latest
        version of each Mind node is returned (highest version number per UUID).

        Args:
            filters: MindQueryFilters schema containing query parameters

        Returns:
            QueryResult: Paginated results with items, total count, and page metadata

        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12**
        """
        from neontology import GraphConnection

        from ..schemas.mind_generic import QueryResult

        gc = GraphConnection()

        # Build WHERE clauses for filters
        where_clauses = []
        params: dict[str, Any] = {}

        # Filter by mind_type (Requirements 4.4, 11.1)
        if filters.mind_type is not None:
            # Get the model class to determine the correct label
            model_class = self.MIND_TYPE_MAP.get(filters.mind_type)
            if model_class is None:
                raise ValueError(f"Unsupported mind_type: {filters.mind_type}")
            # Use the label from the model class
            label = model_class.__name__
            where_clauses.append(f"'{label}' IN labels(n)")

        # Filter by statuses with OR logic (Requirements 2.11)
        if filters.statuses is not None and len(filters.statuses) > 0:
            status_conditions = []
            for idx, status in enumerate(filters.statuses):
                param_name = f"status_{idx}"
                status_conditions.append(f"n.status = ${param_name}")
                params[param_name] = status
            where_clauses.append(f"({' OR '.join(status_conditions)})")

        # Filter by creator (Requirement 11.3)
        if filters.creator is not None:
            where_clauses.append("n.creator = $creator")
            params["creator"] = filters.creator

        # Filter by updated_at date range (Requirement 11.4)
        if filters.updated_after is not None:
            where_clauses.append("n.updated_at >= $updated_after")
            params["updated_after"] = filters.updated_after

        if filters.updated_before is not None:
            where_clauses.append("n.updated_at <= $updated_before")
            params["updated_before"] = filters.updated_before

        # Filter by created_at date range (Requirements 2.8, 2.9)
        if filters.created_after is not None:
            where_clauses.append("n.created_at >= $created_after")
            params["created_after"] = filters.created_after

        if filters.created_before is not None:
            where_clauses.append("n.created_at <= $created_before")
            params["created_before"] = filters.created_before

        # Filter by title search with case-insensitive partial matching (Requirement 2.7)
        if filters.title_search is not None:
            where_clauses.append("toLower(n.title) CONTAINS toLower($title_search)")
            params["title_search"] = filters.title_search

        # Filter by multiple tags with AND logic (Requirement 2.10)
        if filters.tags is not None and len(filters.tags) > 0:
            for idx, tag in enumerate(filters.tags):
                param_name = f"tag_{idx}"
                where_clauses.append(f"${param_name} IN n.tags")
                params[param_name] = tag

        # Build WHERE clause (Requirement 11.5 - AND logic)
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)

        # Build ORDER BY clause (Requirement 11.6)
        sort_field_map = {
            "updated_at": "n.updated_at",
            "created_at": "n.created_at",
            "version": "n.version",
            "title": "n.title",
        }
        sort_field = sort_field_map.get(filters.sort_by, "n.updated_at")
        sort_direction = "DESC" if filters.sort_order == "desc" else "ASC"
        order_clause = f"ORDER BY {sort_field} {sort_direction}"

        # Calculate pagination (Requirement 11.7)
        skip = (filters.page - 1) * filters.page_size
        params["skip"] = skip
        params["limit"] = filters.page_size

        # Query for latest versions only - get the highest version per UUID
        # First, get all matching nodes grouped by UUID with their max version
        cypher = f"""
        MATCH (n)
        {where_clause}
        WITH n.uuid as uuid, MAX(n.version) as max_version
        MATCH (n)
        WHERE n.uuid = uuid AND n.version = max_version
        {where_clause.replace("WHERE", "AND") if where_clause else ""}
        WITH n
        {order_clause}
        WITH collect(n) as all_nodes, count(n) as total_count
        RETURN all_nodes[$skip..$skip+$limit] as nodes, total_count
        """

        result = gc.engine.evaluate_query(cypher, params)

        # Process results
        items = []
        total = 0

        if result and result.records_raw and len(result.records_raw) > 0:
            record = result.records_raw[0]
            total = record.get("total_count", 0)
            nodes = record.get("nodes", [])

            for node_data_raw in nodes:
                # Convert to dict
                node_data = dict(node_data_raw)

                # Convert Neo4j datetime/date objects to Python datetime/date
                for key, value in node_data.items():
                    if hasattr(value, "to_native"):  # Neo4j DateTime/Date objects
                        node_data[key] = value.to_native()

                # Determine mind_type from node labels
                mind_type = None
                if hasattr(node_data_raw, "labels"):
                    labels = node_data_raw.labels
                    # Find the derived type label (not "Mind")
                    for label in labels:
                        if label != "Mind":
                            # Convert label to mind_type format (e.g., "Project" -> "project")
                            for type_name, model_class in self.MIND_TYPE_MAP.items():
                                if model_class.__name__ == label:
                                    mind_type = type_name
                                    break
                            if mind_type:
                                break

                # If we couldn't determine from labels, try to infer from attributes
                if mind_type is None:
                    # Try each model class to see which one fits
                    for type_name, model_class in self.MIND_TYPE_MAP.items():
                        try:
                            _ = model_class(**node_data)
                            mind_type = type_name
                            break
                        except Exception:
                            continue

                if mind_type is None:
                    # Skip nodes we can't identify
                    continue

                # Get the model class
                model_class = self.MIND_TYPE_MAP[mind_type]

                # Instantiate the model
                mind_node = model_class(**node_data)

                # Create MindResponse
                items.append(
                    MindResponse(
                        uuid=mind_node.uuid,
                        mind_type=mind_type,
                        __primarylabel__=mind_type,  # Add __primarylabel__ for frontend compatibility
                        title=mind_node.title,
                        version=mind_node.version,
                        created_at=mind_node.created_at,
                        updated_at=mind_node.updated_at,
                        creator=mind_node.creator,
                        status=mind_node.status,
                        description=mind_node.description,
                        tags=mind_node.tags,
                        type_specific_attributes=self._extract_type_specific_attributes(
                            mind_node, mind_type
                        ),
                    )
                )

        # Calculate total pages
        total_pages = (total + filters.page_size - 1) // filters.page_size if total > 0 else 0

        return QueryResult(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    async def bulk_create(self, minds_data: list[MindCreate]) -> list[MindResponse]:
        """
        Create multiple Mind nodes in a single operation.

        This method validates all items before creating any, ensuring atomicity.
        If any validation fails, the entire batch is rejected. Supports up to
        100 nodes per operation.

        Args:
            minds_data: List of MindCreate schemas containing node creation data

        Returns:
            list[MindResponse]: Complete list of created nodes

        Raises:
            ValueError: If batch size exceeds 100 or any validation fails

        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
        """
        # Validate batch size (Requirement 10.5)
        if len(minds_data) > 100:
            raise ValueError(f"Batch size {len(minds_data)} exceeds maximum of 100 nodes")

        # Validate all items before creating any (Requirement 10.1)
        validation_errors = []
        for idx, mind_data in enumerate(minds_data):
            # Check mind_type is supported
            if mind_data.mind_type not in self.MIND_TYPE_MAP:
                validation_errors.append(
                    {"index": idx, "error": f"Unsupported mind_type: {mind_data.mind_type}"}
                )
                continue

            # Validate required fields are present (already done by Pydantic)
            # Validate type-specific attributes by attempting to instantiate the model
            model_class = self.MIND_TYPE_MAP[mind_data.mind_type]
            try:
                # Test instantiation with dummy data to validate type-specific attributes
                test_data = {
                    "uuid": uuid4(),
                    "title": mind_data.title,
                    "version": 1,
                    "updated_at": datetime.now(timezone.utc),
                    "creator": mind_data.creator,
                    "description": mind_data.description,
                }
                test_data.update(mind_data.type_specific_attributes)
                model_class(**test_data)
            except Exception as e:
                validation_errors.append(
                    {
                        "index": idx,
                        "error": f"Validation failed for {mind_data.mind_type}: {str(e)}",
                    }
                )

        # If any validation fails, reject entire batch (Requirement 10.2)
        if validation_errors:
            error_details = "; ".join(
                [f"Item {err['index']}: {err['error']}" for err in validation_errors]
            )
            raise ValueError(f"Bulk create validation failed: {error_details}")

        # Create all nodes if validation passes (Requirement 10.3)
        created_nodes = []
        for mind_data in minds_data:
            # Use existing create_mind method for consistency
            created_node = await self.create_mind(mind_data)
            created_nodes.append(created_node)

        # Return complete list of created nodes (Requirement 10.4)
        return created_nodes

    async def bulk_update(self, updates_data: list[MindBulkUpdate]) -> list[MindResponse]:
        """
        Update multiple Mind nodes in a single operation.

        This method validates all items before updating any, ensuring atomicity.
        If any validation fails, the entire batch is rejected. Supports up to
        100 nodes per operation. Uses existing update_mind method to ensure
        version tracking.

        Args:
            updates_data: List of MindBulkUpdate schemas containing update data

        Returns:
            list[MindResponse]: Complete list of updated nodes

        Raises:
            ValueError: If batch size exceeds 100 or any validation fails
            MindNotFoundError: If any UUID does not exist in the database

        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
        """
        # Validate batch size (Requirement 10.5)
        if len(updates_data) > 100:
            raise ValueError(f"Batch size {len(updates_data)} exceeds maximum of 100 nodes")

        # Validate all items before updating any (Requirement 10.1)
        validation_errors = []
        existing_nodes = {}

        for idx, update_data in enumerate(updates_data):
            # Check each UUID exists in database
            try:
                existing_node = await self.get_mind(update_data.uuid)
                existing_nodes[str(update_data.uuid)] = existing_node
            except MindNotFoundError:
                validation_errors.append(
                    {"index": idx, "error": f"UUID {update_data.uuid} not found in database"}
                )
                continue

            # Validate update fields
            # Check that at least one field is being updated
            has_update = any(
                [
                    update_data.title is not None,
                    update_data.description is not None,
                    update_data.status is not None,
                    update_data.type_specific_attributes is not None,
                ]
            )
            if not has_update:
                validation_errors.append(
                    {"index": idx, "error": f"No fields to update for UUID {update_data.uuid}"}
                )
                continue

            # Validate type-specific attributes if provided
            if update_data.type_specific_attributes is not None:
                existing_node = existing_nodes[str(update_data.uuid)]
                model_class = self.MIND_TYPE_MAP.get(existing_node.mind_type)
                if model_class is None:
                    validation_errors.append(
                        {"index": idx, "error": f"Unsupported mind_type: {existing_node.mind_type}"}
                    )
                    continue

                try:
                    # Test instantiation with merged data to validate type-specific attributes
                    merged_attrs = existing_node.type_specific_attributes.copy()
                    merged_attrs.update(update_data.type_specific_attributes)

                    test_data = {
                        "uuid": existing_node.uuid,
                        "title": update_data.title
                        if update_data.title is not None
                        else existing_node.title,
                        "version": existing_node.version + 1,
                        "updated_at": datetime.now(timezone.utc),
                        "creator": existing_node.creator,
                        "status": update_data.status
                        if update_data.status is not None
                        else existing_node.status,
                        "description": update_data.description
                        if update_data.description is not None
                        else existing_node.description,
                    }
                    test_data.update(merged_attrs)
                    model_class(**test_data)
                except Exception as e:
                    validation_errors.append(
                        {"index": idx, "error": f"Validation failed for update: {str(e)}"}
                    )

        # If any validation fails, reject entire batch (Requirement 10.2)
        if validation_errors:
            error_details = "; ".join(
                [f"Item {err['index']}: {err['error']}" for err in validation_errors]
            )
            raise ValueError(f"Bulk update validation failed: {error_details}")

        # Update all nodes if validation passes (Requirement 10.3)
        updated_nodes = []
        for update_data in updates_data:
            # Convert MindBulkUpdate to MindUpdate
            mind_update = MindUpdate(
                title=update_data.title,
                description=update_data.description,
                status=update_data.status,
                type_specific_attributes=update_data.type_specific_attributes,
            )
            # Use existing update_mind method for consistency and version tracking
            updated_node = await self.update_mind(update_data.uuid, mind_update)
            updated_nodes.append(updated_node)

        # Return complete list of updated nodes (Requirement 10.4)
        return updated_nodes
