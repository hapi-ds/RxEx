"""
API routes for schedule operations with TaskJuggler integration.

This module defines REST API endpoints for:
- Creating new schedule versions for projects
- Retrieving schedule history
- Querying critical path and scheduled tasks
"""

from typing import Optional

from fastapi import APIRouter, Query, status

from ..schemas.mind_generic import MindResponse
from ..services.scheduler_service import SchedulerService, ScheduleResult, schedule_project

router = APIRouter(prefix="/api/v1/schedules", tags=["scheduling"])


@router.post(
    "/project/{project_uuid}",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    project_uuid: str,
    version: Optional[int] = Query(None, ge=1),
    comments: Optional[str] = Query(None, max_length=500),
):
    """
    Create a new schedule version for a Project Mind node.

    This endpoint runs the Critical Path Method (CPM) algorithm to calculate
    task schedules and creates ScheduleHistory and ScheduledTask nodes linked
    via SCHEDULED relationships.

    **Parameters:**
        - project_uuid: UUID of the Project to schedule
        - version: Optional version number (auto-incremented if not provided)
        - comments: Optional notes about this schedule run

    **Returns:**
        Schedule result with status and metadata
    """
    result = await schedule_project(project_uuid, version, comments)

    return {
        "success": result == ScheduleResult.SUCCESS,
        "status": result,
        "message": f"Schedule version {version or 'auto'} created successfully",
    }


@router.get(
    "/project/{project_uuid}/history",
    response_model=list[MindResponse],
)
async def get_schedule_history(project_uuid: str):
    """
    Get schedule history for a project.

    Retrieves all ScheduleHistory nodes associated with this project,
    showing all versions and their timestamps.
    """
    from neontology import GraphConnection

    gc = GraphConnection()

    cypher = """
    MATCH (p {uuid: $project_uuid})-[:HAS_SCHEDULED]->(h:ScheduleHistory)
    RETURN h ORDER BY h.version DESC
    """

    results = gc.engine.evaluate_query(cypher, {"project_uuid": project_uuid})
    schedules = []

    if results and results.records_raw:
        for record in results.records_raw:
            schedule_data = dict(record["h"])
            # Convert Neo4j datetime objects
            for key, value in schedule_data.items():
                if hasattr(value, "to_native"):
                    schedule_data[key] = value.to_native()

            schedules.append(schedule_data)

    return schedules


@router.get(
    "/project/{project_uuid}/critical-path",
    response_model=list[MindResponse],
)
async def get_critical_path(project_uuid: str, version: Optional[int] = Query(None)):
    """
    Get critical path tasks for a specific schedule version.

    Returns tasks that have zero slack (cannot be delayed without affecting
    the project completion date).
    """
    from neontology import GraphConnection

    gc = GraphConnection()

    cypher = """
    MATCH (p {uuid: $project_uuid})-[:HAS_SCHEDULED]->(h:ScheduleHistory)
    WHERE h.version = COALESCE($version, h.version)
    WITH h ORDER BY h.version DESC LIMIT 1
    MATCH (h)-[:SCHEDULED]->(t:ScheduledTask {is_critical: true})
    RETURN t ORDER BY t.scheduled_start
    """

    params = {"project_uuid": project_uuid}
    if version:
        params["version"] = version

    results = gc.engine.evaluate_query(cypher, params)
    tasks = []

    if results and results.records_raw:
        for record in results.records_raw:
            task_data = dict(record["t"])
            # Convert Neo4j datetime objects
            for key, value in task_data.items():
                if hasattr(value, "to_native"):
                    task_data[key] = value.to_native()

            tasks.append(task_data)

    return tasks


@router.post(
    "/project/{project_uuid}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_schedule(project_uuid: str):
    """
    Cancel a schedule run (not yet implemented).

    This endpoint would allow marking a schedule as cancelled or incomplete.
    """
    # TODO: Implement schedule cancellation logic
    return None


@router.get(
    "/project/{project_uuid}/versions",
    response_model=dict,
)
async def get_available_versions(project_uuid: str):
    """
    Get list of available schedule versions for a project.

    Returns metadata about each version including timestamp and status.
    """
    from neontology import GraphConnection

    gc = GraphConnection()

    cypher = """
    MATCH (p {uuid: $project_uuid})-[:HAS_SCHEDULED]->(h:ScheduleHistory)
    RETURN h ORDER BY h.version ASC
    """

    results = gc.engine.evaluate_query(cypher, {"project_uuid": project_uuid})
    versions = []

    if results and results.records_raw:
        for record in results.records_raw:
            schedule_data = dict(record["h"])
            # Convert Neo4j datetime objects
            for key, value in schedule_data.items():
                if hasattr(value, "to_native"):
                    schedule_data[key] = value.to_native()

            versions.append(schedule_data)

    return {
        "project_uuid": project_uuid,
        "total_versions": len(versions),
        "versions": versions,
    }
