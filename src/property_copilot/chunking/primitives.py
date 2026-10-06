"""Stateless helpers extracted from the reviewed chunking notebook."""

from pathlib import Path
from collections import Counter
from bisect import bisect_right
import hashlib
import html
import json
import math
from property_copilot._display import HTML, display
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def project_root():
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "notebooks"
        ).is_dir():
            return candidate
    raise FileNotFoundError("Start Jupyter in the project or its notebooks directory.")


def validate_stage1(value):
    require(isinstance(value, dict), "Artifact root must be an object.")
    require(value.get("schema_version") == 1, "Unsupported Stage 1 schema version.")
    for name in (
        "source",
        "parser",
        "documents",
        "blocks",
        "diagnostics",
        "metadata_provenance",
    ):
        require(name in value, f"Missing Stage 1 field: {name}")
    require(
        value["diagnostics"].get("stage1_validation", {}).get("result") == "PASS",
        "Stage 1 must report PASS before Stage 2.",
    )
    require(
        isinstance(value["source"].get("sha256"), str)
        and len(value["source"]["sha256"]) == 64,
        "Missing source DOCX fingerprint.",
    )
    docs, blocks = (value["documents"], value["blocks"])
    require(isinstance(docs, list) and docs, "Missing document records.")
    require(isinstance(blocks, list) and blocks, "Missing ordered blocks.")
    doc_ids = [d["document_id"] for d in docs]
    require(len(set(doc_ids)) == len(doc_ids), "Duplicate document IDs.")
    ordinals = [d["ordinal"] for d in docs]
    require(len(set(ordinals)) == len(ordinals), "Duplicate document ordinals.")
    ids = [b["id"] for b in blocks]
    require(len(set(ids)) == len(ids), "Duplicate body block IDs.")
    positions = [b["position"] for b in blocks]
    require(
        positions == sorted(set(positions)),
        "Body positions must be unique and increasing.",
    )
    by_id = {b["id"]: b for b in blocks}
    allowed_regions = {
        "front_matter",
        "document_metadata",
        "reference_rules",
        "full_text",
    }
    for b in blocks:
        require(
            b.get("region") in allowed_regions, f"Unknown region at {b['position']}."
        )
        require(
            b.get("document_id") in doc_ids
            or (b.get("document_id") is None and b["region"] == "front_matter"),
            f"Invalid document membership at {b['position']}.",
        )
        require(
            "source" in b and "structural_annotations" in b,
            "Missing block provenance/annotations.",
        )
        if b["region"] == "full_text":
            require(
                b["type"] == "paragraph" and isinstance(b.get("raw_text"), str),
                "Unexpected full-text block type: review a faithful representation before proceeding.",
            )
        for marker in b["structural_annotations"]["legal_marker_candidates"]:
            start, end = marker["character_span"]
            require(
                marker["block_id"] == b["id"]
                and marker["document_id"] == b["document_id"],
                "Candidate marker references the wrong block/document.",
            )
            require(
                0 <= start < end <= len(b["raw_text"]),
                "Invalid candidate character span.",
            )
            require(
                b["raw_text"][start:end] == marker["matched_label"],
                "Candidate label differs from source.",
            )
    assigned = set()
    for d in docs:
        lo, hi = (
            d["block_range"]["start_index"],
            d["block_range"]["end_index_exclusive"],
        )
        require(0 <= lo < hi <= len(blocks), "Invalid document block range.")
        indices = set(range(lo, hi))
        require(not assigned.intersection(indices), "Overlapping document ranges.")
        assigned.update(indices)
        require(
            all((b["document_id"] == d["document_id"] for b in blocks[lo:hi])),
            "Document range and block membership disagree.",
        )
        require(
            d.get("source_titles") and d.get("source_metadata"),
            "Missing document metadata.",
        )
        for evidence_id in d["boundary_evidence"].values():
            if evidence_id is not None:
                require(
                    evidence_id in by_id
                    and by_id[evidence_id]["document_id"] == d["document_id"],
                    "Invalid document boundary evidence.",
                )
        marker = by_id[d["boundary_evidence"]["full_text_marker_block_id"]]
        require(
            marker["region"] == "full_text"
            and marker["raw_text"] == "Пълен текст / Full text",
            "Full-text delimiter differs from the inspected standalone marker; review it.",
        )
    require(
        assigned == {i for i, b in enumerate(blocks) if b["document_id"] is not None},
        "Document ranges do not account for every assigned block.",
    )
    require(
        dict(Counter((b["region"] for b in blocks)))
        == value["diagnostics"]["region_counts"],
        "Region counts disagree with Stage 1 diagnostics.",
    )
    return {"result": "PASS", "documents": len(docs), "body_blocks": len(blocks)}


