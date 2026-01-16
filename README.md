# AI Assistant — Backend / Frontend split

This repository contains a simple split between a FastAPI backend and a minimal frontend demo for your AI assistant prototype.

How it's organized:
- `backend/` — Python FastAPI backend with routes, controllers, services and schemas.
- `frontend/` — Flutter with providers, screens and services.

Run backend (from project root):

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open the frontend at `http://127.0.0.1:8000/frontend/index.html` (or serve the file with simple HTTP server).
