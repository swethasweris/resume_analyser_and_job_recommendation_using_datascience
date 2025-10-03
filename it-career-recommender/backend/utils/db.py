import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "resume_analyzer")

# Create client and db
_client = AsyncIOMotorClient(MONGO_URI)
db = _client[DB_NAME]

# Collections
users = db["users"]
selections = db["selections"]  # chosen learning paths

async def ensure_indexes():
    await users.create_index("email", unique=True)
    await selections.create_index("user_id")
