"""Chunking: comparison."""

from pathlib import Path
from collections import defaultdict
import hashlib
import json
from property_copilot._display import HTML, display
import re
import zipfile
from urllib.parse import urldefrag
from .primitives import (
    canonical,
    clipped_coverage,
    details_html,
    esc,
    fingerprint,
    highlight_html,
    intersection_length,
    interval_union_length,
    length_summary,
    literal_occurrences,
    reference_components,
    require,
    show_table,
    table_html,
)


class ComparisonSteps:
    """Comparison steps; state belongs to the workflow instance."""

    def comparison_input_fingerprint(self):
        return fingerprint(
            [
                self.FIXED_RESULTS,
                self.STRUCTURAL_RESULTS,
                self.PC_DATA,
                list(self.OS_GROUPS.values()),
                self.H_ANNOTATIONS,
                self.M_REGISTRY,
            ]
        )

    def comparison_metrics(self, sample, strategy, records, parents=()):
        intervals = [(r["start"], r["end"]) for r in records]
        unique = interval_union_length(intervals)
        sizes = [r["end"] - r["start"] for r in records]
        cut_units = {u for r in records for u in self.legal_diagnostic(r)["cut"]}
        return {
            "sample_id": sample["sample_id"],
            "strategy": strategy,
            "records": len(records),
            "sample_coverage_pct": round(
                100 * clipped_coverage(records, sample) / sample["characters"], 2
            ),
            "size_distribution": length_summary(sizes),
            "unique_source_characters_in_displayed_records": unique,
            "extra_characters_outside_sample": unique
            - clipped_coverage(records, sample),
            "overlap_duplicate_characters": sum(sizes) - unique,
            "paragraph_blocks_cut": len(
                {b for r in records for b in self.paragraph_cuts(r)}
            ),
            "reviewed_legal_units_cut": sorted(cut_units),
            "records_combining_reviewed_units": sum(
                (len(self.legal_diagnostic(r)["touched"]) > 1 for r in records)
            ),
            "parent_sizes": [p["end"] - p["start"] for p in parents],
            "parent_containment_not_overlap": bool(parents),
            "source_evidence": [
                {
                    "id": r["id"],
                    "document_id": r["document_id"],
                    "start": r["start"],
                    "end": r["end"],
                }
                for r in records
            ],
        }

    def step_11_side_by_side_strategy_comparison_then_mentor_references(self):
        """Step 11 — Side-by-side strategy comparison, then mentor references."""
        self.ensure_metadata_current()
        self.C_APPROVED_PATHS = [
            self.APPROVED_MANIFEST_PATH,
            self.report_path,
            self.structural_report_path,
            self.pc_report_path,
            self.os_report_path,
            self.history_report_path,
            self.metadata_report_path,
        ]
        self.C_APPROVED_BYTES = {str(p): p.read_bytes() for p in self.C_APPROVED_PATHS}
        self.C_INPUT_FINGERPRINT = self.comparison_input_fingerprint()
        self.C_SPEC = {
            "version": 1,
            "setup_id": self.SETUP_ID,
            "input_fingerprint": self.C_INPUT_FINGERPRINT,
            "display_configuration": self.GALLERY_CONFIGURATION,
            "samples": [s["sample_id"] for s in self.BASELINE_SAMPLES],
            "parent_choice": "smaller reviewed parents covering sample, else smallest existing enclosing parent",
            "new_strategy": False,
            "weighted_score": None,
        }
        self.C_RUN_ID = fingerprint(self.C_SPEC)
        self.C_SELECTIONS = {}
        for self.sample in self.BASELINE_SAMPLES:
            self.did, self.lo, self.hi = (
                self.sample["document_id"],
                self.sample["start"],
                self.sample["end"],
            )
            self.fixed = [
                c
                for c in self.FIXED_RESULTS[self.GALLERY_CONFIGURATION][self.did]
                if intersection_length((self.lo, self.hi), (c["start"], c["end"]))
            ]
            self.units = [
                u
                for u in self.STRUCTURAL_RESULTS[self.did]
                if intersection_length((self.lo, self.hi), (u["start"], u["end"]))
            ]
            self.parents = [
                p
                for p in self.PC_PARENTS.values()
                if p["document_id"] == self.did
                and p["family"] != "section_or_chapter"
                and intersection_length((self.lo, self.hi), (p["start"], p["end"]))
            ]
            self.covered = interval_union_length(
                [
                    (max(self.lo, p["start"]), min(self.hi, p["end"]))
                    for p in self.parents
                ]
            )
            if self.covered < self.hi - self.lo:
                self.enclosing = [
                    p
                    for p in self.PC_PARENTS.values()
                    if p["document_id"] == self.did
                    and p["start"] <= self.lo
                    and (self.hi <= p["end"])
                ]
                if self.enclosing:
                    self.parents = [
                        min(
                            self.enclosing,
                            key=lambda p: (p["end"] - p["start"], p["id"]),
                        )
                    ]
            self.parents.sort(key=lambda p: p["start"])
            self.groups = [
                self.PC_GROUP_BY_KEY[
                    p["case"],
                    "fixed_inside_each_contained_unit"
                    if p["family"] == "section_or_chapter"
                    else "fixed_inside_parent",
                    self.GALLERY_CONFIGURATION,
                ]
                for p in self.parents
            ]
            self.C_SELECTIONS[self.sample["sample_id"]] = {
                "fixed": self.fixed,
                "structural": self.units,
                "parent_group_ids": [g["id"] for g in self.groups],
            }
        self.C_METRICS = []
        for self.sample in self.BASELINE_SAMPLES:
            self.selection = self.C_SELECTIONS[self.sample["sample_id"]]
            for self.strategy in ("fixed", "structural"):
                self.C_METRICS.append(
                    self.comparison_metrics(
                        self.sample, self.strategy, self.selection[self.strategy]
                    )
                )
            self.parents = []
            self.children = []
            for self.gid in self.selection["parent_group_ids"]:
                self.parent, self.kids = self.relationship_display_records(self.gid)
                self.parents.append(self.parent)
                self.children.extend(self.kids)
            self.C_METRICS.append(
                self.comparison_metrics(
                    self.sample, "parent_child", self.children, self.parents
                )
            )
        show_table(
            [
                {
                    k: v
                    for k, v in row.items()
                    if k not in ("source_evidence", "reviewed_legal_units_cut")
                }
                for row in self.C_METRICS
            ]
        )

    def show_strategy_comparison(self, sample_id):
        sample = self.SAMPLE_BY_ID[sample_id]
        selection = self.C_SELECTIONS[sample_id]
        source = self.VIEWS[sample["document_id"]]["text"][
            sample["start"] : sample["end"]
        ]
        panels = []
        for strategy in ("fixed", "structural"):
            records = selection[strategy]
            body = "".join(
                (
                    self.span_card(r, sample, records, self.REVIEWED_PROVISIONS)
                    for r in records
                )
            )
            panels.append(
                "<section><h4>" + esc(strategy) + "</h4>" + body + "</section>"
            )
        body = ""
        for gid in selection["parent_group_ids"]:
            parent, children = self.relationship_display_records(gid)
            body += details_html(
                "Explicit parent choice and relationship set",
                json.dumps(
                    {
                        "group_id": gid,
                        "case": self.PC_GROUPS[gid]["case"],
                        "parent_id": parent["id"],
                        "review_basis": parent["review_basis"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            body += self.relationship_html(
                parent, children, sample, self.REVIEWED_PROVISIONS
            )
        panels.append("<section><h4>parent-child</h4>" + body + "</section>")
        display(
            HTML(
                "<details><summary>"
                + esc(sample_id)
                + " — identical source focus across three strategies</summary>"
                + "<h4>Frozen source span</h4>"
                + highlight_html(source, sample["start"])
                + details_html(
                    "Frozen source mappings",
                    json.dumps(sample["source_spans"], ensure_ascii=False, indent=2),
                )
                + "<div style='display:grid;grid-template-columns:repeat(3,minmax(320px,1fr));gap:12px;overflow-x:auto'>"
                + "".join(panels)
                + "</div></details>"
            )
        )

    def step_11a_aligned_source_and_strategy_panels(self):
        """11a. Aligned source and strategy panels."""
        for self.sample in self.BASELINE_SAMPLES:
            self.show_strategy_comparison(self.sample["sample_id"])
        show_table(
            [
                r
                for r in self.PC_GROUP_DIAGNOSTICS
                if r["configuration"] == self.GALLERY_CONFIGURATION
            ]
        )

    def step_11b_independent_evidence_and_initial_reviewer_rubric(self):
        """11b. Independent evidence and initial reviewer rubric."""
        self.C_SOURCE_REPETITION = []
        for self.did in self.BASELINE_DOCUMENT_IDS:
            self.occurrences = defaultdict(list)
            for self.bid in self.VIEWS[self.did]["block_ids"]:
                if len(self.BLOCKS[self.bid]["raw_text"]) >= 40:
                    self.occurrences[self.BLOCKS[self.bid]["raw_text"]].append(self.bid)
            self.repeated = [
                (text, bids) for text, bids in self.occurrences.items() if len(bids) > 1
            ]
            self.C_SOURCE_REPETITION.append(
                {
                    "document_id": self.did,
                    "exact_repeated_paragraph_groups": len(self.repeated),
                    "extra_occurrence_characters": sum(
                        (len(text) * (len(bids) - 1) for text, bids in self.repeated)
                    ),
                    "examples": [
                        {"verbatim_text": text, "source_block_ids": bids}
                        for text, bids in self.repeated[:3]
                    ],
                    "meaning": "distinct source positions; excluded from overlap duplication",
                }
            )
        show_table(self.C_SOURCE_REPETITION)
        self.C_RUBRIC = []
        for self.row in self.C_METRICS:
            self.evidence = {
                "sample_id": self.row["sample_id"],
                "source_spans": self.row["source_evidence"],
            }
            self.ratings = [
                (
                    "source preservation",
                    "PASS" if self.row["sample_coverage_pct"] == 100 else "FAIL",
                    f"Exact reconstruction validated; displayed records cover {self.row['sample_coverage_pct']}% of frozen sample.",
                ),
                (
                    "legal boundary quality",
                    "CONCERN"
                    if self.row["reviewed_legal_units_cut"]
                    or self.row["records_combining_reviewed_units"]
                    else "UNCERTAIN",
                    f"Reviewed units cut: {self.row['reviewed_legal_units_cut']}; records combining reviewed units: {self.row['records_combining_reviewed_units']}. Absence of flags is not complete legal validation.",
                ),
                (
                    "chunk size",
                    "CONCERN"
                    if (self.row["size_distribution"]["max"] or 0) > 4000
                    else "PASS",
                    f"Observed sizes {self.row['size_distribution']}; 4,000 is an experimental character probe, not a production limit.",
                ),
                (
                    "duplication / overlap",
                    "CONCERN" if self.row["overlap_duplicate_characters"] else "PASS",
                    f"{self.row['overlap_duplicate_characters']} repeated peer source characters. Parent containment and source repetition excluded.",
                ),
                (
                    "context preservation",
                    "UNCERTAIN",
                    f"{self.row['extra_characters_outside_sample']} distinct characters outside the focus are displayed. Inspect definitions, conditions, exceptions and cross-references; extra context need not be relevant.",
                ),
                (
                    "parent expansion",
                    "CONCERN"
                    if self.row["parent_sizes"] and max(self.row["parent_sizes"]) > 8000
                    else "UNCERTAIN",
                    f"Complete parent sizes {self.row['parent_sizes']}; per-child expansion is in Step 7 relationship diagnostics. No parent for flat strategies; no future context budget established.",
                ),
                (
                    "metadata usefulness",
                    "PASS",
                    "Document registry, raw dates, source labels/uncertainty and explicit links can be resolved (Step 10); filtering benefit remains untested.",
                ),
                (
                    "traceability / provenance",
                    "PASS",
                    "Exact block offsets and artifact/DOCX fingerprints resolve through the existing source maps and run registry.",
                ),
                (
                    "long-unit handling",
                    "CONCERN"
                    if self.row["strategy"] == "structural"
                    and (self.row["size_distribution"]["max"] or 0) > 8000
                    else "UNCERTAIN",
                    "Uncapped structural control remains visible; Step 8 validates contained fallback children. No size or fallback policy selected.",
                ),
            ]
            for self.criterion, self.rating, self.explanation in self.ratings:
                self.C_RUBRIC.append(
                    {
                        "sample_id": self.row["sample_id"],
                        "strategy": self.row["strategy"],
                        "criterion": self.criterion,
                        "rating": self.rating,
                        "explanation": self.explanation,
                        "evidence": self.evidence,
                    }
                )
        show_table(
            [
                {
                    k: r[k]
                    for k in (
                        "sample_id",
                        "strategy",
                        "criterion",
                        "rating",
                        "explanation",
                    )
                }
                for r in self.C_RUBRIC
                if r["sample_id"]
                in ("normal_article", "long_article", "nested_structure")
            ]
        )
        display(
            HTML(
                "<details><summary>All samples: complete rubric and source-backed evidence</summary>"
                + table_html(self.C_RUBRIC)
                + "</details>"
            )
        )
        show_table(self.OS_THRESHOLD_ROWS)
        show_table(self.OS_MATCHED_COMPARISONS)
        show_table(
            self.H_SAMPLE_SHARES,
            ["sample_id", "characters", "annotated_characters", "annotated_share_pct"],
        )
        show_table(self.H_WITNESSES)
        show_table(self.M_PLACEMENT)
        self.C_INDEPENDENT = {
            "spec": self.C_SPEC,
            "metrics": self.C_METRICS,
            "rubric": self.C_RUBRIC,
            "source_repetition": self.C_SOURCE_REPETITION,
            "parent_expansion": [
                r
                for r in self.PC_GROUP_DIAGNOSTICS
                if r["configuration"] == self.GALLERY_CONFIGURATION
            ],
            "all_fixed_settings": self.CORPUS_DIAGNOSTICS,
            "oversized_comparisons": self.OS_MATCHED_COMPARISONS,
            "history_shares": self.H_SAMPLE_SHARES,
            "metadata_placement": self.M_PLACEMENT,
        }
        self.C_INDEPENDENT_FINGERPRINT = fingerprint(self.C_INDEPENDENT)
        require(
            all((r["sample_coverage_pct"] == 100 for r in self.C_METRICS)),
            "A selected strategy representation does not cover the frozen sample.",
        )
        print(
            "Independent comparison frozen before mentor loading:",
            self.C_INDEPENDENT_FINGERPRINT,
        )

    def step_11c_separate_read_only_mentor_evaluation_path(self):
        """11c. Separate read-only mentor evaluation path."""
        require(
            fingerprint(self.C_INDEPENDENT) == self.C_INDEPENDENT_FINGERPRINT,
            "Complete independent review before mentor evaluation.",
        )
        self.C_ARCHIVE = self.ROOT / self.corpus["source"]["archive"]
        self.C_ARCHIVE_SHA = hashlib.sha256(self.C_ARCHIVE.read_bytes()).hexdigest()
        with zipfile.ZipFile(self.C_ARCHIVE, "r") as self.archive:
            self.reference_members = [
                name
                for name in self.archive.namelist()
                if name.endswith("/corpus/chunks.jsonl")
            ]
            require(len(self.reference_members) == 1, "Reference path must be unique.")
            self.C_REFERENCE_MEMBER = self.reference_members[0]
            self.reference_bytes = self.archive.read(self.C_REFERENCE_MEMBER)
            self.C_REFERENCE_ROWS = []
            for self.line_number, self.line in enumerate(
                self.reference_bytes.decode("utf-8").splitlines(), 1
            ):
                if not self.line.strip():
                    continue
                self.raw = json.loads(self.line)
                self.C_REFERENCE_ROWS.append(
                    {
                        "archive_line": self.line_number,
                        **{
                            key: self.raw.get(key, "")
                            for key in (
                                "document",
                                "source_ref",
                                "citation",
                                "heading",
                                "text",
                            )
                        },
                    }
                )
            self.builder_member = next(
                (
                    name
                    for name in self.archive.namelist()
                    if name.endswith("/scripts/build_corpus.py")
                )
            )
            self.builder_text = self.archive.read(self.builder_member).decode("utf-8")
        self.C_PREFIX_EVIDENCE = [
            {"archive_member": self.builder_member, "line": i, "verbatim_code": line}
            for i, line in enumerate(self.builder_text.splitlines(), 1)
            if '"embedding_text":' in line
        ]
        show_table(self.C_PREFIX_EVIDENCE)
        self.C_DOCUMENT_MAP = []
        for self.title, self.url in dict.fromkeys(
            ((r["document"], r["source_ref"]) for r in self.C_REFERENCE_ROWS)
        ):
            self.candidates = [
                did
                for did, d in self.M_REGISTRY.items()
                if d["source_titles"]["title"]["raw_text"] == self.title
                and any(
                    (
                        urldefrag(raw_url)[0] == urldefrag(self.url)[0]
                        for raw_url in self.raw_values(did, "source_url")
                    )
                )
            ]
            self.C_DOCUMENT_MAP.append(
                {
                    "mentor_title": self.title,
                    "mentor_url": self.url,
                    "source_document_ids": self.candidates,
                    "status": "exact"
                    if len(self.candidates) == 1
                    else "ambiguous"
                    if self.candidates
                    else "unmatched",
                    "review_basis": "Reviewed title and source-URL agreement; only URL fragment ignored for document identity",
                    "source_title": self.M_REGISTRY[self.candidates[0]][
                        "source_titles"
                    ]["title"]["raw_text"]
                    if len(self.candidates) == 1
                    else None,
                    "source_urls": self.raw_values(self.candidates[0], "source_url")
                    if len(self.candidates) == 1
                    else [],
                }
            )
        self.C_DOC_LOOKUP = {
            (r["mentor_title"], r["mentor_url"]): r for r in self.C_DOCUMENT_MAP
        }
        show_table(self.C_DOCUMENT_MAP)
        self.C_REFERENCE_FINGERPRINT = fingerprint(self.C_REFERENCE_ROWS)
        self.C_REFERENCE_COMPONENTS = {
            r["archive_line"]: reference_components(r["text"])
            for r in self.C_REFERENCE_ROWS
        }
        show_table(
            [
                {
                    "archive_line": r["archive_line"],
                    "citation": r["citation"],
                    **self.C_REFERENCE_COMPONENTS[r["archive_line"]],
                }
                for r in self.C_REFERENCE_ROWS
                if r["archive_line"] in (1, 4, 30)
            ]
        )

    def align_reference(self, reference):
        mapping = self.C_DOC_LOOKUP[reference["document"], reference["source_ref"]]
        result = {
            "archive_line": reference["archive_line"],
            "mentor_citation": reference["citation"],
            "mentor_heading": reference["heading"],
            "document_mapping_status": mapping["status"],
            "status": "unmatched",
            "source_document_id": None,
            "source_matches": [],
            "citation_candidates": [],
            "scope_limit": "Literal excerpt/citation evidence only; full legal-rule equivalence unverified",
        }
        if len(mapping["source_document_ids"]) != 1:
            result.update(
                status=mapping["status"], reason="Document mapping unresolved"
            )
            return result
        did = mapping["source_document_ids"][0]
        result["source_document_id"] = did
        text = self.VIEWS[did]["text"]
        component = self.C_REFERENCE_COMPONENTS[reference["archive_line"]]
        excerpt = component["source_excerpt"]
        citation = self.C_CITATION.search(reference["citation"])
        family = (
            "paragraph_sign" if citation and "§" in citation.group(0) else "article"
        )
        candidates = [
            p
            for p in self.C_CITATION_LOCATIONS[did]
            if citation
            and p["label_number"] == citation.group(1).lower()
            and (p["label_family"] == family)
        ]
        result["citation_candidates"] = candidates

        def compatible(a, b):
            return [
                p for p in candidates if p["start"] <= a and b <= p["evaluation_end"]
            ]

        exact = literal_occurrences(text, excerpt)
        if exact:
            good = [(a, b) for a, b in exact if not citation or compatible(a, b)]
            status = "exact" if len(exact) == 1 and len(good) == 1 else "ambiguous"
            result.update(
                status=status,
                reason="Full literal excerpt occurrence; citation compatibility checked"
                if status == "exact"
                else "Repeated literal text or incompatible/unresolved leading citation",
            )
            matches = exact
        else:
            probes = list(
                dict.fromkeys(
                    (
                        excerpt[i : i + 80]
                        for i in range(0, max(1, len(excerpt) - 59), 40)
                        if len(excerpt[i : i + 80]) >= 60
                    )
                )
            )
            matches = []
            for probe in probes:
                hits = literal_occurrences(text, probe)
                matches.extend(
                    ((a, b) for a, b in hits if not citation or compatible(a, b))
                )
            matches = sorted(set(matches))
            candidate_hits = {
                p["block_id"] for a, b in matches for p in compatible(a, b)
            }
            if matches and (
                citation
                and len(candidate_hits) == 1
                or (not citation and len(matches) == 1)
            ):
                result.update(
                    status="partial",
                    reason="Literal anchor(s) found; complete excerpt differs, is abbreviated, or has ellipses",
                )
            elif matches:
                result.update(
                    status="ambiguous",
                    reason="Literal anchors occur in multiple candidate contexts",
                )
            else:
                result.update(
                    status="unmatched",
                    reason="No citation-compatible literal anchor of at least 60 characters; unresolved, not evidence of missing source",
                )
        result["source_match_count"] = len(matches)
        result["all_source_match_spans"] = [[a, b] for a, b in matches]
        result["source_matches"] = [
            {
                "start": a,
                "end": b,
                "verbatim_source": text[a:b],
                "source_spans": self.source_map(did, a, b),
            }
            for a, b in matches[:6]
        ]
        return result

    def step_11d_citation_and_literal_excerpt_alignment_evaluation_only(self):
        """11d. Citation and literal-excerpt alignment (evaluation only)."""
        self.C_LEADING = re.compile("^\\s*(?:Чл\\.|Член|§)\\s*(\\d+[а-яА-Я]?)\\b", re.I)
        self.C_CITATION = re.compile("(?:чл\\.|член|§)\\s*(\\d+[а-яА-Я]?)\\b", re.I)
        self.C_CITATION_LOCATIONS = {}
        for self.did, self.view in self.VIEWS.items():
            self.locations = []
            for self.bid in self.view["block_ids"]:
                self.block = self.BLOCKS[self.bid]
                self.match = self.C_LEADING.match(self.block["raw_text"])
                self.markers = self.block["structural_annotations"][
                    "legal_marker_candidates"
                ]
                if self.match and any(
                    (m["kind"] in ("article", "paragraph_sign") for m in self.markers)
                ):
                    self._, self.lo, self.hi = self.BLOCK_SPANS[self.bid]
                    self.locations.append(
                        {
                            "label_number": self.match.group(1).lower(),
                            "label_family": "paragraph_sign"
                            if "§" in self.match.group(0)
                            else "article",
                            "start": self.lo,
                            "heading_end": self.hi,
                            "block_id": self.bid,
                            "position": self.block["position"],
                            "raw_heading": self.block["raw_text"],
                            "stage1_evidence": self.markers,
                        }
                    )
            for self.i, self.loc in enumerate(self.locations):
                self.loc["evaluation_end"] = (
                    self.locations[self.i + 1]["start"]
                    if self.i + 1 < len(self.locations)
                    else len(self.view["text"])
                )
            self.C_CITATION_LOCATIONS[self.did] = self.locations
        self.C_ALIGNMENTS = [self.align_reference(r) for r in self.C_REFERENCE_ROWS]
        show_table(
            [
                {
                    "status": status,
                    "evaluation_rows": sum(
                        (a["status"] == status for a in self.C_ALIGNMENTS)
                    ),
                    "meaning": "Reference correspondence only; not corpus completeness or retrieval accuracy",
                }
                for status in ("exact", "partial", "ambiguous", "unmatched")
            ]
        )
        show_table(
            [
                {
                    k: a.get(k)
                    for k in (
                        "archive_line",
                        "mentor_citation",
                        "document_mapping_status",
                        "status",
                        "reason",
                        "source_match_count",
                    )
                }
                for a in self.C_ALIGNMENTS
            ]
        )

    def step_11e_inspect_reference_excerpts_additions_and_source_context(self):
        """11e. Inspect reference excerpts, additions and source context."""
        self.C_REFERENCE_REVIEW = []
        self.selected_lines = []
        for self.status in ("exact", "partial", "ambiguous", "unmatched"):
            self.example = next(
                (a for a in self.C_ALIGNMENTS if a["status"] == self.status), None
            )
            if self.example:
                self.selected_lines.append(self.example["archive_line"])
        for self.a in self.C_ALIGNMENTS:
            if self.a["source_document_id"] in (
                self.DOC_BY_ORDINAL[2]["document_id"],
                self.DOC_BY_ORDINAL[11]["document_id"],
            ):
                self.selected_lines.append(self.a["archive_line"])
        self.selected_lines = list(dict.fromkeys(self.selected_lines))
        for self.line in self.selected_lines:
            self.alignment = next(
                (a for a in self.C_ALIGNMENTS if a["archive_line"] == self.line)
            )
            self.reference = next(
                (r for r in self.C_REFERENCE_ROWS if r["archive_line"] == self.line)
            )
            self.component = self.C_REFERENCE_COMPONENTS[self.line]
            self.C_REFERENCE_REVIEW.append(
                {
                    "archive_line": self.line,
                    "citation": self.reference["citation"],
                    "mapping": self.alignment["status"],
                    "rule_coverage_rating": "UNCERTAIN",
                    "rule_coverage": "Excerpt correspondence cannot establish all conditions/exceptions; compare source context below",
                    "boundary_rating": "CONCERN"
                    if self.alignment["status"] == "partial"
                    else "UNCERTAIN",
                    "boundary_choice": self.alignment["reason"],
                    "context_completeness": "UNCERTAIN: summaries/ellipsis are not replacements for omitted source clauses or history",
                    "citation_rating": "PASS"
                    if self.alignment["status"] in ("exact", "partial")
                    else "UNCERTAIN",
                    "citation_usefulness": "Source Article/anchor location is inspectable; subparagraph citation and legal scope still require review"
                    if self.alignment["status"] in ("exact", "partial")
                    else "Mapping unresolved; do not use as a verified source citation",
                    "context_rating": "CONCERN"
                    if "…" in self.component["source_excerpt"]
                    or "..." in self.component["source_excerpt"]
                    else "UNCERTAIN",
                    "source_match_spans": self.alignment.get(
                        "all_source_match_spans", []
                    ),
                    "source_document_id": self.alignment["source_document_id"],
                }
            )
            self.body = details_html(
                "Mentor excerpt only", self.component["source_excerpt"]
            )
            self.body += details_html(
                "Mentor-added English summary — excluded from source correspondence",
                self.component["english_summary_separate"],
            )
            self.body += details_html(
                "Marker / generated-prefix accounting",
                json.dumps(
                    {
                        k: self.component[k]
                        for k in (
                            "reference_excerpt_offsets",
                            "language_marker_separate",
                            "generated_context_prefix",
                        )
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            self.body += details_html(
                "Citation candidates, uncertainty and matched source maps",
                json.dumps(self.alignment, ensure_ascii=False, indent=2),
            )
            self.did = self.alignment["source_document_id"]
            if self.did:
                for self.match in self.alignment["source_matches"][:2]:
                    self.lo = max(0, self.match["start"] - 180)
                    self.hi = min(
                        len(self.VIEWS[self.did]["text"]), self.match["end"] + 240
                    )
                    self.body += "<h4>Unchanged source context</h4>" + highlight_html(
                        self.VIEWS[self.did]["text"][self.lo : self.hi],
                        self.lo,
                        focus=(self.match["start"], self.match["end"]),
                    )
                if not self.alignment["source_matches"]:
                    for self.candidate in self.alignment["citation_candidates"][:2]:
                        self.body += details_html(
                            "Unresolved candidate heading — not a match",
                            self.candidate["raw_heading"],
                        )
            display(
                HTML(
                    "<details><summary>Reference archive line "
                    + str(self.line)
                    + " / "
                    + esc(self.reference["citation"])
                    + " / "
                    + esc(self.alignment["status"])
                    + "</summary>"
                    + self.body
                    + "</details>"
                )
            )
        show_table(self.C_REFERENCE_REVIEW)

    def step_11f_validation_and_evaluation_isolation(self):
        """11f. Validation and evaluation isolation."""
        require(
            fingerprint(self.C_SPEC) == self.C_RUN_ID
            and self.C_SPEC["display_configuration"] == self.GALLERY_CONFIGURATION
            and (
                self.C_SPEC["samples"]
                == [s["sample_id"] for s in self.BASELINE_SAMPLES]
            ),
            "Comparison configuration changed; rerun Step 11.",
        )
        require(
            fingerprint(self.C_REFERENCE_ROWS) == self.C_REFERENCE_FINGERPRINT,
            "Reference evaluation inputs changed; rerun evaluation.",
        )
        require(
            self.comparison_input_fingerprint() == self.C_INPUT_FINGERPRINT,
            "Reference evaluation changed corpus inputs/results.",
        )
        require(
            fingerprint(self.C_INDEPENDENT) == self.C_INDEPENDENT_FINGERPRINT,
            "Mentor evidence changed independent observations.",
        )
        require(
            hashlib.sha256(self.C_ARCHIVE.read_bytes()).hexdigest()
            == self.C_ARCHIVE_SHA,
            "Source archive changed.",
        )
        require(
            all(
                (
                    Path(p).read_bytes() == data
                    for p, data in self.C_APPROVED_BYTES.items()
                )
            ),
            "Approved artifact/report changed.",
        )
        require(
            all(
                (
                    set(r)
                    == {
                        "archive_line",
                        "document",
                        "source_ref",
                        "citation",
                        "heading",
                        "text",
                    }
                    for r in self.C_REFERENCE_ROWS
                )
            ),
            "Reference allowlist violated.",
        )
        for self.r in self.C_REFERENCE_ROWS:
            self.c = self.C_REFERENCE_COMPONENTS[self.r["archive_line"]]
            self.lo, self.hi = self.c["reference_excerpt_offsets"]
            require(
                self.c["source_excerpt"] == self.r["text"][self.lo : self.hi],
                "Reference excerpt offsets changed.",
            )
        for self.a in self.C_ALIGNMENTS:
            require(
                self.a["status"] in ("exact", "partial", "ambiguous", "unmatched"),
                "Unknown correspondence category.",
            )
            for self.match in self.a["source_matches"]:
                require(
                    self.match["verbatim_source"]
                    == self.reconstruct(self.match["source_spans"])
                    == self.VIEWS[self.a["source_document_id"]]["text"][
                        self.match["start"] : self.match["end"]
                    ],
                    "Reference source evidence mismatch.",
                )
        require(
            literal_occurrences("абв абв", "абв") == [(0, 3), (4, 7)],
            "Repeated literal evidence lost.",
        )
        require(
            literal_occurrences("абв", "липсва") == [],
            "Unmatched literal evidence invented.",
        )
        require(
            reference_components("[EN original] abc [EN summary] explanation")[
                "source_excerpt"
            ]
            == "abc",
            "English original incorrectly removed.",
        )
        require(
            reference_components("текст [EN summary] summary")[
                "english_summary_separate"
            ]
            == "[EN summary] summary",
            "Summary not separated.",
        )
        require(
            self.C_LEADING.match("Чл. 2а. Текст").group(1) == "2а"
            and self.C_CITATION.search("§ 6, ал. 1").group(1) == "6",
            "Cyrillic suffix or § citation lost.",
        )
        require(
            all(
                (
                    r["rating"] in ("PASS", "CONCERN", "FAIL", "UNCERTAIN")
                    for r in self.C_RUBRIC
                )
            ),
            "Invalid reviewer rating.",
        )
        self.ensure_metadata_current()
        print(
            "PASS: independent comparison frozen; reference path read-only; source mappings, approved artifacts and corpus inputs unchanged."
        )

    def step_11g_evidence_table_and_stop_after_step_11(self):
        """11g. Evidence table and stop after Step 11."""
        self.C_FINAL_EVIDENCE = [
            {
                "strategy": "Fixed-Length",
                "strength": "PASS: exact source slices, bounded character size and measured overlap",
                "weakness": "CONCERN: reviewed provisions/paragraphs can be split; history-boundary witnesses show note/context separation",
                "unresolved": "UNCERTAIN: whether overlap restores necessary legal context or improves retrieval",
                "evidence": {
                    "sample_metrics": [
                        r
                        for r in self.C_METRICS
                        if r["strategy"] == "fixed"
                        and r["sample_id"]
                        in ("normal_article", "long_article", "publication_history")
                    ],
                    "history_boundary_witnesses": self.H_WITNESSES,
                },
            },
            {
                "strategy": "Document-Aware Structural",
                "strength": "PASS: complete uncapped provisional source units preserve text without peer overlap",
                "weakness": "CONCERN: uneven sizes and residual/uncertain boundaries; largest residual parent is 45,829 characters",
                "unresolved": "UNCERTAIN: correctness of unreviewed boundaries and a suitable future size policy",
                "evidence": {
                    "sample_metrics": [
                        r
                        for r in self.C_METRICS
                        if r["strategy"] == "structural"
                        and r["sample_id"]
                        in ("long_article", "long_paragraph", "unclassified_heading")
                    ],
                    "size_triggers": self.OS_THRESHOLD_ROWS,
                },
            },
            {
                "strategy": "Parent-Child",
                "strength": "PASS: explicit contained children resolve to complete source parents; small and large context remain inspectable",
                "weakness": "CONCERN: children still split provisions; Chapter context can be excessive and include additional units",
                "unresolved": "UNCERTAIN: which parent context is useful under a later token budget; metadata resolution is not retrieval validation",
                "evidence": {
                    "sample_metrics": [
                        r
                        for r in self.C_METRICS
                        if r["strategy"] == "parent_child"
                        and r["sample_id"]
                        in ("normal_article", "nested_structure", "long_article")
                    ],
                    "same_child_alternatives": self.IDENTICAL_CHILD_COMPARISONS,
                },
            },
        ]
        show_table(
            [
                {k: v for k, v in row.items() if k != "evidence"}
                for row in self.C_FINAL_EVIDENCE
            ]
        )
        self.C_REPORT = {
            "report_version": 1,
            "scope": "Step 11 only — existing strategies and read-only mentor comparison",
            "run_id": self.C_RUN_ID,
            "independent": self.C_INDEPENDENT,
            "independent_fingerprint": self.C_INDEPENDENT_FINGERPRINT,
            "reference_provenance": {
                "archive_sha256": self.C_ARCHIVE_SHA,
                "member": self.C_REFERENCE_MEMBER,
                "member_sha256": hashlib.sha256(self.reference_bytes).hexdigest(),
            },
            "document_mappings": self.C_DOCUMENT_MAP,
            "reference_components": list(self.C_REFERENCE_COMPONENTS.items()),
            "generated_prefix_evidence": self.C_PREFIX_EVIDENCE,
            "reference_alignments": self.C_ALIGNMENTS,
            "reference_review": self.C_REFERENCE_REVIEW,
            "final_evidence": self.C_FINAL_EVIDENCE,
            "decision": "No final strategy or parameters selected; waiting for Step 11 review",
        }
        self.comparison_report_path = (
            self.OUTPUT_DIR
            / f"strategy_comparison_report.{fingerprint(self.C_REPORT)}.json"
        )
        self.comparison_bytes = (canonical(self.C_REPORT) + "\n").encode("utf-8")
        if self.comparison_report_path.exists():
            require(
                self.comparison_report_path.read_bytes() == self.comparison_bytes,
                "Existing comparison report differs.",
            )
        else:
            self.comparison_report_path.write_bytes(self.comparison_bytes)
        require(
            json.loads(self.comparison_report_path.read_text(encoding="utf-8"))
            == json.loads(canonical(self.C_REPORT)),
            "Comparison report round trip failed.",
        )
        print(
            "Strategy/reference report:",
            self.comparison_report_path.relative_to(self.ROOT),
        )
        print(
            "STOP AFTER STEP 11 — evidence ready for review; no final strategy or Hybrid implementation."
        )
