"""Chunking: structural."""

from collections import Counter
import hashlib
import json
import math
from property_copilot._display import HTML, display
import re
from .primitives import (
    canonical,
    details_html,
    esc,
    expect_value_error,
    fingerprint,
    highlight_html,
    intersection_length,
    interval_union_length,
    length_summary,
    require,
    show_json,
    show_table,
    structural_fixture,
    table_html,
)


class StructuralSteps:
    """Structural steps; state belongs to the workflow instance."""

    def step_6a_lock_inputs_and_document_the_conservative_policy(self):
        """6a. Lock inputs and document the conservative policy."""
        self.ensure_baseline_current()
        require(
            fingerprint(self.FIXED_RESULTS) == self.FIXED_RESULTS_FINGERPRINT,
            "Approved fixed-length results changed.",
        )
        require(
            fingerprint(self.APPROVED_MANIFEST) == self.APPROVED_SETUP_ID,
            "Approved sample manifest changed.",
        )
        self.STEP5_REPORT_BYTES = self.report_path.read_bytes()
        self.STEP5_RESULT_FINGERPRINT = self.FIXED_RESULTS_FINGERPRINT
        self.REVIEWED_TITLE_ANCHORS = [
            57,
            59,
            95,
            110,
            112,
            132,
            194,
            240,
            260,
            267,
            293,
            326,
            359,
            407,
            414,
            451,
            453,
            480,
            506,
            541,
            583,
            598,
            600,
            606,
            638,
            646,
            652,
            654,
            661,
            663,
            677,
            701,
            775,
            777,
            795,
            803,
            926,
            980,
            982,
            1067,
            1181,
            1313,
            1315,
            1317,
            1342,
            1443,
            1472,
            1489,
            1543,
            1545,
            1598,
            1600,
            1613,
            1640,
            1661,
            1670,
            1674,
            1688,
            1690,
            1713,
            1731,
            1734,
            1736,
            1795,
            1879,
            1933,
            1944,
            2740,
            2777,
            25781,
            25783,
            25786,
            25817,
            25850,
            25852,
            25876,
            25922,
            25941,
            25952,
            25955,
            25957,
            25962,
            25985,
            25997,
            26012,
            26014,
            26023,
            26026,
            26032,
            26034,
            26038,
            26054,
            26070,
        ]
        self.TITLE_PAIRS = {
            self.BY_POSITION[pos]["id"]: self.BY_POSITION[pos + 1]["id"]
            for pos in self.REVIEWED_TITLE_ANCHORS
        }
        self.OVERRIDE_SPECS = [
            (
                2051,
                "Допълнителни разпоредби",
                "boundary",
                "unclassified",
                "Sample heading remains unclassified; do not invent its legal rank.",
            ),
            (
                2158,
                "Преходни разпоредби",
                "boundary",
                "unclassified",
                "Observed transition into transitional provisions, distinct from additional provisions.",
            ),
            (
                26047,
                "Приложение II се изменя, както следва:",
                "retain",
                None,
                "Amendment instruction within Article 17, not a standalone Annex; next Article starts at 26054.",
            ),
            (
                2246,
                "-------------------------",
                "boundary",
                "residual",
                "Separator and adoption statement between provisions and the next amendment heading.",
            ),
            (
                2722,
                "Релевантни актове от Европейското законодателство",
                "boundary",
                "residual",
                "Related-act listing after the final § provision; preserve as residual text.",
            ),
            (
                26075,
                "Съставено в Брюксел",
                "boundary",
                "residual",
                "Signature, footnotes and publication tail after Article 19; retain without guessing footnote relationships.",
            ),
        ]
        for (
            self.sample_id,
            self.kind,
            self.label,
            self.first,
            self.last,
        ) in self.PROVISION_SPECS:
            self.source_kind = {
                "Article": "article",
                "§ provision": "paragraph_sign",
                "Annex": "annex",
            }[self.kind]
            self.OVERRIDE_SPECS.append(
                (
                    self.first,
                    self.label,
                    "boundary",
                    self.source_kind,
                    f"Explicit source-start review for frozen sample {self.sample_id}; endpoint checked after generation.",
                )
            )
        self.STRUCTURAL_OVERRIDES = {}
        for (
            self.pos,
            self.prefix,
            self.action,
            self.kind,
            self.reason,
        ) in self.OVERRIDE_SPECS:
            self.b = self.BY_POSITION[self.pos]
            require(
                self.b["raw_text"].startswith(self.prefix)
                and self.b["id"] in self.BLOCK_SPANS,
                "Reviewed override source differs.",
            )
            self.STRUCTURAL_OVERRIDES[self.b["id"]] = {
                "action": self.action,
                "kind": self.kind,
                "reason": self.reason,
                "expected_text_sha256": hashlib.sha256(
                    self.b["raw_text"].encode("utf-8")
                ).hexdigest(),
                "position": self.pos,
            }
        self.STRUCTURAL_SPEC = {
            "algorithm": "conservative_flat_structural_v1",
            "setup_id": self.SETUP_ID,
            "source_artifact_sha256": self.artifact_sha256,
            "document_ids": list(self.BASELINE_DOCUMENT_IDS),
            "size_limit": None,
            "overlap": 0,
            "title_pairs": self.TITLE_PAIRS,
            "overrides": self.STRUCTURAL_OVERRIDES,
            "heading_semantics": "Part/Chapter/Section heading-context spans, not entire descendant subtrees",
            "annex_policy": "retain internal uncertain markers until next Annex or explicit reviewed transition",
            "separator_policy": "preceding unit owns inter-block newline",
            "approval": "Steps 1–5 approved; Step 6 only authorized",
        }
        self.STRUCTURAL_ID = fingerprint(self.STRUCTURAL_SPEC)
        self.STRUCTURAL_CONFIGURATION = "structural-uncapped-provisional"
        print("Structural experiment:", self.STRUCTURAL_ID)
        print(
            "Population:",
            len(self.BASELINE_DOCUMENT_IDS),
            "frozen complete documents; size limit: NONE",
        )
        show_table(
            [
                {
                    "position": spec["position"],
                    "action": spec["action"],
                    "role": spec["kind"],
                    "reason": spec["reason"],
                }
                for spec in self.STRUCTURAL_OVERRIDES.values()
            ]
        )
        show_json(
            "Reviewed title pairs (exact source IDs; no inferred hierarchy)",
            [
                {
                    "label_position": self.BLOCKS[a]["position"],
                    "label": self.BLOCKS[a]["raw_text"],
                    "title_position": self.BLOCKS[b]["position"],
                    "title": self.BLOCKS[b]["raw_text"],
                }
                for a, b in self.TITLE_PAIRS.items()
            ],
        )

    def propose_structural_boundaries(
        self, view, block_lookup, overrides=None, title_pairs=None
    ):
        overrides, title_pairs = (overrides or {}, title_pairs or {})
        ids = view["block_ids"]
        blocks = [block_lookup[bid] for bid in ids]
        index_of = {bid: i for i, bid in enumerate(ids)}
        starts = {
            s["block_id"]: s["start"] for s in view["segments"] if s["kind"] == "source"
        }
        attached_titles, residual_after_header = ({}, set())
        for anchor, title in title_pairs.items():
            if anchor not in index_of:
                continue
            require(
                title in index_of and index_of[title] == index_of[anchor] + 1,
                "Title must immediately follow its label in the same document.",
            )
            a, t = (block_lookup[anchor], block_lookup[title])
            candidates = a["structural_annotations"]["legal_marker_candidates"]
            require(
                len(candidates) == 1
                and candidates[0]["kind"] in self.CONTEXT_KINDS | {"article"}
                and (not t["structural_annotations"]["legal_marker_candidates"])
                and t["raw_text"],
                "Title pairing has contradictory source evidence.",
            )
            attached_titles[title] = anchor
            if candidates[0]["kind"] in self.CONTEXT_KINDS and index_of[
                title
            ] + 1 < len(ids):
                residual_after_header.add(index_of[title] + 1)
        ledger, annex_active, scope_id, seen_labels = ([], False, None, set())
        for i, b in enumerate(blocks):
            annotations = b["structural_annotations"]
            candidates = annotations["legal_marker_candidates"]
            heading = annotations["word_heading_level"]
            override = overrides.get(b["id"])
            if override:
                require(
                    hashlib.sha256(b["raw_text"].encode("utf-8")).hexdigest()
                    == override["expected_text_sha256"],
                    "Override text changed; re-inspect source before using it.",
                )
            kind, boundary, decision, reason, uncertainty = (
                None,
                False,
                None,
                None,
                [],
            )
            if override:
                boundary = override["action"] == "boundary"
                kind = override["kind"] if boundary else None
                decision = (
                    "reviewed_boundary"
                    if boundary
                    else "reviewed_false_candidate_retained"
                )
                reason = override["reason"]
            elif b["id"] in attached_titles:
                decision, reason = (
                    "reviewed_title_attached",
                    "Adjacent title retained with inspected label; Word heading rank ignored.",
                )
            elif len(candidates) > 1:
                boundary, kind = (
                    not annex_active,
                    "unclassified" if not annex_active else None,
                )
                decision, reason = (
                    "conflicting_candidates",
                    "Multiple candidate roles: no role selected.",
                )
                uncertainty.append("Conflicting markers; retain uncertainty.")
            elif candidates:
                c = candidates[0]
                lo, hi = c["character_span"]
                supported = (
                    c["kind"] in self.STRUCTURAL_KINDS
                    and c.get("rule") in self.SUPPORTED_RULES
                )
                leading = (
                    lo == 0
                    and 0 < hi <= len(b["raw_text"])
                    and (b["raw_text"][lo:hi] == c["matched_label"])
                )
                tail = b["raw_text"][hi:].lstrip(" .:–—-") if leading else ""
                if not leading:
                    decision, reason = (
                        "nonleading_candidate_retained",
                        "Inline/non-leading evidence does not establish a boundary.",
                    )
                    uncertainty.append("Candidate is not a verified leading label.")
                elif self.AMENDMENT_REFERENCE.match(tail):
                    decision, reason = (
                        "possible_reference_retained",
                        "Leading label is followed by an amendment instruction; not promoted to a standalone provision.",
                    )
                    uncertainty.append(
                        "Reference interpretation is provisional unless explicitly overridden."
                    )
                elif annex_active and c["kind"] != "annex":
                    decision, reason = (
                        "uncertain_marker_inside_annex",
                        "Do not manufacture Annex descendants or infer an Annex exit from this marker.",
                    )
                    uncertainty.append(
                        "Internal Annex role remains unresolved; source block retained in Annex."
                    )
                elif supported:
                    boundary, kind, decision = (True, c["kind"], "candidate_boundary")
                    reason = "Single leading Stage 1 marker and recorded matching rule; provisional legal boundary."
                    uncertainty.append(
                        "Unreviewed legal-boundary interpretation outside explicitly checked samples."
                    )
                else:
                    boundary, kind = (
                        not annex_active,
                        "unclassified" if not annex_active else None,
                    )
                    decision, reason = (
                        "unsupported_candidate",
                        "Unsupported marker rule/role; preserve without selecting a legal role.",
                    )
                    uncertainty.append("Unclassified marker evidence.")
            elif heading is not None:
                boundary, kind = (
                    not annex_active,
                    "unclassified" if not annex_active else None,
                )
                decision = (
                    "unclassified_heading_boundary"
                    if boundary
                    else "uncertain_heading_inside_annex"
                )
                reason = "Heading style supplies a possible transition only; it never supplies legal hierarchy."
                uncertainty.append("Legal role and scope are unclassified.")
            elif i in residual_after_header:
                boundary, kind, decision = (True, "residual", "residual_after_heading")
                reason = "Text after the reviewed label/title and before another evidenced legal boundary is residual."
            elif i == 0:
                boundary, kind, decision = (True, "residual", "document_start_residual")
                reason = "Initial full-text content or marker-free document; no legal role inferred."
            if decision is None:
                continue
            if i == 0 and (not boundary):
                boundary, kind = (True, "unclassified")
                uncertainty.append(
                    "Document must remain represented despite unresolved initial evidence."
                )
            label = (
                candidates[0]["matched_label"]
                if len(candidates) == 1
                else b["raw_text"][:160]
            )
            if boundary and kind in self.STRUCTURAL_KINDS:
                key = (kind, label)
                if key in seen_labels:
                    uncertainty.append(
                        "Repeated label in this document; source-position identity is required."
                    )
                seen_labels.add(key)
            if boundary:
                if kind in self.CONTEXT_KINDS | {"annex", "unclassified", "residual"}:
                    scope_id = b["id"]
                annex_active = kind == "annex"
            ledger.append(
                {
                    "id": f"boundary:{view['document_id']}:{b['position']}",
                    "document_id": view["document_id"],
                    "block_id": b["id"],
                    "position": b["position"],
                    "block_index": i,
                    "offset": starts[b["id"]],
                    "source": b["source"],
                    "source_text": b["raw_text"],
                    "candidate_evidence": candidates,
                    "word_heading_level_evidence_only": heading,
                    "label": label,
                    "creates_boundary": boundary,
                    "proposed_kind": kind,
                    "decision": decision,
                    "reason": reason,
                    "uncertainty": uncertainty,
                    "scope_evidence_block_id_not_parent": scope_id,
                    "attached_to_label_block_id": attached_titles.get(b["id"]),
                    "reviewed_title_block_id": title_pairs.get(b["id"]),
                }
            )
        return ledger

    def step_6b_propose_boundary_decisions_do_not_generate_chunks_yet(self):
        """6b. Propose boundary decisions — do not generate chunks yet."""
        self.STRUCTURAL_KINDS = {
            "part",
            "chapter",
            "section",
            "article",
            "paragraph_sign",
            "annex",
        }
        self.CONTEXT_KINDS = {"part", "chapter", "section"}
        self.SUPPORTED_RULES = {"leading_label_and_heading", "leading_numbered_label"}
        self.AMENDMENT_REFERENCE = re.compile(
            "^се\\s+(?:изменя|изменят|допълва|допълват|отменя|отменят)\\b",
            re.IGNORECASE,
        )
        self.BOUNDARY_LEDGERS = {
            did: self.propose_structural_boundaries(
                self.VIEWS[did],
                self.BLOCKS,
                self.STRUCTURAL_OVERRIDES,
                self.TITLE_PAIRS,
            )
            for did in self.BASELINE_DOCUMENT_IDS
        }
        self.BOUNDARY_LEDGER_FINGERPRINT = fingerprint(self.BOUNDARY_LEDGERS)
        print("Proposed ledger only — structural chunks have not been generated yet.")
        show_table(
            [
                {
                    "document": self.DOCUMENTS[did]["ordinal"],
                    "evidence_rows": len(rows),
                    "proposed_boundaries": sum((r["creates_boundary"] for r in rows)),
                    "uncertain_rows": sum((bool(r["uncertainty"]) for r in rows)),
                }
                for did, rows in self.BOUNDARY_LEDGERS.items()
            ]
        )
        self.LEDGER_COLUMNS = [
            "position",
            "label",
            "creates_boundary",
            "proposed_kind",
            "decision",
            "reason",
            "uncertainty",
        ]
        for self.sample in self.BASELINE_SAMPLES:
            self.rows = [
                r
                for r in self.BOUNDARY_LEDGERS[self.sample["document_id"]]
                if self.sample["first_position"] - 2
                <= r["position"]
                <= self.sample["last_position_inclusive"] + 2
            ]
            display(
                HTML(
                    f"<details><summary>Boundary proposals around {esc(self.sample['sample_id'])}</summary>"
                    + table_html(self.rows, self.LEDGER_COLUMNS)
                    + "</details>"
                )
            )
        for self.did, self.rows in self.BOUNDARY_LEDGERS.items():
            display(
                HTML(
                    f"<details><summary>Complete proposed ledger: Document {self.DOCUMENTS[self.did]['ordinal']}</summary>"
                    + table_html(self.rows, self.LEDGER_COLUMNS)
                    + "</details>"
                )
            )
        show_json(
            "Complete evidence-linked ledger, including retained/rejected candidates",
            self.BOUNDARY_LEDGERS,
        )

    def step_6c_inspect_uncertain_rejected_evidence_before_accepting_the_partition(
        self,
    ):
        """6c. Inspect uncertain/rejected evidence before accepting the partition."""
        self.exception_rows = [
            r
            for rows in self.BOUNDARY_LEDGERS.values()
            for r in rows
            if not r["creates_boundary"]
            and r["decision"] != "reviewed_title_attached"
            or r["proposed_kind"] == "unclassified"
            or any(("Repeated label" in warning for warning in r["uncertainty"]))
        ]
        show_table(self.exception_rows, self.LEDGER_COLUMNS, limit=15)
        show_json(
            "All exceptional/uncertain boundary records (not just the preview)",
            self.exception_rows,
        )
        for self.position in (2051, 2158, 3458, 26033, 26047, 2722, 26075):
            display(HTML(f"<h4>Source evidence around position {self.position}</h4>"))
            show_table(
                [
                    {
                        "position": q,
                        "text": self.BY_POSITION[q]["raw_text"],
                        "markers": [
                            c["matched_label"]
                            for c in self.BY_POSITION[q]["structural_annotations"][
                                "legal_marker_candidates"
                            ]
                        ],
                    }
                    for q in range(self.position - 1, self.position + 2)
                ]
            )
        require(
            fingerprint(self.BOUNDARY_LEDGERS) == self.BOUNDARY_LEDGER_FINGERPRINT,
            "Ledger changed after display; rerun ledger review output.",
        )

    def assemble_structural_units(self, view, ledger, experiment_id):
        boundaries = [r for r in ledger if r["creates_boundary"]]
        require(
            not view["block_ids"] or (boundaries and boundaries[0]["block_index"] == 0),
            "Ledger omits document start.",
        )
        require(
            [r["block_index"] for r in boundaries]
            == sorted({r["block_index"] for r in boundaries}),
            "Duplicate or unordered structural boundaries.",
        )
        records = []
        for index, boundary in enumerate(boundaries):
            next_boundary = (
                boundaries[index + 1] if index + 1 < len(boundaries) else None
            )
            lo, hi = (
                boundary["offset"],
                next_boundary["offset"] if next_boundary else len(view["text"]),
            )
            end_index = (
                next_boundary["block_index"]
                if next_boundary
                else len(view["block_ids"])
            )
            evidence = [
                r
                for r in ledger
                if boundary["block_index"] <= r["block_index"] < end_index
            ]
            records.append(
                {
                    "id": "structural:"
                    + fingerprint(
                        [
                            experiment_id,
                            view["document_id"],
                            boundary["block_id"],
                            lo,
                            hi,
                        ]
                    ),
                    "ordinal": index + 1,
                    "document_id": view["document_id"],
                    "start": lo,
                    "end": hi,
                    "text": view["text"][lo:hi],
                    "block_ids": view["block_ids"][boundary["block_index"] : end_index],
                    "configuration": self.STRUCTURAL_CONFIGURATION,
                    "setup_id": self.SETUP_ID,
                    "structural_id": experiment_id,
                    "record_kind": "provisional structural "
                    + boundary["proposed_kind"],
                    "unit_kind": boundary["proposed_kind"],
                    "span_semantics": "heading/context only; not a complete descendant subtree"
                    if boundary["proposed_kind"] in self.CONTEXT_KINDS
                    else "uncapped flat source span; interpretation provisional",
                    "opening_ledger_id": boundary["id"],
                    "closing_ledger_id": next_boundary["id"]
                    if next_boundary
                    else "document_end",
                    "evidence_ids": [r["id"] for r in evidence],
                    "uncertainty": sorted(
                        {warning for r in evidence for warning in r["uncertainty"]}
                    ),
                    "scope_evidence_block_id_not_parent": boundary[
                        "scope_evidence_block_id_not_parent"
                    ],
                }
            )
        return records

    def validate_structural_results(self):
        seen = set()
        for did, records in self.STRUCTURAL_RESULTS.items():
            view = self.VIEWS[did]
            require(
                "".join((r["text"] for r in records)) == view["text"],
                "Structural text reconstruction failed.",
            )
            require(
                [bid for r in records for bid in r["block_ids"]] == view["block_ids"],
                "Source block coverage/order changed.",
            )
            end = 0
            for r in records:
                self.check_display_record(r)
                require(
                    r["start"] == end and r["end"] >= r["start"],
                    "Gap/overlap in structural partition.",
                )
                require(
                    r["id"] not in seen and r["structural_id"] == self.STRUCTURAL_ID,
                    "Invalid structural identity.",
                )
                seen.add(r["id"])
                require(
                    r["text"]
                    == self.reconstruct(self.source_map(did, r["start"], r["end"])),
                    "Structural source map mismatch.",
                )
                require(
                    not self.paragraph_cuts(r),
                    "A structural boundary cut an original paragraph.",
                )
                require(
                    "parent_id" not in r,
                    "Parent-child relationship introduced unexpectedly.",
                )
                end = r["end"]
            require(end == len(view["text"]), "Document tail missing.")
        return len(seen)

    def step_6d_generate_uncapped_structural_units_from_the_displayed_ledger(self):
        """6d. Generate uncapped structural units from the displayed ledger."""
        self.STRUCTURAL_RESULTS = {
            did: self.assemble_structural_units(
                self.VIEWS[did], self.BOUNDARY_LEDGERS[did], self.STRUCTURAL_ID
            )
            for did in self.BASELINE_DOCUMENT_IDS
        }
        self.STRUCTURAL_RESULTS_FINGERPRINT = fingerprint(self.STRUCTURAL_RESULTS)
        self.STRUCTURAL_GENERATION_CONTEXT = {
            "structural_id": self.STRUCTURAL_ID,
            "ledger_fingerprint": self.BOUNDARY_LEDGER_FINGERPRINT,
            "setup_id": self.SETUP_ID,
        }
        self.structural_count = self.validate_structural_results()
        print(
            "PASS:",
            self.structural_count,
            "uncapped units; exact text/block coverage; no overlaps or paragraph cuts.",
        )
        show_table(
            [
                {
                    "document": self.DOCUMENTS[did]["ordinal"],
                    "units": len(records),
                    "characters": sum((r["end"] - r["start"] for r in records)),
                }
                for did, records in self.STRUCTURAL_RESULTS.items()
            ]
        )

    def structural_summary(self, record):
        return {
            "id": record["id"],
            "document": self.DOCUMENTS[record["document_id"]]["ordinal"],
            "kind": record["unit_kind"],
            "characters": record["end"] - record["start"],
            "first_position": self.BLOCKS[record["block_ids"][0]]["position"],
            "last_position": self.BLOCKS[record["block_ids"][-1]]["position"],
            "scope_evidence_position_not_parent": self.BLOCKS[
                record["scope_evidence_block_id_not_parent"]
            ]["position"]
            if record["scope_evidence_block_id_not_parent"]
            else None,
            "preview": record["text"][:150],
            "uncertainty": record["uncertainty"],
        }

    def step_6e_natural_sizes_residuals_annexes_provisions_and_uncertainty(self):
        """6e. Natural sizes, residuals, Annexes, § provisions, and uncertainty."""
        self.structural_records = [
            r
            for did in self.BASELINE_DOCUMENT_IDS
            for r in self.STRUCTURAL_RESULTS[did]
        ]
        self.STRUCTURAL_SIZE_ROWS = [
            {
                "kind": kind,
                **length_summary(
                    (
                        r["end"] - r["start"]
                        for r in self.structural_records
                        if r["unit_kind"] == kind
                    )
                ),
            }
            for kind in sorted({r["unit_kind"] for r in self.structural_records})
        ]
        show_table(self.STRUCTURAL_SIZE_ROWS)
        show_table(
            [
                {
                    "all_units": self.structural_count,
                    **length_summary(
                        (r["end"] - r["start"] for r in self.structural_records)
                    ),
                    "coverage_pct": 100,
                    "overlap_characters": 0,
                }
            ]
        )
        self.ordered_sizes = sorted(
            (r["end"] - r["start"] for r in self.structural_records)
        )
        self.p10, self.p90 = [
            self.ordered_sizes[max(0, math.ceil(q * len(self.ordered_sizes)) - 1)]
            for q in (0.1, 0.9)
        ]
        self.SMALL_STRUCTURAL = [
            self.structural_summary(r)
            for r in sorted(
                self.structural_records, key=lambda r: (r["end"] - r["start"], r["id"])
            )
            if r["end"] - r["start"] <= self.p10
        ]
        self.LARGE_STRUCTURAL = [
            self.structural_summary(r)
            for r in sorted(
                self.structural_records,
                key=lambda r: (-(r["end"] - r["start"]), r["id"]),
            )
            if r["end"] - r["start"] >= self.p90
        ]
        print(
            "Empirical flags only — small <= p10:",
            self.p10,
            "; large >= p90:",
            self.p90,
            "characters. No fallback is applied.",
        )
        show_table(self.SMALL_STRUCTURAL, limit=8)
        show_table(self.LARGE_STRUCTURAL, limit=8)
        self.SIZE_COMPARISONS = [
            {
                "Step_5_length_for_comparison_only": length,
                "units_exceeding_length": sum(
                    (r["end"] - r["start"] > length for r in self.structural_records)
                ),
                "percent": round(
                    100
                    * sum(
                        (
                            r["end"] - r["start"] > length
                            for r in self.structural_records
                        )
                    )
                    / self.structural_count,
                    2,
                ),
            }
            for length in (1000, 2000, 4000)
        ]
        show_table(self.SIZE_COMPARISONS)
        for self.kind in ("annex", "paragraph_sign", "unclassified", "residual"):
            self.rows = [
                self.structural_summary(r)
                for r in self.structural_records
                if r["unit_kind"] == self.kind
            ]
            display(
                HTML(
                    f"<details><summary>All {esc(self.kind)} units ({len(self.rows)}): sizes and scope evidence</summary>"
                    + table_html(self.rows)
                    + "</details>"
                )
            )
        self.BOUNDARY_DECISION_COUNTS = Counter(
            (r["decision"] for rows in self.BOUNDARY_LEDGERS.values() for r in rows)
        )
        show_table(
            [
                {"decision": key, "count": count}
                for key, count in sorted(self.BOUNDARY_DECISION_COUNTS.items())
            ]
        )
        show_json(
            "All small/large flags (full lists, not just previews)",
            {"small": self.SMALL_STRUCTURAL, "large": self.LARGE_STRUCTURAL},
        )

    def ensure_structural_current(self):
        self.ensure_baseline_current()
        require(
            self.STRUCTURAL_GENERATION_CONTEXT
            == {
                "structural_id": self.STRUCTURAL_ID,
                "ledger_fingerprint": self.BOUNDARY_LEDGER_FINGERPRINT,
                "setup_id": self.SETUP_ID,
            },
            "Generation context is stale; regenerate units from the current displayed ledger.",
        )
        require(
            fingerprint(self.STRUCTURAL_SPEC) == self.STRUCTURAL_ID
            and self.STRUCTURAL_SPEC["overrides"] == self.STRUCTURAL_OVERRIDES
            and (self.STRUCTURAL_SPEC["title_pairs"] == self.TITLE_PAIRS),
            "Structural policy changed; rerun ledger, generation and diagnostics.",
        )
        require(
            fingerprint(self.BOUNDARY_LEDGERS) == self.BOUNDARY_LEDGER_FINGERPRINT,
            "Ledger changed; re-display it before regenerating units.",
        )
        require(
            fingerprint(self.STRUCTURAL_RESULTS) == self.STRUCTURAL_RESULTS_FINGERPRINT,
            "Structural results changed; regenerate diagnostics.",
        )

    def compare_structural_sample(
        self, sample_id, fixed_config="chars-2000-overlap-10pct", max_cards=3
    ):
        self.ensure_structural_current()
        require(
            sample_id in self.SAMPLE_BY_ID and fixed_config in self.CONFIG_BY_ID,
            "Unknown frozen sample/fixed configuration.",
        )
        require(
            max_cards is None or (type(max_cards) is int and max_cards > 0),
            "max_cards must be positive or None.",
        )
        sample = self.SAMPLE_BY_ID[sample_id]
        did, lo, hi = (sample["document_id"], sample["start"], sample["end"])
        source = self.VIEWS[did]["text"][lo:hi]
        columns = []
        for label, records in (
            (fixed_config, self.FIXED_RESULTS[fixed_config][did]),
            (self.STRUCTURAL_CONFIGURATION, self.STRUCTURAL_RESULTS[did]),
        ):
            hits = [
                r
                for r in records
                if intersection_length((lo, hi), (r["start"], r["end"]))
            ]
            cuts = sorted(
                {c for r in hits for c in (r["start"], r["end"]) if lo <= c <= hi}
            )
            overlaps = [
                (b["start"], a["end"])
                for a, b in zip(records, records[1:])
                if b["start"] < a["end"] and b["start"] < hi and (a["end"] > lo)
            ]
            chosen = hits
            if max_cards is not None and len(hits) > max_cards:
                indices = (
                    [0]
                    if max_cards == 1
                    else sorted(
                        {
                            round(i * (len(hits) - 1) / (max_cards - 1))
                            for i in range(max_cards)
                        }
                    )
                )
                chosen = [hits[i] for i in indices]
            body = f"<h4>{esc(label)}</h4><p>{len(hits)} intersecting units; {len(chosen)} shown; {len(hits) - len(chosen)} omitted.</p>"
            body += "<details><summary>Same complete sample: ALL cut points and overlaps</summary>"
            body += highlight_html(source, lo, cuts, overlaps, (lo, hi)) + "</details>"
            for r in chosen:
                index = r["ordinal"] - 1
                body += self.span_card(
                    r,
                    sample,
                    records[max(0, index - 1) : index + 2],
                    self.REVIEWED_PROVISIONS,
                )
                if "unit_kind" in r:
                    body += details_html(
                        "Structural role and exact ledger evidence (not hierarchy)",
                        json.dumps(
                            {
                                k: r[k]
                                for k in (
                                    "unit_kind",
                                    "span_semantics",
                                    "opening_ledger_id",
                                    "closing_ledger_id",
                                    "evidence_ids",
                                    "uncertainty",
                                )
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    )
            columns.append("<div style='flex:1;min-width:320px'>" + body + "</div>")
        display(
            HTML(
                f"<details><summary>Same source: {esc(sample_id)} — fixed vs uncapped structural</summary>"
                + "<div style='display:flex;gap:12px;overflow:auto'>"
                + "".join(columns)
                + "</div></details>"
            )
        )

    def step_6f_same_source_visual_comparison_and_sample_diagnostics(self):
        """6f. Same-source visual comparison and sample diagnostics."""
        self.STRUCTURAL_SAMPLE_DIAGNOSTICS = []
        for self.sample in self.BASELINE_SAMPLES:
            self.lo, self.hi, self.did = (
                self.sample["start"],
                self.sample["end"],
                self.sample["document_id"],
            )
            self.hits = [
                r
                for r in self.STRUCTURAL_RESULTS[self.did]
                if intersection_length((self.lo, self.hi), (r["start"], r["end"]))
            ]
            self.covered = interval_union_length(
                ((max(self.lo, r["start"]), min(self.hi, r["end"])) for r in self.hits)
            )
            self.sample_units = {
                u["id"]
                for u in self.REVIEWED_PROVISIONS
                if u["document_id"] == self.did
                and intersection_length((self.lo, self.hi), (u["start"], u["end"]))
            }
            self.cut_units = {
                uid for r in self.hits for uid in self.legal_diagnostic(r)["cut"]
            } & self.sample_units
            self.contained_units = {
                uid for r in self.hits for uid in self.legal_diagnostic(r)["contained"]
            } & self.sample_units
            require(
                self.covered == self.hi - self.lo,
                "Structural sample coverage incomplete.",
            )
            self.STRUCTURAL_SAMPLE_DIAGNOSTICS.append(
                {
                    "sample": self.sample["sample_id"],
                    "units": len(self.hits),
                    "kinds": sorted({r["unit_kind"] for r in self.hits}),
                    "coverage_pct": 100,
                    "whole_sample_in_one_unit": any(
                        (
                            r["start"] <= self.lo and self.hi <= r["end"]
                            for r in self.hits
                        )
                    ),
                    "ledger_units_cut": len(self.cut_units)
                    if self.sample_units
                    else "unassessed",
                    "ledger_units_contained": len(self.contained_units)
                    if self.sample_units
                    else "unassessed",
                    "paragraphs_cut": sum(
                        (bool(self.paragraph_cuts(r)) for r in self.hits)
                    ),
                    "outside_sample_characters": interval_union_length(
                        ((r["start"], r["end"]) for r in self.hits)
                    )
                    - self.covered,
                }
            )
        show_table(self.STRUCTURAL_SAMPLE_DIAGNOSTICS)
        for self.sample in self.BASELINE_SAMPLES:
            self.compare_structural_sample(self.sample["sample_id"])

    def step_6g_corpus_comparison_and_observed_counterexamples(self):
        """6g. Corpus comparison and observed counterexamples."""
        self.structural_cut_units = {
            uid
            for r in self.structural_records
            for uid in self.legal_diagnostic(r)["cut"]
        }
        self.structural_contained_units = {
            uid
            for r in self.structural_records
            for uid in self.legal_diagnostic(r)["contained"]
        }
        self.STRUCTURAL_COMPARISON_ROW = {
            "configuration": self.STRUCTURAL_CONFIGURATION,
            "chunks": self.structural_count,
            "size_min": min(self.ordered_sizes),
            "size_median": length_summary(self.ordered_sizes)["median_p50"],
            "size_max": max(self.ordered_sizes),
            "extra_character_pct": 0.0,
            "paragraphs_cut": 0,
            "ledger_units_cut_of_9": len(self.structural_cut_units),
            "ledger_units_contained_somewhere_of_9": len(
                self.structural_contained_units
            ),
            "chunks_combining_ledger_units": sum(
                (
                    len(self.legal_diagnostic(r)["touched"]) > 1
                    for r in self.structural_records
                )
            ),
        }
        show_table(
            self.CORPUS_DIAGNOSTICS + [self.STRUCTURAL_COMPARISON_ROW],
            list(self.STRUCTURAL_COMPARISON_ROW),
        )
        for self.record in (
            min(self.structural_records, key=lambda r: r["end"] - r["start"]),
            max(self.structural_records, key=lambda r: r["end"] - r["start"]),
        ):
            display(
                HTML(
                    "<h4>Observed size extreme — retained without resizing</h4>"
                    + self.span_card(
                        self.record, reviewed_units=self.REVIEWED_PROVISIONS
                    )
                )
            )
            show_json(
                "Extreme unit interpretation", self.structural_summary(self.record)
            )
        print(
            "Observed structural result:",
            self.structural_count,
            "units; sizes",
            min(self.ordered_sizes),
            "to",
            max(self.ordered_sizes),
            "characters.",
        )
        print(
            "Residual/unclassified units:",
            sum(
                (
                    r["unit_kind"] in {"residual", "unclassified"}
                    for r in self.structural_records
                )
            ),
        )
        print(
            "Reviewed provision boundaries cut:",
            len(self.structural_cut_units),
            "of",
            len(self.REVIEWED_PROVISIONS),
            "annotated units.",
        )
        print(
            "The false Annex marker in EU Article 17 stays in its Article; repeated Annex labels remain separate source occurrences."
        )
        print(
            "All other candidate boundaries remain provisional. Size variation and detached heading context require human review."
        )
        print(
            "No final strategy selected. No parent-child links, size caps, or fallback splitting introduced."
        )

    def step_6h_validate_conservative_behavior_and_save_a_separate_report(self):
        """6h. Validate conservative behavior and save a separate report."""
        self.fixture_view, self.fixture_blocks = structural_fixture(
            [
                ("Преамбюл", None, None),
                ("Глава първа", "chapter", 2),
                ("ОБЩИ ПОЛОЖЕНИЯ", None, 3),
                ("междинен текст", None, None),
                ("Чл. 2а. правило", "article", None),
                ("Виж чл. 99 и § 1 вътре в текста.", None, None),
                ("Неясен раздел", None, 2),
                ("§ 1. текст", "paragraph_sign", None),
                ("Друга неясна група", None, 3),
                ("§ 1. друг текст", "paragraph_sign", None),
                ("Приложение I", "annex", 2),
                ("Чл. 1. образец в приложение", "article", None),
                ("Приложение I", "annex", 2),
                ("", None, None),
            ]
        )
        self.fixture_pairs = {"fixture-1": "fixture-2"}
        self.fixture_ledger = self.propose_structural_boundaries(
            self.fixture_view, self.fixture_blocks, title_pairs=self.fixture_pairs
        )
        self.fixture_units = self.assemble_structural_units(
            self.fixture_view, self.fixture_ledger, "fixture"
        )
        require(
            "".join((r["text"] for r in self.fixture_units))
            == self.fixture_view["text"],
            "Fixture text changed.",
        )
        require(
            [bid for r in self.fixture_units for bid in r["block_ids"]]
            == self.fixture_view["block_ids"],
            "Fixture empty block lost.",
        )
        require(
            not any((r["position"] == 5 for r in self.fixture_ledger)),
            "Inline citation became a boundary.",
        )
        require(
            next((r for r in self.fixture_ledger if r["position"] == 2))["decision"]
            == "reviewed_title_attached",
            "Detached title not retained.",
        )
        require(
            next((r for r in self.fixture_ledger if r["position"] == 3))[
                "proposed_kind"
            ]
            == "residual",
            "Interstitial residual lost.",
        )
        require(
            next((r for r in self.fixture_ledger if r["position"] == 6))[
                "proposed_kind"
            ]
            == "unclassified",
            "Unknown heading assigned a legal role.",
        )
        require(
            not next((r for r in self.fixture_ledger if r["position"] == 11))[
                "creates_boundary"
            ],
            "Annex internal Article manufactured as a separate unit.",
        )
        require(
            sum((r["unit_kind"] == "annex" for r in self.fixture_units)) == 2,
            "Repeated Annex labels collapsed.",
        )
        require(
            any(
                (
                    "Repeated label" in w
                    for r in self.fixture_ledger
                    for w in r["uncertainty"]
                )
            ),
            "Repeated labels not flagged.",
        )
        self.changed_ranks = json.loads(json.dumps(self.fixture_blocks))
        for self.b in self.changed_ranks.values():
            if self.b["structural_annotations"]["word_heading_level"] is not None:
                self.b["structural_annotations"]["word_heading_level"] = 6
        self.changed_ledger = self.propose_structural_boundaries(
            self.fixture_view, self.changed_ranks, title_pairs=self.fixture_pairs
        )
        require(
            [
                (r["offset"], r["proposed_kind"], r["creates_boundary"])
                for r in self.changed_ledger
            ]
            == [
                (r["offset"], r["proposed_kind"], r["creates_boundary"])
                for r in self.fixture_ledger
            ],
            "Word heading rank changed legal boundaries.",
        )
        self.false_view, self.false_blocks = structural_fixture(
            [
                ("Чл. 1. изменя друг акт", "article", None),
                ("Приложение II се изменя, както следва:", "annex", 2),
                ("Чл. 2. текст", "article", None),
            ]
        )
        self.false_ledger = self.propose_structural_boundaries(
            self.false_view, self.false_blocks
        )
        require(
            not self.false_ledger[1]["creates_boundary"],
            "Amendment reference became Annex boundary.",
        )
        self.conflicting = json.loads(json.dumps(self.false_blocks))
        self.conflicting["fixture-2"]["structural_annotations"][
            "legal_marker_candidates"
        ].append(
            {
                **self.conflicting["fixture-2"]["structural_annotations"][
                    "legal_marker_candidates"
                ][0],
                "kind": "paragraph_sign",
            }
        )
        require(
            self.propose_structural_boundaries(self.false_view, self.conflicting)[-1][
                "proposed_kind"
            ]
            == "unclassified",
            "Conflicting markers guessed a legal role.",
        )
        expect_value_error(
            lambda: self.propose_structural_boundaries(
                self.fixture_view,
                self.fixture_blocks,
                title_pairs={"fixture-1": "fixture-3"},
            ),
            "immediately follow",
        )
        expect_value_error(
            lambda: self.propose_structural_boundaries(
                self.false_view,
                self.false_blocks,
                overrides={
                    "fixture-1": {
                        "expected_text_sha256": "changed",
                        "action": "retain",
                        "kind": None,
                        "reason": "test",
                    }
                },
            ),
            "Override text changed",
        )
        self.correct_generation_context = self.STRUCTURAL_GENERATION_CONTEXT
        try:
            self.STRUCTURAL_GENERATION_CONTEXT = {
                **self.correct_generation_context,
                "ledger_fingerprint": "stale",
            }
            expect_value_error(
                self.ensure_structural_current, "Generation context is stale"
            )
        finally:
            self.STRUCTURAL_GENERATION_CONTEXT = self.correct_generation_context
        for self.did, self.rows in self.BOUNDARY_LEDGERS.items():
            require(
                all(
                    (
                        r["scope_evidence_block_id_not_parent"] is None
                        or self.BLOCKS[r["scope_evidence_block_id_not_parent"]][
                            "document_id"
                        ]
                        == self.did
                        for r in self.rows
                    )
                ),
                "Scope evidence leaked across document boundaries.",
            )
        require(
            self.validate_structural_results() == self.structural_count,
            "Structural count changed.",
        )
        for self.unit in self.REVIEWED_PROVISIONS:
            self.hits = [
                r
                for r in self.STRUCTURAL_RESULTS[self.unit["document_id"]]
                if intersection_length(
                    (self.unit["start"], self.unit["end"]), (r["start"], r["end"])
                )
            ]
            require(
                len(self.hits) == 1
                and self.hits[0]["start"] == self.unit["start"]
                and (self.hits[0]["end"] >= self.unit["end"]),
                "Inspected provision was split or merged with preceding content.",
            )
            require(
                set(self.hits[0]["text"][self.unit["end"] - self.unit["start"] :])
                <= {"\n"},
                "Inspected endpoint swallowed following content.",
            )
        self.false_annex = next(
            (
                r
                for r in self.BOUNDARY_LEDGERS[self.DOC_BY_ORDINAL[11]["document_id"]]
                if r["position"] == 26047
            )
        )
        require(
            not self.false_annex["creates_boundary"],
            "Reviewed false Annex became a boundary.",
        )
        self.article17 = next(
            (
                r
                for r in self.STRUCTURAL_RESULTS[self.DOC_BY_ORDINAL[11]["document_id"]]
                if r["block_ids"][0] == self.BY_POSITION[26038]["id"]
            )
        )
        require(
            self.BY_POSITION[26047]["id"] in self.article17["block_ids"]
            and self.BY_POSITION[26054]["id"] not in self.article17["block_ids"],
            "Article 17/18 boundary mishandled.",
        )
        require(
            len(self.STRUCTURAL_RESULTS[self.DOC_BY_ORDINAL[16]["document_id"]]) == 1
            and self.STRUCTURAL_RESULTS[self.DOC_BY_ORDINAL[16]["document_id"]][0][
                "unit_kind"
            ]
            == "residual",
            "Marker-free document gained a hierarchy.",
        )
        require(
            max(self.ordered_sizes) > max((c["length"] for c in self.CONFIGURATIONS)),
            "Uncapped baseline unexpectedly has a fixed-length cap.",
        )
        self.ensure_structural_current()
        self.repeated_ledgers = {
            did: self.propose_structural_boundaries(
                self.VIEWS[did],
                self.BLOCKS,
                self.STRUCTURAL_OVERRIDES,
                self.TITLE_PAIRS,
            )
            for did in self.BASELINE_DOCUMENT_IDS
        }
        require(
            fingerprint(self.repeated_ledgers) == self.BOUNDARY_LEDGER_FINGERPRINT,
            "Boundary ledger is not reproducible.",
        )
        require(
            fingerprint(
                {
                    did: self.assemble_structural_units(
                        self.VIEWS[did], self.repeated_ledgers[did], self.STRUCTURAL_ID
                    )
                    for did in self.BASELINE_DOCUMENT_IDS
                }
            )
            == self.STRUCTURAL_RESULTS_FINGERPRINT,
            "Structural IDs/text are not reproducible.",
        )
        require(
            fingerprint(self.FIXED_RESULTS) == self.STEP5_RESULT_FINGERPRINT
            and self.report_path.read_bytes() == self.STEP5_REPORT_BYTES,
            "Approved fixed-length baseline/report changed.",
        )
        require(
            self.APPROVED_MANIFEST_PATH.read_bytes() == self.approved_manifest_bytes,
            "Frozen sample manifest changed.",
        )
        require(
            hashlib.sha256(self.ARTIFACT.read_bytes()).hexdigest()
            == self.artifact_sha256
            and fingerprint(self.corpus) == self.corpus_fingerprint_before,
            "Stage 1 source changed.",
        )
        print(
            "PASS: conservative boundary fixtures; full text/block coverage; sample endpoints; false Annex; reproducibility; unchanged inputs and fixed baseline."
        )

    def step_6i_save_the_structural_report_and_approved_checkpoint(self):
        """6i. Save the structural report and approved checkpoint."""
        self.STRUCTURAL_REPORT = {
            "report_version": 1,
            "scope": "Step 6 only; uncapped provisional structural baseline",
            "structural_spec": self.STRUCTURAL_SPEC,
            "structural_id": self.STRUCTURAL_ID,
            "approved_fixed_result_fingerprint": self.STEP5_RESULT_FINGERPRINT,
            "boundary_ledgers": self.BOUNDARY_LEDGERS,
            "boundary_ledger_fingerprint": self.BOUNDARY_LEDGER_FINGERPRINT,
            "structural_result_fingerprint": self.STRUCTURAL_RESULTS_FINGERPRINT,
            "units": [
                {k: v for k, v in r.items() if k != "text"}
                for r in self.structural_records
            ],
            "size_by_kind": self.STRUCTURAL_SIZE_ROWS,
            "comparison_lengths_only": self.SIZE_COMPARISONS,
            "sample_diagnostics": self.STRUCTURAL_SAMPLE_DIAGNOSTICS,
            "corpus_comparison": self.CORPUS_DIAGNOSTICS
            + [self.STRUCTURAL_COMPARISON_ROW],
            "validation": "PASS: source fidelity, coverage, no overlap/cap, conservative fixtures, sample boundaries, deterministic ledger/IDs",
            "decision": "No final strategy selected; waiting for Step 6 review",
        }
        self.structural_report_path = (
            self.OUTPUT_DIR
            / f"structural_report.{fingerprint(self.STRUCTURAL_REPORT)}.json"
        )
        self.structural_report_bytes = (
            canonical(self.STRUCTURAL_REPORT) + "\n"
        ).encode("utf-8")
        if self.structural_report_path.exists():
            require(
                self.structural_report_path.read_bytes()
                == self.structural_report_bytes,
                "Existing structural report differs.",
            )
        else:
            self.structural_report_path.write_bytes(self.structural_report_bytes)
        require(
            json.loads(self.structural_report_path.read_text(encoding="utf-8"))
            == self.STRUCTURAL_REPORT,
            "Structural report round-trip failed.",
        )
        print("Structural report:", self.structural_report_path.relative_to(self.ROOT))
        print(
            "Approved Step 6 baseline verified. Step 7 follows; no final strategy selected."
        )
