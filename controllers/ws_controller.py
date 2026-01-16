from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils.ws_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    ws://localhost:8000/ws?user_id=1
    """
    await manager.connect(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(user_id)
