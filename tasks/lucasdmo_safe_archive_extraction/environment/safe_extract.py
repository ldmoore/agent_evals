"""Helpers for extracting small ZIP archives."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile


def extract_archive(archive_path: Path, destination: Path) -> list[Path]:
    """Extract archive members and return paths written below destination."""
    written: list[Path] = []
    with ZipFile(archive_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            target = destination / member.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                output.write(source.read())
            written.append(target)
    return written
