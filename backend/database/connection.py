"""
Async MongoDB connection using Motor.
Collections are lazily accessed — no explicit table creation needed.
Falls back gracefully if MongoDB is unavailable (uses in-memory store).
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import get_settings
from utils.logger import setup_logger

log = setup_logger("database")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None

# ── In-memory fallback for development without MongoDB ──
_memory_store: dict[str, list[dict]] = {
    "resumes": [],
    "profiles": [],
    "jobs": [],
    "matches": [],
}


class MemoryCollection:
    """Minimal MongoDB-like interface backed by a list (dev fallback)."""

    def __init__(self, name: str):
        self.name = name
        if name not in _memory_store:
            _memory_store[name] = []

    async def insert_one(self, doc: dict):
        _memory_store[self.name].append(doc)

        class Result:
            inserted_id = doc.get("_id", str(len(_memory_store[self.name])))
        return Result()

    async def find_one(self, query: dict):
        for doc in _memory_store[self.name]:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def find(self, query: dict = None):
        """
        Returns a cursor synchronously — matches Motor's API.
        Motor's find() is NOT a coroutine; it returns an AsyncIOMotorCursor.
        Do NOT await this. Use cursor.to_list() instead.
        """
        filtered = list(_memory_store.get(self.name, []))
        if query:
            filtered = [
                d for d in filtered
                if all(d.get(k) == v for k, v in query.items())
            ]
        return MemoryCursor(filtered)

    async def update_one(self, query: dict, update: dict):
        for doc in _memory_store[self.name]:
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                return

    async def delete_one(self, query: dict):
        store = _memory_store[self.name]
        _memory_store[self.name] = [
            d for d in store
            if not all(d.get(k) == v for k, v in query.items())
        ]


class MemoryCursor:
    """Mimics AsyncIOMotorCursor — chainable, with async to_list()."""

    def __init__(self, docs: list):
        self._docs = docs

    def sort(self, *a, **kw):
        return self

    def limit(self, n: int):
        self._docs = self._docs[:n]
        return self

    def skip(self, n: int):
        self._docs = self._docs[n:]
        return self

    async def to_list(self, length=None):
        if length:
            return self._docs[:length]
        return self._docs


class MemoryDB:
    """Dict-based DB that quacks like AsyncIOMotorDatabase."""
    def __getattr__(self, name):
        return MemoryCollection(name)

    def __getitem__(self, name):
        return MemoryCollection(name)


async def connect_db():
    """Initialize MongoDB connection. Falls back to in-memory if unavailable."""
    global _client, _db
    settings = get_settings()

    try:
        _client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
        await _client.admin.command("ping")
        _db = _client[settings.mongodb_db]
        log.info(f"MongoDB connected: {settings.mongodb_db}")
    except Exception as e:
        log.warning(f"MongoDB unavailable ({e}). Using in-memory store.")
        _db = MemoryDB()


async def close_db():
    global _client
    if _client:
        _client.close()
        log.info("MongoDB connection closed")


def get_db():
    """Get current database instance."""
    if _db is None:
        return MemoryDB()
    return _db