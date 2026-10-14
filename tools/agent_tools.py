
from langchain.tools import tool

from tools.task_tools import (
    create_task as save_task,
    list_tasks as fetch_tasks,
    complete_task as finish_task,
)


@tool
def create_productivity_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    deadline: str = "",
) -> str:
    """Create and save a task. Use priority low, medium, or high.
    Use deadline format YYYY-MM-DD, or leave it empty if unknown."""
    return save_task(
        title=title,
        description=description,
        priority=priority,
        deadline=deadline or None,
    )


@tool
def list_productivity_tasks(
    status: str = "",
    priority: str = "",
) -> str:
    """List saved tasks. Optionally filter by status
    (pending or completed) and priority (low, medium, high)."""
    return fetch_tasks(
        status=status or None,
        priority=priority or None,
    )


@tool
def complete_productivity_task(task_id: int) -> str:
    """Mark a pending task as completed using its numeric task ID."""
    return finish_task(task_id)


PRODUCTIVITY_TOOLS = [
    create_productivity_task,
    list_productivity_tasks,
    complete_productivity_task,
]
