# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared read-only ZIP inventory gate for native GIS and manufacturer adapters.

Validate the entire directory before exposing any member to an adapter/provider.
No extraction, nested archive traversal or filesystem path construction occurs here.
"""
from pathlib import PurePosixPath
import stat

MAX_ENTRIES = 10000
MAX_BYTES = 512 * 1024 * 1024


def validated_members(archive, check=lambda: None, *, max_entries=MAX_ENTRIES,
                      max_bytes=MAX_BYTES):
    """Return file-name -> ZipInfo, rejecting unsafe/ambiguous archives as a unit.

    `check` raises the caller's cancellation exception. Original accepted names
    remain unchanged for native /vsizip/ URIs and source provenance. Case-folded
    aliases are rejected conservatively for consistent Windows/provider lookup.
    Nested ZIPs remain opaque entries for the caller to report, never recurse.
    """
    check()
    entries = archive.infolist()
    if len(entries) > max_entries:
        raise ValueError('Archive exceeds preview limits (10,000 entries / 512 MiB)')
    total, seen, members = 0, set(), {}
    for entry in entries:
        check()
        total += entry.file_size
        if total > max_bytes:
            raise ValueError('Archive exceeds preview limits (10,000 entries / 512 MiB)')
        name = entry.filename
        bare = name[:-1] if entry.is_dir() else name
        parts = bare.split('/')
        mode = stat.S_IFMT(entry.external_attr >> 16)
        if (entry.orig_filename != name or not bare or '\\' in name or ':' in name or '\x00' in name
                or PurePosixPath(name).is_absolute()
                or any(part in ('', '.', '..') for part in parts)
                or entry.flag_bits & 1
                or mode not in (0, stat.S_IFREG, stat.S_IFDIR)):
            raise ValueError('Unsafe, linked or encrypted ZIP member; not scanned')
        key = bare.casefold()
        if key in seen:
            raise ValueError('Unsafe duplicate or case-ambiguous ZIP member; not scanned')
        seen.add(key)
        if not entry.is_dir():
            members[name] = entry
    return members
