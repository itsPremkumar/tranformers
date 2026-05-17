import sys
import io
import asyncio
from fastapi import FastAPI
from app.core.config import settings
from app.routes.robot import router as robot_router
from app.routes.websockets import router as websockets_router
from app.services import check_ollama, proactive_loop, proactive_voice_loop, VOICE_ENABLED

# Force UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = FastAPI(title=settings.PROJECT_NAME)

# Include Routers
app.include_router(robot_router)
app.include_router(websockets_router)

@app.on_event("startup")
async def startup():
    check_ollama()
    asyncio.create_task(proactive_loop())
    if VOICE_ENABLED:
        asyncio.create_task(proactive_voice_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
