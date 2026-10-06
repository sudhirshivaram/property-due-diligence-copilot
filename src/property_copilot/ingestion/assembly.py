"""Assemble the intermediate corpus."""

from collections import Counter
from importlib.metadata import version
from property_copilot._display import display
import sys
import json
from copy import deepcopy
from .primitives import (
    assert_original_fields_preserved,
    preview_record,
    record_digest,
    show_full_record,
    show_rows,
    table_paragraphs,
    text_with_evidence,
)


class AssemblySteps:
    """Assembly steps; state belongs to the workflow instance."""

    def attach_existing_annotations(self, record, annotation):
        record["document_id"] = annotation["document_id"]
        record["region"] = annotation["region"]
        record["structural_annotations"] = deepcopy(
            {
                key: value
                for key, value in annotation.items()
                if key not in {"document_id", "region"}
            }
        )
        marker = self.marker_by_block.get(record["id"])
        record["structural_annotations"]["legal_marker_candidates"] = (
            [deepcopy(marker)] if marker else []
        )

    def step_6_assemble_the_simple_intermediate_representation(self):
        """Step 6 — Assemble the simple intermediate representation."""
        self.step5_inputs_before = record_digest(
            [
                self.document_boundaries,
                self.block_annotations,
                self.cell_paragraph_annotations,
                self.legal_marker_candidates,
            ]
        )
        self.assembled_blocks = deepcopy(self.ordered_blocks)
        for self.assembled in self.assembled_blocks:
            self.attach_existing_annotations(
                self.assembled, self.block_annotations[self.assembled["id"]]
            )
            if self.assembled["type"] == "table":
                for self.paragraph in table_paragraphs(self.assembled):
                    self.attach_existing_annotations(
                        self.paragraph,
                        self.cell_paragraph_annotations[self.paragraph["id"]],
                    )
        print("Assembled body blocks:", len(self.assembled_blocks))
        print(
            "Original IDs and order retained:",
            [b["id"] for b in self.assembled_blocks]
            == [b["id"] for b in self.ordered_blocks],
        )

    def step_6b_build_complete_document_descriptors_with_source_evidence(self):
        """6b. Build complete document descriptors with source evidence."""
        self.assembled_documents = []
        for self.boundary in self.document_boundaries:
            self.evidence = self.boundary["evidence"]
            self.title = self.block_by_id[self.evidence["title_block_id"]]
            self.subtitle = self.block_by_id[self.evidence["subtitle_block_id"]]
            self.metadata_table = self.block_by_id[
                self.evidence["metadata_table_block_id"]
            ]
            self.raw_rows = []
            for self.row in self.metadata_table["rows"]:
                self.label_cell, self.value_cell = self.row["cells"]
                self.raw_rows.append(
                    {
                        "row_index": self.row["row_index"],
                        "label_column_index": self.label_cell["column_index"],
                        "value_column_index": self.value_cell["column_index"],
                        "label_paragraphs": [
                            text_with_evidence(p) for p in self.label_cell["paragraphs"]
                        ],
                        "value_paragraphs": [
                            text_with_evidence(p) for p in self.value_cell["paragraphs"]
                        ],
                    }
                )
            self.assembled_documents.append(
                {
                    "document_id": self.boundary["document_id"],
                    "ordinal": self.boundary["ordinal"],
                    "source_titles": {
                        "title": text_with_evidence(self.title),
                        "subtitle": text_with_evidence(self.subtitle),
                    },
                    "block_range": {
                        key: self.boundary[key]
                        for key in (
                            "start_index",
                            "end_index_exclusive",
                            "first_body_position",
                            "last_body_position",
                        )
                    },
                    "source_metadata": {
                        "table_block_id": self.metadata_table["id"],
                        "table_source": deepcopy(self.metadata_table["source"]),
                        "rows": self.raw_rows,
                    },
                    "boundary_evidence": deepcopy(self.evidence),
                }
            )
        print("Document descriptors:", len(self.assembled_documents))
        print(
            "Metadata representation: verbatim table rows with paragraph/cell evidence; no inferred fields"
        )

    def step_6c_assemble_the_corpus_envelope(self):
        """6c. Assemble the corpus envelope."""
        self.corpus = {
            "schema_version": 1,
            "source": deepcopy(self.manifest),
            "parser": {
                "name": "python-docx",
                "version": version("python-docx"),
                "lxml_version": version("lxml"),
                "python_version": sys.version.split()[0],
                "xml_inspector": "xml.etree.ElementTree",
            },
            "documents": self.assembled_documents,
            "blocks": self.assembled_blocks,
            "auxiliary_content": deepcopy(self.auxiliary_content),
            "layout_markers": deepcopy(self.layout_markers),
            "diagnostics": {
                "inventory_counts": deepcopy(self.counts),
                "region_counts": dict(self.region_counts),
                "candidate_marker_counts": dict(
                    Counter((m["kind"] for m in self.legal_marker_candidates))
                ),
                "warnings": [
                    {
                        "code": "candidate_markers_only",
                        "count": len(self.legal_marker_candidates),
                        "message": "Legal-marker annotations remain candidates; no final legal hierarchy exists.",
                    },
                    {
                        "code": "unclassified_headings",
                        "count": len(self.unclassified_headings),
                        "message": "Unclassified full-text headings are preserved without assigning a legal role.",
                    },
                    {
                        "code": "rendered_page_numbers_unavailable",
                        "message": "Explicit breaks and footer field instructions are retained; rendered page numbers are unavailable.",
                    },
                ],
                "assembly_checks": {},
            },
        }
        show_rows(
            [
                {
                    "component": key,
                    "representation": type(value).__name__,
                    "entries": len(value) if isinstance(value, (dict, list)) else value,
                }
                for key, value in self.corpus.items()
            ]
        )
        show_full_record(
            {
                "schema_version": self.corpus["schema_version"],
                "source": self.corpus["source"],
                "parser": self.corpus["parser"],
            },
            "Corpus provenance and parser information",
        )

    def step_6d_inspect_representative_assembled_records(self):
        """6d. Inspect representative assembled records."""
        self.INSPECT_DOCUMENT_ORDINAL = 1
        self.ir_document = next(
            (
                d
                for d in self.corpus["documents"]
                if d["ordinal"] == self.INSPECT_DOCUMENT_ORDINAL
            )
        )
        self.ir_by_id = {b["id"]: b for b in self.corpus["blocks"]}
        self.ir_table = self.ir_by_id[
            self.ir_document["source_metadata"]["table_block_id"]
        ]
        self.ir_article = next(
            (
                b
                for b in self.corpus["blocks"]
                if b["document_id"] == self.ir_document["document_id"]
                and b["type"] == "paragraph"
                and any(
                    (
                        m["kind"] == "article"
                        for m in b["structural_annotations"]["legal_marker_candidates"]
                    )
                )
            )
        )
        display(self.ir_document)
        show_full_record(
            self.ir_document,
            "Complete document descriptor — all titles, metadata rows, range and evidence",
        )
        show_full_record(
            self.ir_article,
            "Complete representative article paragraph — original text, runs and candidate annotation",
        )
        show_full_record(
            self.ir_table,
            "Complete representative table — nested annotated cell paragraphs",
        )
        self.sequence_start = self.ir_document["block_range"]["start_index"]
        show_rows(
            [
                {
                    "index in corpus blocks": i,
                    "body position": b["position"],
                    "type": b["type"],
                    "document ID": b["document_id"],
                    "region": b["region"],
                    "style": b["style"]["resolved_id"],
                    "text preview": preview_record(b)["preview (display only)"],
                }
                for i, b in enumerate(
                    self.corpus["blocks"][
                        self.sequence_start : self.sequence_start + 4
                    ],
                    start=self.sequence_start,
                )
            ]
        )
        show_full_record(
            self.corpus["auxiliary_content"][0],
            "Auxiliary footer retained separately with field instructions",
        )

    def step_6e_check_assembly_integrity_and_json_compatibility(self):
        """6e. Check assembly integrity and JSON compatibility."""
        assert self.corpus["source"] == self.manifest
        assert self.corpus["source"] is not self.manifest
        assert len(self.corpus["documents"]) == len(self.document_boundaries) == 21
        for self.original, self.assembled in zip(
            self.ordered_blocks, self.corpus["blocks"], strict=True
        ):
            assert_original_fields_preserved(self.original, self.assembled)
        self.paragraphs_and_tables = list(self.corpus["blocks"]) + [
            p
            for b in self.corpus["blocks"]
            if b["type"] == "table"
            for p in table_paragraphs(b)
        ]
        self.all_ir_records = {b["id"]: b for b in self.paragraphs_and_tables}
        assert len(self.all_ir_records) == len(self.paragraphs_and_tables)
        for self.assembled in self.paragraphs_and_tables:
            self.annotation = (
                self.block_annotations
                if self.assembled["id"] in self.block_annotations
                else self.cell_paragraph_annotations
            )[self.assembled["id"]]
            assert self.assembled["document_id"] == self.annotation["document_id"]
            assert self.assembled["region"] == self.annotation["region"]
            self.structural = self.assembled["structural_annotations"]
            assert {
                k: v
                for k, v in self.structural.items()
                if k != "legal_marker_candidates"
            } == {
                k: v
                for k, v in self.annotation.items()
                if k not in {"document_id", "region"}
            }
            self.expected_marker = self.marker_by_block.get(self.assembled["id"])
            assert self.structural["legal_marker_candidates"] == (
                [self.expected_marker] if self.expected_marker else []
            )
        for self.descriptor, self.boundary in zip(
            self.corpus["documents"], self.document_boundaries, strict=True
        ):
            assert self.descriptor["document_id"] == self.boundary["document_id"]
            assert self.descriptor["boundary_evidence"] == self.boundary["evidence"]
            assert self.descriptor["block_range"] == {
                k: self.boundary[k] for k in self.descriptor["block_range"]
            }
            self.span = self.corpus["blocks"][
                self.descriptor["block_range"]["start_index"] : self.descriptor[
                    "block_range"
                ]["end_index_exclusive"]
            ]
            assert self.span and all(
                (b["document_id"] == self.descriptor["document_id"] for b in self.span)
            )
            for self.title in self.descriptor["source_titles"].values():
                self.evidence = self.all_ir_records[self.title["block_id"]]
                assert (
                    self.title["raw_text"] == self.evidence["raw_text"]
                    and self.title["source"] == self.evidence["source"]
                )
            self.metadata = self.descriptor["source_metadata"]
            self.table = self.all_ir_records[self.metadata["table_block_id"]]
            assert self.metadata["table_source"] == self.table["source"]
            for self.metadata_row, self.row in zip(
                self.metadata["rows"], self.table["rows"], strict=True
            ):
                assert self.metadata_row["row_index"] == self.row["row_index"]
                for self.field, self.column in [
                    ("label_paragraphs", 0),
                    ("value_paragraphs", 1),
                ]:
                    assert self.metadata_row[self.field] == [
                        text_with_evidence(p)
                        for p in self.row["cells"][self.column]["paragraphs"]
                    ]
            assert all(
                (
                    value is None or value in self.all_ir_records
                    for value in self.descriptor["boundary_evidence"].values()
                )
            )
        assert (
            self.corpus["auxiliary_content"] == self.auxiliary_content
            and self.corpus["auxiliary_content"] is not self.auxiliary_content
        )
        assert (
            self.corpus["layout_markers"] == self.layout_markers
            and self.corpus["layout_markers"] is not self.layout_markers
        )
        assert record_digest(self.ordered_blocks) == self.step4_digest_before
        assert (
            record_digest(
                [
                    self.document_boundaries,
                    self.block_annotations,
                    self.cell_paragraph_annotations,
                    self.legal_marker_candidates,
                ]
            )
            == self.step5_inputs_before
        )
        self.corpus["diagnostics"]["assembly_checks"] = {
            "original_fields_and_order": "passed",
            "document_ranges_and_membership": "passed",
            "metadata_and_title_evidence": "passed",
            "annotations_and_candidates": "passed",
            "auxiliary_content_and_layout": "passed",
            "step4_step5_inputs_unchanged": "passed",
        }
        self.json_utf8_size = len(
            json.dumps(self.corpus, ensure_ascii=False, allow_nan=False).encode("utf-8")
        )
        show_rows(
            [
                {"assembly check": check, "result": result}
                for check, result in self.corpus["diagnostics"][
                    "assembly_checks"
                ].items()
            ]
        )
        print(
            "PASS: corpus is UTF-8 JSON serializable; in-memory encoded size:",
            self.json_utf8_size,
            "bytes",
        )
        print(
            "PASS: 21 descriptors,",
            len(self.corpus["blocks"]),
            "ordered body records, unchanged source text/provenance, resolved evidence",
        )
