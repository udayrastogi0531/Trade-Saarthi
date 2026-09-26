"""WebSocket gateway — real-time copilot, alerts, signal feed."""

import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.core.logging import get_logger
from backend.app.core.metrics import COPILOT_WS_CONNECTIONS, WS_HEARTBEATS
from backend.app.db.session import AsyncSessionLocal
from backend.app.modules.copilot.engine import CopilotEngine

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
  def __init__(self) -> None:
    self.active: dict[str, WebSocket] = {}

  async def connect(self, ws: WebSocket, client_id: str) -> None:
    await ws.accept()
    self.active[client_id] = ws
    COPILOT_WS_CONNECTIONS.inc()

  def disconnect(self, client_id: str) -> None:
    self.active.pop(client_id, None)

  async def send_json(self, client_id: str, data: dict) -> None:
    ws = self.active.get(client_id)
    if ws:
      await ws.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/copilot")
async def copilot_websocket(websocket: WebSocket):
  """
  WebSocket protocol (JSON messages):
  - Client → {"type":"chat","message":"...","session_id":"...","language":"hinglish"}
  - Server → {"type":"token","content":"..."} ... {"type":"done","content":"..."}
  - Client → {"type":"ping"}
  - Server → {"type":"pong"}
  - Server → {"type":"alert","message":"...","alert_type":"signal"}
  """
  client_id = str(uuid.uuid4())
  await manager.connect(websocket, client_id)
  logger.info("ws_connected", client_id=client_id)

  try:
    while True:
      try:
        raw = await websocket.receive_text()
      except WebSocketDisconnect:
        raise

      try:
        data = json.loads(raw)
      except json.JSONDecodeError:
        try:
          await websocket.send_json({"type": "error", "message": "Invalid JSON"})
        except Exception:
          pass
        continue

      msg_type = data.get("type", "chat")

      if msg_type == "ping":
        WS_HEARTBEATS.inc()
        try:
          await websocket.send_json({"type": "pong"})
        except Exception:
          break
        continue

      if msg_type == "chat":
        message = data.get("message", "").strip()
        if not message:
          await websocket.send_json({"type": "error", "message": "Empty message"})
          continue

        session_id = data.get("session_id")
        language = data.get("language", "hinglish")
        account_id = data.get("account_id", 1)

        engine = CopilotEngine()
        async with AsyncSessionLocal() as db:
          try:
            async for chunk in engine.stream_chat(
              db, message, session_id, language, account_id
            ):
              parsed = json.loads(chunk.strip())
              await websocket.send_json(parsed)
            await db.commit()
          except Exception as exc:
            await db.rollback()
            try:
              await websocket.send_json({"type": "error", "message": str(exc)})
            except Exception:
              break

  except WebSocketDisconnect:
    logger.info("ws_disconnected", client_id=client_id)
  except Exception as exc:
    logger.warning("ws_session_error", client_id=client_id, error=str(exc))
  finally:
    manager.disconnect(client_id)


async def broadcast_alert(message: str, alert_type: str = "system") -> None:
  """Push alert to all connected copilot clients."""
  payload = {"type": "alert", "message": message, "alert_type": alert_type}
  for client_id in list(manager.active.keys()):
    try:
      await manager.send_json(client_id, payload)
    except Exception:
      manager.disconnect(client_id)
