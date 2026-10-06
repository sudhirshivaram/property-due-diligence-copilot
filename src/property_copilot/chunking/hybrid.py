"""Chunking: hybrid."""

from collections import Counter
from .integrity import verify_implementation
import hashlib
import json
from property_copilot._display import HTML, display
from .primitives import (
    canonical,
    check_os_windows,
    details_html,
    esc,
    expect_value_error,
    fingerprint,
    highlight_html,
    hybrid_review_ready,
    intersection_length,
    length_summary,
    require,
    show_json,
    show_table,
    table_html,
)


class HybridSteps:
    """Hybrid steps; state belongs to the workflow instance."""

    def step_12_hybrid_experiment_conclusions_and_stage_2_review(self):
        """Step 12 — Hybrid experiment, conclusions and Stage 2 review."""
        self.HY_STEP11_APPROVED = True
        self.HY_READY = hybrid_review_ready(
            self.HY_STEP11_APPROVED,
            vars(self).get("C_INDEPENDENT"),
            vars(self).get("OS_DIAGNOSTICS"),
            vars(self).get("C_FINAL_EVIDENCE"),
        )
        if not self.HY_READY:
            print("hybrid hypothesis pending review")
        else:
            self.ensure_metadata_current()
            require(
                fingerprint(self.C_INDEPENDENT) == self.C_INDEPENDENT_FINGERPRINT
                and self.comparison_input_fingerprint() == self.C_INPUT_FINGERPRINT,
                "Approved observations or source results changed; review before building the hybrid.",
            )
            print(
                "Evidence gate PASS: Step 11 approved; independent observations and Step 8 diagnostics recorded."
            )

    def step_12_hybrid_experiment_conclusions_and_stage_2_review_2(self):
        """Step 12 — Hybrid experiment, conclusions and Stage 2 review."""
        if self.HY_READY:
            self.HY_PRIOR_PATHS = [
                self.APPROVED_MANIFEST_PATH,
                self.report_path,
                self.structural_report_path,
                self.pc_report_path,
                self.os_report_path,
                self.history_report_path,
                self.metadata_report_path,
                self.comparison_report_path,
                self.ARTIFACT,
                self.C_ARCHIVE,
                self.ROOT / "notebooks/01_document_ingestion_parsing.ipynb",
                self.ROOT / "docs/stage-02-chunking-experiments-plan.md",
            ]
            self.HY_PRIOR_HASHES = {
                str(p.relative_to(self.ROOT)): hashlib.sha256(
                    p.read_bytes()
                ).hexdigest()
                for p in self.HY_PRIOR_PATHS
            }
            self.HY_APPROVED_CODE_HASHES = verify_implementation(self.ROOT)
            self.HY_SHORTLIST = [
                {
                    "id": "hybrid-4000-aware-2000-overlap0",
                    "threshold": 4000,
                    "setting": "boundary_aware-chars-2000-overlap-0pct",
                    "role": "provisional lead",
                },
                {
                    "id": "hybrid-4000-aware-2000-overlap10",
                    "threshold": 4000,
                    "setting": "boundary_aware-chars-2000-overlap-10pct",
                    "role": "overlap sensitivity",
                },
                {
                    "id": "hybrid-2000-aware-2000-overlap0",
                    "threshold": 2000,
                    "setting": "boundary_aware-chars-2000-overlap-0pct",
                    "role": "lower size-trigger sensitivity",
                },
            ]
            self.HY_LEAD = self.HY_SHORTLIST[0]["id"]
            self.HY_RULES = [
                {
                    "id": "retain_units",
                    "rule": "Retain each existing structural unit whole when size <= trigger; no merging or new hierarchy",
                    "observed_tradeoff": "Fixed windows cut reviewed provisions or combine neighboring provisions; uncapped units preserve source boundaries but have uneven sizes",
                    "evidence": {
                        "step11_metrics": [
                            r
                            for r in self.C_METRICS
                            if r["sample_id"]
                            in (
                                "normal_article",
                                "short_neighbors",
                                "transitional_provision",
                            )
                        ],
                        "structural_run": self.STRUCTURAL_ID,
                    },
                    "support": "Supported for exact preservation; legal boundary correctness remains provisional",
                },
                {
                    "id": "size_trigger",
                    "rule": "Lead trigger 4,000 characters; retain larger units as complete parents",
                    "observed_tradeoff": "2,000 triggers 120 units, 4,000 triggers 43, 8,000 triggers 11; 4,000 leaves 77 additional 2–4k units intact versus 2,000",
                    "evidence": {"step8_thresholds": self.OS_THRESHOLD_ROWS},
                    "support": "Provisional compromise, not a proven token/context budget",
                },
                {
                    "id": "controlled_children",
                    "rule": "Reuse Step 8 paragraph/whitespace-aware children at 2,000 characters",
                    "observed_tradeoff": "At trigger 4,000 and zero overlap: aware cuts 6 paragraphs versus 169 exact; aware makes 236 children versus 219 exact",
                    "evidence": {
                        "step8_rows": [
                            r
                            for r in self.OS_DIAGNOSTICS
                            if r["threshold"] == 4000
                            and r["setting"]
                            in (
                                "exact-chars-2000-overlap-0pct",
                                "boundary_aware-chars-2000-overlap-0pct",
                            )
                        ]
                    },
                    "support": "Supported mechanical paragraph preservation, with more/underfilled children; semantic focus untested",
                },
                {
                    "id": "overlap",
                    "rule": "Start at 0%; retain 10% requested overlap as sensitivity alternative",
                    "observed_tradeoff": "Aware 0% has 0 duplicate characters and 6 paragraph cuts; aware 10% has 13,543 duplicate characters and 7 cuts at trigger 4,000",
                    "evidence": {
                        "step8_rows": [
                            r
                            for r in self.OS_DIAGNOSTICS
                            if r["threshold"] == 4000
                            and r["setting"].startswith("boundary_aware-chars-2000")
                        ]
                    },
                    "support": "Provisional: avoids observed duplication; loses repeated local context whose retrieval value is unknown",
                },
                {
                    "id": "parent_policy",
                    "rule": "Link oversized children to the original complete structural unit, not an automatically widened Section/Chapter",
                    "observed_tradeoff": "Step 7 identical children can point to much larger parents with additional units; a complete parent can still be 45,829 characters",
                    "evidence": {
                        "same_child_parent_comparisons": self.IDENTICAL_CHILD_COMPARISONS
                    },
                    "support": "Supported containment/traceability; future parent inclusion needs an explicit context-budget policy",
                },
                {
                    "id": "uncertainty",
                    "rule": "Keep unclassified/residual spans and existing uncertainty explicit; oversized unknowns get source-container links only",
                    "observed_tradeoff": "Weak structure, publication preambles and unclassified headings do not establish legal ancestry",
                    "evidence": {
                        "samples": [
                            s
                            for s in self.BASELINE_SAMPLES
                            if s["sample_id"]
                            in (
                                "weak_structure",
                                "unclassified_heading",
                                "long_paragraph",
                                "publication_history",
                            )
                        ]
                    },
                    "support": "Supported conservative source accounting; tiny headings and large prose contexts remain counterexamples",
                },
                {
                    "id": "history_metadata",
                    "rule": "Keep all history verbatim; resolve separate annotations, raw document fields and provenance through existing registries",
                    "observed_tradeoff": "History can dominate chunks; attribution remains uncertain. Registry joins aid inspection without copying long notes or inventing effective dates",
                    "evidence": {
                        "history_shares": self.H_SAMPLE_SHARES,
                        "history_witnesses": self.H_WITNESSES,
                        "metadata_run": self.M_RUN_ID,
                    },
                    "support": "Supported source fidelity; metadata-only history removal and filtering effectiveness remain untested",
                },
            ]
            self.HY_SPEC = {
                "version": 1,
                "setup_id": self.SETUP_ID,
                "source_fingerprint": self.C_INPUT_FINGERPRINT,
                "structural_fingerprint": self.STRUCTURAL_RESULTS_FINGERPRINT,
                "step8_fingerprint": self.OS_DATA_FINGERPRINT,
                "independent_observations": self.C_INDEPENDENT_FINGERPRINT,
                "shortlist": self.HY_SHORTLIST,
                "rules_fingerprint": fingerprint(self.HY_RULES),
                "stage11_approved": self.HY_STEP11_APPROVED,
                "meaningful_provisional_kinds": [
                    "article",
                    "paragraph_sign",
                    "annex",
                    "part",
                    "chapter",
                    "section",
                ],
                "uncertain_kinds": ["unclassified", "residual"],
                "mentor_builder_input": False,
            }
            self.HY_RUN_ID = fingerprint(self.HY_SPEC)
            show_table(
                [
                    {k: r[k] for k in ("id", "rule", "observed_tradeoff", "support")}
                    for r in self.HY_RULES
                ]
            )
            show_table(self.HY_SHORTLIST)

    def step_12a_construct_the_hypothesis_from_existing_source_spans(self):
        """12a. Construct the hypothesis from existing source spans."""
        if self.HY_READY:

            def hybrid_action(size, threshold):
                return "retain_whole" if size <= threshold else "reuse_tested_children"

            self.hybrid_action = hybrid_action

            def build_hybrid(config):
                require(
                    config in self.HY_SHORTLIST,
                    "Only reviewed shortlist configurations are allowed.",
                )
                require(
                    fingerprint(self.STRUCTURAL_RESULTS)
                    == self.HY_SPEC["structural_fingerprint"]
                    and fingerprint(list(self.OS_GROUPS.values()))
                    == self.HY_SPEC["step8_fingerprint"],
                    "Structural or tested child evidence changed; rebuild/review before composing hybrid.",
                )
                parents, leaves, links, unit_rows = ({}, {}, {}, [])
                document_ordinals = Counter()
                for did in self.BASELINE_DOCUMENT_IDS:
                    for unit in self.STRUCTURAL_RESULTS[did]:
                        uid = unit["id"]
                        size = unit["end"] - unit["start"]
                        uncertain = unit["unit_kind"] in self.HY_SPEC["uncertain_kinds"]
                        common = {
                            "document_id": did,
                            "setup_id": self.SETUP_ID,
                            "configuration": config["id"],
                            "run_ref": self.HY_RUN_ID,
                            "document_registry_ref": did,
                            "structural_unit_id": uid,
                            "source_kind": unit["unit_kind"],
                            "source_boundary_evidence_ids": unit["evidence_ids"],
                            "source_uncertainty": unit["uncertainty"],
                            "ancestry_assertion": None,
                            "interpretation": "explicitly uncertain source span"
                            if uncertain
                            else "provisional structural role; legal meaning unverified",
                        }
                        action = self.hybrid_action(size, config["threshold"])
                        if action == "retain_whole":
                            pieces = [
                                {
                                    "start": unit["start"],
                                    "end": unit["end"],
                                    "split_reason": "preserved_original_unit_at_or_below_trigger",
                                }
                            ]
                            parent_id = None
                            tested_group_id = None
                        else:
                            tested = self.OS_GROUPS[uid, config["setting"]]
                            tested_group_id = tested["id"]
                            require(
                                config["threshold"] in tested["eligible_thresholds"],
                                "Step 8 did not test this trigger/parent pair.",
                            )
                            parent_id = "hybrid-parent:" + fingerprint(
                                [
                                    self.HY_RUN_ID,
                                    config["id"],
                                    uid,
                                    unit["start"],
                                    unit["end"],
                                ]
                            )
                            parents[parent_id] = {
                                **common,
                                "id": parent_id,
                                "ordinal": unit["ordinal"],
                                "start": unit["start"],
                                "end": unit["end"],
                                "text": self.VIEWS[did]["text"][
                                    unit["start"] : unit["end"]
                                ],
                                "source_spans": self.source_map(
                                    did, unit["start"], unit["end"]
                                ),
                                "block_ids": unit["block_ids"],
                                "record_kind": "uncertain source container"
                                if uncertain
                                else "complete provisional structural parent",
                                "parent_role": "uncertain source container"
                                if uncertain
                                else unit["unit_kind"],
                                "tested_group_ref": tested_group_id,
                            }
                            pieces = tested["children"]
                        child_ids = []
                        for order, piece in enumerate(pieces, 1):
                            a, b = (piece["start"], piece["end"])
                            cid = "hybrid-span:" + fingerprint(
                                [self.HY_RUN_ID, config["id"], uid, a, b]
                            )
                            document_ordinals[did] += 1
                            record = {
                                **common,
                                "id": cid,
                                "ordinal": document_ordinals[did],
                                "start": a,
                                "end": b,
                                "text": self.VIEWS[did]["text"][a:b],
                                "source_spans": self.source_map(did, a, b),
                                "record_kind": "hybrid child"
                                if parent_id
                                else "hybrid preserved unit",
                                "split_reason": piece["split_reason"],
                                "action": action,
                                "tested_child_ref": piece.get("id")
                                if parent_id
                                else None,
                                "actual_previous_overlap": max(
                                    0, pieces[order - 2]["end"] - a
                                )
                                if order > 1
                                else 0,
                                "actual_next_overlap": max(
                                    0, b - pieces[order]["start"]
                                )
                                if order < len(pieces)
                                else 0,
                            }
                            if parent_id:
                                record["parent_id"] = parent_id
                                rid = "hybrid-link:" + fingerprint(
                                    [
                                        self.HY_RUN_ID,
                                        config["id"],
                                        parent_id,
                                        cid,
                                        order,
                                    ]
                                )
                                record["relationship_id"] = rid
                                links[rid] = {
                                    "id": rid,
                                    "parent_id": parent_id,
                                    "child_id": cid,
                                    "order": order,
                                    "relationship_type": "contained_source_span",
                                    "tested_group_ref": tested_group_id,
                                }
                            leaves[cid] = record
                            child_ids.append(cid)
                        unit_rows.append(
                            {
                                "source_unit_id": uid,
                                "document_id": did,
                                "source_kind": unit["unit_kind"],
                                "original_size": size,
                                "action": action,
                                "parent_id": parent_id,
                                "output_ids": child_ids,
                                "uncertain_source_role": uncertain,
                                "tested_group_ref": tested_group_id,
                            }
                        )
                return {
                    "configuration": config,
                    "parents": parents,
                    "outputs": leaves,
                    "links": links,
                    "unit_decisions": unit_rows,
                }

            self.build_hybrid = build_hybrid
            self.HY_RESULTS = {
                config["id"]: self.build_hybrid(config) for config in self.HY_SHORTLIST
            }
            self.HY_RESULT_FINGERPRINT = fingerprint(self.HY_RESULTS)
            self.HY_LEAD_RESULT = self.HY_RESULTS[self.HY_LEAD]
            print(
                "Provisional lead composed:",
                len(self.HY_LEAD_RESULT["outputs"]),
                "candidate payload spans;",
                len(self.HY_LEAD_RESULT["parents"]),
                "complete parents retained.",
            )

    def step_12b_inspect_the_same_frozen_samples_before_aggregate_diagnostics(self):
        """12b. Inspect the same frozen samples before aggregate diagnostics."""
        if self.HY_READY:
            self.HY_CONTROL_CONFIGURATION = "chars-2000-overlap-0pct"
            self.HY_SAMPLE_VIEWS = {}
            self.HY_SAMPLE_METRICS = []
            for self.sample in self.BASELINE_SAMPLES:
                self.did, self.lo, self.hi = (
                    self.sample["document_id"],
                    self.sample["start"],
                    self.sample["end"],
                )
                self.intersects = lambda r: (
                    r["document_id"] == self.did
                    and intersection_length((self.lo, self.hi), (r["start"], r["end"]))
                    > 0
                )
                self.fixed = [
                    r
                    for r in self.FIXED_RESULTS[self.HY_CONTROL_CONFIGURATION][self.did]
                    if self.intersects(r)
                ]
                self.structural = [
                    r for r in self.STRUCTURAL_RESULTS[self.did] if self.intersects(r)
                ]
                self.pc_records = []
                self.pc_parents = []
                self.pc_groups = []
                for self.old_gid in self.C_SELECTIONS[self.sample["sample_id"]][
                    "parent_group_ids"
                ]:
                    self.old = self.PC_GROUPS[self.old_gid]
                    self.group = self.PC_GROUP_BY_KEY[
                        self.old["case"],
                        self.old["mode"],
                        self.HY_CONTROL_CONFIGURATION,
                    ]
                    self.parent, self.children = self.relationship_display_records(
                        self.group["id"]
                    )
                    self.pc_groups.append(self.group["id"])
                    self.pc_parents.append(self.parent)
                    self.pc_records.extend(
                        (c for c in self.children if self.intersects(c))
                    )
                self.hybrid = [
                    r
                    for r in self.HY_LEAD_RESULT["outputs"].values()
                    if self.intersects(r)
                ]
                self.parent_ids = list(
                    dict.fromkeys(
                        (r["parent_id"] for r in self.hybrid if "parent_id" in r)
                    )
                )
                self.hybrid_parents = [
                    self.HY_LEAD_RESULT["parents"][pid] for pid in self.parent_ids
                ]
                self.HY_SAMPLE_VIEWS[self.sample["sample_id"]] = {
                    "fixed": self.fixed,
                    "structural": self.structural,
                    "parent_child": self.pc_records,
                    "hybrid": self.hybrid,
                    "pc_group_ids": self.pc_groups,
                    "hybrid_parent_ids": self.parent_ids,
                }
                for self.strategy, self.records, self.parents in (
                    ("fixed", self.fixed, []),
                    ("structural", self.structural, []),
                    ("parent_child", self.pc_records, self.pc_parents),
                    ("hybrid", self.hybrid, self.hybrid_parents),
                ):
                    self.row = self.comparison_metrics(
                        self.sample, self.strategy, self.records, self.parents
                    )
                    self.row["metric_scope"] = (
                        "payload spans intersecting frozen sample; complete context parents excluded from overlap"
                    )
                    self.ratios = [
                        (p["end"] - p["start"]) / (r["end"] - r["start"])
                        for r in self.records
                        for p in self.parents
                        if r.get("parent_id") == p["id"]
                    ]
                    self.row["parent_expansion_ratios"] = length_summary(self.ratios)
                    self.HY_SAMPLE_METRICS.append(self.row)
                self.source = self.VIEWS[self.did]["text"][self.lo : self.hi]
                self.panels = []
                for self.strategy, self.records in (
                    ("fixed", self.fixed),
                    ("structural", self.structural),
                    ("parent_child", self.pc_records),
                    ("hybrid", self.hybrid),
                ):
                    self.body = "".join(
                        (
                            self.span_card(
                                r, self.sample, self.records, self.REVIEWED_PROVISIONS
                            )
                            for r in self.records
                        )
                    )
                    if self.strategy == "parent_child":
                        for self.gid in self.pc_groups:
                            self.parent, self.children = (
                                self.relationship_display_records(self.gid)
                            )
                            self.body += (
                                "<details><summary>Complete control parent and all children</summary>"
                                + self.relationship_html(
                                    self.parent,
                                    self.children,
                                    self.sample,
                                    self.REVIEWED_PROVISIONS,
                                )
                                + "</details>"
                            )
                    if self.strategy == "hybrid":
                        self.body += details_html(
                            "Hybrid decisions and uncertainty",
                            json.dumps(
                                [
                                    {
                                        k: r[k]
                                        for k in (
                                            "id",
                                            "structural_unit_id",
                                            "source_kind",
                                            "interpretation",
                                            "ancestry_assertion",
                                            "source_uncertainty",
                                            "action",
                                            "split_reason",
                                        )
                                    }
                                    for r in self.records
                                ],
                                ensure_ascii=False,
                                indent=2,
                            ),
                        )
                        for self.parent in self.hybrid_parents:
                            self.children = [
                                r
                                for r in self.HY_LEAD_RESULT["outputs"].values()
                                if r.get("parent_id") == self.parent["id"]
                            ]
                            self.body += (
                                "<details><summary>Complete hybrid parent and all children — no truncation</summary>"
                                + self.relationship_html(
                                    self.parent,
                                    self.children,
                                    self.sample,
                                    self.REVIEWED_PROVISIONS,
                                )
                                + "</details>"
                            )
                    self.panels.append(
                        "<section><h4>"
                        + esc(self.strategy)
                        + "</h4>"
                        + self.body
                        + "</section>"
                    )
                display(
                    HTML(
                        "<details><summary>"
                        + esc(self.sample["sample_id"])
                        + " — hybrid and matched existing controls</summary>"
                        + "<h4>Same frozen source span</h4>"
                        + highlight_html(self.source, self.lo)
                        + "<div style='display:grid;grid-template-columns:repeat(4,minmax(320px,1fr));gap:12px;overflow-x:auto'>"
                        + "".join(self.panels)
                        + "</div></details>"
                    )
                )
            show_table(
                [
                    {
                        k: v
                        for k, v in r.items()
                        if k not in ("source_evidence", "reviewed_legal_units_cut")
                    }
                    for r in self.HY_SAMPLE_METRICS
                ]
            )

    def step_12c_improvements_regressions_and_the_shortlist_s_measured_costs(self):
        """12c. Improvements, regressions and the shortlist's measured costs."""
        if self.HY_READY:
            self.HY_DELTAS = []
            for self.sample in self.BASELINE_SAMPLES:
                self.rows = {
                    r["strategy"]: r
                    for r in self.HY_SAMPLE_METRICS
                    if r["sample_id"] == self.sample["sample_id"]
                }
                self.hy = self.rows["hybrid"]
                for self.name in ("fixed", "structural", "parent_child"):
                    self.base = self.rows[self.name]
                    self.HY_DELTAS.append(
                        {
                            "sample_id": self.sample["sample_id"],
                            "baseline": self.name,
                            "paragraphs_cut_delta": self.hy["paragraph_blocks_cut"]
                            - self.base["paragraph_blocks_cut"],
                            "reviewed_units_cut_delta": len(
                                self.hy["reviewed_legal_units_cut"]
                            )
                            - len(self.base["reviewed_legal_units_cut"]),
                            "records_combining_reviewed_units_delta": self.hy[
                                "records_combining_reviewed_units"
                            ]
                            - self.base["records_combining_reviewed_units"],
                            "overlap_duplicate_characters_delta": self.hy[
                                "overlap_duplicate_characters"
                            ]
                            - self.base["overlap_duplicate_characters"],
                            "payload_count_delta": self.hy["records"]
                            - self.base["records"],
                            "max_payload_size_delta": self.hy["size_distribution"][
                                "max"
                            ]
                            - self.base["size_distribution"]["max"],
                            "extra_source_characters_delta": self.hy[
                                "extra_characters_outside_sample"
                            ]
                            - self.base["extra_characters_outside_sample"],
                            "evidence": {
                                "hybrid": self.hy["source_evidence"],
                                "baseline": self.base["source_evidence"],
                            },
                        }
                    )
            show_table(
                [
                    {k: v for k, v in r.items() if k != "evidence"}
                    for r in self.HY_DELTAS
                ]
            )
            self.HY_AGGREGATES = []
            self.HY_SENSITIVITY_SAMPLES = []
            for self.config in self.HY_SHORTLIST:
                self.result = self.HY_RESULTS[self.config["id"]]
                self.records = list(self.result["outputs"].values())
                self.sizes = [len(r["text"]) for r in self.records]
                self.parents = list(self.result["parents"].values())
                self.total = sum(
                    (len(self.VIEWS[did]["text"]) for did in self.BASELINE_DOCUMENT_IDS)
                )
                self.cut_paragraphs = {
                    bid for r in self.records for bid in self.paragraph_cuts(r)
                }
                self.ratios = [
                    len(parents_record["text"]) / len(r["text"])
                    for r in self.records
                    if "parent_id" in r
                    for parents_record in [self.result["parents"][r["parent_id"]]]
                ]
                self.HY_AGGREGATES.append(
                    {
                        "configuration": self.config["id"],
                        "role": self.config["role"],
                        "source_characters": self.total,
                        "original_structural_units": len(self.OS_CONTROL),
                        "retained_whole_units": sum(
                            (
                                d["action"] == "retain_whole"
                                for d in self.result["unit_decisions"]
                            )
                        ),
                        "oversized_parents": len(self.parents),
                        "uncertain_source_containers": sum(
                            (
                                p["source_kind"] in self.HY_SPEC["uncertain_kinds"]
                                for p in self.parents
                            )
                        ),
                        "children": len(self.result["links"]),
                        "candidate_payload_count": len(self.records),
                        "payload_sizes": length_summary(self.sizes),
                        "payloads_above_2000": sum((s > 2000 for s in self.sizes)),
                        "payloads_below_100": sum((s < 100 for s in self.sizes)),
                        "paragraph_blocks_cut": len(self.cut_paragraphs),
                        "duplicate_peer_characters": sum(self.sizes) - self.total,
                        "complete_parent_sizes": length_summary(
                            [len(p["text"]) for p in self.parents]
                        ),
                        "parent_expansion": length_summary(self.ratios),
                        "uncertain_output_spans": sum(
                            (
                                r["source_kind"] in self.HY_SPEC["uncertain_kinds"]
                                for r in self.records
                            )
                        ),
                    }
                )
                for self.sample in self.BASELINE_SAMPLES:
                    self.relevant = [
                        r
                        for r in self.records
                        if r["document_id"] == self.sample["document_id"]
                        and intersection_length(
                            (r["start"], r["end"]),
                            (self.sample["start"], self.sample["end"]),
                        )
                    ]
                    self.metrics = self.comparison_metrics(
                        self.sample, "hybrid", self.relevant
                    )
                    self.HY_SENSITIVITY_SAMPLES.append(
                        {"configuration": self.config["id"], **self.metrics}
                    )
            show_table(self.HY_AGGREGATES)
            display(
                HTML(
                    "<details><summary>All three shortlist configurations on all frozen samples</summary>"
                    + table_html(
                        [
                            {k: v for k, v in r.items() if k != "source_evidence"}
                            for r in self.HY_SENSITIVITY_SAMPLES
                        ]
                    )
                    + "</details>"
                )
            )
            self.HY_TRADEOFFS = [
                {
                    "observation": "Fewer avoidable paragraph cuts in oversized units",
                    "rating": "PASS",
                    "limit": "Mechanical evidence only; children still split long provisions",
                    "evidence_rule": "controlled_children",
                },
                {
                    "observation": "Whole small Articles/§ units preserved instead of forced child splitting",
                    "rating": "PASS",
                    "limit": "Whole units can reach 4,000 characters, above the 2,000-character child target",
                    "evidence_rule": "retain_units",
                },
                {
                    "observation": "Versus uncapped structural units, long rules are now fragmented in the candidate payload layer",
                    "rating": "CONCERN",
                    "limit": "Complete parents remain available, but later expansion must be deliberately budgeted",
                    "evidence_rule": "parent_policy",
                },
                {
                    "observation": "Tiny headings/residual units remain; no automatic merging solves weak structure",
                    "rating": "CONCERN",
                    "limit": "Uncertain spans remain traceable; usefulness as future search targets untested",
                    "evidence_rule": "uncertainty",
                },
                {
                    "observation": "Zero-overlap lead avoids duplication but may lose useful adjacent context",
                    "rating": "UNCERTAIN",
                    "limit": "10% sensitivity retains variable actual overlap; retrieval tests must decide",
                    "evidence_rule": "overlap",
                },
                {
                    "observation": "Parent context remains as large as the source requires",
                    "rating": "CONCERN",
                    "limit": "45,829-character residual context and 18,756-character Article are not assumed to fit a model budget",
                    "evidence_rule": "parent_policy",
                },
                {
                    "observation": "History remains intact and separately inspectable",
                    "rating": "PASS",
                    "limit": "History share/metadata usefulness does not establish retrieval quality or effective dates",
                    "evidence_rule": "history_metadata",
                },
            ]
            show_table(self.HY_TRADEOFFS)

    def step_12d_validate_the_composition_and_preservation_contract(self):
        """12d. Validate the composition and preservation contract."""
        if self.HY_READY:

            def ensure_hybrid_current():
                require(
                    self.HY_READY and self.HY_STEP11_APPROVED,
                    "hybrid hypothesis pending review",
                )
                require(
                    fingerprint(self.HY_SPEC) == self.HY_RUN_ID
                    and self.HY_SPEC["shortlist"] == self.HY_SHORTLIST
                    and (
                        fingerprint(self.HY_RULES) == self.HY_SPEC["rules_fingerprint"]
                    ),
                    "Hybrid rules/settings changed; rebuild Step 12.",
                )
                require(
                    fingerprint(self.HY_RESULTS) == self.HY_RESULT_FINGERPRINT,
                    "Hybrid results changed; rebuild comparisons.",
                )
                require(
                    fingerprint(self.C_INDEPENDENT)
                    == self.HY_SPEC["independent_observations"]
                    and self.comparison_input_fingerprint()
                    == self.HY_SPEC["source_fingerprint"],
                    "Approved source/evidence changed; review and rebuild the hybrid.",
                )
                require(
                    [s["sample_id"] for s in self.BASELINE_SAMPLES]
                    == self.C_SPEC["samples"]
                    and fingerprint(self.frozen_samples())
                    == fingerprint(self.BASELINE_SAMPLES),
                    "Frozen sample selection changed; rebuild Stage 2 comparisons.",
                )

            self.ensure_hybrid_current = ensure_hybrid_current
            self.HY_VALIDATION_COUNTS = []
            for self.config in self.HY_SHORTLIST:
                self.result = self.HY_RESULTS[self.config["id"]]
                self.parents = self.result["parents"]
                self.records = self.result["outputs"]
                require(
                    len(self.records) == len(set(self.records))
                    and len(self.result["links"]) == len(set(self.result["links"])),
                    "Duplicate hybrid identity.",
                )
                for self.decision in self.result["unit_decisions"]:
                    self.unit = self.STRUCTURAL_BY_ID[self.decision["source_unit_id"]]
                    self.outputs = [
                        self.records[cid] for cid in self.decision["output_ids"]
                    ]
                    require(
                        self.decision["action"]
                        == self.hybrid_action(
                            len(self.unit["text"]), self.config["threshold"]
                        ),
                        "Incorrect size branch.",
                    )
                    if self.decision["action"] == "retain_whole":
                        require(
                            len(self.outputs) == 1
                            and self.outputs[0]["text"] == self.unit["text"]
                            and ("parent_id" not in self.outputs[0]),
                            "Preserved unit changed or got an invented parent.",
                        )
                    else:
                        self.parent = self.parents[self.decision["parent_id"]]
                        self.tested = self.OS_GROUPS[
                            self.unit["id"], self.config["setting"]
                        ]
                        require(
                            self.parent["text"] == self.unit["text"]
                            and self.parent["source_spans"]
                            == self.source_map(
                                self.unit["document_id"],
                                self.unit["start"],
                                self.unit["end"],
                            ),
                            "Complete parent changed.",
                        )
                        require(
                            "parent_id" not in self.parent
                            and self.parent["id"] not in self.records,
                            "Cycle or parent included as candidate payload.",
                        )
                        require(
                            self.parent["id"]
                            == "hybrid-parent:"
                            + fingerprint(
                                [
                                    self.HY_RUN_ID,
                                    self.config["id"],
                                    self.unit["id"],
                                    self.unit["start"],
                                    self.unit["end"],
                                ]
                            ),
                            "Parent ID changed.",
                        )
                        require(
                            [(c["start"], c["end"], c["text"]) for c in self.outputs]
                            == [
                                (c["start"], c["end"], c["text"])
                                for c in self.tested["children"]
                            ],
                            "New child splitter or modified spans introduced.",
                        )
                        self.relative = [
                            {
                                "start": c["start"] - self.parent["start"],
                                "end": c["end"] - self.parent["start"],
                                "text": c["text"],
                            }
                            for c in self.outputs
                        ]
                        check_os_windows(
                            self.parent["text"],
                            self.relative,
                            self.tested["setting"]["target"],
                            self.tested["setting"]["overlap"],
                        )
                        if self.unit["unit_kind"] in self.HY_SPEC["uncertain_kinds"]:
                            require(
                                self.parent["parent_role"]
                                == "uncertain source container"
                                and self.parent["ancestry_assertion"] is None,
                                "Invented ancestry for uncertain content.",
                            )
                        for self.order, self.child in enumerate(self.outputs, 1):
                            self.link = self.result["links"][
                                self.child["relationship_id"]
                            ]
                            require(
                                self.link["parent_id"] == self.parent["id"]
                                and self.link["child_id"] == self.child["id"]
                                and (self.link["order"] == self.order),
                                "Broken link/order.",
                            )
                            require(
                                self.link["id"]
                                == "hybrid-link:"
                                + fingerprint(
                                    [
                                        self.HY_RUN_ID,
                                        self.config["id"],
                                        self.parent["id"],
                                        self.child["id"],
                                        self.order,
                                    ]
                                ),
                                "Link ID changed.",
                            )
                            require(
                                self.parent["document_id"] == self.child["document_id"]
                                and self.parent["start"]
                                <= self.child["start"]
                                < self.child["end"]
                                <= self.parent["end"],
                                "Child escaped its parent.",
                            )
                    for self.child in self.outputs:
                        require(
                            self.child["text"]
                            == self.reconstruct(self.child["source_spans"])
                            == self.VIEWS[self.child["document_id"]]["text"][
                                self.child["start"] : self.child["end"]
                            ],
                            "Source reconstruction failed.",
                        )
                        require(
                            self.child["id"]
                            == "hybrid-span:"
                            + fingerprint(
                                [
                                    self.HY_RUN_ID,
                                    self.config["id"],
                                    self.unit["id"],
                                    self.child["start"],
                                    self.child["end"],
                                ]
                            ),
                            "Output identity changed.",
                        )
                        require(
                            self.child["document_registry_ref"] in self.M_REGISTRY
                            and self.child["source_kind"] == self.unit["unit_kind"]
                            and (
                                self.child["source_boundary_evidence_ids"]
                                == self.unit["evidence_ids"]
                            )
                            and (
                                self.child["source_uncertainty"]
                                == self.unit["uncertainty"]
                            ),
                            "Provenance/uncertainty lost.",
                        )
                for self.did in self.BASELINE_DOCUMENT_IDS:
                    self.ordered = sorted(
                        (
                            r
                            for r in self.records.values()
                            if r["document_id"] == self.did
                        ),
                        key=lambda r: (r["start"], r["end"]),
                    )
                    self.end = 0
                    self.restored = []
                    for self.r in self.ordered:
                        require(
                            self.r["start"] <= self.end < self.r["end"],
                            "Gap or redundant candidate payload.",
                        )
                        require(
                            self.r["actual_previous_overlap"]
                            == self.end - self.r["start"],
                            "Measured peer overlap mismatch.",
                        )
                        self.restored.append(
                            self.r["text"][self.end - self.r["start"] :]
                        )
                        self.end = self.r["end"]
                    require(
                        self.end == len(self.VIEWS[self.did]["text"])
                        and "".join(self.restored) == self.VIEWS[self.did]["text"],
                        "Whole document does not reconstruct exactly.",
                    )
                require(
                    fingerprint(self.build_hybrid(self.config))
                    == fingerprint(self.result),
                    "Hybrid IDs/results are not reproducible.",
                )
                self.HY_VALIDATION_COUNTS.append(
                    {
                        "configuration": self.config["id"],
                        "outputs_checked": len(self.records),
                        "parents_checked": len(self.parents),
                        "relationships_checked": len(self.result["links"]),
                        "coverage": "100% exact document reconstruction",
                    }
                )
            require(
                all(
                    (
                        r["sample_coverage_pct"] == 100
                        for r in self.HY_SAMPLE_METRICS + self.HY_SENSITIVITY_SAMPLES
                    )
                ),
                "A frozen sample is not fully covered.",
            )
            require(
                not hybrid_review_ready(
                    False,
                    self.C_INDEPENDENT,
                    self.OS_DIAGNOSTICS,
                    self.C_FINAL_EVIDENCE,
                )
                and (
                    not hybrid_review_ready(
                        True, {}, self.OS_DIAGNOSTICS, self.C_FINAL_EVIDENCE
                    )
                ),
                "Observation/approval gate failed.",
            )
            require(
                self.hybrid_action(0, 4000) == "retain_whole"
                and self.hybrid_action(4000, 4000) == "retain_whole"
                and (self.hybrid_action(4001, 4000) == "reuse_tested_children"),
                "Threshold edge case changed.",
            )
            expect_value_error(
                lambda: self.build_hybrid(
                    {"text": "mentor reference", "threshold": 4000}
                ),
                "Only reviewed shortlist configurations",
            )
            self.old_threshold = self.HY_SHORTLIST[0]["threshold"]
            try:
                self.HY_SHORTLIST[0]["threshold"] = 3999
                expect_value_error(
                    self.ensure_hybrid_current, "Hybrid rules/settings changed"
                )
            finally:
                self.HY_SHORTLIST[0]["threshold"] = self.old_threshold
            require(
                all(
                    (
                        hashlib.sha256((self.ROOT / p).read_bytes()).hexdigest()
                        == digest
                        for p, digest in self.HY_PRIOR_HASHES.items()
                    )
                ),
                "An original artifact/report/archive changed.",
            )
            require(
                verify_implementation(self.ROOT) == self.HY_APPROVED_CODE_HASHES,
                "Earlier refactored implementation changed.",
            )
            require(
                hashlib.sha256(self.ARTIFACT.read_bytes()).hexdigest()
                == self.artifact_sha256
                and self.corpus["source"]["sha256"] == self.M_RUN["source"]["sha256"],
                "Source fingerprints differ.",
            )
            self.ensure_hybrid_current()
            show_table(self.HY_VALIDATION_COUNTS)
            print(
                "PASS: exact source coverage, contained complete parents, tested child spans, stable IDs, provenance, uncertainty, unchanged prior artifacts/code, and review gate."
            )

    def step_12e_what_is_supported_provisional_and_unresolved(self):
        """12e. What is supported, provisional and unresolved?."""
        if self.HY_READY:
            self.ensure_hybrid_current()
            self.HY_DECISION = {
                "status": "provisional shortlist for later embedding/retrieval experiments; not production-optimal",
                "lead": self.HY_SHORTLIST[0],
                "sensitivity_alternatives": self.HY_SHORTLIST[1:],
                "structural_policy": "Keep original provisional units whole at/below trigger; no new boundaries, merging or ancestry",
                "parent_policy": "Retain original oversized source unit; explicit parent lookup, no automatic whole-parent LLM insertion or Chapter widening",
                "metadata_provenance": "Existing Stage 10 document/run registries plus source-unit, span, parent/link references; raw dates, never effective-date inference",
                "ambiguous_spans": "Retain residual/unclassified labels and warnings; oversized unknown spans remain uncertain source containers",
                "history": "Unchanged original text plus separate Stage 9 candidate annotations; no removal or metadata-only policy",
                "supported_decisions": [
                    "Exact source reconstruction and containment",
                    "Reuse of already-tested boundaries/child spans",
                    "Fewer avoidable paragraph cuts with aware splitting",
                    "Explicit uncertainty and provenance preservation",
                ],
                "provisional_choices": [
                    "4,000-character trigger",
                    "2,000-character child target",
                    "0% lead overlap",
                    "Source-unit parent rather than widened Chapter",
                ],
                "unresolved_tests": [
                    "Actual Bulgarian tokenizer sizes and model context limits",
                    "Held-out legal questions requiring conditions, exceptions and cross-references",
                    "Lead versus overlap/threshold sensitivity and strict fixed/uncapped structural controls",
                    "Child-only versus budgeted parent context, including long Article/residual counterexamples",
                    "Unclassified headings, weak structure and residual/navigation target usefulness",
                    "History scope attribution and qualitative-noise hypotheses",
                    "Metadata filtering semantics, raw version dates and citation completeness",
                    "All-21-document generalization beyond the four-document experiment population",
                ],
                "next_stage_not_implemented": [
                    "embeddings",
                    "vector storage",
                    "retrieval",
                    "reranking",
                    "RAG",
                    "LLM calls",
                    "agents",
                ],
            }
            show_json("Stage 2 provisional decision", self.HY_DECISION)
            self.HY_REPORT = {
                "report_version": 1,
                "scope": "Step 12 only — provisional hybrid, conclusions and Stage 2 review",
                "run_id": self.HY_RUN_ID,
                "spec": self.HY_SPEC,
                "rule_ledger": self.HY_RULES,
                "result_fingerprint": self.HY_RESULT_FINGERPRINT,
                "results": {
                    config_id: {
                        **{
                            k: v
                            for k, v in result.items()
                            if k not in ("parents", "outputs")
                        },
                        "parents": {
                            pid: {k: v for k, v in p.items() if k != "text"}
                            for pid, p in result["parents"].items()
                        },
                        "outputs": {
                            cid: {k: v for k, v in c.items() if k != "text"}
                            for cid, c in result["outputs"].items()
                        },
                    }
                    for config_id, result in self.HY_RESULTS.items()
                },
                "sample_metrics": self.HY_SAMPLE_METRICS,
                "baseline_deltas": self.HY_DELTAS,
                "shortlist_aggregates": self.HY_AGGREGATES,
                "sensitivity_samples": self.HY_SENSITIVITY_SAMPLES,
                "tradeoffs": self.HY_TRADEOFFS,
                "decision": self.HY_DECISION,
                "provenance": {
                    "artifact_sha256": self.artifact_sha256,
                    "docx_sha256": self.corpus["source"]["sha256"],
                    "registry_ref": self.M_RUN_ID,
                    "unchanged_prior_artifacts": self.HY_PRIOR_HASHES,
                    "unchanged_prior_code": self.HY_APPROVED_CODE_HASHES,
                },
                "validation": {
                    "status": "PASS",
                    "configurations": self.HY_VALIDATION_COUNTS,
                    "legal_validation": False,
                },
            }
            self.hybrid_report_path = (
                self.OUTPUT_DIR
                / f"hybrid_experiment_report.{fingerprint(self.HY_REPORT)}.json"
            )
            self.hybrid_bytes = (canonical(self.HY_REPORT) + "\n").encode("utf-8")
            if self.hybrid_report_path.exists():
                require(
                    self.hybrid_report_path.read_bytes() == self.hybrid_bytes,
                    "Existing hybrid report differs.",
                )
            else:
                self.hybrid_report_path.write_bytes(self.hybrid_bytes)
            require(
                json.loads(self.hybrid_report_path.read_text(encoding="utf-8"))
                == self.HY_REPORT,
                "Hybrid report round trip failed.",
            )
            self.lead = self.HY_AGGREGATES[0]
            self.HY_SUMMARY = f"# Stage 2 — provisional decision for review\n\n    Carry forward the source-preserving hybrid as a **hypothesis for embedding/retrieval evaluation**, not a production-optimal strategy.\n\n    - **Units:** preserve existing provisional structural units through 4,000 Unicode characters. Retain larger units as complete parents.\n    - **Children:** reuse Step 8 paragraph/whitespace-aware splitting at 2,000 characters, initially 0% overlap. No new splitter.\n    - **Sensitivity shortlist:** 4,000 / 2,000 / 10% requested overlap; 2,000 / 2,000 / 0% overlap.\n    - **Parents:** original oversized unit only; no automatic Chapter expansion or assumption the complete parent fits an LLM budget.\n    - **Uncertainty:** keep residual/unclassified spans and warnings; oversized unknowns remain source containers with no asserted legal ancestry.\n    - **Metadata/history:** existing document/run registries, exact source maps and explicit links; dates and history remain verbatim, with history annotations separate.\n\n    Why carry it forward: at the 4,000 trigger and 2,000/0% setting, aware splitting cuts 6 source paragraphs versus 169 with exact windows, with full coverage in both. It produces 236 children rather than 219: paragraph preservation costs more, sometimes underfilled, spans. Whole shorter units avoid unnecessary provision splitting. These are mechanical observations, not retrieval findings.\n\n    The lead retains {self.lead['retained_whole_units']} units whole and {self.lead['oversized_parents']} complete parents, including {self.lead['uncertain_source_containers']} uncertain source containers. Its {self.lead['children']} children plus kept units make {self.lead['candidate_payload_count']} payload spans covering {self.lead['source_characters']:,} source characters across four complete documents. Peer overlap duplication is {self.lead['duplicate_peer_characters']} characters. All 12 frozen samples are covered.\n\n    Regressions and limits: long rules are fragmented in the payload layer versus uncapped structural units; {self.lead['payloads_above_2000']} intact payloads still exceed 2,000 characters and {self.lead['payloads_below_100']} are shorter than 100. Complete parents can reach {self.lead['complete_parent_sizes']['max']:,} characters. Tiny headings, weak structure and uncertain boundaries remain. Zero overlap may lose useful local context. History may dominate some spans, but its retrieval effect is untested.\n\n    Next evaluation must test actual Bulgarian token budgets; conditions, exceptions and cross-references; overlap/threshold sensitivities; budgeted parent expansion; ambiguous-content targets; history scope and metadata filters. Generalization beyond the four experimental documents is unresolved. The mentor material remains a qualitative reference, not exhaustive ground truth or a corpus-building input.\n\n    Validation: exact source reconstruction, coverage, containment, deterministic IDs, provenance, and unchanged earlier artifacts/code. A restart reproducibility check accompanies the executed notebook. Legal correctness is not established by these checks.\n\n    **Stopped after Step 12 for review. No embeddings, vector storage, retrieval, reranking, RAG, LLM calls or agents implemented.**\n    "
            self.hybrid_summary_path = (
                self.OUTPUT_DIR / f"stage2_decision_summary.{self.HY_RUN_ID}.md"
            )
            if self.hybrid_summary_path.exists():
                require(
                    self.hybrid_summary_path.read_text(encoding="utf-8")
                    == self.HY_SUMMARY,
                    "Existing decision summary differs.",
                )
            else:
                self.hybrid_summary_path.write_text(self.HY_SUMMARY, encoding="utf-8")
            display(
                HTML(details_html("Concise Stage 2 decision summary", self.HY_SUMMARY))
            )
            print("Hybrid report:", self.hybrid_report_path.relative_to(self.ROOT))
            print(
                "Stage 2 decision summary:",
                self.hybrid_summary_path.relative_to(self.ROOT),
            )
            print(
                "STOP AFTER STEP 12 — provisional hybrid and Stage 2 conclusions ready for review; no next-stage implementation."
            )
