"""
Scheduler Service with Critical Path Method (CPM) algorithm.

This module implements task scheduling using the Critical Path Method algorithm,
supporting multiple schedule versions and proper version tracking via SCHEDULED
relationships between INPUT and SCHEDULED layer nodes.

Enhanced with:
- Recursive CONTAINS traversal for nested project structures
- DFS-based cycle detection on PREDATES dependency graph
- HAS_SCHEDULED relationship creation from Project to ScheduleHistory
- Resource-based cost calculation via ASSIGNED_TO relationships
- Computed aggregates on ScheduleHistory (global_start, global_end, total_effort, total_cost)
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from neontology import GraphConnection
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ScheduleResult:
    """Schedule result status codes."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class SchedulerService:
    """
    Service class for scheduling Mind nodes using CPM algorithm.
    """

    def __init__(
        self,
        business_hours_start: int = 8,
        business_hours_end: int = 17,
        working_days: list[int] | None = None,
        holidays: list[datetime] | None = None,
    ):
        self.business_hours_start = business_hours_start
        self.business_hours_end = business_hours_end
        self.working_days = working_days or [0, 1, 2, 3, 4]
        self.holidays = holidays or []
        self.scheduled_tasks: dict[str, dict] = {}
        self.critical_path: list[str] = []

    async def schedule_project(
        self,
        project_uuid: str,
        version: int | None = None,
        comments: str | None = None,
    ) -> ScheduleResult | dict:
        """
        Create a new schedule version for a Project Mind node.

        Returns ScheduleResult.SUCCESS on success, or a dict with error details
        on failure (cycle detection, missing project, etc.).
        """
        project = await self._get_project_node(project_uuid)
        if not project:
            return {"status": ScheduleResult.ERROR, "error": "Project not found", "uuid": project_uuid}

        start_date = getattr(project, "start_date", datetime.now(timezone.utc))
        end_date = getattr(project, "end_date", None)

        # Convert date objects to datetime for scheduling calculations
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_date = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc)

        if not end_date:
            end_date = start_date + timedelta(days=365)

        # Task 3.1: Recursive CONTAINS traversal
        task_nodes = await self._get_project_tasks_recursive(project_uuid)
        if not task_nodes:
            return {"status": ScheduleResult.ERROR, "error": "Project has no tasks to schedule"}

        # Build task graph for cycle detection and topological sort
        task_graph = await self._build_task_graph(task_nodes)

        # Task 3.2: Cycle detection before scheduling
        cycle = await self._detect_cycles(task_graph)
        if cycle is not None:
            return {
                "status": ScheduleResult.ERROR,
                "error": "Cyclic dependency detected",
                "cycle": cycle,
            }

        # Task 3.3: Auto-increment version
        version_num = version or await self._get_next_version_number(project_uuid)
        schedule_id = f"{project_uuid}_v{version_num}"

        from ..models.mind_types import ScheduleHistory
        from ..models.enums import StatusEnum

        history_node = ScheduleHistory(
            title=f"Schedule {version_num} for {project.title}",
            description=comments,
            status=StatusEnum.DONE,
            schedule_id=schedule_id,
            scheduled_at=datetime.now(timezone.utc),
            version=version_num,
            creator=project.creator,
        )
        history_node.create()

        # Task 3.3: Create HAS_SCHEDULED relationship
        await self._create_has_scheduled_relationship(project, history_node)

        sorted_tasks = self._topological_sort(task_graph)
        if not sorted_tasks:
            return {"status": ScheduleResult.ERROR, "error": "Failed to sort task graph"}

        await self._calculate_earliest_dates(sorted_tasks, start_date)
        await self._calculate_latest_dates(sorted_tasks, end_date)
        self.critical_path = await self._identify_critical_path(sorted_tasks)
        await self._calculate_slack(sorted_tasks)

        from ..models.mind_types import ScheduledTask
        from ..models.mind import Scheduled

        total_cost = 0.0

        for task_data in sorted_tasks:
            input_task = task_data["task"]

            # Task 3.4: Resource-based cost calculation
            duration = self.scheduled_tasks[str(input_task.uuid)].get("scheduled_duration", 1)
            base_cost, variable_cost = await self._calculate_resource_costs(input_task, duration)
            task_total_cost = base_cost + variable_cost
            total_cost += task_total_cost

            self.scheduled_tasks[str(input_task.uuid)]["base_cost"] = base_cost
            self.scheduled_tasks[str(input_task.uuid)]["variable_cost"] = variable_cost
            self.scheduled_tasks[str(input_task.uuid)]["total_cost"] = task_total_cost

            scheduled_task = await self._create_scheduled_task(
                task_data=task_data,
                schedule_history=history_node,
                source_task=input_task,
            )

            scheduled_rel = Scheduled(
                source=input_task,
                target=scheduled_task,
                version=version_num,
                scheduled_at=datetime.now(timezone.utc),
            )
            scheduled_rel.merge()

        # Task 3.5: Computed aggregates on ScheduleHistory
        history_node.total_effort = sum(
            t.get("scheduled_duration", 0) for t in self.scheduled_tasks.values()
        )
        history_node.total_cost = total_cost

        all_starts = [t.get("scheduled_start") for t in self.scheduled_tasks.values() if t.get("scheduled_start")]
        all_ends = [t.get("scheduled_end") for t in self.scheduled_tasks.values() if t.get("scheduled_end")]

        history_node.global_start = min(all_starts) if all_starts else None
        history_node.global_end = max(all_ends) if all_ends else None

        history_node.merge()

        return ScheduleResult.SUCCESS

    async def _get_project_node(self, project_uuid: str):
        """Get Project node by UUID."""
        from ..models.mind_types import Project

        try:
            project = Project.match(project_uuid)
            if project:
                return project

            gc = GraphConnection()
            cypher = "MATCH (p:Project {uuid: $uuid}) RETURN p ORDER BY p.version DESC LIMIT 1"
            results = gc.engine.evaluate_query(cypher, {"uuid": project_uuid})

            if results and results.records_raw:
                record = results.records_raw[0]
                return Project(**dict(record["p"]))

        except Exception as e:
            logger.warning(
                "Failed to retrieve Project node %s: %s",
                project_uuid,
                e,
            )

        return None

    async def _get_project_tasks_recursive(self, project_uuid: str) -> list:
        """Get all Task nodes contained in a project via recursive CONTAINS traversal.

        Uses variable-length path to find tasks nested under Phases and Work Packages
        at arbitrary depth. Tasks without explicit duration or effort default to 1 day.

        Args:
            project_uuid: UUID of the project to query.

        Returns:
            List of Task model instances found in the project hierarchy.
        """
        gc = GraphConnection()

        cypher = """
        MATCH (p {uuid: $project_uuid})-[:CONTAINS*]->(t:Task)
        RETURN DISTINCT t
        """

        results = gc.engine.evaluate_query(cypher, {"project_uuid": project_uuid})
        tasks = []

        if results and results.records_raw:
            for record in results.records_raw:
                try:
                    task_data = dict(record["t"])
                except (KeyError, TypeError):
                    continue

                for key, value in task_data.items():
                    if hasattr(value, "to_native"):
                        task_data[key] = value.to_native()

                from ..models.mind_types import Task

                try:
                    task = Task(**task_data)
                    tasks.append(task)
                except ValidationError as e:
                    task_uuid = task_data.get("uuid", "<unknown>")
                    for error in e.errors():
                        field = ".".join(str(loc) for loc in error.get("loc", ()))
                        value = error.get("input", "<unavailable>")
                        constraint = error.get("type", "<unknown>")
                        logger.warning(
                            "Skipped Task node %s: %s = %s violated %s",
                            task_uuid,
                            field or "<unavailable>",
                            value,
                            constraint,
                        )
                    continue

        return tasks

    async def _build_task_graph(self, tasks: list) -> dict:
        """Build dependency graph from tasks and their PREDATES relationships.

        Args:
            tasks: List of Task model instances.

        Returns:
            Dict mapping task UUID to graph node data including predecessors/successors.
        """
        task_graph: dict[str, dict] = {}

        for task in tasks:
            task_id = str(task.uuid)
            predecessors = []

            gc = GraphConnection()
            pred_cypher = """
            MATCH (t {uuid: $task_uuid})<-[:PREDATES]-(pred:Task)
            RETURN DISTINCT pred.uuid as uuid
            """

            pred_results = gc.engine.evaluate_query(pred_cypher, {"task_uuid": task_id})

            if pred_results and pred_results.records_raw:
                for record in pred_results.records_raw:
                    predecessors.append(str(record["uuid"]))

            task_graph[task_id] = {
                "task": task,
                "predecessors": predecessors,
                "successors": [],
                "earliest_start": None,
                "earliest_end": None,
                "latest_start": None,
                "latest_end": None,
            }

        # Build successor lists
        for tid, data in task_graph.items():
            for pred_id in data["predecessors"]:
                if pred_id in task_graph:
                    task_graph[pred_id]["successors"].append(tid)

        return task_graph

    async def _detect_cycles(self, task_graph: dict) -> list[str] | None:
        """Detect cycles in the task dependency graph using DFS.

        Args:
            task_graph: Dict mapping task UUID to graph node data.

        Returns:
            List of task UUIDs forming the cycle if found, None otherwise.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {tid: WHITE for tid in task_graph}
        parent: dict[str, str | None] = {tid: None for tid in task_graph}

        def dfs(node: str) -> list[str] | None:
            color[node] = GRAY
            for successor in task_graph[node]["successors"]:
                if successor not in color:
                    continue
                if color[successor] == GRAY:
                    # Found a cycle — reconstruct path
                    cycle = [successor]
                    current = node
                    while current != successor:
                        cycle.append(current)
                        current = parent.get(current, successor)
                    cycle.append(successor)
                    cycle.reverse()
                    return cycle
                if color[successor] == WHITE:
                    parent[successor] = node
                    result = dfs(successor)
                    if result is not None:
                        return result
            color[node] = BLACK
            return None

        for tid in task_graph:
            if color[tid] == WHITE:
                result = dfs(tid)
                if result is not None:
                    return result

        return None

    def _topological_sort(self, task_graph: dict) -> list[dict]:
        """Topologically sort tasks using Kahn's algorithm.

        Args:
            task_graph: Dict mapping task UUID to graph node data.

        Returns:
            List of task graph node dicts in topological order.
        """
        in_degree = {
            tid: len([p for p in data["predecessors"] if p in task_graph])
            for tid, data in task_graph.items()
        }
        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        sorted_tasks = []

        while queue:
            current_id = queue.pop(0)
            if current_id not in task_graph:
                continue

            sorted_tasks.append(task_graph[current_id])

            for successor_id in task_graph[current_id]["successors"]:
                if successor_id in in_degree:
                    in_degree[successor_id] -= 1
                    if in_degree[successor_id] == 0:
                        queue.append(successor_id)

        return sorted_tasks

    async def _get_next_version_number(self, project_uuid: str) -> int:
        """Get the next version number for a project's schedule.

        Queries existing HAS_SCHEDULED relationships to determine the max version.

        Args:
            project_uuid: UUID of the project.

        Returns:
            Next version number (max existing + 1, or 1 if none exist).
        """
        gc = GraphConnection()

        cypher = """
        MATCH (p {uuid: $project_uuid})-[:HAS_SCHEDULED]->(h:ScheduleHistory)
        WITH MAX(h.version) as max_version
        RETURN COALESCE(max_version, 0) + 1 as next_version
        """

        results = gc.engine.evaluate_query(cypher, {"project_uuid": project_uuid})

        if results and results.records_raw:
            return results.records_raw[0].get("next_version", 1)

        return 1

    async def _create_has_scheduled_relationship(self, project, history_node) -> None:
        """Create HAS_SCHEDULED relationship from Project to ScheduleHistory.

        Args:
            project: The Project node.
            history_node: The ScheduleHistory node.
        """
        from ..models.mind import HasScheduled

        has_scheduled = HasScheduled(
            source=project,
            target=history_node,
        )
        has_scheduled.merge()

    async def _calculate_resource_costs(self, task, duration: float) -> tuple[float, float]:
        """Calculate resource-based costs for a task with inheritance.

        Queries ASSIGNED_TO relationships to Resources, including inherited
        assignments from parent nodes (WorkPackage, Phase, Project) via the
        CONTAINS hierarchy. Direct assignments to the task take precedence,
        but if none exist, resources are inherited from ancestors.

        Args:
            task: The Task node.
            duration: Scheduled duration in days.

        Returns:
            Tuple of (base_cost, variable_cost).
        """
        gc = GraphConnection()

        # Query for resources assigned directly to this task OR inherited from
        # ancestors via CONTAINS hierarchy. Uses variable-length path to walk
        # up the hierarchy and find all ASSIGNED_TO relationships.
        cypher = """
        // First try direct assignments to the task
        OPTIONAL MATCH (r:Resource)-[a:ASSIGNED_TO]->(t {uuid: $task_uuid})
        WITH collect({hourly_rate: r.hourly_rate, effort_allocation: a.effort_allocation, direct: true}) as direct_assignments

        // Then find inherited assignments from ancestors via CONTAINS
        OPTIONAL MATCH (ancestor)-[:CONTAINS*]->(t {uuid: $task_uuid})
        WHERE ancestor:Project OR ancestor:Task
        OPTIONAL MATCH (r2:Resource)-[a2:ASSIGNED_TO]->(ancestor)
        WITH direct_assignments, collect({hourly_rate: r2.hourly_rate, effort_allocation: a2.effort_allocation, direct: false}) as inherited_assignments

        // Combine: use direct if any exist, otherwise use inherited
        WITH direct_assignments, inherited_assignments,
             [x IN direct_assignments WHERE x.hourly_rate IS NOT NULL] as valid_direct
        RETURN CASE WHEN size(valid_direct) > 0 THEN valid_direct
                    ELSE [x IN inherited_assignments WHERE x.hourly_rate IS NOT NULL]
               END as assignments
        """

        results = gc.engine.evaluate_query(cypher, {"task_uuid": str(task.uuid)})

        base_cost = 0.0
        if results and results.records_raw:
            assignments = results.records_raw[0].get("assignments") or []
            for assignment in assignments:
                hourly_rate = assignment.get("hourly_rate") or 0.0
                effort_allocation = assignment.get("effort_allocation") or 0.0
                # duration in days * 8 hours/day * hourly_rate * effort_allocation
                base_cost += duration * 8 * float(hourly_rate) * float(effort_allocation)

        # variable_cost could be extended later (e.g., overtime, materials)
        variable_cost = 0.0

        return base_cost, variable_cost

    async def _calculate_earliest_dates(self, sorted_tasks: list, start_date: datetime):
        """Forward pass — calculate earliest start/end dates for all tasks.

        Args:
            sorted_tasks: Topologically sorted list of task graph node dicts.
            start_date: Project start date.
        """
        for task_data in sorted_tasks:
            task = task_data["task"]

            task_start = getattr(task, "start", None)

            if task_start and isinstance(task_start, datetime):
                earliest_start = self._normalize_date(task_start)
            else:
                earliest_start = start_date

                for pred_id in task_data["predecessors"]:
                    if pred_id in self.scheduled_tasks:
                        pred_end = self.scheduled_tasks[pred_id]["scheduled_end"]
                        earliest_start = max(earliest_start, pred_end)

                earliest_start = self._adjust_for_holidays(earliest_start)

            # Default duration: 1 business day for tasks without explicit duration or effort
            # Milestones have 0 duration (they're points in time, not work items)
            duration_days = 1
            
            task_type = getattr(task, "task_type", None)
            if task_type and getattr(task_type, "value", str(task_type)).upper() == "MILESTONE":
                duration_days = 0
            elif hasattr(task, "length") and task.length:
                duration_days = task.length
            elif hasattr(task, "effort") and task.effort:
                duration_days = task.effort / 8  # Convert hours to days

            task_data["earliest_start"] = earliest_start
            task_data["earliest_end"] = earliest_start + timedelta(days=duration_days)

            self.scheduled_tasks[str(task.uuid)] = {
                "scheduled_start": earliest_start,
                "scheduled_end": earliest_start + timedelta(days=duration_days),
                "scheduled_duration": duration_days,
                "is_critical": False,
            }

    async def _calculate_latest_dates(self, sorted_tasks: list, project_end: datetime):
        """Backward pass — calculate latest start/end dates for all tasks.

        Args:
            sorted_tasks: Topologically sorted list of task graph node dicts.
            project_end: Project end date.
        """
        for task_data in reversed(sorted_tasks):
            task_id = str(task_data["task"].uuid)

            if not task_data["successors"]:
                latest_end = self._normalize_date(project_end)
            else:
                successors_with_dates = [
                    s for s in task_data["successors"]
                    if s in self.scheduled_tasks
                ]
                latest_end = min(
                    self.scheduled_tasks[succ_id]["scheduled_start"]
                    for succ_id in successors_with_dates
                ) if successors_with_dates else project_end

            duration_days = self.scheduled_tasks[task_id].get("scheduled_duration", 1)

            task_data["latest_start"] = max(
                task_data["earliest_start"],
                latest_end - timedelta(days=duration_days)
            )
            task_data["latest_end"] = latest_end

    async def _identify_critical_path(self, sorted_tasks: list) -> list[str]:
        """Identify tasks on the critical path (zero slack).

        Args:
            sorted_tasks: Topologically sorted list of task graph node dicts.

        Returns:
            List of task UUIDs on the critical path.
        """
        critical_path = []

        for task_data in sorted_tasks:
            slack_start = (
                task_data["latest_start"] - task_data["earliest_start"]
            )

            is_critical = abs(slack_start.total_seconds()) < 60
            task_data["is_critical"] = is_critical
            task_data["slack_start"] = slack_start

            if is_critical:
                critical_path.append(str(task_data["task"].uuid))

        return critical_path

    async def _calculate_slack(self, sorted_tasks: list):
        """Calculate slack times for all tasks.

        Args:
            sorted_tasks: Topologically sorted list of task graph node dicts.
        """
        for task_data in sorted_tasks:
            self.scheduled_tasks[str(task_data["task"].uuid)]["slack_end"] = (
                task_data["latest_end"] - task_data["earliest_end"]
            )

    async def _create_scheduled_task(self, task_data: dict, schedule_history, source_task):
        """Create a ScheduledTask node with cost data.

        Args:
            task_data: Graph node dict with computed schedule data.
            schedule_history: The ScheduleHistory node for this schedule run.
            source_task: The source Task node.

        Returns:
            The created ScheduledTask node.
        """
        from ..models.mind_types import ScheduledTask
        from ..models.enums import StatusEnum

        task_id = str(source_task.uuid)
        scheduled_start = task_data.get("scheduled_start", task_data["earliest_start"])
        scheduled_end = task_data.get("scheduled_end", task_data["earliest_end"])

        # Convert timedelta slack values to float days
        slack_start_td = task_data.get("slack_start", timedelta(0))
        slack_end_td = self.scheduled_tasks[task_id].get("slack_end", timedelta(0))
        slack_start_days = slack_start_td.total_seconds() / 86400 if isinstance(slack_start_td, timedelta) else float(slack_start_td or 0)
        slack_end_days = slack_end_td.total_seconds() / 86400 if isinstance(slack_end_td, timedelta) else float(slack_end_td or 0)

        scheduled_task = ScheduledTask(
            title=f"Scheduled: {source_task.title}",
            description="Computed schedule state",
            creator=source_task.creator,
            status=StatusEnum.DONE,
            source_task_uuid=source_task.uuid,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            scheduled_duration=self.scheduled_tasks[task_id].get("scheduled_duration"),
            is_critical=task_data.get("is_critical", False),
            slack_start=slack_start_days,
            slack_end=slack_end_days,
            base_cost=self.scheduled_tasks[task_id].get("base_cost", 0.0),
            variable_cost=self.scheduled_tasks[task_id].get("variable_cost", 0.0),
            total_cost=self.scheduled_tasks[task_id].get("total_cost", 0.0),
        )
        scheduled_task.create()

        return scheduled_task

    def _normalize_date(self, date: datetime) -> datetime:
        """Normalize to business hours start.

        Args:
            date: Date to normalize.

        Returns:
            Date normalized to business hours start time.
        """
        return datetime(
            date.year, date.month, date.day,
            self.business_hours_start, 0, 0,
            tzinfo=date.tzinfo or timezone.utc
        )

    def _adjust_for_holidays(self, date: datetime) -> datetime:
        """Adjust date to skip holidays and weekends.

        Args:
            date: Date to adjust.

        Returns:
            Next valid business day.
        """
        while (
            date.weekday() not in self.working_days
            or date.date() in [h.date() for h in self.holidays]
        ):
            date += timedelta(days=1)

        return self._normalize_date(date)


async def schedule_project(
    project_uuid: str,
    version: int | None = None,
    comments: str | None = None,
) -> ScheduleResult | dict:
    """Convenience function to schedule a project.

    Args:
        project_uuid: UUID of the project to schedule.
        version: Optional explicit version number.
        comments: Optional schedule run comments.

    Returns:
        ScheduleResult.SUCCESS or dict with error details.
    """
    scheduler = SchedulerService()
    return await scheduler.schedule_project(project_uuid, version, comments)
