from fastapi import APIRouter
from services.task_service import TaskService
from schemas.task_schema import TaskCreate

router = APIRouter(prefix="/tasks", tags=["Tasks"])

task_service = TaskService()

@router.post("/")
def create_task(task: TaskCreate, user_id: int):
    return task_service.create_task(task, user_id)

@router.get("/")
def get_tasks():
    return task_service.get_tasks()
