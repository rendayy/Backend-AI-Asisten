import asyncio
from datetime import datetime
from utils.ws_manager import manager

async def task_reminder_worker(task_service):
    print("[SCHEDULER] Reminder worker started")

    while True:
        tasks = task_service.check_overdue_tasks()
        print(f"[SCHEDULER] found {len(tasks)} overdue tasks")

        for task in tasks:
            await manager.send_to_user(
                task["user_id"],
                {
                    "type": "reminder",
                    "title": task["title"],
                    "description": task["description"],
                    "due_date": datetime.fromtimestamp(
                        task["due_date"]
                    ).isoformat()
                }
            )

            print("[SCHEDULER] reminder sent to", task["user_id"])

        await asyncio.sleep(5)
