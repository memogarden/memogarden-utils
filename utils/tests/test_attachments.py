"""Content-addressed store behavior (promoted from gmail-importer's
TestAttachmentStore alongside the class itself)."""

from utils.attachments import AttachmentStore

PDF_BYTES = b"%PDF-1.4 fake invoice content"


def test_write_returns_hash_and_relative_path(tmp_path):
    store = AttachmentStore(tmp_path / "attachments")
    rel, digest = store.write(PDF_BYTES, "invoice.pdf")
    assert rel.endswith(".pdf")
    assert digest in rel
    assert (store.root / rel).read_bytes() == PDF_BYTES


def test_sharded_two_levels(tmp_path):
    store = AttachmentStore(tmp_path / "attachments")
    rel, digest = store.write(PDF_BYTES, "invoice.pdf")
    parts = rel.split("/")
    assert len(parts) == 3
    assert parts[0] == digest[:2]
    assert parts[1] == digest[2:4]


def test_same_content_different_name_deduplicates(tmp_path):
    store = AttachmentStore(tmp_path / "attachments")
    rel1, d1 = store.write(PDF_BYTES, "a.pdf")
    rel2, d2 = store.write(PDF_BYTES, "totally-different-name.pdf")
    assert rel1 == rel2
    assert d1 == d2
    assert len([p for p in store.root.rglob("*") if p.is_file()]) == 1


def test_extension_sanitized(tmp_path):
    store = AttachmentStore(tmp_path / "attachments")
    _, digest = store.write(PDF_BYTES, "../../evil/..%2F..pdf")
    name = store.path_for(digest, ".pdf").name
    written = [p.name for p in store.root.rglob("*") if p.is_file()]
    assert written == [f"{digest}.pdf"]


def test_no_extension(tmp_path):
    store = AttachmentStore(tmp_path / "attachments")
    rel, digest = store.write(PDF_BYTES, "README")
    assert rel.split("/")[-1] == digest
