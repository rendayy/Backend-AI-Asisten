from services.chat_service import handle_chat
from services.task_service import TaskService
from schemas.task_schema import TaskCreate

task_service = TaskService()

def chat_controller(current_user, message: str):
    result = handle_chat(current_user, message)

    # 🔥 JIKA CHAT MENGHASILKAN TASK
    if result.get("type") == "create_task":
        task_data = result["task"]

        task = TaskCreate(
            title=task_data["title"],
            description=task_data["description"],
            due_date=task_data["due_date"]
        )

        task_service.create_task(task, current_user["id"])

        return {
            "reply": result["reply"]
        }

    # 🔥 CHAT NORMAL / AI
    return result
