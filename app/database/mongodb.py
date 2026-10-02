from pymongo import MongoClient
from app.core.config import settings


client = MongoClient(
    host=settings.mongo_host,
    port=settings.mongo_port,
    username=settings.mongo_username,
    password=settings.mongo_password,
    authSource="admin",
    serverSelectionTimeoutMS=5000
)

database = client[settings.mongo_database]

sessions_collection = database["sessions"]
messages_collection = database["messages"]


def check_mongodb_connection():
    try:
        client.admin.command("ping")
        return True
    except Exception as error:
        print(f"ERRO MONGODB: {error}")
        return False