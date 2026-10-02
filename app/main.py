from fastapi import FastAPI

from app.database.mongodb import check_mongodb_connection
from app.routers.chat import router as chat_router


app = FastAPI(
    title="VOLTA Mongo API",
    description="API responsável pelas funcionalidades conversacionais armazenadas no MongoDB.",
    version="1.0.0"
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "service": "VOLTA Mongo API",
        "status": "running"
    }


@app.get("/health")
def health():
    mongo_connected = check_mongodb_connection()

    return {
        "api": "online",
        "mongodb": "connected" if mongo_connected else "disconnected"
    }