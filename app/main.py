from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.config import settings
from app.api.router import router
from app.api.websocket import ws_manager
from app.api.tokens import decode_jwt_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    uploads_path = Path("uploads")
    (uploads_path / "avatars").mkdir(parents=True, exist_ok=True)
    (uploads_path / "company-logos").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Sales API",
    description="API for sales management",
    version="0.1.0",
    debug=settings.DEBUG,
)

uploads_dir = Path("uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None):
    if not token:
        await websocket.close(code=4001)
        return

    try:
        payload = decode_jwt_token(token)
        user_id = payload.user_id
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to Sales API", "version": "0.1.0"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
