from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    description: Optional[str]
    due_date: datetime

class TaskResponse(TaskCreate):
    id: int
    user_id: int
    is_completed: bool
    is_notified: bool
