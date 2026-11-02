import hashlib
from pathlib import Path


class DiskCache:
    """Tiny file cache: one file per key, named by the SHA-256 hash of the key."""

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def _path(self, key: str) -> Path:
        return self.directory / f"{hashlib.sha256(key.encode('utf-8')).hexdigest()}.json"

    def get(self, key: str) -> str | None:
        path = self._path(key)
        return path.read_text(encoding="utf-8") if path.exists() else None

    def set(self, key: str, value: str) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self._path(key).write_text(value, encoding="utf-8")
