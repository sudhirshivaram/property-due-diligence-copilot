"""Chunking: oversized."""

from pathlib import Path
from collections import Counter
import hashlib
import json
from property_copilot._display import HTML, display
from .primitives import (
    aware_windows,
    canonical,
    check_os_windows,
    esc,
    expect_value_error,
    fingerprint,
    fixed_length_windows,
    highlight_html,
    intersection_length,
    length_summary,
    oversized_eligible,
    require,
    show_table,
    table_html,
)


class OversizedSteps:
    """Oversized steps; state belongs to the workflow instance."""

    def step_8_oversized_unit_experiments_stop_here_for_review(self):
        """Step 8 — Oversized-unit experiments (stop here for review)."""
        self.ensure_pc_current()
        self.OS_APPROVED_BYTES = {
            str(p): p.read_bytes()
            for p in (
                self.APPROVED_MANIFEST_PATH,
                self.report_path,
                self.structural_report_path,
                self.pc_report_path,
            )
        }
        self.OS_APPROVED_FINGERPRINTS = (
            fingerprint(self.STRUCTURAL_RESULTS),
            fingerprint(self.FIXED_RESULTS),
            fingerprint(self.PC_DATA),
        )
        self.OS_THRESHOLDS = [2000, 4000, 8000]
        self.OS_SETTINGS = [
            {
                "id": f"{method}-chars-{target}-overlap-{pct}pct",
                "method": method,
                "target": target,
                "overlap_percent": pct,
                "overlap": target * pct // 100,
            }
            for method in ("exact", "boundary_aware")
            for target in (1000, 2000)
            for pct in (0, 10)
        ]
        self.OS_SPEC = {
            "version": 1,
            "scope": "Step 8 controlled experiments only",
            "setup_id": self.SETUP_ID,
            "structural_id": self.STRUCTURAL_ID,
            "structural_result": self.STRUCTURAL_RESULTS_FINGERPRINT,
            "artifact_sha256": self.artifact_sha256,
            "thresholds": self.OS_THRESHOLDS,
            "settings": self.OS_SETTINGS,
            "eligibility": "parent characters strictly greater than threshold",
            "paragraphs": "source block spans; added separator attached to preceding block",
            "boundary_algorithm": "farthest paragraph end, else whitespace, else exact; overlap at safe boundaries within requested budget",
            "final_policy": None,
        }
        self.OS_RUN_ID = fingerprint(self.OS_SPEC)
        self.OS_CONTROL = [
            u
            for did in self.BASELINE_DOCUMENT_IDS
            for u in self.STRUCTURAL_RESULTS[did]
        ]
        self.OS_THRESHOLD_ROWS = []
        for self.threshold in self.OS_THRESHOLDS:
            self.affected = [
                u for u in self.OS_CONTROL if u["end"] - u["start"] > self.threshold
            ]
            self.OS_THRESHOLD_ROWS.append(
                {
                    "trigger": self.threshold,
                    "control_units": len(self.OS_CONTROL),
                    "affected_units": len(self.affected),
                    "affected_pct": round(
                        100 * len(self.affected) / len(self.OS_CONTROL), 2
                    ),
                    "unchanged_control_units": len(self.OS_CONTROL)
                    - len(self.affected),
                    "affected_types": dict(
                        sorted(Counter((u["unit_kind"] for u in self.affected)).items())
                    ),
                    "affected_parent_sizes": length_summary(
                        [u["end"] - u["start"] for u in self.affected]
                    ),
                }
            )
        print(
            "Uncapped Step 6 control:",
            len(self.OS_CONTROL),
            "units across",
            len(self.BASELINE_DOCUMENT_IDS),
            "complete documents",
        )
        show_table(
            [
                {
                    "unit_kind": kind,
                    **length_summary(
                        [
                            u["end"] - u["start"]
                            for u in self.OS_CONTROL
                            if u["unit_kind"] == kind
                        ]
                    ),
                }
                for kind in sorted({u["unit_kind"] for u in self.OS_CONTROL})
            ]
        )
        show_table(self.OS_THRESHOLD_ROWS)
        show_table(self.OS_SETTINGS)

    def parent_paragraph_spans(self, parent):
        lo, hi = (parent["start"], parent["end"])
        segments = self.VIEWS[parent["document_id"]]["segments"]
        spans = []
        for i, segment in enumerate(segments):
            if segment["kind"] != "source":
                continue
            end = segment["end"]
            if i + 1 < len(segments) and segments[i + 1]["kind"] == "separator":
                end = segments[i + 1]["end"]
            a, b = (max(lo, segment["start"]), min(hi, end))
            if a < b:
                spans.append((a - lo, b - lo))
        return spans

    def os_windows(self, parent, setting):
        text = self.VIEWS[parent["document_id"]]["text"][
            parent["start"] : parent["end"]
        ]
        if setting["method"] == "exact":
            return [
                {
                    **w,
                    "end_reason": "parent_end"
                    if w["end"] == len(text)
                    else "exact_fixed_window",
                    "next_start_reason": "exact_requested_overlap",
                }
                for w in fixed_length_windows(
                    text, setting["target"], setting["overlap"]
                )
            ]
        require(setting["method"] == "boundary_aware", "Unknown splitting method.")
        return aware_windows(
            text,
            self.parent_paragraph_spans(parent),
            setting["target"],
            setting["overlap"],
        )

    def step_8a_boundary_aware_mechanics_and_their_costs(self):
        """8a. Boundary-aware mechanics and their costs."""
        self.OS_SYNTHETIC_CASES = [
            ([], 8),
            (["Чл. 2а. (изм.)", "§ 1. Изключение.", ""], 10),
            (["а" * 73], 10),
            (["   " * 14, "край"], 10),
            (["а б в г д е ж з и к л м н о п", "Чл. 3."], 10),
            (["1234567890"], 10),
            (["аб", "вг", "де", "жз", "и"], 10),
        ]
        for self.paragraphs, self.target in self.OS_SYNTHETIC_CASES:
            self.text, self.spans, self.cursor = ("\n".join(self.paragraphs), [], 0)
            for self.i, self.paragraph in enumerate(self.paragraphs):
                self.end = (
                    self.cursor
                    + len(self.paragraph)
                    + (self.i < len(self.paragraphs) - 1)
                )
                if self.end > self.cursor:
                    self.spans.append((self.cursor, self.end))
                self.cursor = self.end
            for self.overlap in (0, max(1, self.target // 10), self.target - 1):
                self.windows = aware_windows(
                    self.text, self.spans, self.target, self.overlap
                )
                check_os_windows(self.text, self.windows, self.target, self.overlap)
                require(
                    self.windows
                    == aware_windows(self.text, self.spans, self.target, self.overlap),
                    "Nondeterministic synthetic splitter.",
                )
        require(
            not oversized_eligible(2000, 2000) and oversized_eligible(2001, 2000),
            "Threshold equality changed.",
        )
        require(
            any(
                (
                    w["end_reason"] == "exact_no_available_boundary"
                    for w in aware_windows("я" * 25, [(0, 25)], 10, 1)
                )
            ),
            "Unbroken-text exact fallback is not exercised.",
        )
        self.whole = aware_windows("абвг\nдежз\nий", [(0, 5), (5, 10), (10, 12)], 8, 0)
        require(
            [(w["start"], w["end"]) for w in self.whole] == [(0, 5), (5, 12)],
            "Short paragraphs were needlessly split.",
        )
        self.whitespace_case = aware_windows("абвг дежз ийкл", [(0, 13)], 8, 0)
        require(
            self.whitespace_case[0]["end"] == 5
            and self.whitespace_case[0]["end_reason"] == "whitespace_inside_paragraph",
            "Oversized paragraph did not prefer available whitespace.",
        )
        print(
            "PASS: synthetic coverage, exact reconstruction, strict progress, equality, Unicode and unbroken-text fallback."
        )

    def ensure_os_current(self):
        self.ensure_pc_current()
        require(
            fingerprint(self.OS_SPEC) == self.OS_RUN_ID
            and self.OS_SPEC["thresholds"] == self.OS_THRESHOLDS
            and (self.OS_SPEC["settings"] == self.OS_SETTINGS),
            "Step 8 settings changed; rerun generation and diagnostics.",
        )
        require(
            fingerprint(self.STRUCTURAL_RESULTS) == self.OS_SPEC["structural_result"],
            "Structural input changed; rebuild Step 8.",
        )
        require(
            fingerprint(list(self.OS_GROUPS.values())) == self.OS_DATA_FINGERPRINT,
            "Step 8 child results changed; rebuild diagnostics.",
        )

    def os_group_metrics(self, group):
        children = group["children"]
        parent = self.OS_PARENTS[group["parent_id"]]
        size = parent["end"] - parent["start"]
        return {
            "parent_id": parent["id"],
            "unit_kind": parent["unit_kind"],
            "parent_characters": size,
            "setting": group["setting"]["id"],
            "eligible_thresholds": group["eligible_thresholds"],
            "children": len(children),
            "child_sizes": length_summary([len(c["text"]) for c in children]),
            "actual_overlap": length_summary(
                [c["actual_previous_overlap"] for c in children[1:]]
            ),
            "duplicated_characters": sum((len(c["text"]) for c in children)) - size,
            "paragraph_blocks_cut": len(
                {bid for c in children for bid in c["paragraph_blocks_cut"]}
            ),
            "short_paragraph_blocks_cut": len(
                {bid for c in children for bid in c["short_paragraph_blocks_cut"]}
            ),
            "end_reasons": dict(
                sorted(Counter((c["split_reason"] for c in children)).items())
            ),
        }

    def step_8b_generate_experimental_children_while_retaining_every_complete_parent(
        self,
    ):
        """8b. Generate experimental children while retaining every complete parent."""
        self.OS_PARENTS = {
            u["id"]: u
            for u in self.OS_CONTROL
            if oversized_eligible(u["end"] - u["start"], min(self.OS_THRESHOLDS))
        }
        self.OS_GROUPS = {}
        for self.pid, self.parent in self.OS_PARENTS.items():
            for self.setting in self.OS_SETTINGS:
                self.windows = self.os_windows(self.parent, self.setting)
                check_os_windows(
                    self.parent["text"],
                    self.windows,
                    self.setting["target"],
                    self.setting["overlap"],
                )
                self.gid = "oversized-set:" + fingerprint(
                    [self.OS_RUN_ID, self.pid, self.setting["id"]]
                )
                self.children = []
                for self.ordinal, self.window in enumerate(self.windows, 1):
                    self.a, self.b = (
                        self.parent["start"] + self.window["start"],
                        self.parent["start"] + self.window["end"],
                    )
                    self.cid = "oversized-child:" + fingerprint(
                        [self.OS_RUN_ID, self.pid, self.setting["id"], self.a, self.b]
                    )
                    self.child = {
                        "id": self.cid,
                        "ordinal": self.ordinal,
                        "document_id": self.parent["document_id"],
                        "start": self.a,
                        "end": self.b,
                        "text": self.window["text"],
                        "setup_id": self.SETUP_ID,
                        "configuration": self.setting["id"],
                        "record_kind": "oversized experiment child",
                        "parent_id": self.pid,
                        "relationship_id": "oversized-link:"
                        + fingerprint([self.gid, self.cid, self.ordinal]),
                        "source_spans": self.source_map(
                            self.parent["document_id"], self.a, self.b
                        ),
                        "split_reason": self.window["end_reason"],
                        "next_start_reason": self.window.get(
                            "next_start_reason", "parent_complete"
                        ),
                        "requested_overlap": self.setting["overlap"],
                        "actual_previous_overlap": max(
                            0,
                            self.windows[self.ordinal - 2]["end"]
                            - self.window["start"],
                        )
                        if self.ordinal > 1
                        else 0,
                        "actual_next_overlap": max(
                            0, self.window["end"] - self.windows[self.ordinal]["start"]
                        )
                        if self.ordinal < len(self.windows)
                        else 0,
                        "context_expansion_ratio": round(
                            (self.parent["end"] - self.parent["start"])
                            / (self.b - self.a),
                            4,
                        ),
                    }
                    require(
                        self.reconstruct(self.child["source_spans"])
                        == self.child["text"],
                        "Child source reconstruction failed.",
                    )
                    self.child["paragraph_blocks_cut"] = self.paragraph_cuts(self.child)
                    self.child["short_paragraph_blocks_cut"] = [
                        bid
                        for bid in self.child["paragraph_blocks_cut"]
                        if len(self.BLOCKS[bid]["raw_text"]) <= self.setting["target"]
                    ]
                    self.child["reviewed_boundary_diagnostics"] = self.legal_diagnostic(
                        self.child
                    )
                    self.children.append(self.child)
                self.OS_GROUPS[self.pid, self.setting["id"]] = {
                    "id": self.gid,
                    "parent_id": self.pid,
                    "setting": self.setting,
                    "eligible_thresholds": [
                        t
                        for t in self.OS_THRESHOLDS
                        if oversized_eligible(
                            self.parent["end"] - self.parent["start"], t
                        )
                    ],
                    "children": self.children,
                }
        self.OS_DATA_FINGERPRINT = fingerprint(list(self.OS_GROUPS.values()))
        self.OS_GROUP_METRICS = [
            self.os_group_metrics(g) for g in self.OS_GROUPS.values()
        ]
        print(
            "Complete affected parents retained:",
            len(self.OS_PARENTS),
            "; distinct parent/setting experiments:",
            len(self.OS_GROUPS),
        )

    def step_8c_matched_diagnostics_compare_methods_within_each_threshold_and_settin(
        self,
    ):
        """8c. Matched diagnostics — compare methods within each threshold and setting."""
        self.ensure_os_current()
        self.OS_DIAGNOSTICS = []
        for self.threshold in self.OS_THRESHOLDS:
            for self.setting in self.OS_SETTINGS:
                self.groups = [
                    g
                    for g in self.OS_GROUPS.values()
                    if g["setting"]["id"] == self.setting["id"]
                    and self.threshold in g["eligible_thresholds"]
                ]
                self.children = [c for g in self.groups for c in g["children"]]
                self.sizes = [len(c["text"]) for c in self.children]
                self.originals = sum(
                    (
                        self.OS_PARENTS[g["parent_id"]]["end"]
                        - self.OS_PARENTS[g["parent_id"]]["start"]
                        for g in self.groups
                    )
                )
                self.duplicate = sum(self.sizes) - self.originals
                self.overlaps = [
                    c["actual_previous_overlap"]
                    for g in self.groups
                    for c in g["children"][1:]
                ]
                self.metrics = [self.os_group_metrics(g) for g in self.groups]
                self.OS_DIAGNOSTICS.append(
                    {
                        "threshold": self.threshold,
                        "setting": self.setting["id"],
                        "affected_parents": len(self.groups),
                        "children": len(self.children),
                        "child_size_distribution": length_summary(self.sizes),
                        "actual_overlap_distribution": length_summary(self.overlaps),
                        "overlap_below_requested": sum(
                            (x < self.setting["overlap"] for x in self.overlaps)
                        ),
                        "duplicated_characters": self.duplicate,
                        "duplication_pct_of_parent_text": round(
                            100 * self.duplicate / self.originals, 2
                        )
                        if self.originals
                        else 0,
                        "paragraph_blocks_cut": sum(
                            (m["paragraph_blocks_cut"] for m in self.metrics)
                        ),
                        "short_paragraph_blocks_cut": sum(
                            (m["short_paragraph_blocks_cut"] for m in self.metrics)
                        ),
                        "end_reasons": dict(
                            sorted(
                                Counter(
                                    (c["split_reason"] for c in self.children)
                                ).items()
                            )
                        ),
                        "covered_parent_characters_pct": 100 if self.groups else None,
                    }
                )
        show_table(
            [
                {
                    k: r[k]
                    for k in (
                        "threshold",
                        "setting",
                        "affected_parents",
                        "children",
                        "paragraph_blocks_cut",
                        "short_paragraph_blocks_cut",
                        "duplication_pct_of_parent_text",
                        "overlap_below_requested",
                    )
                }
                for r in self.OS_DIAGNOSTICS
            ]
        )
        display(
            HTML(
                "<details><summary>All 24 configurations: sizes, measured overlap and cut reasons</summary>"
                + table_html(self.OS_DIAGNOSTICS)
                + "</details>"
            )
        )
        self.OS_MATCHED_COMPARISONS = []
        for self.threshold in self.OS_THRESHOLDS:
            for self.target in (1000, 2000):
                for self.pct in (0, 10):
                    self.exact, self.aware = [
                        next(
                            (
                                r
                                for r in self.OS_DIAGNOSTICS
                                if r["threshold"] == self.threshold
                                and r["setting"]
                                == f"{method}-chars-{self.target}-overlap-{self.pct}pct"
                            )
                        )
                        for method in ("exact", "boundary_aware")
                    ]
                    self.OS_MATCHED_COMPARISONS.append(
                        {
                            "threshold": self.threshold,
                            "target": self.target,
                            "overlap_pct": self.pct,
                            "aware_minus_exact_children": self.aware["children"]
                            - self.exact["children"],
                            "aware_minus_exact_paragraphs_cut": self.aware[
                                "paragraph_blocks_cut"
                            ]
                            - self.exact["paragraph_blocks_cut"],
                            "aware_minus_exact_duplication_chars": self.aware[
                                "duplicated_characters"
                            ]
                            - self.exact["duplicated_characters"],
                            "interpretation": "Trade-offs on identical parents; no winner score",
                        }
                    )
        show_table(self.OS_MATCHED_COMPARISONS)

    def show_oversized_example(self, sample_id, target=2000, overlap_pct=10):
        self.ensure_os_current()
        example = next((e for e in self.OS_EXAMPLES if e["sample_id"] == sample_id))
        parent, sample = (
            self.OS_PARENTS[example["parent_id"]],
            self.SAMPLE_BY_ID[sample_id],
        )
        display(
            HTML(
                "<h4>"
                + esc(sample_id)
                + " — complete uncapped control and matched children</h4>"
            )
        )
        show_table([m for m in self.OS_GROUP_METRICS if m["parent_id"] == parent["id"]])
        for method in ("exact", "boundary_aware"):
            setting_id = f"{method}-chars-{target}-overlap-{overlap_pct}pct"
            require(
                (parent["id"], setting_id) in self.OS_GROUPS,
                "Choose a tested child setting.",
            )
            group = self.OS_GROUPS[parent["id"], setting_id]
            children = group["children"]
            rows = [
                {
                    "ordinal": c["ordinal"],
                    "child_id": c["id"],
                    "parent_id": parent["id"],
                    "relationship_id": c["relationship_id"],
                    "characters": len(c["text"]),
                    "source_span": [c["start"], c["end"]],
                    "parent_relative_span": [
                        c["start"] - parent["start"],
                        c["end"] - parent["start"],
                    ],
                    "intersects_frozen_sample": bool(
                        intersection_length(
                            (c["start"], c["end"]), (sample["start"], sample["end"])
                        )
                    ),
                    **{
                        k: c[k]
                        for k in (
                            "split_reason",
                            "next_start_reason",
                            "requested_overlap",
                            "actual_previous_overlap",
                            "actual_next_overlap",
                            "context_expansion_ratio",
                            "paragraph_blocks_cut",
                            "reviewed_boundary_diagnostics",
                        )
                    },
                }
                for c in children
            ]
            cuts = sorted({p for c in children for p in (c["start"], c["end"])})
            overlaps = [
                (b["start"], a["end"])
                for a, b in zip(children, children[1:])
                if b["start"] < a["end"]
            ]
            body = (
                "<p>Complete parent: "
                + str(len(parent["text"]))
                + " characters; children: "
                + str(len(children))
                + ".</p>"
            )
            body += "<details><summary>Source panel: all cuts (bars), overlap (gold), frozen sample (blue)</summary>"
            body += (
                highlight_html(
                    parent["text"],
                    parent["start"],
                    cuts,
                    overlaps,
                    (sample["start"], sample["end"]),
                )
                + "</details>"
            )
            body += table_html(rows)
            body += self.relationship_html(
                parent, children, sample, self.REVIEWED_PROVISIONS
            )
            display(
                HTML(
                    "<details><summary>"
                    + esc(setting_id)
                    + " — full parent and all children</summary>"
                    + body
                    + "</details>"
                )
            )

    def step_8d_representative_parents_children_and_cut_points(self):
        """8d. Representative parents, children and cut points."""
        self.OS_EXAMPLES = [
            {
                "sample_id": sample_id,
                "parent_id": self.STRUCTURAL_BY_FIRST_BLOCK[
                    self.BY_POSITION[position]["id"]
                ]["id"],
            }
            for sample_id, position in [
                ("long_article", 2779),
                ("transitional_provision", 2159),
                ("annex", 2848),
                ("publication_history", 54),
            ]
        ]
        self.OS_EXAMPLES.insert(
            1,
            {
                "sample_id": "long_paragraph",
                "parent_id": next(
                    (
                        u["id"]
                        for u in self.OS_CONTROL
                        if u["document_id"]
                        == self.SAMPLE_BY_ID["long_paragraph"]["document_id"]
                        and u["start"]
                        <= self.SAMPLE_BY_ID["long_paragraph"]["start"]
                        < u["end"]
                    )
                ),
            },
        )
        self.OS_EXAMPLE_ROWS = []
        for self.example in self.OS_EXAMPLES:
            self.parent = self.OS_PARENTS[self.example["parent_id"]]
            self.sample = self.SAMPLE_BY_ID[self.example["sample_id"]]
            self.OS_EXAMPLE_ROWS.append(
                {
                    "sample": self.example["sample_id"],
                    "kind": self.parent["unit_kind"],
                    "parent_characters": len(self.parent["text"]),
                    "sample_characters": self.sample["characters"],
                    "sample_coverage_pct": round(
                        100
                        * intersection_length(
                            (self.parent["start"], self.parent["end"]),
                            (self.sample["start"], self.sample["end"]),
                        )
                        / self.sample["characters"],
                        2,
                    ),
                    **{
                        f"trigger_{t}": "split experiment"
                        if len(self.parent["text"]) > t
                        else "retain uncapped control"
                        for t in self.OS_THRESHOLDS
                    },
                }
            )
        show_table(self.OS_EXAMPLE_ROWS)
        for self.example in self.OS_EXAMPLES:
            self.show_oversized_example(self.example["sample_id"])

    def step_8e_preservation_reproducibility_and_limits(self):
        """8e. Preservation, reproducibility and limits."""
        self.ensure_os_current()
        self.OS_VALIDATED_CHILDREN = 0
        for (self.pid, self.setting_id), self.group in self.OS_GROUPS.items():
            self.parent, self.setting, self.children = (
                self.OS_PARENTS[self.pid],
                self.group["setting"],
                self.group["children"],
            )
            require(
                "parent_id" not in self.parent and self.parent["id"] == self.pid,
                "Parent link cycle or unresolved parent.",
            )
            require(
                self.parent == self.STRUCTURAL_BY_ID[self.pid],
                "Original uncapped parent changed.",
            )
            self.rerun = self.os_windows(self.parent, self.setting)
            check_os_windows(
                self.parent["text"],
                self.rerun,
                self.setting["target"],
                self.setting["overlap"],
            )
            require(len(self.rerun) == len(self.children), "Rerun child count changed.")
            require(
                len({c["id"] for c in self.children}) == len(self.children),
                "Duplicate child IDs.",
            )
            for self.i, (self.child, self.w) in enumerate(
                zip(self.children, self.rerun), 1
            ):
                require(
                    self.child["parent_id"] == self.pid
                    and self.child["document_id"] == self.parent["document_id"]
                    and (
                        self.parent["start"]
                        <= self.child["start"]
                        < self.child["end"]
                        <= self.parent["end"]
                    ),
                    "Child escaped parent.",
                )
                require(
                    self.child["start"] == self.parent["start"] + self.w["start"]
                    and self.child["end"] == self.parent["start"] + self.w["end"]
                    and (
                        self.child["text"]
                        == self.w["text"]
                        == self.reconstruct(self.child["source_spans"])
                    ),
                    "Source spans changed on rerun.",
                )
                require(
                    self.child["id"]
                    == "oversized-child:"
                    + fingerprint(
                        [
                            self.OS_RUN_ID,
                            self.pid,
                            self.setting_id,
                            self.child["start"],
                            self.child["end"],
                        ]
                    ),
                    "Unstable child ID.",
                )
                require(
                    self.child["relationship_id"]
                    == "oversized-link:"
                    + fingerprint([self.group["id"], self.child["id"], self.i]),
                    "Unstable relationship ID.",
                )
                self.OS_VALIDATED_CHILDREN += 1
        self.os_original_target = self.OS_SETTINGS[0]["target"]
        try:
            self.OS_SETTINGS[0]["target"] += 1
            expect_value_error(self.ensure_os_current, "Step 8 settings changed")
        finally:
            self.OS_SETTINGS[0]["target"] = self.os_original_target
        self.os_first_child = next(iter(self.OS_GROUPS.values()))["children"][0]
        self.os_original_reason = self.os_first_child["split_reason"]
        try:
            self.os_first_child["split_reason"] = "stale edit"
            expect_value_error(self.ensure_os_current, "Step 8 child results changed")
        finally:
            self.os_first_child["split_reason"] = self.os_original_reason
        require(
            self.OS_APPROVED_FINGERPRINTS
            == (
                fingerprint(self.STRUCTURAL_RESULTS),
                fingerprint(self.FIXED_RESULTS),
                fingerprint(self.PC_DATA),
            ),
            "An approved baseline changed.",
        )
        require(
            all(
                (
                    Path(path).read_bytes() == data
                    for path, data in self.OS_APPROVED_BYTES.items()
                )
            ),
            "An approved report or manifest changed.",
        )
        require(
            hashlib.sha256(self.ARTIFACT.read_bytes()).hexdigest()
            == self.artifact_sha256
            and fingerprint(self.corpus) == self.corpus_fingerprint_before,
            "Stage 1 input changed.",
        )
        self.ensure_os_current()
        print(
            "PASS:",
            self.OS_VALIDATED_CHILDREN,
            "children: source fidelity, complete parent coverage, containment, links, deterministic regeneration.",
        )
        print(
            "PASS: frozen manifest, Steps 5–7 reports/results, Stage 1 source unchanged; stale settings rejected."
        )

    def step_8f_review_observations_and_stop(self):
        """8f. Review observations and stop."""
        self.ensure_os_current()
        self.OS_REPORT = {
            "report_version": 1,
            "scope": "Step 8 only — oversized-unit experiments",
            "run_id": self.OS_RUN_ID,
            "spec": self.OS_SPEC,
            "data_fingerprint": self.OS_DATA_FINGERPRINT,
            "control_units": len(self.OS_CONTROL),
            "threshold_diagnostics": self.OS_THRESHOLD_ROWS,
            "parents": {
                pid: {k: v for k, v in parent.items() if k != "text"}
                for pid, parent in self.OS_PARENTS.items()
            },
            "relationship_sets": [
                {
                    **{k: v for k, v in group.items() if k != "children"},
                    "children": [
                        {k: v for k, v in child.items() if k != "text"}
                        for child in group["children"]
                    ],
                }
                for group in self.OS_GROUPS.values()
            ],
            "configuration_diagnostics": self.OS_DIAGNOSTICS,
            "matched_comparisons": self.OS_MATCHED_COMPARISONS,
            "sample_examples": self.OS_EXAMPLES,
            "sample_trigger_diagnostics": self.OS_EXAMPLE_ROWS,
            "parent_setting_diagnostics": self.OS_GROUP_METRICS,
            "validation": {
                "status": "PASS",
                "children_checked": self.OS_VALIDATED_CHILDREN,
                "source_fidelity": True,
                "coverage": True,
                "containment": True,
                "legal_validation": False,
            },
            "decision": "No threshold, size or splitting method selected; waiting for Step 8 review",
        }
        self.os_report_path = (
            self.OUTPUT_DIR
            / f"oversized_unit_report.{fingerprint(self.OS_REPORT)}.json"
        )
        self.os_report_bytes = (canonical(self.OS_REPORT) + "\n").encode("utf-8")
        if self.os_report_path.exists():
            require(
                self.os_report_path.read_bytes() == self.os_report_bytes,
                "Existing oversized-unit report differs.",
            )
        else:
            self.os_report_path.write_bytes(self.os_report_bytes)
        require(
            json.loads(self.os_report_path.read_text(encoding="utf-8"))
            == self.OS_REPORT,
            "Report round trip failed.",
        )
        print("Oversized-unit report:", self.os_report_path.relative_to(self.ROOT))
        print(
            "STOP AFTER STEP 8 — experiments ready for review; no final threshold, child size or method selected."
        )