def esc(value):
    return html.escape(str(value), quote=True)


def table_html(rows, columns=None, limit=None):
    rows = list(rows)
    columns = list(columns or (rows[0].keys() if rows else []))
    visible = rows if limit is None else rows[:limit]
    header = "".join((f"<th>{esc(c)}</th>" for c in columns))
    body = "".join(
        (
            "<tr>"
            + "".join((f"<td>{esc(row.get(c, ''))}</td>" for c in columns))
            + "</tr>"
            for row in visible
        )
    )
    note = f"Showing {len(visible)} of {len(rows)} rows."
    return f"<p>{note}</p><div style='overflow:auto'><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>"


def show_table(rows, columns=None, limit=None):
    display(HTML(table_html(rows, columns, limit)))


def details_html(label, text):
    return f"<details><summary>{esc(label)}</summary><pre style='white-space:pre-wrap;overflow-wrap:anywhere'>{esc(text)}</pre></details>"


def show_json(label, value):
    display(HTML(details_html(label, json.dumps(value, ensure_ascii=False, indent=2))))


def build_document_view(document, ordered_blocks):
    document_id = document["document_id"]
    delimiter_id = document["boundary_evidence"]["full_text_marker_block_id"]
    selected = [
        b
        for b in ordered_blocks
        if b["document_id"] == document_id and b["region"] == "full_text"
    ]
    delimiter = [b for b in selected if b["id"] == delimiter_id]
    require(
        len(delimiter) == 1 and delimiter[0]["raw_text"] == "Пълен текст / Full text",
        "Expected one evidence-linked standalone delimiter.",
    )
    kept = [b for b in selected if b["id"] != delimiter_id]
    pieces, segments, offset = ([], [], 0)
    for i, b in enumerate(kept):
        if i:
            segments.append(
                {
                    "kind": "separator",
                    "start": offset,
                    "end": offset + 1,
                    "left_block_id": kept[i - 1]["id"],
                    "right_block_id": b["id"],
                }
            )
            pieces.append("\n")
            offset += 1
        text = b["raw_text"]
        segments.append(
            {
                "kind": "source",
                "start": offset,
                "end": offset + len(text),
                "block_id": b["id"],
                "position": b["position"],
            }
        )
        pieces.append(text)
        offset += len(text)
    return {
        "document_id": document_id,
        "text": "".join(pieces),
        "segments": segments,
        "block_ids": [b["id"] for b in kept],
        "delimiter_block_id": delimiter_id,
    }


def length_summary(values):
    values = sorted(values)
    if not values:
        return {
            "count": 0,
            "min": None,
            "p25": None,
            "median_p50": None,
            "p90": None,
            "p95": None,
            "p75": None,
            "max": None,
        }

    def percentile(p):
        return values[max(0, math.ceil(p * len(values)) - 1)]

    return {
        "count": len(values),
        "min": values[0],
        "p25": percentile(0.25),
        "median_p50": percentile(0.5),
        "p75": percentile(0.75),
        "p90": percentile(0.9),
        "p95": percentile(0.95),
        "max": values[-1],
    }


def highlight_html(text, origin=0, cuts=(), overlaps=(), focus=None):
    end = origin + len(text)
    boundaries = {origin, end}
    cut_set = {c for c in cuts if origin <= c <= end}
    boundaries.update(cut_set)
    for lo, hi in list(overlaps) + ([focus] if focus is not None else []):
        if lo < end and hi > origin:
            boundaries.update((max(origin, lo), min(end, hi)))
    ordered = sorted(boundaries)
    output = []
    for index, lo in enumerate(ordered):
        if lo in cut_set:
            output.append(
                "<b title='Supplied boundary; not source text' style='color:#a00'>│</b>"
            )
        if index + 1 == len(ordered):
            break
        hi = ordered[index + 1]
        fragment = esc(text[lo - origin : hi - origin])
        color = (
            "#ffe39a"
            if any((a <= lo and hi <= b for a, b in overlaps))
            else "#dcefff"
            if focus is not None and focus[0] <= lo and (hi <= focus[1])
            else None
        )
        output.append(
            f"<mark style='background:{color};color:#111'>{fragment}</mark>"
            if color
            else fragment
        )
    return (
        "<pre style='white-space:pre-wrap;overflow-wrap:anywhere'>"
        + "".join(output)
        + "</pre>"
    )


