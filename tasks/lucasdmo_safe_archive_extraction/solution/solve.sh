#!/bin/bash
set -euo pipefail

cat > /app/safe_extract.py <<'PY'
"""Secure extraction helpers for small ZIP archives."""

from __future__ import annotations

import re
import stat
from pathlib import Path
from zipfile import ZipFile, ZipInfo


_DRIVE = re.compile(r"^[A-Za-z]:")


def _invalid(member_name: str) -> ValueError:
    return ValueError(f"unsafe archive member: {member_name}")


def _target_for(member: ZipInfo, destination: Path) -> Path:
    name = member.filename
    parts = re.split(r"[/\\\\]", name)
    if (
        not name
        or name.startswith(("/", "\\\\"))
        or _DRIVE.match(name)
        or ".." in parts
    ):
        raise _invalid(name)
    retained = [part for part in parts if part not in ("", ".")]
    if not retained:
        raise _invalid(name)
    return destination.joinpath(*retained)


def _is_directory(member: ZipInfo) -> bool:
    mode = (member.external_attr >> 16) & 0xFFFF
    kind = stat.S_IFMT(mode)
    if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise _invalid(member.filename)
    return member.is_dir() or kind == stat.S_IFDIR


def extract_archive(archive_path: Path, destination: Path) -> list[Path]:
    """Validate all members, then safely extract regular files."""
    with ZipFile(archive_path) as archive:
        members = archive.infolist()
        if destination.exists() and (destination.is_symlink() or not destination.is_dir()):
            if members:
                raise _invalid(members[0].filename)
            return []

        planned: list[tuple[ZipInfo, Path, bool]] = []
        planned_kinds: dict[Path, bool] = {}
        for member in members:
            target = _target_for(member, destination)
            is_directory = _is_directory(member)
            if target in planned_kinds:
                raise _invalid(member.filename)
            planned_kinds[target] = is_directory
            if target.exists() or target.is_symlink():
                if not (is_directory and target.is_dir() and not target.is_symlink()):
                    raise _invalid(member.filename)
            planned.append((member, target, is_directory))

        for member, target, _ in planned:
            parent = target.parent
            while True:
                if parent.is_symlink():
                    raise _invalid(member.filename)
                if parent == destination:
                    break
                parent = parent.parent
            ancestor = target.parent
            while ancestor != destination:
                if planned_kinds.get(ancestor) is False:
                    raise _invalid(member.filename)
                ancestor = ancestor.parent

        written: list[Path] = []
        for member, target, is_directory in planned:
            if is_directory:
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("xb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
            written.append(target)
        return written
PY
