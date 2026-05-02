from fastapi import FastAPI
from app.api.routes import router
from app.storage.mysql import mysql_client

app = FastAPI(title="Fitness Recommendation Agent")

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    # Initialize MySQL tables
    try:
        mysql_client.init_tables()
        print("MySQL tables initialized")
    except Exception as e:
        print(f"Warning: MySQL initialization failed: {e}")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)