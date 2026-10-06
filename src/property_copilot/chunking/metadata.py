"""Chunking: metadata."""

from pathlib import Path
import hashlib
import html
import json
from property_copilot._display import HTML, display
from urllib.parse import urlsplit
from .primitives import (
    canonical,
    details_html,
    esc,
    expect_value_error,
    fingerprint,
    intersection_length,
    require,
    show_json,
    show_table,
)


class MetadataSteps:
    """Metadata steps; state belongs to the workflow instance."""

    def registry_field(self, did, field):
        require(did in self.M_REGISTRY, "Unknown registry document.")
        require(field in self.M_LABELS, "Unsupported registry field.")
        doc = self.M_REGISTRY[did]
        return [
            {
                "row_reference": i,
                "row_index": doc["source_metadata"]["rows"][i]["row_index"],
                "value_paragraphs": doc["source_metadata"]["rows"][i][
                    "value_paragraphs"
                ],
            }
            for i in doc["field_row_references"][field]
        ]

    def raw_values(self, did, field):
        return [
            p["raw_text"]
            for row in self.registry_field(did, field)
            for p in row["value_paragraphs"]
        ]

    def step_10_metadata_experiments_stop_here_for_review(self):
        """Step 10 — Metadata experiments (stop here for review)."""
        self.ensure_history_current()
        self.M_APPROVED_PATHS = [
            self.APPROVED_MANIFEST_PATH,
            self.report_path,
            self.structural_report_path,
            self.pc_report_path,
            self.os_report_path,
            self.history_report_path,
        ]
        self.M_APPROVED_BYTES = {str(p): p.read_bytes() for p in self.M_APPROVED_PATHS}
        self.M_BASELINE_FINGERPRINTS = [
            fingerprint(self.FIXED_RESULTS),
            fingerprint(self.STRUCTURAL_RESULTS),
            fingerprint(self.PC_DATA),
            fingerprint(list(self.OS_GROUPS.values())),
            fingerprint(self.H_ANNOTATIONS),
        ]
        self.M_LABELS = {
            "jurisdiction": "Юрисдикция / Jurisdiction",
            "source_url": "Източник / Source URL",
            "official_reference": "ДВ / Official reference",
            "version_date": "Версия / Version date",
            "accessed_date": "Достъпено / Accessed",
            "note": "Бележка / Note",
        }
        self.M_SPEC = {
            "version": 1,
            "setup_id": self.SETUP_ID,
            "artifact_sha256": self.artifact_sha256,
            "labels": self.M_LABELS,
            "registry_population": "all 21 Stage 1 document descriptors",
            "chunk_population": "existing Step 2 baseline documents only",
            "representative_sample": "long_article",
            "display_configuration": self.GALLERY_CONFIGURATION,
            "date_interpretation": "verbatim source only; version date is not effective date",
            "production_schema": False,
        }
        self.M_RUN_ID = fingerprint(self.M_SPEC)
        self.M_RUN = {
            "id": self.M_RUN_ID,
            "artifact_sha256": self.artifact_sha256,
            "source": json.loads(canonical(self.corpus["source"])),
            "parser": json.loads(canonical(self.corpus["parser"])),
            "setup_id": self.SETUP_ID,
            "fixed_run_id": self.BASELINE_ID,
            "structural_run_id": self.STRUCTURAL_ID,
            "parent_child_run_id": self.PC_RUN_ID,
        }
        self.M_REGISTRY = {}
        for self.did, self.document in self.DOCUMENTS.items():
            self.metadata = json.loads(canonical(self.document["source_metadata"]))
            self.index = {
                field: [
                    i
                    for i, row in enumerate(self.metadata["rows"])
                    if [p["raw_text"] for p in row["label_paragraphs"]] == [label]
                ]
                for field, label in self.M_LABELS.items()
            }
            self.M_REGISTRY[self.did] = {
                "document_id": self.did,
                "ordinal": self.document["ordinal"],
                "source_titles": json.loads(canonical(self.document["source_titles"])),
                "source_metadata": self.metadata,
                "field_row_references": self.index,
                "run_ref": self.M_RUN_ID,
            }
        self.M_REGISTRY_FINGERPRINT = fingerprint(self.M_REGISTRY)
        show_table(
            [
                {
                    "document": d["ordinal"],
                    "document_id": did,
                    "Bulgarian_title": d["source_titles"]["title"]["raw_text"],
                    "English_title": d["source_titles"]["subtitle"]["raw_text"],
                    "jurisdiction_raw": self.raw_values(did, "jurisdiction"),
                    "version_date_raw": self.raw_values(did, "version_date"),
                    "missing_or_duplicate_rows": {
                        field: len(refs)
                        for field, refs in d["field_row_references"].items()
                        if len(refs) != 1
                    },
                }
                for did, d in self.M_REGISTRY.items()
            ]
        )
        self.M_SAMPLE = self.SAMPLE_BY_ID[self.M_SPEC["representative_sample"]]
        show_json(
            "Complete representative document registry record — all original metadata and source locations",
            self.M_REGISTRY[self.M_SAMPLE["document_id"]],
        )
        show_json(
            "Run-level source/DOCX fingerprints and parser provenance", self.M_RUN
        )

    def step_10a_source_field_inventory_and_selective_resolution(self):
        """10a. Source field inventory and selective resolution."""
        self.M_FIELD_INVENTORY = []
        for self.field in self.M_LABELS:
            self.entries = self.registry_field(self.M_SAMPLE["document_id"], self.field)
            self.M_FIELD_INVENTORY.append(
                {
                    "field": self.field,
                    "raw_values": self.raw_values(
                        self.M_SAMPLE["document_id"], self.field
                    ),
                    "registry_row_references": [
                        e["row_reference"] for e in self.entries
                    ],
                    "source_evidence": [
                        {"block_id": p["block_id"], "source": p["source"]}
                        for e in self.entries
                        for p in e["value_paragraphs"]
                    ],
                    "placement": "selective join: possible future filter"
                    if self.field in ("jurisdiction", "version_date")
                    else "registry lookup",
                }
            )
        show_table(self.M_FIELD_INVENTORY)

    def join_metadata(self, minimal):
        require(minimal["run_ref"] == self.M_RUN_ID, "Stale metadata run reference.")
        require(minimal["chunk_id"] in self.PC_CHILDREN, "Unknown chunk reference.")
        require(
            minimal["relationship_id"] in self.PC_LINKS,
            "Unknown relationship reference.",
        )
        child = self.PC_CHILDREN[minimal["chunk_id"]]
        link = self.PC_LINKS[minimal["relationship_id"]]
        require(
            link["child_id"] == child["id"], "Relationship belongs to another child."
        )
        require(
            minimal["document_id"] == child["document_id"]
            and minimal["document_span"] == [child["start"], child["end"]],
            "Chunk reference/span mismatch.",
        )
        group = self.PC_GROUPS[link["relationship_set_id"]]
        parent = self.PC_PARENTS[link["parent_id"]]
        did = child["document_id"]
        doc = self.M_REGISTRY[did]
        unit = self.STRUCTURAL_BY_ID[link["source_structural_unit_id"]]
        ledger = next(
            (
                row
                for row in self.BOUNDARY_LEDGERS[did]
                if row["id"] == unit["opening_ledger_id"]
            )
        )
        ordered = [
            self.PC_CHILDREN[self.PC_LINKS[rid]["child_id"]]
            for rid in group["relationship_ids"]
        ]
        index = link["ordinal"] - 1
        previous = (
            intersection_length(
                (ordered[index - 1]["start"], ordered[index - 1]["end"]),
                (child["start"], child["end"]),
            )
            if index
            else 0
        )
        following = (
            intersection_length(
                (ordered[index + 1]["start"], ordered[index + 1]["end"]),
                (child["start"], child["end"]),
            )
            if index + 1 < len(ordered)
            else 0
        )
        mapped = self.source_map(did, child["start"], child["end"])
        positions = sorted({s["position"] for s in mapped if s["kind"] == "source"})
        source_urls = self.raw_values(did, "source_url")
        citation = f"{doc['source_titles']['title']['raw_text']} — {ledger['label']} (provisional source label); body positions {positions}; document characters [{child['start']}, {child['end']})"
        return {
            "A_document_join": {
                "document_registry_ref": did,
                "Bulgarian_title": doc["source_titles"]["title"],
                "English_title": doc["source_titles"]["subtitle"],
                "jurisdiction_raw": self.raw_values(did, "jurisdiction"),
                "version_date_raw": self.raw_values(did, "version_date"),
                "filter_field_evidence": {
                    "jurisdiction": self.registry_field(did, "jurisdiction"),
                    "version_date": self.registry_field(did, "version_date"),
                },
            },
            "B_structural": {
                "unit_id": unit["id"],
                "provisional_kind": unit["unit_kind"],
                "unit_span": [unit["start"], unit["end"]],
                "opening_boundary_evidence": ledger,
                "closing_ledger_ref": unit["closing_ledger_id"],
                "scope_evidence_block_id_not_parent": unit[
                    "scope_evidence_block_id_not_parent"
                ],
                "uncertainty": unit["uncertainty"],
                "child_is_complete_unit": child["start"] == unit["start"]
                and child["end"] == unit["end"],
            },
            "C_chunk_generated": {
                "id": child["id"],
                "strategy": "parent-child relationship experiment",
                "configuration_id": group["configuration"],
                "ordinal_in_selected_relationship": link["ordinal"],
                "character_count": child["end"] - child["start"],
                "source_spans": mapped,
                "actual_previous_overlap": previous,
                "actual_next_overlap": following,
                "split_mechanism_from_relationship_mode": group["mode"],
                "setup_id": self.SETUP_ID,
            },
            "D_parent_child": {
                "relationship_id": link["id"],
                "relationship_set_id": group["id"],
                "parent_id": parent["id"],
                "child_order": link["ordinal"],
                "relationship_type": group["mode"],
                "parent_source_span": [parent["start"], parent["end"]],
                "parent_source_map": parent["source_spans"],
                "parent_role": parent["parent_role"],
                "parent_review_basis": parent["review_basis"],
                "parent_uncertainty": parent.get(
                    "uncertainty",
                    "See review basis and structural evidence; legal meaning unverified",
                ),
            },
            "E_provenance_citation": {
                "document_registry_ref": did,
                "run_ref": self.M_RUN_ID,
                "artifact_sha256": self.M_RUN["artifact_sha256"],
                "docx_sha256": self.M_RUN["source"]["sha256"],
                "source_urls_raw": source_urls,
                "official_reference_registry_rows": doc["field_row_references"][
                    "official_reference"
                ],
                "source_block_ids": [
                    s["block_id"] for s in mapped if s["kind"] == "source"
                ],
                "citation_display": citation,
                "url_verification": "Source-supplied; not fetched or independently verified",
            },
        }

    def step_10b_the_same_chunk_two_metadata_views(self):
        """10b. The same chunk, two metadata views."""
        self.M_SELECTED_GROUP = next(
            (
                g
                for g in self.PC_GROUPS.values()
                if g["mode"] == "fixed_inside_parent"
                and g["configuration"] == self.M_SPEC["display_configuration"]
                and (
                    self.PC_PARENTS[g["parent_id"]]["document_id"]
                    == self.M_SAMPLE["document_id"]
                )
                and (
                    self.PC_PARENTS[g["parent_id"]]["start"]
                    <= self.M_SAMPLE["start"]
                    < self.PC_PARENTS[g["parent_id"]]["end"]
                )
            )
        )
        self.M_SELECTED_LINK = self.PC_LINKS[
            self.M_SELECTED_GROUP["relationship_ids"][
                min(1, len(self.M_SELECTED_GROUP["relationship_ids"]) - 1)
            ]
        ]
        self.M_MINIMAL = {
            "chunk_id": self.M_SELECTED_LINK["child_id"],
            "document_id": self.PC_CHILDREN[self.M_SELECTED_LINK["child_id"]][
                "document_id"
            ],
            "document_span": [
                self.PC_CHILDREN[self.M_SELECTED_LINK["child_id"]]["start"],
                self.PC_CHILDREN[self.M_SELECTED_LINK["child_id"]]["end"],
            ],
            "relationship_id": self.M_SELECTED_LINK["id"],
            "run_ref": self.M_RUN_ID,
        }
        self.M_JOINED = self.join_metadata(self.M_MINIMAL)
        self.M_CHILD_TEXT = self.PC_CHILDREN[self.M_MINIMAL["chunk_id"]]["text"]
        display(
            HTML(
                "<h4>One unchanged chunk payload (shared by both metadata views)</h4>"
                + details_html("Complete verbatim child text", self.M_CHILD_TEXT)
            )
        )
        display(
            HTML(
                "<div style='display:grid;grid-template-columns:1fr 1fr;gap:16px'><section><h4>Minimal metadata</h4>"
                + details_html(
                    "Minimal references",
                    json.dumps(self.M_MINIMAL, ensure_ascii=False, indent=2),
                )
                + "</section><section><h4>Selectively enriched / joined metadata</h4>"
                + "".join(
                    (
                        details_html(
                            category, json.dumps(value, ensure_ascii=False, indent=2)
                        )
                        for category, value in self.M_JOINED.items()
                    )
                )
                + "</section></div>"
            )
        )
        show_table(
            [
                {"category": key, "fields": list(value)}
                for key, value in self.M_JOINED.items()
            ]
        )
        display(
            HTML(
                "<p>"
                + esc(self.M_JOINED["E_provenance_citation"]["citation_display"])
                + "</p>"
            )
        )
        for self.url in self.M_JOINED["E_provenance_citation"]["source_urls_raw"]:
            self.parsed = urlsplit(self.url)
            if self.parsed.scheme in ("https", "http") and self.parsed.netloc:
                display(
                    HTML(
                        '<p>Source-supplied URL: <a href="'
                        + html.escape(self.url, quote=True)
                        + '" rel="noopener noreferrer">'
                        + esc(self.url)
                        + "</a> (not fetched)</p>"
                    )
                )
            else:
                display(
                    HTML(
                        "<p>Source URL retained as text (not a validated HTTP link): "
                        + esc(self.url)
                        + "</p>"
                    )
                )

    def step_10c_split_reasons_are_generated_evidence_source_fields_are_not(self):
        """10c. Split reasons are generated evidence; source fields are not."""
        self.M_REASON_EXAMPLES = []
        self.selected_unit = self.M_SELECTED_LINK["source_structural_unit_id"]
        for self.method in ("exact", "boundary_aware"):
            self.group = self.OS_GROUPS.get(
                (self.selected_unit, f"{self.method}-chars-2000-overlap-10pct")
            )
            if self.group:
                self.child = self.group["children"][0]
                self.M_REASON_EXAMPLES.append(
                    {
                        k: self.child[k]
                        for k in (
                            "id",
                            "parent_id",
                            "configuration",
                            "split_reason",
                            "next_start_reason",
                            "requested_overlap",
                            "actual_previous_overlap",
                            "actual_next_overlap",
                        )
                    }
                )
        show_table(self.M_REASON_EXAMPLES)
        self.M_PLACEMENT = [
            {
                "fields": "Bulgarian / English titles",
                "owner": "document registry",
                "use": "bilingual display, document identification and citation",
                "caution": "Never prepend to original chunk text",
            },
            {
                "fields": "jurisdiction; raw version date",
                "owner": "registry; selective joined view",
                "use": "possible future filtering",
                "caution": "Raw version is not effective date; semantics/coverage need review",
            },
            {
                "fields": "URL; official reference",
                "owner": "document registry",
                "use": "source navigation and citation lookup",
                "caution": "Source-provided references do not verify current legal status or URL reachability",
            },
            {
                "fields": "accessed date; long note",
                "owner": "document registry",
                "use": "source collection context and limitations",
                "caution": "Not provision-specific dates or demonstrated retrieval filter needs",
            },
            {
                "fields": "labels; scope; heading locations; uncertainty",
                "owner": "structural unit and boundary ledger",
                "use": "citation context and boundary debugging",
                "caution": "Provisional source evidence, not manufactured ancestry",
            },
            {
                "fields": "IDs; spans; configuration; overlaps; split reasons",
                "owner": "chunk/experiment records",
                "use": "traceability, reproducibility and debugging",
                "caution": "Character counts are not tokens; generation evidence is not legal evidence",
            },
            {
                "fields": "parent link; order; relationship mode",
                "owner": "explicit relationship set",
                "use": "context resolution and containment",
                "caution": "Shared children may have multiple parent alternatives",
            },
            {
                "fields": "DOCX/artifact fingerprints; parser provenance",
                "owner": "run record",
                "use": "verify exactly which source and parser produced the experiment",
                "caution": "Resolve by run reference; no need to repeat parser details per child",
            },
        ]
        show_table(self.M_PLACEMENT)

    def ensure_metadata_current(self):
        self.ensure_history_current()
        require(
            fingerprint(self.M_SPEC) == self.M_RUN_ID
            and fingerprint(self.M_REGISTRY) == self.M_REGISTRY_FINGERPRINT,
            "Metadata settings or registry changed; rebuild Step 10 views.",
        )
        require(
            self.M_JOINED == self.join_metadata(self.M_MINIMAL),
            "Joined view is stale; rebuild Step 10 display.",
        )

    def check_no_unsupported_fields(self, value):
        if isinstance(value, dict):
            require(
                not self.M_FORBIDDEN.intersection(value),
                "Unsupported metadata field introduced.",
            )
            for v in value.values():
                self.check_no_unsupported_fields(v)
        elif isinstance(value, list):
            for v in value:
                self.check_no_unsupported_fields(v)

    def step_10d_validate_references_and_source_fidelity(self):
        """10d. Validate references and source fidelity."""
        require(
            len(self.M_REGISTRY) == len(self.DOCUMENTS) == 21,
            "Document registry population changed.",
        )
        for self.did, self.doc in self.M_REGISTRY.items():
            self.original = self.DOCUMENTS[self.did]
            require(
                self.doc["source_titles"] == self.original["source_titles"]
                and self.doc["source_metadata"] == self.original["source_metadata"],
                "Registry changed source fields or evidence.",
            )
            for self.field, self.label in self.M_LABELS.items():
                self.expected = [
                    p["raw_text"]
                    for row in self.original["source_metadata"]["rows"]
                    if [p["raw_text"] for p in row["label_paragraphs"]] == [self.label]
                    for p in row["value_paragraphs"]
                ]
                require(
                    self.raw_values(self.did, self.field) == self.expected,
                    "Field value normalized or dropped.",
                )
        require(
            self.M_CHILD_TEXT
            == self.reconstruct(self.M_JOINED["C_chunk_generated"]["source_spans"])
            == self.VIEWS[self.M_MINIMAL["document_id"]]["text"][
                slice(*self.M_MINIMAL["document_span"])
            ],
            "Joined representation changed source text.",
        )
        self.link = self.PC_LINKS[self.M_MINIMAL["relationship_id"]]
        self.parent = self.PC_PARENTS[self.link["parent_id"]]
        require(
            self.parent["document_id"] == self.M_MINIMAL["document_id"]
            and self.parent["start"]
            <= self.M_MINIMAL["document_span"][0]
            < self.M_MINIMAL["document_span"][1]
            <= self.parent["end"],
            "Relationship containment failed.",
        )
        require(
            self.M_JOINED["D_parent_child"]["child_order"] == self.link["ordinal"]
            and self.PC_GROUPS[self.link["relationship_set_id"]]["relationship_ids"][
                self.link["ordinal"] - 1
            ]
            == self.link["id"],
            "Relationship order mismatch.",
        )
        require(
            self.M_JOINED["E_provenance_citation"]["docx_sha256"]
            == self.corpus["source"]["sha256"],
            "DOCX fingerprint mismatch.",
        )
        expect_value_error(
            lambda: self.registry_field("unknown", "note"), "Unknown registry document"
        )
        expect_value_error(
            lambda: self.registry_field(self.M_MINIMAL["document_id"], "in_force"),
            "Unsupported registry field",
        )
        expect_value_error(
            lambda: self.join_metadata({**self.M_MINIMAL, "document_span": [0, 1]}),
            "Chunk reference/span mismatch",
        )
        expect_value_error(
            lambda: self.join_metadata(
                {**self.M_MINIMAL, "relationship_id": "unknown"}
            ),
            "Unknown relationship reference",
        )
        self.other_link = next(
            (
                r
                for r in self.PC_LINKS.values()
                if r["child_id"] != self.M_MINIMAL["chunk_id"]
            )
        )
        expect_value_error(
            lambda: self.join_metadata(
                {**self.M_MINIMAL, "relationship_id": self.other_link["id"]}
            ),
            "Relationship belongs to another child",
        )
        require(
            set(self.M_MINIMAL)
            == {
                "chunk_id",
                "document_id",
                "document_span",
                "relationship_id",
                "run_ref",
            },
            "Minimal view copied document fields.",
        )
        self.M_FORBIDDEN = {
            "topic",
            "city",
            "district",
            "in_force",
            "page",
            "pages",
            "page_number",
            "effective_date",
        }
        self.check_no_unsupported_fields(self.M_REGISTRY)
        self.check_no_unsupported_fields(self.M_MINIMAL)
        self.check_no_unsupported_fields(self.M_JOINED)
        require(
            all(
                (
                    Path(p).read_bytes() == data
                    for p, data in self.M_APPROVED_BYTES.items()
                )
            ),
            "An approved report or manifest changed.",
        )
        require(
            self.M_BASELINE_FINGERPRINTS
            == [
                fingerprint(self.FIXED_RESULTS),
                fingerprint(self.STRUCTURAL_RESULTS),
                fingerprint(self.PC_DATA),
                fingerprint(list(self.OS_GROUPS.values())),
                fingerprint(self.H_ANNOTATIONS),
            ],
            "Canonical chunks/evidence changed.",
        )
        require(
            hashlib.sha256(self.ARTIFACT.read_bytes()).hexdigest()
            == self.artifact_sha256
            and fingerprint(self.corpus) == self.corpus_fingerprint_before,
            "Stage 1 source changed.",
        )
        self.ensure_metadata_current()
        print(
            "PASS: 21 source-faithful registry records, raw dates, exact joined chunk, valid explicit relationship, provenance and unchanged approved artifacts."
        )

    def step_10e_review_and_stop(self):
        """10e. Review and stop."""
        self.ensure_metadata_current()
        self.M_REPORT = {
            "report_version": 1,
            "scope": "Step 10 only — metadata representations",
            "run_id": self.M_RUN_ID,
            "spec": self.M_SPEC,
            "run_record": self.M_RUN,
            "document_registry": self.M_REGISTRY,
            "registry_fingerprint": self.M_REGISTRY_FINGERPRINT,
            "representative_sample": self.M_SPEC["representative_sample"],
            "minimal_view": self.M_MINIMAL,
            "joined_view": self.M_JOINED,
            "source_field_inventory": self.M_FIELD_INVENTORY,
            "existing_split_reason_examples": self.M_REASON_EXAMPLES,
            "placement_observations": self.M_PLACEMENT,
            "validation": "PASS: registry fidelity, raw dates, reference joins, unchanged payload and approved artifacts",
            "decision": "Experimental views only; no production schema or final metadata policy selected",
        }
        self.metadata_report_path = (
            self.OUTPUT_DIR
            / f"metadata_experiment_report.{fingerprint(self.M_REPORT)}.json"
        )
        self.metadata_report_bytes = (canonical(self.M_REPORT) + "\n").encode("utf-8")
        if self.metadata_report_path.exists():
            require(
                self.metadata_report_path.read_bytes() == self.metadata_report_bytes,
                "Existing metadata report differs.",
            )
        else:
            self.metadata_report_path.write_bytes(self.metadata_report_bytes)
        require(
            json.loads(self.metadata_report_path.read_text(encoding="utf-8"))
            == self.M_REPORT,
            "Metadata report round trip failed.",
        )
        print(
            "Metadata experiment report:",
            self.metadata_report_path.relative_to(self.ROOT),
        )
        print(
            "STOP AFTER STEP 10 — registry and joined views ready for review; no production schema selected."
        )
