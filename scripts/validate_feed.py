#!/usr/bin/env python3
"""Validate a URV-compatible ReVanced API v4 feed and optional .rvp artifact."""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_FIELDS = {"download_url", "created_at", "description", "version"}
OPTIONAL_FIELDS = {"signature_download_url", "page_url"}


def fail(message: str) -> None:
    raise ValueError(message)


def parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.strip():
        fail("created_at must be a non-empty ISO-8601 string")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        fail(f"created_at is not valid ISO-8601: {exc}")


def validate_url(value: object, field: str, *, json_suffix: bool = False) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty URL")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{field} must be an absolute HTTPS URL")
    if json_suffix and not parsed.path.lower().endswith(".rvp"):
        fail(f"{field} must point to a .rvp artifact")


def validate_feed(path: Path, expected_version: str | None) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"feed is not valid JSON: {exc}")

    if not isinstance(data, dict):
        fail("feed root must be a JSON object")
    unknown = set(data) - REQUIRED_FIELDS - OPTIONAL_FIELDS
    missing = REQUIRED_FIELDS - set(data)
    if missing:
        fail(f"feed is missing required fields: {', '.join(sorted(missing))}")
    if unknown:
        fail(f"feed contains unsupported fields: {', '.join(sorted(unknown))}")

    validate_url(data["download_url"], "download_url", json_suffix=True)
    for field in ("signature_download_url", "page_url"):
        if field in data and data[field] is not None:
            validate_url(data[field], field)

    parse_timestamp(data["created_at"])
    for field in ("description", "version"):
        if not isinstance(data[field], str) or not data[field].strip():
            fail(f"{field} must be a non-empty string")
    if expected_version and data["version"] != expected_version:
        fail(f"feed version {data['version']!r} does not match expected {expected_version!r}")

    return data


def validate_artifact(path: Path) -> dict[str, object]:
    if not path.is_file() or path.stat().st_size <= 0:
        fail(f"artifact is missing or empty: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                fail("artifact contains a corrupt ZIP entry")
            names = archive.namelist()
            dex_entries = [
                name for name in names if name.lower().endswith(".dex")
            ]
            if not dex_entries:
                fail("artifact contains no DEX entries")
            empty_dex = [
                name for name in dex_entries if archive.getinfo(name).file_size <= 0
            ]
            if empty_dex:
                fail(f"artifact contains empty DEX entries: {', '.join(empty_dex)}")
            if not any(name.upper() == "META-INF/MANIFEST.MF" for name in names):
                fail("artifact is missing META-INF/MANIFEST.MF")
    except zipfile.BadZipFile as exc:
        fail(f"artifact is not a valid ZIP/JAR/.rvp file: {exc}")

    return {
        "bytes": path.stat().st_size,
        "dex_entries": len(dex_entries),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed", type=Path, required=True)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--expected-version")
    args = parser.parse_args()

    try:
        feed = validate_feed(args.feed, args.expected_version)
        artifact = validate_artifact(args.artifact) if args.artifact else None
    except ValueError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1

    result = {
        "valid": True,
        "feed_version": feed["version"],
        "download_url": feed["download_url"],
    }
    if artifact:
        result["artifact"] = artifact
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

