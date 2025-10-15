"""Filesystem storage utilities for the crawler."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console()


@dataclass(slots=True)
class StorageManager:
    """Persist fetched resources to disk."""

    output_dir: Path

    def __post_init__(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_text(self, url: str, content: str) -> Path:
        destination = self._path_for(url, suffix=".html")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        console.log(f"Saved page -> {destination}")
        return destination

    def save_binary(self, url: str, payload: bytes, mime_hint: str | None = None) -> Path:
        suffix = guess_extension(url, mime_hint)
        destination = self._path_for(url, suffix=suffix)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        console.log(f"Saved asset -> {destination}")
        return destination

    def _path_for(self, url: str, *, suffix: str) -> Path:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        parts: list[str] = [self._sanitize(part) for part in parsed.path.split("/") if part]
        if not parts:
            parts = ["index"]
        if parsed.query:
            parts.append(self._sanitize(parsed.query))
        filename = parts[-1]
        parent_parts = parts[:-1]
        if "." not in filename:
            filename = f"{filename}{suffix}"
        elif not filename.endswith(suffix):
            filename = f"{filename}{suffix}"
        destination = self.output_dir.joinpath(parsed.netloc, *parent_parts, filename)
        return destination

    def _sanitize(self, value: str) -> str:
        keep = [c if c.isalnum() or c in {"-", "_", "."} else "-" for c in value]
        sanitized = "".join(keep).strip("-_") or "segment"
        return sanitized


def guess_extension(url: str, mime_hint: str | None) -> str:
    from mimetypes import guess_extension as mime_guess_extension
    from urllib.parse import urlparse

    if mime_hint:
        ext = mime_guess_extension(mime_hint.split(";")[0].strip())
        if ext:
            return ext

    parsed = urlparse(url)
    path = parsed.path
    if "." in path.split("/")[-1]:
        return ""
    return ".bin"
