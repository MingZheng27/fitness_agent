import logging
import sys
from fastapi import FastAPI
from app.api.routes import router
from app.storage.mysql import mysql_client

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = FastAPI(title="Fitness Recommendation Agent")

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    try:
        mysql_client.init_tables()
        logger.info("MySQL tables initialized successfully")
    except Exception as e:
        logger.error(f"MySQL initialization failed: {e}")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)