"""Publish the bundled front page for the news-image-20261122 bounty.

Reads news.png sitting next to this file and drops an exact byte-for-byte
copy at $MAKEFUN_OUTPUT_DIR/entry.png. The copy is re-read and checked
(size and sha256) before the program reports success, so a truncated or
corrupted write can never pass silently.
"""

import hashlib
import os
import sys
from pathlib import Path

SOURCE_NAME = "news.png"
TARGET_NAME = "entry.png"
MAX_BYTES = 1_048_576


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def fingerprint(path):
    """Return (size, sha256 hex) of the file at path."""
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
    return total, digest.hexdigest()


def main():
    here = Path(__file__).resolve().parent
    source = here / SOURCE_NAME

    if not source.is_file():
        fail(f"missing bundled image: {source}")

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        fail("MAKEFUN_OUTPUT_DIR is not set")

    destination = Path(out_dir) / TARGET_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)

    source_size, source_hash = fingerprint(source)
    if source_size > MAX_BYTES:
        fail(f"bundled image is {source_size} bytes, over the {MAX_BYTES} byte limit")

    # Stream the copy so memory stays flat no matter the file size.
    with source.open("rb") as reader, destination.open("wb") as writer:
        while True:
            block = reader.read(1 << 20)
            if not block:
                break
            writer.write(block)

    copy_size, copy_hash = fingerprint(destination)
    if copy_size != source_size or copy_hash != source_hash:
        fail("verification failed: output does not match the bundled image")

    # Re-read the source to prove it did not change while we were copying.
    final_size, final_hash = fingerprint(source)
    if final_size != source_size or final_hash != source_hash:
        fail("verification failed: bundled image changed during the copy")

    print(f"OK entry.png written: {copy_size} bytes sha256={copy_hash}")


if __name__ == "__main__":
    main()
