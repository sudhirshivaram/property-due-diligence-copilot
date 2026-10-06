"""Shared helper functions."""

from hashlib import sha256
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET
from html import escape
from property_copilot._display import display, HTML
import json
import re
from copy import deepcopy


def load_source(archive, member):
    if not archive.is_file():
        raise FileNotFoundError(f"Source archive is missing: {archive}")
    try:
        with ZipFile(archive) as bundle:
            matches = [entry for entry in bundle.infolist() if entry.filename == member]
            if len(matches) != 1:
                raise ValueError(f"Expected exactly one {member}; found {len(matches)}")
            return bundle.read(matches[0])
    except BadZipFile as exc:
        raise ValueError("Source archive is not a valid ZIP") from exc


def show_rows(rows):
    """Small escaped HTML table; no dataframe dependency or source HTML execution."""
    if not rows:
        print("No rows")
        return
    columns = list(rows[0])
    header = "".join((f"<th>{escape(str(k))}</th>" for k in columns))
    content = "".join(
        (
            "<tr>"
            + "".join(
                (
                    f"<td style='white-space:pre-wrap'>{escape(str(row.get(k, '')))}</td>"
                    for k in columns
                )
            )
            + "</tr>"
            for row in rows
        )
    )
    display(
        HTML(f"<table><thead><tr>{header}</tr></thead><tbody>{content}</tbody></table>")
    )


def base_record(kind, position, part, path, source_hash):
    identity = f"{source_hash}:{part}:{path}"
    return {
        "id": sha256(identity.encode("utf-8")).hexdigest(),
        "type": kind,
        "position": position,
        "source": {"part": part, "path": path},
    }


def property_xml(element):
    return ET.tostring(element, encoding="unicode") if element is not None else None


def table_paragraphs(block):
    return [
        p for row in block["rows"] for cell in row["cells"] for p in cell["paragraphs"]
    ]


def preview_record(block):
    paragraphs = [block] if block["type"] == "paragraph" else table_paragraphs(block)
    preview = " | ".join((p["raw_text"] for p in paragraphs))[:160]
    return {
        "position": block["position"],
        "type": block["type"],
        "style": block["style"]["name"],
        "preview (display only)": preview,
        "characters": sum((len(p["raw_text"]) for p in paragraphs)),
    }


def show_full_record(record, title):
    content = escape(json.dumps(record, ensure_ascii=False, indent=2))
    display(
        HTML(
            f"<details><summary>{escape(title)}</summary><pre>{content}</pre></details>"
        )
    )


def all_paragraph_records(blocks):
    return [
        p
        for b in blocks
        for p in ([b] if b["type"] == "paragraph" else table_paragraphs(b))
    ]


def heading_level(block):
    if block["type"] != "paragraph":
        return None
    match = re.fullmatch("Heading([1-9])", block["style"]["resolved_id"] or "")
    return int(match.group(1)) if match else None


def nonempty_paragraph(block):
    return (
        block["type"] == "paragraph"
        and bool(block["raw_text"])
        and (not block["raw_text"].isspace())
    )


def is_region_marker(block, label):
    return heading_level(block) == 2 and block["raw_text"] == label


def test_paragraph(text, style="Normal"):
    return {
        "id": "unassigned",
        "position": 0,
        "type": "paragraph",
        "raw_text": text,
        "style": {"explicit_id": style, "resolved_id": style, "name": style},
        "source": {"part": "synthetic", "path": "/unassigned"},
    }


def numbered_test_blocks(blocks):
    result = deepcopy(blocks)
    for i, block in enumerate(result):
        block.update(
            id=f"test-{i}",
            position=i,
            source={"part": "synthetic", "path": f"/children/{i}"},
        )
    return result


def record_digest(value):
    return sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode(
            "utf-8"
        )
    ).hexdigest()


def text_with_evidence(paragraph):
    return {
        "raw_text": paragraph["raw_text"],
        "block_id": paragraph["id"],
        "source": deepcopy(paragraph["source"]),
    }


def assert_original_fields_preserved(original, assembled):
    for key, value in original.items():
        if key != "rows":
            assert assembled[key] == value, (original["id"], key)
    assert assembled is not original
    if original["type"] == "table":
        assert len(assembled["rows"]) == len(original["rows"])
        for row_before, row_after in zip(
            original["rows"], assembled["rows"], strict=True
        ):
            assert row_after["row_index"] == row_before["row_index"]
            for cell_before, cell_after in zip(
                row_before["cells"], row_after["cells"], strict=True
            ):
                assert cell_after["column_index"] == cell_before["column_index"]
                for before, after in zip(
                    cell_before["paragraphs"], cell_after["paragraphs"], strict=True
                ):
                    assert_original_fields_preserved(before, after)


def paragraph_evidence_display(paragraphs):
    return "\n".join(
        (p["source"]["part"] + ":" + p["source"]["path"] for p in paragraphs)
    )


def file_sha256(path):
    digest = sha256()
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(piece)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)
