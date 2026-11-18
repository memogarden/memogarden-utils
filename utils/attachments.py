"""Content-addressed binary storage, shared by every document provider.

Binaries live under <root>/<h2>/<h2>/<sha256><ext>: the file is named by
its own content hash, so identical files deduplicate across providers and
any copy can be integrity-checked against the fact's sha256.

Promoted from gmail_importer.attachments (2026-11-18) so the RFC-013
sessions drain stores downloads in the SAME store as gmail attachments —
one canonical residence, shared postprocessing (RFC-013 §8).
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def safe_ext(filename: str) -> str:
    """Filesystem-safe extension from an original filename ('' if none)."""
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    ext = name.rsplit(".", 1)[1]
    cleaned = "".join(c for c in ext if c.isalnum())
    if not cleaned:
        return ""
    return "." + cleaned[:10]


class AttachmentStore:
    """Content-addressed binary store rooted at a directory on disk."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def path_for(self, digest: str, ext: str = "") -> Path:
        return self.root / digest[:2] / digest[2:4] / f"{digest}{ext}"

    def write(self, data: bytes, original_filename: str) -> tuple[str, str]:
        """Write bytes; returns (path relative to root, sha256 hex digest).

        Idempotent: content already present is left untouched (same hash
        means the same bytes).
        """
        digest = hashlib.sha256(data).hexdigest()
        path = self.path_for(digest, safe_ext(original_filename))
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.parent / (path.name + ".part")
            tmp.write_bytes(data)
            tmp.rename(path)
        return str(path.relative_to(self.root)), digest
