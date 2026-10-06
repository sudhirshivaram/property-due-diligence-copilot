import warnings
from zipfile import ZipFile

import pytest

from property_copilot.ingestion.primitives import base_record, load_source


def test_source_member_must_be_unique_and_exact(tmp_path):
    path = tmp_path / "corpus.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("full_text/document.docx", b"original bytes")
    assert load_source(path, "full_text/document.docx") == b"original bytes"
    with pytest.raises(ValueError, match="found 0"):
        load_source(path, "document.docx")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with ZipFile(path, "a") as archive:
            archive.writestr("full_text/document.docx", b"duplicate")
    with pytest.raises(ValueError, match="found 2"):
        load_source(path, "full_text/document.docx")


def test_corrupt_and_missing_archives_fail_explicitly(tmp_path):
    path = tmp_path / "bad.zip"
    with pytest.raises(FileNotFoundError):
        load_source(path, "member")
    path.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="not a valid ZIP"):
        load_source(path, "member")


def test_record_identity_tracks_content_part_and_source_path():
    original = base_record("paragraph", 0, "word/document.xml", "/body/0", "sha-a")
    assert original == base_record(
        "paragraph", 0, "word/document.xml", "/body/0", "sha-a"
    )
    alternatives = [
        base_record("paragraph", 0, part, path, digest)["id"]
        for part, path, digest in [
            ("word/document.xml", "/body/1", "sha-a"),
            ("word/footer.xml", "/body/0", "sha-a"),
            ("word/document.xml", "/body/0", "sha-b"),
        ]
    ]
    assert original["id"] not in alternatives
    assert len(set(alternatives)) == 3
