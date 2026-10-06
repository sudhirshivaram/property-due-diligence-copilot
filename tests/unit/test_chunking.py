from copy import deepcopy

import pytest

from property_copilot.chunking import aware_windows, fixed_length_windows
from property_copilot.chunking.primitives import validate_relationship_group
from property_copilot.chunking.setup import SetupSteps
from property_copilot.schemas.chunk import SourceSpan


def restore(windows):
    end = 0
    parts = []
    for window in windows:
        assert window["start"] <= end < window["end"]
        parts.append(window["text"][end - window["start"] :])
        end = window["end"]
    return "".join(parts)


@pytest.mark.parametrize("text", ["", "Чл. 1.\nБългарски текст § 2.🙂", "a" * 103])
@pytest.mark.parametrize("target,overlap", [(1, 0), (7, 0), (7, 2), (7, 6)])
def test_fixed_preserves_unicode_and_exact_coverage(text, target, overlap):
    windows = fixed_length_windows(text, target, overlap)
    assert restore(windows) == text
    for index, window in enumerate(windows):
        assert window["start"] == index * (target - overlap)
        assert window["text"] == text[window["start"] : window["end"]]
        assert len(window["text"]) <= target


@pytest.mark.parametrize(
    "length,overlap", [(0, 0), (4, 4), (4, -1), (True, 0), (4, 1.5)]
)
def test_fixed_rejects_invalid_settings(length, overlap):
    with pytest.raises(ValueError):
        fixed_length_windows("текст", length, overlap)


def test_aware_prefers_paragraph_boundary_and_preserves_parent():
    text = "abc\ndef ghi jkl"
    windows = aware_windows(text, [(0, 3), (4, len(text))], 8, 0)
    assert windows[0]["end"] == 4
    assert windows[0]["end_reason"] == "paragraph_boundary"
    assert restore(windows) == text
    assert all(len(w["text"]) <= 8 for w in windows)


def test_source_map_crosses_added_separator_without_claiming_source_text():
    session = SetupSteps()
    session.BLOCKS = {
        "a": {
            "id": "a",
            "position": 0,
            "raw_text": "аб",
            "source": {"part": "word/document.xml", "path": "/body/0"},
        },
        "b": {
            "id": "b",
            "position": 1,
            "raw_text": "вг",
            "source": {"part": "word/document.xml", "path": "/body/1"},
        },
    }
    session.VIEWS = {
        "doc": {
            "text": "аб\nвг",
            "segments": [
                {"kind": "source", "start": 0, "end": 2, "block_id": "a"},
                {
                    "kind": "separator",
                    "start": 2,
                    "end": 3,
                    "left_block_id": "a",
                    "right_block_id": "b",
                },
                {"kind": "source", "start": 3, "end": 5, "block_id": "b"},
            ],
        }
    }
    session.SEGMENT_ENDS = {"doc": [2, 3, 5]}
    spans = session.source_map("doc", 1, 4)
    assert session.reconstruct(spans) == "б\nв"
    assert [s["kind"] for s in spans] == ["source", "separator", "source"]
    assert spans[0]["block_start"] == 1 and spans[2]["block_start"] == 0
    for span in spans:
        SourceSpan.model_validate(span)
    assert session.source_map("doc", 2, 2) == []
    with pytest.raises(ValueError):
        session.source_map("doc", -1, 4)


def relationship_fixture():
    parent = {"id": "p", "document_id": "doc", "start": 0, "end": 6, "text": "abcdef"}
    children = {
        "a": {"id": "a", "document_id": "doc", "start": 0, "end": 4, "text": "abcd"},
        "b": {"id": "b", "document_id": "doc", "start": 3, "end": 6, "text": "def"},
    }
    group = {"id": "g", "parent_id": "p", "relationship_ids": ["r1", "r2"]}
    links = {
        f"r{i}": {
            "id": f"r{i}",
            "parent_id": "p",
            "child_id": child,
            "relationship_set_id": "g",
            "ordinal": i,
        }
        for i, child in enumerate(children, 1)
    }
    return group, {"p": parent}, children, links


def test_relationship_accepts_overlap_but_rejects_cross_document_and_gaps():
    group, parents, children, links = relationship_fixture()
    validate_relationship_group(group, parents, children, links)
    invalid = deepcopy(children)
    invalid["b"]["document_id"] = "other"
    with pytest.raises(ValueError, match="crosses documents"):
        validate_relationship_group(group, parents, invalid, links)
    invalid = deepcopy(children)
    invalid["b"].update(start=5, text="f")
    with pytest.raises(ValueError, match="gap"):
        validate_relationship_group(group, parents, invalid, links)
