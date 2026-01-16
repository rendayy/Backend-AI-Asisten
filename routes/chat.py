from fastapi import APIRouter, Depends, HTTPException
from controllers.chat_controller import chat_controller
from services.assistant_service import get_current_user
from schemas.schemas import ChatMessage, ChatResponse
from schemas.task_schema import TaskCreate
from controllers.task_controller import task_service
from datetime import datetime

router = APIRouter(prefix="/assistant/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
def chat_route(
    payload: ChatMessage,
    current_user: dict = Depends(get_current_user),
):
    try:
        res = chat_controller(current_user, payload.message)

        # 🔔 JIKA CHAT MEMINTA REMINDER
        if res.get("type") == "create_task":
            task = res["task"]

            task_service.create_task(
                TaskCreate(
                    title=task["title"],
                    description=task["description"],
                    due_date=datetime.fromisoformat(task["due_date"]),
                ),
                user_id=current_user["id"],
            )

            return {
                "reply": res["reply"],
                "action": None,
            }

        # 💬 CHAT BIASA
        return {
            "reply": res.get("reply"),
            "action": res.get("action"),
        }

    except Exception as e:
        print("[CHAT ERROR]", e)
        raise HTTPException(status_code=500, detail="chat_handler_error")