def intersection_length(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def expect_value_error(action, expected):
    try:
        action()
    except ValueError as exc:
        require(expected in str(exc), f"Unexpected error: {exc}")
    else:
        raise AssertionError(f"Expected ValueError containing {expected!r}")


def fixed_length_windows(text, length, overlap):
    require(isinstance(text, str), "Text must be a string.")
    require(type(length) is int and length > 0, "Length must be a positive integer.")
    require(
        type(overlap) is int and 0 <= overlap < length,
        "Overlap must be an integer in [0, length).",
    )
    windows = []
    start = 0
    while start < len(text):
        end = min(start + length, len(text))
        windows.append({"start": start, "end": end, "text": text[start:end]})
        if end == len(text):
            break
        start += length - overlap
    return windows


def offsets(text, length, overlap):
    return [(w["start"], w["end"]) for w in fixed_length_windows(text, length, overlap)]


def interval_union_length(intervals):
    total, end = (0, None)
    for lo, hi in sorted(intervals):
        require(lo <= hi, "Reversed interval.")
        if end is None or lo > end:
            total += hi - lo
        else:
            total += max(0, hi - end)
        end = hi if end is None else max(end, hi)
    return total


def structural_fixture(items):
    blocks = []
    for i, (text, kind, heading) in enumerate(items):
        candidates = []
        if kind:
            label = re.match(
                "(?:Чл\\.\\s*\\d+[а-я]?|§\\s*\\d+[а-я]?|Приложение\\s+[IVX]+|Глава\\s+\\w+)",
                text,
            ).group()
            candidates = [
                {
                    "kind": kind,
                    "matched_label": label,
                    "character_span": [0, len(label)],
                    "rule": "leading_numbered_label"
                    if kind in {"article", "paragraph_sign"}
                    else "leading_label_and_heading",
                }
            ]
        blocks.append(
            {
                "id": f"fixture-{i}",
                "position": i,
                "document_id": "structural-fixture",
                "raw_text": text,
                "source": {"part": "fixture", "path": str(i)},
                "structural_annotations": {
                    "word_heading_level": heading,
                    "legal_marker_candidates": candidates,
                },
            }
        )
    offset, segments = (0, [])
    for i, b in enumerate(blocks):
        if i:
            segments.append({"kind": "separator", "start": offset, "end": offset + 1})
            offset += 1
        segments.append(
            {
                "kind": "source",
                "block_id": b["id"],
                "start": offset,
                "end": offset + len(b["raw_text"]),
            }
        )
        offset += len(b["raw_text"])
    view = {
        "document_id": "structural-fixture",
        "text": "\n".join((b["raw_text"] for b in blocks)),
        "block_ids": [b["id"] for b in blocks],
        "segments": segments,
    }
    return (view, {b["id"]: b for b in blocks})


def validate_relationship_group(group, parents, children, links):
    require(group["parent_id"] in parents, "Unknown parent in relationship set.")
    parent = parents[group["parent_id"]]
    require(
        not parent.get("parent_id"),
        "Parents cannot themselves have a parent in this two-level experiment.",
    )
    ordered_links = [links[rid] for rid in group["relationship_ids"]]
    require(
        [r["ordinal"] for r in ordered_links] == list(range(1, len(ordered_links) + 1)),
        "Child order is not contiguous.",
    )
    require(
        len({r["child_id"] for r in ordered_links}) == len(ordered_links),
        "Duplicate child within relationship set.",
    )
    covered_end, restored = (parent["start"], [])
    previous_start = parent["start"]
    for link in ordered_links:
        require(
            link["relationship_set_id"] == group["id"]
            and link["parent_id"] == parent["id"],
            "Relationship points to wrong set/parent.",
        )
        require(link["child_id"] != parent["id"], "Self-link is forbidden.")
        require(link["child_id"] in children, "Unknown child in relationship.")
        child = children[link["child_id"]]
        require(
            child["document_id"] == parent["document_id"], "Child crosses documents."
        )
        require(
            parent["start"] <= child["start"] < child["end"] <= parent["end"],
            "Child is not fully contained in parent.",
        )
        require(
            previous_start <= child["start"] <= covered_end
            and child["end"] > covered_end,
            "Child gap, redundant span, or source-order error.",
        )
        expected = parent["text"][
            child["start"] - parent["start"] : child["end"] - parent["start"]
        ]
        require(
            child["text"] == expected, "Child text differs from parent source slice."
        )
        restored.append(child["text"][covered_end - child["start"] :])
        previous_start, covered_end = (child["start"], child["end"])
    require(
        covered_end == parent["end"] and "".join(restored) == parent["text"],
        "Children do not reconstruct complete parent.",
    )


def oversized_eligible(size, threshold):
    return size > threshold


def aware_windows(text, paragraph_spans, target, overlap):
    fixed_length_windows("", target, overlap)
    n = len(text)
    require(
        all((0 <= a < b <= n for a, b in paragraph_spans)), "Invalid paragraph span."
    )
    require(
        all((b <= c for (a, b), (c, d) in zip(paragraph_spans, paragraph_spans[1:]))),
        "Paragraph spans must be ordered and disjoint.",
    )
    edges = sorted(
        {0, n, *(a for a, b in paragraph_spans), *(b for a, b in paragraph_spans)}
    )
    whitespace = [i + 1 for i, char in enumerate(text) if char.isspace()]
    result, start, covered = ([], 0, 0)
    while start < n:
        limit = min(start + target, n)
        require(limit > covered, "Boundary splitter cannot advance.")
        if limit == n:
            end, reason = (n, "parent_end")
        else:
            candidates = edges[
                bisect_right(edges, covered) : bisect_right(edges, limit)
            ]
            if candidates:
                end, reason = (candidates[-1], "paragraph_boundary")
            else:
                candidates = whitespace[
                    bisect_right(whitespace, covered) : bisect_right(whitespace, limit)
                ]
                end, reason = (
                    (candidates[-1], "whitespace_inside_paragraph")
                    if candidates
                    else (limit, "exact_no_available_boundary")
                )
        result.append(
            {"start": start, "end": end, "text": text[start:end], "end_reason": reason}
        )
        if end == n:
            break
        lower = max(start + 1, end - overlap)
        next_starts = [p for p in edges if lower <= p < end]
        if next_starts:
            next_start, start_reason = (next_starts[0], "paragraph_overlap")
        elif overlap and any(
            (a < end < b and b - a > target for a, b in paragraph_spans)
        ):
            safe = [
                p
                for p in whitespace
                if lower <= p < end
                and any(
                    (a < p <= end < b and b - a > target for a, b in paragraph_spans)
                )
            ]
            next_start, start_reason = (
                (safe[0], "whitespace_overlap")
                if safe
                else (end, "overlap_reduced_to_zero")
            )
        else:
            next_start, start_reason = (
                end,
                "no_overlap" if not overlap else "overlap_reduced_to_zero",
            )
        result[-1]["next_start_reason"] = start_reason
        require(
            start < next_start <= end and 0 <= end - next_start <= overlap,
            "Overlap does not advance safely.",
        )
        start, covered = (next_start, end)
    return result


def check_os_windows(text, windows, target, overlap):
    if not text:
        require(not windows, "Empty input produced children.")
        return
    require(
        windows[0]["start"] == 0 and windows[-1]["end"] == len(text),
        "Missing parent ends.",
    )
    require(
        interval_union_length([(w["start"], w["end"]) for w in windows]) == len(text),
        "Parent coverage gap.",
    )
    previous_start, covered, recovered = (-1, 0, "")
    for w in windows:
        a, b = (w["start"], w["end"])
        require(
            previous_start < a <= covered < b <= len(text) and b - a <= target,
            "Invalid child progress/size.",
        )
        require(
            covered - a <= overlap and w["text"] == text[a:b], "Overlap/text mismatch."
        )
        recovered += w["text"][covered - a :]
        previous_start, covered = (a, b)
    require(
        recovered == text, "Removing measured overlaps failed exact reconstruction."
    )


def clipped_coverage(records, sample):
    return interval_union_length(
        [
            (max(sample["start"], r["start"]), min(sample["end"], r["end"]))
            for r in records
            if r["document_id"] == sample["document_id"]
            and intersection_length(
                (sample["start"], sample["end"]), (r["start"], r["end"])
            )
        ]
    )


def reference_components(text):
    marker = "[EN summary]"
    index = text.find(marker)
    body = text if index < 0 else text[:index]
    summary = "" if index < 0 else text[index:]
    prefix = "[EN original]" if body.startswith("[EN original]") else ""
    lo = len(prefix)
    while lo < len(body) and body[lo].isspace():
        lo += 1
    hi = len(body)
    while hi > lo and body[hi - 1].isspace():
        hi -= 1
    return {
        "raw_reference_text": text,
        "source_excerpt": body[lo:hi],
        "reference_excerpt_offsets": [lo, hi],
        "english_summary_separate": summary,
        "language_marker_separate": prefix,
        "generated_context_prefix": "Document title + generated § section + heading, per builder evidence; excluded from excerpt alignment",
    }


def literal_occurrences(text, excerpt):
    if not excerpt:
        return []
    found = []
    start = 0
    while True:
        i = text.find(excerpt, start)
        if i < 0:
            break
        found.append((i, i + len(excerpt)))
        start = i + 1
    return found


def hybrid_review_ready(approved, independent, oversized, observations):
    return bool(
        approved
        and independent
        and independent.get("rubric")
        and oversized
        and observations
    )
