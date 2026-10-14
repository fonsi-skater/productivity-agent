
import sqlite3
from pathlib import Path
from datetime import datetime

# Locate the project's data folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "tasks.db"


def get_connection():
    """Open a connection to the task database."""
    return sqlite3.connect(DATABASE_PATH)


def initialize_database():
    """Create the tasks table if it does not exist."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'medium',
                deadline TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)


def create_task(title, description="", priority="medium", deadline=None):
    """Save a new task and return its database ID."""
    allowed_priorities = {"low", "medium", "high"}

    title = title.strip()
    priority = priority.lower().strip()

    if not title:
        return "Error: Task title cannot be empty."

    if priority not in allowed_priorities:
        return "Error: Priority must be low, medium, or high."

    if deadline:
        try:
            datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            return "Error: Deadline must use YYYY-MM-DD format."

    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tasks
                (title, description, priority, deadline, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                priority,
                deadline,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        task_id = cursor.lastrowid

    return f"Task created successfully. Task ID: {task_id}"


def list_tasks(status=None, priority=None):
    """List saved tasks, optionally filtering by status or priority."""
    valid_statuses = {"pending", "completed"}
    valid_priorities = {"low", "medium", "high"}

    if status and status not in valid_statuses:
        return "Error: Status must be pending or completed."

    if priority and priority not in valid_priorities:
        return "Error: Priority must be low, medium, or high."

    initialize_database()

    query = """
        SELECT id, title, description, priority, deadline, status
        FROM tasks
        WHERE 1 = 1
    """
    parameters = []

    if status:
        query += " AND status = ?"
        parameters.append(status)

    if priority:
        query += " AND priority = ?"
        parameters.append(priority)

    query += " ORDER BY id"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    if not rows:
        return "No tasks found."

    return "\n".join(
        f"ID: {row[0]} | Title: {row[1]} | "
        f"Priority: {row[3]} | Deadline: {row[4] or 'None'} | "
        f"Status: {row[5]} | Description: {row[2]}"
        for row in rows
    )

def complete_task(task_id):
    """Mark an existing pending task as completed."""
    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE tasks
            SET status = 'completed'
            WHERE id = ? AND status = 'pending'
            """,
            (task_id,),
        )

        if cursor.rowcount == 0:
            existing = connection.execute(
                "SELECT status FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()

            if existing is None:
                return f"Error: Task {task_id} was not found."

            if existing[0] == "completed":
                return f"Task {task_id} is already completed."

        return f"Task {task_id} marked as completed."



