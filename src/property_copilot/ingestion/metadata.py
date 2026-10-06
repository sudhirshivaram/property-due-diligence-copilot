"""Ingestion: metadata."""

from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json
from copy import deepcopy
from .primitives import (
    paragraph_evidence_display,
    record_digest,
    show_full_record,
    show_rows,
    table_paragraphs,
    text_with_evidence,
)


class MetadataSteps:
    """Metadata steps; state belongs to the workflow instance."""

    def classified_source_rows(self, descriptor):
        metadata = descriptor["source_metadata"]
        fields = []
        for row in metadata["rows"]:
            labels = [p["raw_text"] for p in row["label_paragraphs"]]
            field_key = (
                self.FIELD_BY_SOURCE_LABEL.get(labels[0]) if len(labels) == 1 else None
            )
            fields.append(
                {
                    "field": field_key,
                    "raw_labels": labels,
                    "raw_values": [p["raw_text"] for p in row["value_paragraphs"]],
                    "evidence": {
                        "table_block_id": metadata["table_block_id"],
                        "table_source": deepcopy(metadata["table_source"]),
                        "row_index": row["row_index"],
                        "label_column_index": row["label_column_index"],
                        "value_column_index": row["value_column_index"],
                        "label_paragraphs": deepcopy(row["label_paragraphs"]),
                        "value_paragraphs": deepcopy(row["value_paragraphs"]),
                    },
                }
            )
        return fields

    def step_7_separate_extracted_generated_structurally_interpreted_and_deferred_me(
        self,
    ):
        """Step 7 — Separate extracted, generated, structurally interpreted, and deferred metadata."""
        self.step6_field_names = [
            key for key in self.corpus if key != "metadata_provenance"
        ]
        self.step6_before_metadata = record_digest(
            {key: self.corpus[key] for key in self.step6_field_names}
        )
        self.FIELD_BY_SOURCE_LABEL = {
            "Юрисдикция / Jurisdiction": "jurisdiction",
            "Източник / Source URL": "source_url",
            "ДВ / Official reference": "official_reference",
            "Версия / Version date": "version_date",
            "Достъпено / Accessed": "accessed",
            "Бележка / Note": "note",
        }
        self.metadata_blocks_by_id = {b["id"]: b for b in self.corpus["blocks"]}
        self.metadata_documents = []
        for self.descriptor in self.corpus["documents"]:
            self.start = self.descriptor["block_range"]["start_index"]
            self.end = self.descriptor["block_range"]["end_index_exclusive"]
            self.span = self.corpus["blocks"][self.start : self.end]
            self.explicit_markers = []
            for self.key in ["reference_marker_block_id", "full_text_marker_block_id"]:
                self.marker_id = self.descriptor["boundary_evidence"][self.key]
                if self.marker_id is not None:
                    self.marker_block = self.metadata_blocks_by_id[self.marker_id]
                    self.explicit_markers.append(
                        {
                            **text_with_evidence(self.marker_block),
                            "explicit_style_id": self.marker_block["style"][
                                "explicit_id"
                            ],
                        }
                    )
            self.regions = []
            for self.region in dict.fromkeys((b["region"] for b in self.span)):
                self.region_blocks = [
                    b for b in self.span if b["region"] == self.region
                ]
                self.regions.append(
                    {
                        "region": self.region,
                        "evidence_block_ids": list(
                            dict.fromkeys(
                                (
                                    b["structural_annotations"][
                                        "region_evidence_block_id"
                                    ]
                                    for b in self.region_blocks
                                )
                            )
                        ),
                    }
                )
            self.candidates = [
                deepcopy(m)
                for b in self.span
                for m in b["structural_annotations"]["legal_marker_candidates"]
            ]
            self.metadata_documents.append(
                {
                    "document_id": self.descriptor["document_id"],
                    "source_extracted": {
                        "titles": deepcopy(self.descriptor["source_titles"]),
                        "metadata_fields": self.classified_source_rows(self.descriptor),
                        "explicit_region_marker_texts": self.explicit_markers,
                    },
                    "generated": {
                        "document_id": self.descriptor["document_id"],
                        "encounter_ordinal": self.descriptor["ordinal"],
                        "body_block_count": len(self.span),
                        "first_body_position": self.descriptor["block_range"][
                            "first_body_position"
                        ],
                        "last_body_position": self.descriptor["block_range"][
                            "last_body_position"
                        ],
                    },
                    "structurally_interpreted": {
                        "block_range": deepcopy(self.descriptor["block_range"]),
                        "boundary_evidence": deepcopy(
                            self.descriptor["boundary_evidence"]
                        ),
                        "regions": self.regions,
                        "candidate_legal_markers": self.candidates,
                    },
                }
            )
        print(
            "Classified document metadata for",
            len(self.metadata_documents),
            "documents",
        )
        print(
            "Source metadata rows retained:",
            sum(
                (
                    len(d["source_extracted"]["metadata_fields"])
                    for d in self.metadata_documents
                )
            ),
        )

    def step_7b_keep_package_properties_separate_from_legal_document_metadata(self):
        """7b. Keep package properties separate from legal-document metadata."""
        self.CORE_PROPERTIES_PART = "docProps/core.xml"
        with ZipFile(BytesIO(self.docx_bytes)) as self.metadata_package:
            self.core_properties_root = ET.fromstring(
                self.metadata_package.read(self.CORE_PROPERTIES_PART)
            )
        self.package_properties = []
        for self.index, self.element in enumerate(self.core_properties_root):
            self.package_properties.append(
                {
                    "qualified_name": self.element.tag,
                    "name": self.element.tag.rsplit("}", 1)[-1],
                    "raw_value": self.element.text,
                    "attributes": dict(self.element.attrib),
                    "source": {
                        "part": self.CORE_PROPERTIES_PART,
                        "path": f"/coreProperties/children/{self.index}",
                    },
                }
            )
        show_rows(
            [
                {
                    "property": p["name"],
                    "raw value": p["raw_value"],
                    "category": "source_extracted — DOCX package only",
                    "evidence": p["source"]["part"] + ":" + p["source"]["path"],
                }
                for p in self.package_properties
            ]
        )

    def step_7c_make_generated_interpreted_and_deferred_fields_explicit(self):
        """7c. Make generated, interpreted, and deferred fields explicit."""
        self.DEFERRED_METADATA = [
            {
                "field": "normalized_legal_hierarchy",
                "status": "deferred",
                "reason": "Candidate markers are not a final legal tree.",
            },
            {
                "field": "legal_date_interpretation",
                "status": "deferred",
                "reason": "Effective dates, amendment applicability and legal currency require later interpretation; source date strings stay unchanged.",
            },
            {
                "field": "language_classification",
                "status": "deferred",
                "reason": "No language detection or inferred language labels now.",
            },
            {
                "field": "topic_labels",
                "status": "deferred",
                "reason": "No inferred topic or domain labels now.",
            },
            {
                "field": "property_facts",
                "status": "deferred",
                "reason": "No extraction or inference of property/investment facts now.",
            },
            {
                "field": "normalized_jurisdiction_and_source_fields",
                "status": "deferred",
                "reason": "Keep raw jurisdiction, URL, reference and date values; no reconciliation or normalization.",
            },
            {
                "field": "chunk_level_metadata",
                "status": "deferred",
                "reason": "Chunks do not exist in this stage.",
            },
            {
                "field": "document_to_chunk_metadata_inheritance",
                "status": "deferred",
                "reason": "Which document fields to copy or inherit is explicitly undecided until chunking/metadata design.",
            },
        ]
        self.METADATA_FIELD_GUIDE = [
            {
                "field_path": "documents[*].source_titles / source_metadata.rows",
                "category": "source_extracted",
                "note": "Verbatim source values and evidence, not verified legal facts.",
            },
            {
                "field_path": "blocks[*].style.explicit_id / raw_text / run events",
                "category": "source_extracted",
                "note": "Source-authored text, applied style and explicit markers; text is not itself a derived legal role.",
            },
            {
                "field_path": "auxiliary_content[*].blocks[*].runs[*].events",
                "category": "source_extracted",
                "note": "Original footer/header text and field instructions, not rendered page numbers.",
            },
            {
                "field_path": "metadata_provenance.source_extracted.package_properties",
                "category": "source_extracted",
                "note": "Package-level properties only; never substituted for legal dates.",
            },
            {
                "field_path": "source / parser / schema_version",
                "category": "generated",
                "note": "Local locator, measured bytes, hash and software provenance; source URLs inside tables are a different category.",
            },
            {
                "field_path": "documents[*].document_id / ordinal; blocks[*].id / position / source",
                "category": "generated",
                "note": "Generated identity, encounter order and evidence addresses.",
            },
            {
                "field_path": "diagnostics.*_counts / assembly_checks",
                "category": "generated",
                "note": "Computed counts/check results; some counts summarize structurally interpreted labels.",
            },
            {
                "field_path": "documents[*].block_range / boundary_evidence; blocks[*].document_id / region",
                "category": "structurally_interpreted",
                "note": "Membership and regions are inferred from the observed structural pattern; the ID value itself is generated.",
            },
            {
                "field_path": "blocks[*].style.resolved_id / structural_annotations.word_heading_level",
                "category": "structurally_interpreted",
                "note": "Default style resolution and numeric level interpretation do not establish a legal hierarchy.",
            },
            {
                "field_path": "blocks[*].structural_annotations.legal_marker_candidates",
                "category": "structurally_interpreted",
                "note": "Candidate marker roles with exact matched source labels and evidence spans.",
            },
        ]
        self.metadata_provenance = {
            "source_extracted": {"package_properties": self.package_properties},
            "generated": {
                "source_locator_and_fingerprint": deepcopy(self.corpus["source"]),
                "parser": deepcopy(self.corpus["parser"]),
                "schema_version": self.corpus["schema_version"],
                "inventory_counts": deepcopy(
                    self.corpus["diagnostics"]["inventory_counts"]
                ),
            },
            "documents": self.metadata_documents,
            "deferred": deepcopy(self.DEFERRED_METADATA),
            "field_guide": deepcopy(self.METADATA_FIELD_GUIDE),
        }
        self.corpus["metadata_provenance"] = self.metadata_provenance
        show_rows(self.METADATA_FIELD_GUIDE)
        show_rows(self.DEFERRED_METADATA)

    def step_7d_actual_document_example_black_sea_coast_spatial_development_act(self):
        """7d. Actual document example — Black Sea Coast Spatial Development Act."""
        self.REQUESTED_SOURCE_SUBTITLE = "Black Sea Coast Spatial Development Act"
        self.matching_documents = [
            d
            for d in self.corpus["documents"]
            if d["source_titles"]["subtitle"]["raw_text"]
            == self.REQUESTED_SOURCE_SUBTITLE
        ]
        if len(self.matching_documents) != 1:
            raise ValueError(
                "Expected exactly one named Act; review the document inventory"
            )
        self.metadata_example_document = self.matching_documents[0]
        self.metadata_example = next(
            (
                d
                for d in self.metadata_provenance["documents"]
                if d["document_id"] == self.metadata_example_document["document_id"]
            )
        )
        print(
            "Selected:",
            self.metadata_example_document["source_titles"]["subtitle"]["raw_text"],
            "— actual source ordinal",
            self.metadata_example_document["ordinal"],
        )
        show_rows(
            [
                {
                    "actual ordinal": d["ordinal"],
                    "source title": d["source_titles"]["title"]["raw_text"],
                    "source subtitle": d["source_titles"]["subtitle"]["raw_text"],
                }
                for d in self.corpus["documents"]
                if d["ordinal"] in {self.metadata_example_document["ordinal"], 10}
            ]
        )
        print("1. Source/extracted metadata — values unchanged")
        self.source_display = [
            {
                "field": key,
                "original label": "source title paragraph",
                "raw value": title["raw_text"],
                "category": "source_extracted",
                "evidence": title["source"]["part"] + ":" + title["source"]["path"],
            }
            for key, title in self.metadata_example["source_extracted"][
                "titles"
            ].items()
        ]
        self.source_display += [
            {
                "field": field["field"],
                "original label": "\n".join(field["raw_labels"]),
                "raw value": "\n".join(field["raw_values"]),
                "category": "source_extracted",
                "evidence": paragraph_evidence_display(
                    field["evidence"]["value_paragraphs"]
                ),
            }
            for field in self.metadata_example["source_extracted"]["metadata_fields"]
        ]
        show_rows(self.source_display)
        print("2. Generated ingestion metadata — not source legal assertions")
        self.generated_display = [
            {
                "field": key,
                "value": value,
                "category": "generated",
                "basis": "existing ingestion record",
            }
            for key, value in self.metadata_example["generated"].items()
        ]
        self.generated_display += [
            {
                "field": "file." + key,
                "value": value,
                "category": "generated",
                "basis": "local source locator or measured fingerprint",
            }
            for key, value in self.metadata_provenance["generated"][
                "source_locator_and_fingerprint"
            ].items()
        ]
        self.generated_display += [
            {
                "field": "parser",
                "value": json.dumps(
                    self.metadata_provenance["generated"]["parser"], ensure_ascii=False
                ),
                "category": "generated",
                "basis": "installed software",
            },
            {
                "field": "schema_version",
                "value": self.metadata_provenance["generated"]["schema_version"],
                "category": "generated",
                "basis": "notebook record format",
            },
        ]
        show_rows(self.generated_display)
        print("3. Structurally interpreted metadata — evidence-backed code decisions")
        self.interpreted = self.metadata_example["structurally_interpreted"]
        self.interpreted_display = [
            {
                "field": "document boundary range",
                "value": json.dumps(self.interpreted["block_range"]),
                "category": "structurally_interpreted",
                "evidence": json.dumps(
                    self.interpreted["boundary_evidence"], ensure_ascii=False
                ),
            }
        ]
        self.interpreted_display += [
            {
                "field": "region",
                "value": region["region"],
                "category": "structurally_interpreted",
                "evidence": ", ".join(region["evidence_block_ids"]),
            }
            for region in self.interpreted["regions"]
        ]
        self.example_markers = []
        for self.marker_kind in dict.fromkeys(
            (m["kind"] for m in self.interpreted["candidate_legal_markers"])
        ):
            self.example_markers.append(
                next(
                    (
                        m
                        for m in self.interpreted["candidate_legal_markers"]
                        if m["kind"] == self.marker_kind
                    )
                )
            )
        self.interpreted_display += [
            {
                "field": "candidate legal role",
                "value": m["kind"]
                + " (candidate); source label: "
                + m["matched_label"],
                "category": "structurally_interpreted",
                "evidence": m["source"]["part"]
                + ":"
                + m["source"]["path"]
                + " span="
                + str(m["character_span"]),
            }
            for m in self.example_markers
        ]
        show_rows(self.interpreted_display)
        print(
            "4. Deferred metadata — no values computed or inheritance policy selected"
        )
        show_rows(
            [
                {**item, "category": "deferred"}
                for item in self.metadata_provenance["deferred"]
            ]
        )
        show_full_record(
            self.metadata_example,
            "Complete categorized metadata for the named Act, including all source evidence",
        )

    def step_7e_check_metadata_fidelity_and_category_separation(self):
        """7e. Check metadata fidelity and category separation."""
        self.all_metadata_paragraphs = {
            p["id"]: p
            for b in self.corpus["blocks"]
            for p in ([b] if b["type"] == "paragraph" else table_paragraphs(b))
        }
        for self.descriptor, self.classified in zip(
            self.corpus["documents"], self.metadata_provenance["documents"], strict=True
        ):
            assert self.classified["document_id"] == self.descriptor["document_id"]
            assert (
                self.classified["source_extracted"]["titles"]
                == self.descriptor["source_titles"]
            )
            self.fields = self.classified["source_extracted"]["metadata_fields"]
            assert [f["field"] for f in self.fields] == list(
                self.FIELD_BY_SOURCE_LABEL.values()
            )
            for self.original_row, self.field in zip(
                self.descriptor["source_metadata"]["rows"], self.fields, strict=True
            ):
                assert self.field["raw_labels"] == [
                    p["raw_text"] for p in self.original_row["label_paragraphs"]
                ]
                assert self.field["raw_values"] == [
                    p["raw_text"] for p in self.original_row["value_paragraphs"]
                ]
                self.evidence = self.field["evidence"]
                assert (
                    self.evidence["table_block_id"]
                    == self.descriptor["source_metadata"]["table_block_id"]
                )
                assert (
                    self.evidence["table_source"]
                    == self.descriptor["source_metadata"]["table_source"]
                )
                for self.key in [
                    "row_index",
                    "label_column_index",
                    "value_column_index",
                    "label_paragraphs",
                    "value_paragraphs",
                ]:
                    assert self.evidence[self.key] == self.original_row[self.key]
                for self.item in (
                    self.evidence["label_paragraphs"]
                    + self.evidence["value_paragraphs"]
                ):
                    self.actual = self.all_metadata_paragraphs[self.item["block_id"]]
                    assert (
                        self.item["raw_text"] == self.actual["raw_text"]
                        and self.item["source"] == self.actual["source"]
                    )
            self.structural = self.classified["structurally_interpreted"]
            assert self.structural["block_range"] == self.descriptor["block_range"]
            assert (
                self.structural["boundary_evidence"]
                == self.descriptor["boundary_evidence"]
            )
            self.span = self.corpus["blocks"][
                self.descriptor["block_range"]["start_index"] : self.descriptor[
                    "block_range"
                ]["end_index_exclusive"]
            ]
            assert self.structural["candidate_legal_markers"] == [
                m
                for b in self.span
                for m in b["structural_annotations"]["legal_marker_candidates"]
            ]
            for self.marker in self.classified["source_extracted"][
                "explicit_region_marker_texts"
            ]:
                self.block = self.metadata_blocks_by_id[self.marker["block_id"]]
                assert (
                    self.marker["raw_text"] == self.block["raw_text"]
                    and self.marker["source"] == self.block["source"]
                )
                assert (
                    self.marker["explicit_style_id"]
                    == self.block["style"]["explicit_id"]
                )
        for self.record, self.element in zip(
            self.metadata_provenance["source_extracted"]["package_properties"],
            self.core_properties_root,
            strict=True,
        ):
            assert self.record["raw_value"] == self.element.text and self.record[
                "attributes"
            ] == dict(self.element.attrib)
            assert self.record["qualified_name"] == self.element.tag
        assert all(
            (
                item["status"] == "deferred"
                and set(item) == {"field", "status", "reason"}
                for item in self.metadata_provenance["deferred"]
            )
        )
        assert any(
            (
                item["field"] == "document_to_chunk_metadata_inheritance"
                for item in self.metadata_provenance["deferred"]
            )
        )
        assert (
            record_digest({key: self.corpus[key] for key in self.step6_field_names})
            == self.step6_before_metadata
        )
        self.synthetic_descriptor = deepcopy(self.corpus["documents"][0])
        self.synthetic_row = self.synthetic_descriptor["source_metadata"]["rows"][0]
        self.synthetic_row["label_paragraphs"][0]["raw_text"] = (
            "  Unknown source label  "
        )
        self.synthetic_row["value_paragraphs"][0]["raw_text"] = ""
        self.synthetic_descriptor["source_metadata"]["rows"] = [
            self.synthetic_row,
            deepcopy(self.synthetic_row),
        ]
        self.synthetic_before = record_digest(self.synthetic_descriptor)
        self.synthetic_classification = self.classified_source_rows(
            self.synthetic_descriptor
        )
        assert len(self.synthetic_classification) == 2
        assert all(
            (
                f["field"] is None
                and f["raw_labels"] == ["  Unknown source label  "]
                and (f["raw_values"] == [""])
                for f in self.synthetic_classification
            )
        )
        assert record_digest(self.synthetic_descriptor) == self.synthetic_before
        print(
            "PASS: all 21 documents / 126 source metadata rows and evidence preserved unchanged"
        )
        print(
            "PASS: package properties scoped separately; deferred fields contain no inferred values or inheritance decisions"
        )
        print(
            "PASS: original Step 6 corpus fields unchanged; unknown/duplicate/empty metadata preserved"
        )
