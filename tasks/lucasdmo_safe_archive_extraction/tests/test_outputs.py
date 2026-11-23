"""Verifier-only tests for safe archive extraction."""

from __future__ import annotations

import stat
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest
from safe_extract import extract_archive


def make_archive(path: Path, entries: list[tuple[str, str]]) -> None:
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, data in entries:
            archive.writestr(name, data)


def snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


@pytest.mark.parametrize(
    "bad_name",
    [
        "../outside.txt",
        "nested/../looks-safe.txt",
        "/absolute.txt",
        "C:\\temp\\drive.txt",
        "\\\\server\\share\\unc.txt",
        "nested\\..\\escape.txt",
    ],
)
def test_rejects_portable_unsafe_names_without_partial_writes(
    tmp_path: Path, bad_name: str
) -> None:
    archive_path = tmp_path / "bad.zip"
    destination = tmp_path / "out"
    destination.mkdir()
    (destination / "keep.txt").write_text("unchanged")
    make_archive(archive_path, [("safe-first.txt", "must not appear"), (bad_name, "bad")])

    with pytest.raises(ValueError) as error:
        extract_archive(archive_path, destination)
    assert bad_name in str(error.value)
    assert snapshot(destination) == {"keep.txt": b"unchanged"}


def test_rejects_symlink_member_before_writing_other_members(tmp_path: Path) -> None:
    archive_path = tmp_path / "link.zip"
    destination = tmp_path / "out"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("safe.txt", "must not appear")
        link = ZipInfo("linked")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, "target")

    with pytest.raises(ValueError) as error:
        extract_archive(archive_path, destination)
    assert "linked" in str(error.value)
    assert not destination.exists()


def test_never_overwrites_existing_destination_file(tmp_path: Path) -> None:
    archive_path = tmp_path / "existing.zip"
    destination = tmp_path / "out"
    destination.mkdir()
    (destination / "already.txt").write_text("before")
    make_archive(archive_path, [("new.txt", "must not appear"), ("already.txt", "after")])

    with pytest.raises(ValueError) as error:
        extract_archive(archive_path, destination)
    assert "already.txt" in str(error.value)
    assert snapshot(destination) == {"already.txt": b"before"}


def test_returns_files_in_member_order_and_creates_safe_directories(tmp_path: Path) -> None:
    archive_path = tmp_path / "good.zip"
    destination = tmp_path / "out"
    make_archive(archive_path, [("a/one.txt", "1"), ("two.txt", "2")])

    written = extract_archive(archive_path, destination)

    assert [path.relative_to(destination) for path in written] == [
        Path("a/one.txt"),
        Path("two.txt"),
    ]
    assert snapshot(destination) == {"a/one.txt": b"1", "two.txt": b"2"}
