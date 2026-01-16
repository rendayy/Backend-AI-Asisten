from dotenv import load_dotenv
load_dotenv()  # 🔥 WAJIB, PALING ATAS

import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import assistant as assistant_router
from routes import chat as chat_router
from controllers import ws_controller
from controllers import task_controller

from scheduler.reminder_worker import task_reminder_worker
from controllers.task_controller import task_service
from models.users_model import _ensure_db

print("OPENROUTER_API_KEY loaded:", bool(os.getenv("OPENROUTER_API_KEY")))
print("OPENROUTER_MODEL:", os.getenv("OPENROUTER_MODEL"))

app = FastAPI(title="AI Assistant Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTERS
app.include_router(assistant_router.router)
app.include_router(task_controller.router)
app.include_router(ws_controller.router)
app.include_router(chat_router.router)

@app.get("/")
def root():
    return {"message": "AI Assistant backend is running"}

@app.on_event("startup")
async def start_scheduler():
    print("[STARTUP] Initializing database...")
    _ensure_db()

    print("[STARTUP] Starting reminder scheduler...")
    asyncio.create_task(
        task_reminder_worker(task_service)
    )
