from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from safe_extract import extract_archive


def make_archive(path: Path, files: dict[str, str]) -> None:
    with ZipFile(path, "w") as archive:
        for name, contents in files.items():
            archive.writestr(name, contents)


def test_extracts_nested_regular_files(tmp_path: Path) -> None:
    archive_path = tmp_path / "example.zip"
    destination = tmp_path / "out"
    make_archive(archive_path, {"notes/today.txt": "hello", "README": "ok"})

    written = extract_archive(archive_path, destination)

    assert [path.relative_to(destination) for path in written] == [
        Path("notes/today.txt"),
        Path("README"),
    ]
    assert (destination / "notes/today.txt").read_text() == "hello"
    assert (destination / "README").read_text() == "ok"
