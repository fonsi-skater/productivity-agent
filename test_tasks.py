
from tools.task_tools import complete_task, list_tasks

print(complete_task(1))

print("\nALL TASKS")
print(list_tasks())

print("\nPENDING TASKS")
print(list_tasks(status="pending"))

print("\nCOMPLETED TASKS")
print(list_tasks(status="completed"))
