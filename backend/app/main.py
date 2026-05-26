import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, get_db
from app.core.seed import seed_initial_data
from app.api.router import api_router
from app.services.websocket import ws_manager, redis_event_listener

# Configure logging style
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Nginx handles routing, but allowing all simplifies container networks
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global background task reference
redis_task = None

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database tables...")
    await init_db()
    
    # Run seed script within an ad-hoc session
    from app.core.database import async_session_maker
    async with async_session_maker() as db:
        await seed_initial_data(db)
        
    # Start Redis Pub/Sub listener in the background
    global redis_task
    redis_task = asyncio.create_task(redis_event_listener())
    logger.info("Application startup lifecycle complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down background tasks...")
    if redis_task:
        redis_task.cancel()
        try:
            await redis_task
        except asyncio.CancelledError:
            pass
    logger.info("Application shutdown complete.")

# Map v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Real-time WebSocket Gateway
@app.route(settings.WS_STR)
@app.websocket(settings.WS_STR)
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open. WebSockets from clients can send pings/pongs
            data = await websocket.receive_text()
            # Simple Echo or message parsing could go here if needed.
            # E.g. Client requests specific OLT metrics sub
            pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        ws_manager.disconnect(websocket)
