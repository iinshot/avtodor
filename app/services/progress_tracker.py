import asyncio

class ProgressTracker:
    def __init__(self):
        self._progress = 0
        self._lock = asyncio.Lock()
        self._items = 0

    async def set(self, value: int):
        async with self._lock:
            self._progress = max(0, min(100, value))

    async def increment(self, step: int = 1):
        async with self._lock:
            self._progress = min(100, self._progress + step)

    async def get(self):
        async with self._lock:
            return {
                "progress": self._progress,
                "items_count": self._items,
            }

    async def set_items(self, count):
        async with self._lock:
            self._items = count

progress_tracker = ProgressTracker()