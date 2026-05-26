import logging
import asyncio
import json
import redis.asyncio as aioredis
from typing import List, Dict, Any
from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections and handles broadcasting."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON message to all connected browsers."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
                
        for connection in disconnected:
            self.disconnect(connection)


ws_manager = ConnectionManager()


async def redis_event_listener():
    """Background listener that subscribes to Redis Pub/Sub and broadcasts to WebSockets."""
    logger.info("Initializing Redis Pub/Sub WebSockets Listener...")
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("noc_events")
        
        while True:
            try:
                # Read message with a short timeout
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    # Broadcast the notification/alert to all NOC screens
                    await ws_manager.broadcast(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Redis subscriber loop: {str(e)}")
                await asyncio.sleep(2)
    except Exception as e:
        logger.critical(f"Failed to connect to Redis Pub/Sub: {str(e)}")
