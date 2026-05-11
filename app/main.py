import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.storage.mysql import mysql_client

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        mysql_client.init_tables()
        logger.info("MySQL tables initialized successfully")
    except Exception as e:
        logger.error(f"MySQL initialization failed: {e}")
    yield


app = FastAPI(title="Fitness Recommendation Agent", lifespan=lifespan)

# Include API routes
app.include_router(router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def web_app():
    return FileResponse(str(INDEX_FILE))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
