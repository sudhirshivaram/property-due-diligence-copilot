"""Ingestion: boundaries."""

from hashlib import sha256
from collections import Counter
import json
import re
from collections import defaultdict
from copy import deepcopy
from .primitives import (
    heading_level,
    is_region_marker,
    nonempty_paragraph,
    numbered_test_blocks,
    preview_record,
    show_full_record,
    show_rows,
    table_paragraphs,
    test_paragraph,
)


class BoundariesSteps:
    """Boundaries steps; state belongs to the workflow instance."""

    def matches_metadata_layout(self, block):
        if block["type"] != "table" or len(block["rows"]) != len(self.METADATA_LABELS):
            return False
        for row, expected_label in zip(block["rows"], self.METADATA_LABELS):
            if len(row["cells"]) != 2:
                return False
            label_paragraphs = row["cells"][0]["paragraphs"]
            if (
                len(label_paragraphs) != 1
                or label_paragraphs[0]["raw_text"] != expected_label
            ):
                return False
        return True

    def discover_document_starts(self, blocks):
        starts, audit = ([], [])
        for index, block in enumerate(blocks):
            if heading_level(block) != 1:
                continue
            follows = blocks[index + 1 : index + 3]
            subtitle_ok = (
                len(follows) == 2
                and nonempty_paragraph(follows[0])
                and (heading_level(follows[0]) is None)
            )
            table_ok = len(follows) == 2 and self.matches_metadata_layout(follows[1])
            accepted = nonempty_paragraph(block) and subtitle_ok and table_ok
            audit.append(
                {
                    "index": index,
                    "position": block["position"],
                    "title": block["raw_text"],
                    "subtitle pattern": subtitle_ok,
                    "table-label pattern": table_ok,
                    "verified start": accepted,
                }
            )
            if accepted:
                starts.append(index)
        if not starts:
            raise ValueError(
                "No source starts match the title/subtitle/table pattern; review source structure"
            )
        unmatched = [
            a["position"]
            for a in audit
            if not a["verified start"] and a["index"] >= starts[0]
        ]
        if unmatched:
            raise ValueError(
                f"Unmatched Heading1 inside source material at body positions {unmatched}; review"
            )
        return (starts, audit)

    def step_5_identify_document_boundaries_and_structural_markers(self):
        """Step 5 — Identify document boundaries and structural markers."""
        self.step4_digest_before = sha256(
            json.dumps(self.ordered_blocks, ensure_ascii=False, sort_keys=True).encode(
                "utf-8"
            )
        ).hexdigest()
        self.METADATA_LABELS = (
            "Юрисдикция / Jurisdiction",
            "Източник / Source URL",
            "ДВ / Official reference",
            "Версия / Version date",
            "Достъпено / Accessed",
            "Бележка / Note",
        )
        self.FULL_TEXT_MARKER = "Пълен текст / Full text"
        self.REFERENCE_MARKER = "Извлечени правила (reference) / Extracted rules"
        self.source_start_indices, self.boundary_audit = self.discover_document_starts(
            self.ordered_blocks
        )
        show_rows(self.boundary_audit)
        print("Verified source-document starts:", len(self.source_start_indices))
        assert len(self.source_start_indices) == 21, (
            "This source snapshot should contain 21 verified sources; review changes"
        )

    def label_documents(self, blocks):
        starts, audit = self.discover_document_starts(blocks)
        documents, annotations = ([], {})
        for block in blocks[: starts[0]]:
            annotations[block["id"]] = {
                "document_id": None,
                "region": "front_matter",
                "word_heading_level": heading_level(block),
                "region_evidence_block_id": None,
            }
        for ordinal, start in enumerate(starts, start=1):
            stop = starts[ordinal] if ordinal < len(starts) else len(blocks)
            full = [
                i
                for i in range(start, stop)
                if is_region_marker(blocks[i], self.FULL_TEXT_MARKER)
            ]
            refs = [
                i
                for i in range(start, stop)
                if is_region_marker(blocks[i], self.REFERENCE_MARKER)
            ]
            if len(full) != 1 or len(refs) > 1:
                raise ValueError(
                    f"Review source at body position {blocks[start]['position']}: full-text markers={len(full)}, reference markers={len(refs)}"
                )
            if full[0] <= start + 2 or (refs and (not start + 2 < refs[0] < full[0])):
                raise ValueError(
                    f"Region markers out of order at body position {blocks[start]['position']}"
                )
            document_id = "source-document:" + blocks[start]["id"]
            documents.append(
                {
                    "document_id": document_id,
                    "ordinal": ordinal,
                    "title": blocks[start]["raw_text"],
                    "start_index": start,
                    "end_index_exclusive": stop,
                    "first_body_position": blocks[start]["position"],
                    "last_body_position": blocks[stop - 1]["position"],
                    "evidence": {
                        "title_block_id": blocks[start]["id"],
                        "subtitle_block_id": blocks[start + 1]["id"],
                        "metadata_table_block_id": blocks[start + 2]["id"],
                        "reference_marker_block_id": blocks[refs[0]]["id"]
                        if refs
                        else None,
                        "full_text_marker_block_id": blocks[full[0]]["id"],
                    },
                }
            )
            for i in range(start, stop):
                if i >= full[0]:
                    region, evidence_id = ("full_text", blocks[full[0]]["id"])
                elif refs and i >= refs[0]:
                    region, evidence_id = ("reference_rules", blocks[refs[0]]["id"])
                else:
                    region, evidence_id = ("document_metadata", blocks[start + 2]["id"])
                block = blocks[i]
                annotations[block["id"]] = {
                    "document_id": document_id,
                    "region": region,
                    "word_heading_level": heading_level(block),
                    "region_evidence_block_id": evidence_id,
                }
        return (documents, annotations)

    def step_5b_assign_regions_using_explicit_delimiters(self):
        """5b. Assign regions using explicit delimiters."""
        self.document_boundaries, self.block_annotations = self.label_documents(
            self.ordered_blocks
        )
        self.cell_paragraph_annotations = {}
        for self.block in self.ordered_blocks:
            if self.block["type"] == "table":
                for self.paragraph in table_paragraphs(self.block):
                    self.inherited = dict(self.block_annotations[self.block["id"]])
                    self.inherited.update(
                        container_block_id=self.block["id"],
                        word_heading_level=heading_level(self.paragraph),
                    )
                    self.cell_paragraph_annotations[self.paragraph["id"]] = (
                        self.inherited
                    )
        self.block_by_id = {b["id"]: b for b in self.ordered_blocks}
        self.region_counts = Counter(
            (a["region"] for a in self.block_annotations.values())
        )
        self.inventory = []
        for self.document in self.document_boundaries:
            self.span = self.ordered_blocks[
                self.document["start_index"] : self.document["end_index_exclusive"]
            ]
            self.regions = Counter(
                (self.block_annotations[b["id"]]["region"] for b in self.span)
            )
            self.inventory.append(
                {
                    "source": self.document["ordinal"],
                    "title": self.document["title"],
                    "first body position": self.document["first_body_position"],
                    "last body position (inclusive)": self.document[
                        "last_body_position"
                    ],
                    "document_metadata": self.regions["document_metadata"],
                    "reference_rules": self.regions["reference_rules"],
                    "full_text": self.regions["full_text"],
                    "full-text marker position": self.block_by_id[
                        self.document["evidence"]["full_text_marker_block_id"]
                    ]["position"],
                }
            )
        show_rows(self.inventory)
        show_rows(
            [
                {"region": region, "body blocks": count}
                for region, count in self.region_counts.items()
            ]
        )
        print(
            "Table-cell paragraphs inheriting their table's region:",
            len(self.cell_paragraph_annotations),
        )

    def annotated_preview(self, block, limit=110):
        preview = preview_record(block)
        annotation = self.block_annotations[block["id"]]
        return {
            "body position": block["position"],
            "type": block["type"],
            "style": block["style"]["resolved_id"],
            "region": annotation["region"],
            "preview": preview["preview (display only)"][:limit],
        }

    def step_5c_review_complete_spans_and_boundary_evidence(self):
        """5c. Review complete spans and boundary evidence."""
        print("Corpus front matter: first five blocks")
        show_rows([self.annotated_preview(b) for b in self.ordered_blocks[:5]])
        self.windows = []
        for self.document in self.document_boundaries:
            self.start = self.document["start_index"]
            for self.b in self.ordered_blocks[max(0, self.start - 1) : self.start + 4]:
                self.windows.append(
                    {
                        "source start": self.document["ordinal"],
                        **self.annotated_preview(self.b),
                    }
                )
        show_rows(self.windows)
        self.SELECTED_DOCUMENT_ORDINAL = 20
        self.selected_document = next(
            (
                d
                for d in self.document_boundaries
                if d["ordinal"] == self.SELECTED_DOCUMENT_ORDINAL
            )
        )
        self.start, self.stop = (
            self.selected_document["start_index"],
            self.selected_document["end_index_exclusive"],
        )
        show_full_record(
            self.selected_document,
            "Complete document boundary descriptor and evidence IDs",
        )
        self.intervals = []
        for self.i in range(self.start, self.stop):
            self.b = self.ordered_blocks[self.i]
            self.region = self.block_annotations[self.b["id"]]["region"]
            if not self.intervals or self.intervals[-1]["region"] != self.region:
                self.intervals.append(
                    {
                        "region": self.region,
                        "start index": self.i,
                        "end index exclusive": self.i + 1,
                        "first body position": self.b["position"],
                        "last body position": self.b["position"],
                    }
                )
            else:
                self.intervals[-1].update(
                    {
                        "end index exclusive": self.i + 1,
                        "last body position": self.b["position"],
                    }
                )
        show_rows(self.intervals)
        print("Selected source opening:")
        show_rows(
            [
                self.annotated_preview(b)
                for b in self.ordered_blocks[self.start : self.start + 5]
            ]
        )
        print("Selected source ending and next source:")
        show_rows(
            [
                self.annotated_preview(b)
                for b in self.ordered_blocks[
                    max(self.start, self.stop - 3) : min(
                        len(self.ordered_blocks), self.stop + 3
                    )
                ]
            ]
        )
        self.complete_span_view = []
        for self.b in self.ordered_blocks[self.start : self.stop]:
            self.entry = {
                "body_position": self.b["position"],
                "block_id": self.b["id"],
                "source": self.b["source"],
                "region": self.block_annotations[self.b["id"]]["region"],
                "type": self.b["type"],
                "style": self.b["style"],
            }
            if self.b["type"] == "paragraph":
                self.entry.update(
                    raw_text=self.b["raw_text"], break_markers=self.b["break_markers"]
                )
            else:
                self.entry["rows"] = [
                    {
                        "row_index": row["row_index"],
                        "cells": [
                            {
                                "column_index": cell["column_index"],
                                "paragraphs": [
                                    {"block_id": p["id"], "raw_text": p["raw_text"]}
                                    for p in cell["paragraphs"]
                                ],
                            }
                            for cell in row["cells"]
                        ],
                    }
                    for row in self.b["rows"]
                ]
            self.complete_span_view.append(self.entry)
        show_full_record(
            self.complete_span_view,
            "Every block in the selected document span — full text, no truncation",
        )

    def detect_legal_candidate(self, block, annotation):
        if block["type"] != "paragraph" or annotation["region"] != "full_text":
            return None
        if block["raw_text"] in {self.FULL_TEXT_MARKER, self.REFERENCE_MARKER}:
            return None
        level = heading_level(block)
        for kind, pattern, requires_heading in self.MARKER_RULES:
            if requires_heading and level not in {2, 3}:
                continue
            match = pattern.match(block["raw_text"])
            if match:
                return {
                    "kind": kind,
                    "status": "candidate",
                    "block_id": block["id"],
                    "document_id": annotation["document_id"],
                    "source": dict(block["source"]),
                    "matched_label": match.group("label"),
                    "character_span": list(match.span("label")),
                    "word_heading_level": level,
                    "rule": "leading_label_and_heading"
                    if requires_heading
                    else "leading_numbered_label",
                }
        return None

    def step_5d_identify_candidate_structural_legal_markers(self):
        """5d. Identify candidate structural/legal markers."""
        self.MARKER_RULES = [
            (
                "part",
                re.compile(
                    "^[ \\t]*(?P<label>Част\\b(?:[ \\t]+[^\\s.]+)?)", re.IGNORECASE
                ),
                True,
            ),
            (
                "chapter",
                re.compile(
                    "^[ \\t]*(?P<label>Глава\\b(?:[ \\t]+[^\\s.]+)?)", re.IGNORECASE
                ),
                True,
            ),
            (
                "section",
                re.compile(
                    "^[ \\t]*(?P<label>Раздел\\b(?:[ \\t]+[^\\s.]+)?)", re.IGNORECASE
                ),
                True,
            ),
            (
                "article",
                re.compile(
                    "^[ \\t]*(?P<label>(?:Чл\\.|Член\\b)[ \\t]*[0-9]+[а-я]?)(?=$|[\\s.,:;()])",
                    re.IGNORECASE,
                ),
                False,
            ),
            (
                "paragraph_sign",
                re.compile(
                    "^[ \\t]*(?P<label>§[ \\t]*[0-9]+[а-я]?)(?=$|[\\s.,:;()])",
                    re.IGNORECASE,
                ),
                False,
            ),
            (
                "annex",
                re.compile(
                    "^[ \\t]*(?P<label>Приложение\\b(?:[ \\t]+№?[ \\t]*(?:[0-9]+[а-я]?|[IVXLCDMІ]+)\\b)?)",
                    re.IGNORECASE,
                ),
                True,
            ),
        ]
        self.legal_marker_candidates = [
            candidate
            for b in self.ordered_blocks
            if (
                candidate := self.detect_legal_candidate(
                    b, self.block_annotations[b["id"]]
                )
            )
            is not None
        ]
        self.marker_by_block = {m["block_id"]: m for m in self.legal_marker_candidates}
        show_rows(
            [
                {"candidate kind": kind, "count": count}
                for kind, count in Counter(
                    (m["kind"] for m in self.legal_marker_candidates)
                ).items()
            ]
        )
        self.representative_markers = []
        for self.kind in [
            "part",
            "chapter",
            "section",
            "article",
            "paragraph_sign",
            "annex",
        ]:
            self.representative_markers.append(
                next(
                    (m for m in self.legal_marker_candidates if m["kind"] == self.kind)
                )
            )
        self.representative_markers.append(
            next(
                (
                    m
                    for m in self.legal_marker_candidates
                    if m["kind"] == "article" and m["matched_label"].startswith("Член")
                )
            )
        )
        show_rows(
            [
                {
                    "kind": m["kind"],
                    "body position": self.block_by_id[m["block_id"]]["position"],
                    "matched label (verbatim)": m["matched_label"],
                    "Word heading level": m["word_heading_level"],
                    "rule": m["rule"],
                    "source preview": self.block_by_id[m["block_id"]]["raw_text"][:250],
                }
                for m in self.representative_markers
            ]
        )
        show_full_record(
            self.representative_markers,
            "Candidate marker annotations with exact evidence locations",
        )
        self.unclassified_headings = [
            b
            for b in self.ordered_blocks
            if self.block_annotations[b["id"]]["region"] == "full_text"
            and heading_level(b) in {2, 3}
            and (b["raw_text"] != self.FULL_TEXT_MARKER)
            and (b["id"] not in self.marker_by_block)
        ]
        print(
            "Full-text headings retained without a candidate classification:",
            len(self.unclassified_headings),
        )
        show_rows([self.annotated_preview(b) for b in self.unclassified_headings[:8]])
        self.heading_occurrences = defaultdict(list)
        for self.b in self.unclassified_headings:
            self.heading_occurrences[self.b["raw_text"]].append(self.b["position"])
        show_rows(
            [
                {
                    "repeated heading (unchanged)": text,
                    "occurrences": len(positions),
                    "first body positions": positions[:8],
                }
                for text, positions in self.heading_occurrences.items()
                if len(positions) > 1
            ][:5]
        )
        print(
            "Part and Chapter examples share Heading2: this is Word formatting, not a final legal parent/child relationship."
        )

    def step_5e_check_coverage_conservative_behavior_and_unchanged_records(self):
        """5e. Check coverage, conservative behavior, and unchanged records."""
        assert len(self.document_boundaries) == 21
        assert len(self.block_annotations) == len(self.ordered_blocks)
        assert set(self.block_annotations) == {b["id"] for b in self.ordered_blocks}
        assert sum(self.region_counts.values()) == len(self.ordered_blocks)
        assert (
            self.document_boundaries[0]["start_index"] == self.source_start_indices[0]
        )
        assert self.document_boundaries[-1]["end_index_exclusive"] == len(
            self.ordered_blocks
        )
        for self.left, self.right in zip(
            self.document_boundaries, self.document_boundaries[1:]
        ):
            assert self.left["end_index_exclusive"] == self.right["start_index"]
        for self.d in self.document_boundaries:
            self.span = self.ordered_blocks[
                self.d["start_index"] : self.d["end_index_exclusive"]
            ]
            assert all(
                (
                    self.block_annotations[b["id"]]["document_id"]
                    == self.d["document_id"]
                    for b in self.span
                )
            )
            assert (
                sum((is_region_marker(b, self.FULL_TEXT_MARKER) for b in self.span))
                == 1
            )
            assert (
                self.block_annotations[self.d["evidence"]["full_text_marker_block_id"]][
                    "region"
                ]
                == "full_text"
            )
            if self.d["evidence"]["reference_marker_block_id"]:
                assert (
                    self.block_annotations[
                        self.d["evidence"]["reference_marker_block_id"]
                    ]["region"]
                    == "reference_rules"
                )
            assert all(
                (
                    e is None or e in self.block_by_id
                    for e in self.d["evidence"].values()
                )
            )
        assert all(
            (
                self.block_annotations[b["id"]]["document_id"] is None
                for b in self.ordered_blocks[: self.source_start_indices[0]]
            )
        )
        assert all(
            (
                a["document_id"]
                == self.block_annotations[a["container_block_id"]]["document_id"]
                and a["region"]
                == self.block_annotations[a["container_block_id"]]["region"]
                for a in self.cell_paragraph_annotations.values()
            )
        )
        assert len(self.cell_paragraph_annotations) == len(
            [
                p
                for b in self.ordered_blocks
                if b["type"] == "table"
                for p in table_paragraphs(b)
            ]
        )
        assert (
            len(
                [
                    d
                    for d in self.document_boundaries
                    if d["evidence"]["reference_marker_block_id"] is None
                ]
            )
            == 2
        )
        for self.marker in self.legal_marker_candidates:
            self.b = self.block_by_id[self.marker["block_id"]]
            self.lo, self.hi = self.marker["character_span"]
            assert self.b["raw_text"][self.lo : self.hi] == self.marker["matched_label"]
            assert self.marker["source"] == self.b["source"]
            assert self.block_annotations[self.b["id"]]["region"] == "full_text"
            assert self.marker["word_heading_level"] == heading_level(self.b)
        assert (
            sha256(
                json.dumps(
                    self.ordered_blocks, ensure_ascii=False, sort_keys=True
                ).encode("utf-8")
            ).hexdigest()
            == self.step4_digest_before
        )
        print(
            "PASS: 21 contiguous document spans, front matter, exact region coverage, optional references, cell inheritance, marker evidence, unchanged Step 4 records"
        )

    def step_5e_check_coverage_conservative_behavior_and_unchanged_records_2(self):
        """5e. Check coverage, conservative behavior, and unchanged records."""
        self.sample_doc = [
            test_paragraph("Test source", "Heading1"),
            test_paragraph("Subtitle"),
            deepcopy(self.first_table_record),
            test_paragraph(self.FULL_TEXT_MARKER, "Heading2"),
            test_paragraph("Чл. 2а. Exact text."),
        ]
        self.minimal = numbered_test_blocks(self.sample_doc)
        self.test_documents, self.test_annotations = self.label_documents(self.minimal)
        assert (
            len(self.test_documents) == 1
            and self.test_documents[0]["evidence"]["reference_marker_block_id"] is None
        )
        assert self.test_annotations[self.minimal[-1]["id"]]["region"] == "full_text"
        self.with_reference = numbered_test_blocks(
            self.sample_doc[:3]
            + [
                test_paragraph(self.REFERENCE_MARKER, "Heading2"),
                test_paragraph("чл. 8, т. 1 — reference excerpt"),
            ]
            + self.sample_doc[3:]
        )
        self._, self.reference_annotations = self.label_documents(self.with_reference)
        assert (
            self.reference_annotations[self.with_reference[4]["id"]]["region"]
            == "reference_rules"
        )
        self.failures = {
            "missing full-text marker": self.sample_doc[:3] + self.sample_doc[4:],
            "duplicate full-text marker": self.sample_doc
            + [test_paragraph(self.FULL_TEXT_MARKER, "Heading2")],
            "reversed region markers": self.sample_doc
            + [test_paragraph(self.REFERENCE_MARKER, "Heading2")],
            "duplicate reference marker": self.sample_doc[:3]
            + [test_paragraph(self.REFERENCE_MARKER, "Heading2")] * 2
            + self.sample_doc[3:],
            "unmatched internal Heading1": self.sample_doc
            + [test_paragraph("Unexpected heading", "Heading1")],
            "marker text with wrong style": self.sample_doc[:3]
            + [test_paragraph(self.FULL_TEXT_MARKER)]
            + self.sample_doc[4:],
        }
        for self.case, self.blocks in self.failures.items():
            try:
                self.label_documents(numbered_test_blocks(self.blocks))
            except ValueError:
                pass
            else:
                raise AssertionError(
                    f"Expected an explicit review failure: {self.case}"
                )
        self.candidate_cases = [
            ("Чл. 2а. Текст", "Normal", "full_text", "article"),
            ("Член 1", "Heading3", "full_text", "article"),
            ("  § 1а. Текст", "Normal", "full_text", "paragraph_sign"),
            ("ГЛАВА II", "Heading2", "full_text", "chapter"),
            ("Раздел ІV", "Heading3", "full_text", "section"),
            ("Приложение № 2а към чл. 7", "Heading2", "full_text", "annex"),
            ("Съгласно чл. 1 се изисква...", "Normal", "full_text", None),
            ("Членове:", "Normal", "full_text", None),
            ("Глава първа.", "Normal", "full_text", None),
            ("Чл. 8. Reference excerpt", "Normal", "reference_rules", None),
            ("Член 1", "Heading3", "document_metadata", None),
        ]
        for (
            self.text,
            self.style,
            self.region,
            self.expected_kind,
        ) in self.candidate_cases:
            self.block = test_paragraph(self.text, self.style)
            self.result = self.detect_legal_candidate(
                self.block, {"document_id": "test-document", "region": self.region}
            )
            assert (
                self.result["kind"] if self.result else None
            ) == self.expected_kind, self.text
            assert self.block["raw_text"] == self.text
        print(
            "PASS: optional reference region; six malformed-boundary/marker cases; eleven positive and negative legal-marker cases"
        )
