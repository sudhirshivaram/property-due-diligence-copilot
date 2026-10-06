"""Chunking: parent child."""

import hashlib
import json
from property_copilot._display import HTML, display
from .primitives import (
    canonical,
    details_html,
    esc,
    expect_value_error,
    fingerprint,
    fixed_length_windows,
    intersection_length,
    interval_union_length,
    length_summary,
    require,
    show_json,
    show_table,
    table_html,
    validate_relationship_group,
)


class ParentChildSteps:
    """Parent Child steps; state belongs to the workflow instance."""

    def step_7a_preserve_approved_artifacts_and_declare_evidenced_parent_candidates(
        self,
    ):
        """7a. Preserve approved artifacts and declare evidenced parent candidates."""
        self.ensure_structural_current()
        self.APPROVED_STRUCTURAL_ID = (
            "cf6e1ba11a3b5d373dd8da1a7e5120059c4bdd956123440840c0b391dcbad259"
        )
        self.APPROVED_STRUCTURAL_RESULT = (
            "8d11499a43d36e51ab0570a0a4283397e550b3eba6daacc31bfe41e2b2e44775"
        )
        require(
            self.STRUCTURAL_ID == self.APPROVED_STRUCTURAL_ID
            and self.STRUCTURAL_RESULTS_FINGERPRINT == self.APPROVED_STRUCTURAL_RESULT,
            "Structural setup differs from approved Step 6; review before changing parent candidates.",
        )
        self.STEP6_REPORT_BYTES = self.structural_report_path.read_bytes()
        self.STEP7_FIXED_REPORT_BYTES = self.report_path.read_bytes()
        self.PC_CONFIGURATIONS = json.loads(self.CONFIGURATIONS_JSON)
        self.PC_CONFIG_BY_ID = {c["id"]: c for c in self.PC_CONFIGURATIONS}
        self.STRUCTURAL_BY_ID = {r["id"]: r for r in self.structural_records}
        self.STRUCTURAL_BY_FIRST_BLOCK = {
            r["block_ids"][0]: r for r in self.structural_records
        }
        self.PARENT_CANDIDATES = []
        for (
            self.sample_id,
            self.kind,
            self.label,
            self.first,
            self.last,
        ) in self.PROVISION_SPECS:
            self.unit = self.STRUCTURAL_BY_FIRST_BLOCK[
                self.BY_POSITION[self.first]["id"]
            ]
            self.PARENT_CANDIDATES.append(
                {
                    "case": f"unit-{self.first}",
                    "family": "annex"
                    if self.kind == "Annex"
                    else "article_or_paragraph_sign",
                    "parent_role": self.unit["unit_kind"],
                    "document_id": self.unit["document_id"],
                    "start": self.unit["start"],
                    "end": self.unit["end"],
                    "member_unit_ids": [self.unit["id"]],
                    "review_basis": f"Inspected {self.kind} source extent in frozen sample {self.sample_id}.",
                    "opening_position": self.first,
                    "closing_position_exclusive": None,
                    "boundary_evidence_ids": [
                        self.unit["opening_ledger_id"],
                        self.unit["closing_ledger_id"],
                    ],
                }
            )
        for self.position, self.reason in [
            (54, "Publication/history preamble; no legal-parent role inferred."),
            (2051, "Reviewed additional-provision heading remains unclassified."),
            (2158, "Reviewed transitional heading remains unclassified."),
            (
                25688,
                "Complete EU preamble/recital residual containing the long-paragraph sample.",
            ),
            (
                28934,
                "Complete weakly structured source-page residual including navigation.",
            ),
        ]:
            self.unit = self.STRUCTURAL_BY_FIRST_BLOCK[
                self.BY_POSITION[self.position]["id"]
            ]
            require(
                self.unit["unit_kind"] in {"unclassified", "residual"},
                "Unexpected legal role for unclassified parent.",
            )
            self.PARENT_CANDIDATES.append(
                {
                    "case": f"unclassified-{self.position}",
                    "family": "reviewed_unclassified_span",
                    "parent_role": self.unit["unit_kind"],
                    "document_id": self.unit["document_id"],
                    "start": self.unit["start"],
                    "end": self.unit["end"],
                    "member_unit_ids": [self.unit["id"]],
                    "review_basis": self.reason,
                    "opening_position": self.position,
                    "closing_position_exclusive": None,
                    "boundary_evidence_ids": [
                        self.unit["opening_ledger_id"],
                        self.unit["closing_ledger_id"],
                    ],
                }
            )
        self.LARGER_PARENT_SPECS = [
            (
                "chapter-zut-1",
                "chapter",
                59,
                95,
                "Глава първа.",
                "Глава втора.",
                "Consecutive Chapter I/II labels.",
            ),
            (
                "section-zut-3-1",
                "section",
                112,
                132,
                "Раздел I.",
                "Раздел II.",
                "Section I/II labels inside the inspected Chapter III range.",
            ),
            (
                "chapter-zut-3",
                "chapter",
                110,
                451,
                "Глава трета.",
                "Глава четвърта.",
                "Consecutive Chapter III/IV labels; includes multiple Sections.",
            ),
            (
                "chapter-ordinance3-2",
                "chapter",
                2777,
                2818,
                "Глава втора.",
                "Допълнителни разпоредби",
                "Chapter II ends at the inspected transition into additional provisions; no legal role assigned to that closing heading.",
            ),
            (
                "chapter-eu-1",
                "chapter",
                25781,
                25850,
                "ГЛАВА I",
                "ГЛАВА II",
                "Consecutive EU Chapter I/II labels.",
            ),
        ]
        for (
            self.case,
            self.role,
            self.first,
            self.stop,
            self.prefix,
            self.stop_prefix,
            self.reason,
        ) in self.LARGER_PARENT_SPECS:
            self.start_unit = self.STRUCTURAL_BY_FIRST_BLOCK[
                self.BY_POSITION[self.first]["id"]
            ]
            self.stop_unit = self.STRUCTURAL_BY_FIRST_BLOCK[
                self.BY_POSITION[self.stop]["id"]
            ]
            require(
                self.BY_POSITION[self.first]["raw_text"].startswith(self.prefix)
                and self.BY_POSITION[self.stop]["raw_text"].startswith(
                    self.stop_prefix
                ),
                "Larger-parent boundary text changed.",
            )
            require(
                self.start_unit["unit_kind"] == self.role
                and self.start_unit["document_id"] == self.stop_unit["document_id"],
                "Larger parent lacks supported opening role or same-document closing evidence.",
            )
            self.did, self.lo, self.hi = (
                self.start_unit["document_id"],
                self.start_unit["start"],
                self.stop_unit["start"],
            )
            self.members = [
                r
                for r in self.STRUCTURAL_RESULTS[self.did]
                if self.lo <= r["start"] and r["end"] <= self.hi
            ]
            require(
                self.members
                and self.members[0]["start"] == self.lo
                and (self.members[-1]["end"] == self.hi)
                and (
                    "".join((r["text"] for r in self.members))
                    == self.VIEWS[self.did]["text"][self.lo : self.hi]
                ),
                "Larger parent does not match complete structural units.",
            )
            self.PARENT_CANDIDATES.append(
                {
                    "case": self.case,
                    "family": "section_or_chapter",
                    "parent_role": self.role,
                    "document_id": self.did,
                    "start": self.lo,
                    "end": self.hi,
                    "member_unit_ids": [r["id"] for r in self.members],
                    "opening_position": self.first,
                    "closing_position_exclusive": self.stop,
                    "review_basis": self.reason,
                    "boundary_evidence_ids": [
                        self.start_unit["opening_ledger_id"],
                        self.stop_unit["opening_ledger_id"],
                    ],
                }
            )
        self.PC_SPEC = {
            "version": 1,
            "scope": "Step 7 relationship alternatives only",
            "setup_id": self.SETUP_ID,
            "structural_id": self.STRUCTURAL_ID,
            "structural_result_fingerprint": self.STRUCTURAL_RESULTS_FINGERPRINT,
            "parent_candidates": self.PARENT_CANDIDATES,
            "fixed_configurations": self.PC_CONFIGURATIONS,
            "unit_parent_mode": "fixed_inside_parent",
            "larger_parent_modes": [
                "whole_contained_units",
                "fixed_inside_each_contained_unit",
            ],
            "fallback_policy": None,
            "annex_subsections": "not established by reviewed evidence; whole Annex only",
            "approval": "Steps 1–6 approved; Step 7 only authorized",
        }
        self.PC_RUN_ID = fingerprint(self.PC_SPEC)
        show_table(
            [
                {
                    "case": c["case"],
                    "role": c["parent_role"],
                    "document": self.DOCUMENTS[c["document_id"]]["ordinal"],
                    "characters": c["end"] - c["start"],
                    "contained_units": len(c["member_unit_ids"]),
                    "start_position": c["opening_position"],
                    "end_position_exclusive": c["closing_position_exclusive"],
                    "review_basis": c["review_basis"],
                }
                for c in self.PARENT_CANDIDATES
            ]
        )
        show_json(
            "Parent boundary evidence and exact constituent Step 6 IDs",
            self.PARENT_CANDIDATES,
        )
        print("Relationship experiment:", self.PC_RUN_ID)

    def build_parent_child_experiment(self):
        parents, children, groups, links = ({}, {}, {}, {})

        def register_child(did, lo, hi):
            child_id = "pc-child:" + fingerprint([self.SETUP_ID, did, lo, hi])
            if child_id not in children:
                children[child_id] = {
                    "id": child_id,
                    "document_id": did,
                    "start": lo,
                    "end": hi,
                    "text": self.VIEWS[did]["text"][lo:hi],
                    "source_spans": self.source_map(did, lo, hi),
                    "setup_id": self.SETUP_ID,
                    "record_kind": "parent-child experimental child span",
                }
            return child_id

        for parent_order, candidate in enumerate(self.PARENT_CANDIDATES, 1):
            did, lo, hi = (
                candidate["document_id"],
                candidate["start"],
                candidate["end"],
            )
            parent_id = "pc-parent:" + fingerprint(
                [self.PC_RUN_ID, candidate["case"], did, lo, hi]
            )
            parents[parent_id] = {
                **candidate,
                "id": parent_id,
                "ordinal": parent_order,
                "configuration": "complete experimental parent",
                "setup_id": self.SETUP_ID,
                "record_kind": "complete experimental "
                + candidate["parent_role"]
                + " parent",
                "text": self.VIEWS[did]["text"][lo:hi],
                "source_spans": self.source_map(did, lo, hi),
                "source_artifact_sha256": self.artifact_sha256,
                "source_docx_sha256": self.corpus["source"]["sha256"],
                "block_ids": [
                    bid
                    for uid in candidate["member_unit_ids"]
                    for bid in self.STRUCTURAL_BY_ID[uid]["block_ids"]
                ],
            }
            modes = [("fixed_inside_parent", c["id"]) for c in self.PC_CONFIGURATIONS]
            if candidate["family"] == "section_or_chapter":
                modes = [("whole_contained_units", "uncapped-structural-units")] + [
                    ("fixed_inside_each_contained_unit", c["id"])
                    for c in self.PC_CONFIGURATIONS
                ]
            for mode, config_id in modes:
                group_id = "pc-set:" + fingerprint(
                    [self.PC_RUN_ID, parent_id, mode, config_id]
                )
                group = {
                    "id": group_id,
                    "parent_id": parent_id,
                    "case": candidate["case"],
                    "mode": mode,
                    "configuration": config_id,
                    "relationship_ids": [],
                }
                groups[group_id] = group
                members = [
                    self.STRUCTURAL_BY_ID[uid] for uid in candidate["member_unit_ids"]
                ]
                if mode == "fixed_inside_parent":
                    require(
                        len(members) == 1,
                        "Direct mode expects one complete structural-unit parent.",
                    )
                order = 0
                for member in members:
                    if mode == "whole_contained_units":
                        spans = [(member["start"], member["end"])]
                    else:
                        config = self.PC_CONFIG_BY_ID[config_id]
                        spans = [
                            (member["start"] + w["start"], member["start"] + w["end"])
                            for w in fixed_length_windows(
                                member["text"],
                                config["length"],
                                config["overlap_characters"],
                            )
                        ]
                    for child_lo, child_hi in spans:
                        order += 1
                        child_id = register_child(did, child_lo, child_hi)
                        relation_id = "pc-link:" + fingerprint(
                            [group_id, parent_id, child_id, order]
                        )
                        links[relation_id] = {
                            "id": relation_id,
                            "relationship_set_id": group_id,
                            "parent_id": parent_id,
                            "child_id": child_id,
                            "ordinal": order,
                            "source_structural_unit_id": member["id"],
                            "source_unit_kind": member["unit_kind"],
                        }
                        group["relationship_ids"].append(relation_id)
        return {
            "parents": parents,
            "children": children,
            "groups": groups,
            "links": links,
        }

    def step_7b_relationship_identity_and_controlled_child_construction(self):
        """7b. Relationship identity and controlled child construction."""
        self.PC_DATA = self.build_parent_child_experiment()
        self.PC_DATA_FINGERPRINT = fingerprint(self.PC_DATA)
        self.PC_GENERATION_CONTEXT = {
            "run_id": self.PC_RUN_ID,
            "setup_id": self.SETUP_ID,
            "structural_result": self.STRUCTURAL_RESULTS_FINGERPRINT,
        }
        self.PC_PARENTS, self.PC_CHILDREN, self.PC_GROUPS, self.PC_LINKS = [
            self.PC_DATA[k] for k in ("parents", "children", "groups", "links")
        ]
        self.PC_PARENT_BY_CASE = {p["case"]: p for p in self.PC_PARENTS.values()}
        self.PC_GROUP_BY_KEY = {
            (g["case"], g["mode"], g["configuration"]): g
            for g in self.PC_GROUPS.values()
        }
        print(
            len(self.PC_PARENTS),
            "parent candidates;",
            len(self.PC_GROUPS),
            "relationship sets;",
            len(self.PC_CHILDREN),
            "distinct child source spans;",
            len(self.PC_LINKS),
            "ordered relationships.",
        )

    def step_7c_validate_links_containment_ordering_full_coverage_and_provenance(self):
        """7c. Validate links, containment, ordering, full coverage, and provenance."""
        for self.group in self.PC_GROUPS.values():
            validate_relationship_group(
                self.group, self.PC_PARENTS, self.PC_CHILDREN, self.PC_LINKS
            )
            self.parent = self.PC_PARENTS[self.group["parent_id"]]
            self.links = [self.PC_LINKS[rid] for rid in self.group["relationship_ids"]]
            for self.uid in self.parent["member_unit_ids"]:
                self.member = self.STRUCTURAL_BY_ID[self.uid]
                self.actual = [
                    (
                        self.PC_CHILDREN[r["child_id"]]["start"],
                        self.PC_CHILDREN[r["child_id"]]["end"],
                    )
                    for r in self.links
                    if r["source_structural_unit_id"] == self.uid
                ]
                if self.group["mode"] == "whole_contained_units":
                    self.expected = [(self.member["start"], self.member["end"])]
                else:
                    self.config = self.PC_CONFIG_BY_ID[self.group["configuration"]]
                    self.expected = [
                        (
                            self.member["start"] + w["start"],
                            self.member["start"] + w["end"],
                        )
                        for w in fixed_length_windows(
                            self.member["text"],
                            self.config["length"],
                            self.config["overlap_characters"],
                        )
                    ]
                require(
                    self.actual == self.expected,
                    "Child spans differ from whole units or already-tested fixed windows.",
                )
        for self.node in list(self.PC_PARENTS.values()) + list(
            self.PC_CHILDREN.values()
        ):
            require(
                self.node["text"]
                == self.VIEWS[self.node["document_id"]]["text"][
                    self.node["start"] : self.node["end"]
                ]
                == self.reconstruct(self.node["source_spans"]),
                "Node source mapping/text changed.",
            )
        require(
            all(("parent_id" not in c for c in self.PC_CHILDREN.values())),
            "Shared child registry must not choose one arbitrary parent.",
        )
        print(
            "PASS: every relationship has valid IDs, ordered contained children, exact parent reconstruction, and source mappings."
        )

    def step_7d_parent_sizes_child_counts_and_context_expansion_diagnostics(self):
        """7d. Parent sizes, child counts, and context-expansion diagnostics."""
        self.LEGAL_PARENT_KINDS = {"article", "paragraph_sign", "annex"}
        self.PC_GROUP_DIAGNOSTICS, self.PC_LINK_DIAGNOSTICS = ([], {})
        for self.group in self.PC_GROUPS.values():
            self.parent = self.PC_PARENTS[self.group["parent_id"]]
            self.parent_size = self.parent["end"] - self.parent["start"]
            self.members = [
                self.STRUCTURAL_BY_ID[uid] for uid in self.parent["member_unit_ids"]
            ]
            self.legal_members = [
                m for m in self.members if m["unit_kind"] in self.LEGAL_PARENT_KINDS
            ]
            self.sizes, self.ratios, self.legal_child_ratios = ([], [], [])
            for self.rid in self.group["relationship_ids"]:
                self.relation = self.PC_LINKS[self.rid]
                self.child = self.PC_CHILDREN[self.relation["child_id"]]
                self.size = self.child["end"] - self.child["start"]
                self.ratio = self.parent_size / self.size
                self.touched = [
                    m
                    for m in self.legal_members
                    if intersection_length(
                        (self.child["start"], self.child["end"]), (m["start"], m["end"])
                    )
                ]
                self.PC_LINK_DIAGNOSTICS[self.rid] = {
                    "parent_characters": self.parent_size,
                    "child_characters": self.size,
                    "context_expansion_ratio": round(self.ratio, 4),
                    "added_context_characters": self.parent_size - self.size,
                    "parent_legal_unit_count": len(self.legal_members),
                    "other_legal_units": len(self.legal_members) - len(self.touched),
                }
                self.sizes.append(self.size)
                self.ratios.append(self.ratio)
                if self.relation["source_unit_kind"] in self.LEGAL_PARENT_KINDS:
                    self.legal_child_ratios.append(self.ratio)
            self.PC_GROUP_DIAGNOSTICS.append(
                {
                    "relationship_set_id": self.group["id"],
                    "case": self.group["case"],
                    "family": self.parent["family"],
                    "mode": self.group["mode"],
                    "configuration": self.group["configuration"],
                    "parent_characters": self.parent_size,
                    "child_count": len(self.sizes),
                    "child_size_min": min(self.sizes),
                    "child_size_max": max(self.sizes),
                    "expansion_min": round(min(self.ratios), 4),
                    "expansion_median": round(
                        length_summary(self.ratios)["median_p50"], 4
                    ),
                    "expansion_max": round(max(self.ratios), 4),
                    "legal_child_expansion_median": round(
                        length_summary(self.legal_child_ratios)["median_p50"], 4
                    )
                    if self.legal_child_ratios
                    else "not applicable",
                    "overlap_extra_character_pct": round(
                        100 * (sum(self.sizes) - self.parent_size) / self.parent_size, 2
                    ),
                    "parent_legal_units": len(self.legal_members),
                    "one_child_equals_parent": len(self.sizes) == 1
                    and self.sizes[0] == self.parent_size,
                    "coverage_pct": 100,
                }
            )
        for self.family in (
            "article_or_paragraph_sign",
            "section_or_chapter",
            "annex",
            "reviewed_unclassified_span",
        ):
            self.rows = [
                r for r in self.PC_GROUP_DIAGNOSTICS if r["family"] == self.family
            ]
            display(
                HTML(
                    f"<details><summary>{esc(self.family)}: all settings and child modes ({len(self.rows)} sets)</summary>"
                    + table_html(self.rows)
                    + "</details>"
                )
            )
        show_table(
            [
                r
                for r in self.PC_GROUP_DIAGNOSTICS
                if r["configuration"]
                in {self.GALLERY_CONFIGURATION, "uncapped-structural-units"}
            ],
            [
                "case",
                "mode",
                "configuration",
                "parent_characters",
                "child_count",
                "child_size_min",
                "child_size_max",
                "expansion_median",
                "expansion_max",
                "legal_child_expansion_median",
                "parent_legal_units",
                "one_child_equals_parent",
            ],
        )
        self.PC_SAMPLE_COVERAGE = []
        for self.sample in self.BASELINE_SAMPLES:
            self.lo, self.hi, self.did = (
                self.sample["start"],
                self.sample["end"],
                self.sample["document_id"],
            )
            self.parents = [
                p
                for p in self.PC_PARENTS.values()
                if p["document_id"] == self.did
                and intersection_length((self.lo, self.hi), (p["start"], p["end"]))
            ]
            self.covered = interval_union_length(
                (
                    (max(self.lo, p["start"]), min(self.hi, p["end"]))
                    for p in self.parents
                )
            )
            require(
                self.covered == self.hi - self.lo,
                "Parent candidate set leaves a frozen sample source character unrepresented.",
            )
            self.PC_SAMPLE_COVERAGE.append(
                {
                    "sample": self.sample["sample_id"],
                    "covered_by_union_of_candidates_pct": 100,
                    "fully_containing_parent_cases": [
                        p["case"]
                        for p in self.parents
                        if p["start"] <= self.lo and self.hi <= p["end"]
                    ],
                    "partially_intersecting_parent_cases": [
                        p["case"]
                        for p in self.parents
                        if not (p["start"] <= self.lo and self.hi <= p["end"])
                    ],
                }
            )
        show_table(self.PC_SAMPLE_COVERAGE)

    def step_7e_identical_children_under_different_parents_controlled_comparison(self):
        """7e. Identical children under different parents — controlled comparison."""
        self.IDENTICAL_CHILD_COMPARISONS = []
        for self.narrow in self.PC_PARENTS.values():
            if self.narrow["family"] != "article_or_paragraph_sign":
                continue
            self.uid = self.narrow["member_unit_ids"][0]
            for self.larger in self.PC_PARENTS.values():
                if (
                    self.larger["family"] != "section_or_chapter"
                    or self.uid not in self.larger["member_unit_ids"]
                ):
                    continue
                for self.config in self.PC_CONFIGURATIONS:
                    self.a = self.PC_GROUP_BY_KEY[
                        self.narrow["case"], "fixed_inside_parent", self.config["id"]
                    ]
                    self.b = self.PC_GROUP_BY_KEY[
                        self.larger["case"],
                        "fixed_inside_each_contained_unit",
                        self.config["id"],
                    ]
                    self.narrow_ids = [
                        self.PC_LINKS[rid]["child_id"]
                        for rid in self.a["relationship_ids"]
                    ]
                    self.larger_ids = [
                        self.PC_LINKS[rid]["child_id"]
                        for rid in self.b["relationship_ids"]
                        if self.PC_LINKS[rid]["source_structural_unit_id"] == self.uid
                    ]
                    require(
                        self.narrow_ids == self.larger_ids,
                        "Controlled parent comparison changed child boundaries or identity.",
                    )
                    self.IDENTICAL_CHILD_COMPARISONS.append(
                        {
                            "configuration": self.config["id"],
                            "unit_parent": self.narrow["case"],
                            "larger_parent": self.larger["case"],
                            "identical_child_spans": len(self.narrow_ids),
                            "unit_parent_characters": self.narrow["end"]
                            - self.narrow["start"],
                            "larger_parent_characters": self.larger["end"]
                            - self.larger["start"],
                            "same_child_parent_size_multiplier": round(
                                (self.larger["end"] - self.larger["start"])
                                / (self.narrow["end"] - self.narrow["start"]),
                                4,
                            ),
                            "example_child_id": self.narrow_ids[0],
                        }
                    )
        show_table(
            [
                r
                for r in self.IDENTICAL_CHILD_COMPARISONS
                if r["configuration"] == self.GALLERY_CONFIGURATION
            ]
        )
        display(
            HTML(
                "<details><summary>Identical-child comparisons across ALL nine settings</summary>"
                + table_html(self.IDENTICAL_CHILD_COMPARISONS)
                + "</details>"
            )
        )
        print(
            "PASS:",
            len(self.IDENTICAL_CHILD_COMPARISONS),
            "same-child parent comparisons; no child boundary changes.",
        )

    def ensure_pc_current(self):
        self.ensure_structural_current()
        require(
            fingerprint(self.PC_SPEC) == self.PC_RUN_ID
            and self.PC_SPEC["parent_candidates"] == self.PARENT_CANDIDATES
            and (self.PC_SPEC["fixed_configurations"] == self.PC_CONFIGURATIONS)
            and (canonical(self.PC_CONFIGURATIONS) == self.CONFIGURATIONS_JSON),
            "Parent candidates/settings changed; rebuild Step 7 relationships and diagnostics.",
        )
        require(
            self.PC_GENERATION_CONTEXT
            == {
                "run_id": self.PC_RUN_ID,
                "setup_id": self.SETUP_ID,
                "structural_result": self.STRUCTURAL_RESULTS_FINGERPRINT,
            },
            "Parent-child generation context is stale.",
        )

    def relationship_display_records(self, group_id):
        self.ensure_pc_current()
        require(group_id in self.PC_GROUPS, "Unknown relationship set.")
        group = self.PC_GROUPS[group_id]
        parent = {
            **self.PC_PARENTS[group["parent_id"]],
            "configuration": group["mode"] + " / " + group["configuration"],
        }
        children = [
            {
                **self.PC_CHILDREN[self.PC_LINKS[rid]["child_id"]],
                "parent_id": parent["id"],
                "ordinal": self.PC_LINKS[rid]["ordinal"],
                "relationship_id": rid,
                "configuration": parent["configuration"],
            }
            for rid in group["relationship_ids"]
        ]
        return (parent, children)

    def show_parent_child_set(self, group_id, sample_id=None):
        parent, children = self.relationship_display_records(group_id)
        group = self.PC_GROUPS[group_id]
        sample = self.SAMPLE_BY_ID[sample_id] if sample_id is not None else None
        if sample:
            require(
                sample["document_id"] == parent["document_id"],
                "Gallery sample and parent belong to different documents.",
            )
            pct = round(
                100
                * intersection_length(
                    (sample["start"], sample["end"]), (parent["start"], parent["end"])
                )
                / sample["characters"],
                2,
            )
            note = f"Parent covers {pct}% of this frozen sample. Its full extent is displayed."
        else:
            note = "Complete parent extent; all ordered children are displayed."
        rows = []
        for rid in group["relationship_ids"]:
            link = self.PC_LINKS[rid]
            child = self.PC_CHILDREN[link["child_id"]]
            rows.append(
                {
                    "order": link["ordinal"],
                    "relationship_id": rid,
                    "parent_id": parent["id"],
                    "child_id": child["id"],
                    "source_span": [child["start"], child["end"]],
                    "parent_relative_span": [
                        child["start"] - parent["start"],
                        child["end"] - parent["start"],
                    ],
                    "source_unit_kind": link["source_unit_kind"],
                    **self.PC_LINK_DIAGNOSTICS[rid],
                }
            )
        body = f"<p>{esc(note)} Child count: {len(children)}. No parent or child text has been truncated.</p>"
        body += details_html(
            "Parent hypothesis, role, and boundary provenance",
            json.dumps(
                {
                    k: parent[k]
                    for k in (
                        "case",
                        "parent_role",
                        "review_basis",
                        "boundary_evidence_ids",
                        "member_unit_ids",
                        "source_artifact_sha256",
                        "source_docx_sha256",
                    )
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        body += (
            "<details><summary>All ordered relationship IDs, source spans and expansion ratios</summary>"
            + table_html(rows)
            + "</details>"
        )
        body += self.relationship_html(
            parent, children, sample, self.REVIEWED_PROVISIONS
        )
        display(
            HTML(
                f"<details><summary>{esc(sample_id or parent['case'])}: {esc(parent['case'])} / {esc(group['mode'])} / {esc(group['configuration'])}</summary>"
                + body
                + "</details>"
            )
        )

    def step_7f_complete_parents_and_ordered_children_on_the_frozen_samples(self):
        """7f. Complete parents and ordered children on the frozen samples."""
        self.GALLERY_PARENT_CASES = {
            "normal_article": "unit-61",
            "short_neighbors": "chapter-zut-1",
            "nested_structure": "chapter-zut-3",
            "long_article": "unit-2779",
            "additional_provision": "unit-2052",
            "transitional_provision": "unit-2159",
            "annex": "unit-2848",
            "long_paragraph": "unclassified-25688",
            "publication_history": "unclassified-54",
            "eu_article": "unit-25783",
            "unclassified_heading": "unclassified-2051",
            "weak_structure": "unclassified-28934",
        }
        for self.sample in self.BASELINE_SAMPLES:
            self.case = self.GALLERY_PARENT_CASES[self.sample["sample_id"]]
            self.mode = (
                "fixed_inside_each_contained_unit"
                if self.PC_PARENT_BY_CASE[self.case]["family"] == "section_or_chapter"
                else "fixed_inside_parent"
            )
            self.show_parent_child_set(
                self.PC_GROUP_BY_KEY[self.case, self.mode, self.GALLERY_CONFIGURATION][
                    "id"
                ],
                self.sample["sample_id"],
            )
        self.show_parent_child_set(
            self.PC_GROUP_BY_KEY[
                "section-zut-3-1", "whole_contained_units", "uncapped-structural-units"
            ]["id"],
            "nested_structure",
        )

    def resolve_child_parent(self, child_id, relationship_set_id=None):
        self.ensure_pc_current()
        require(
            relationship_set_id in self.PC_GROUPS,
            "Choose a valid relationship-set ID; a shared child can have multiple experimental parents.",
        )
        require(child_id in self.PC_CHILDREN, "Unknown child ID.")
        group = self.PC_GROUPS[relationship_set_id]
        matches = [
            self.PC_LINKS[rid]
            for rid in group["relationship_ids"]
            if self.PC_LINKS[rid]["child_id"] == child_id
        ]
        require(
            len(matches) == 1,
            "Child is not uniquely linked in the selected relationship set.",
        )
        link = matches[0]
        parent, child = (self.PC_PARENTS[link["parent_id"]], self.PC_CHILDREN[child_id])
        require(
            parent["document_id"] == child["document_id"]
            and parent["start"] <= child["start"] < child["end"] <= parent["end"],
            "Linked child is not contained in its parent.",
        )
        return (parent, child, link)

    def step_7g_manual_child_parent_resolution_no_search(self):
        """7g. Manual child → parent resolution (no search)."""
        self.MANUAL_RELATIONSHIP_SET = self.PC_GROUP_BY_KEY[
            "unit-2779", "fixed_inside_parent", self.GALLERY_CONFIGURATION
        ]["id"]
        self.MANUAL_CHILD_ID = self.PC_LINKS[
            self.PC_GROUPS[self.MANUAL_RELATIONSHIP_SET]["relationship_ids"][0]
        ]["child_id"]
        self.manual_parent, self.manual_child, self.manual_link = (
            self.resolve_child_parent(
                self.MANUAL_CHILD_ID, self.MANUAL_RELATIONSHIP_SET
            )
        )
        show_table(
            [
                {
                    "relationship_set_id": self.MANUAL_RELATIONSHIP_SET,
                    "selected_child_id": self.MANUAL_CHILD_ID,
                    "resolved_parent_id": self.manual_parent["id"],
                    "relationship_id": self.manual_link["id"],
                    **self.PC_LINK_DIAGNOSTICS[self.manual_link["id"]],
                }
            ]
        )
        self.manual_parent_display, self.manual_children_display = (
            self.relationship_display_records(self.MANUAL_RELATIONSHIP_SET)
        )
        self.manual_selected_display = next(
            (c for c in self.manual_children_display if c["id"] == self.MANUAL_CHILD_ID)
        )
        display(
            HTML(
                "<h4>Manually selected child</h4>"
                + self.span_card(
                    self.manual_selected_display,
                    reviewed_units=self.REVIEWED_PROVISIONS,
                )
                + "<h4>Resolved COMPLETE parent (no truncation)</h4>"
                + self.span_card(
                    self.manual_parent_display, reviewed_units=self.REVIEWED_PROVISIONS
                )
            )
        )

    def step_7h_same_child_article_vs_section_vs_chapter_context(self):
        """7h. Same child, Article vs Section vs Chapter context."""
        self.shared_group = self.PC_GROUP_BY_KEY[
            "unit-114", "fixed_inside_parent", self.GALLERY_CONFIGURATION
        ]
        self.SHARED_CHILD_ID = self.PC_LINKS[self.shared_group["relationship_ids"][0]][
            "child_id"
        ]
        self.SHARED_CHILD_CONTEXT_ROWS = []
        self.columns = []
        for self.case, self.mode in [
            ("unit-114", "fixed_inside_parent"),
            ("section-zut-3-1", "fixed_inside_each_contained_unit"),
            ("chapter-zut-3", "fixed_inside_each_contained_unit"),
        ]:
            self.group = self.PC_GROUP_BY_KEY[
                self.case, self.mode, self.GALLERY_CONFIGURATION
            ]
            self.parent, self.child, self.link = self.resolve_child_parent(
                self.SHARED_CHILD_ID, self.group["id"]
            )
            self.parent_view, self._ = self.relationship_display_records(
                self.group["id"]
            )
            self.SHARED_CHILD_CONTEXT_ROWS.append(
                {
                    "same_child_id": self.child["id"],
                    "parent_case": self.case,
                    "parent_id": self.parent["id"],
                    "relationship_id": self.link["id"],
                    **self.PC_LINK_DIAGNOSTICS[self.link["id"]],
                }
            )
            self.columns.append(
                f"<div style='flex:1;min-width:320px'><h4>{esc(self.case)}</h4>"
                + self.span_card(
                    self.parent_view, reviewed_units=self.REVIEWED_PROVISIONS
                )
                + "</div>"
            )
        show_table(self.SHARED_CHILD_CONTEXT_ROWS)
        display(
            HTML(
                details_html(
                    "The identical complete child text in all three alternatives",
                    self.PC_CHILDREN[self.SHARED_CHILD_ID]["text"],
                )
            )
        )
        display(
            HTML(
                "<details><summary>Complete Article / Section / Chapter parents for the SAME child</summary>"
                + "<div style='display:flex;gap:12px;overflow:auto'>"
                + "".join(self.columns)
                + "</div></details>"
            )
        )
        print(
            "Observed: one identical source child resolves to parents of",
            [row["parent_characters"] for row in self.SHARED_CHILD_CONTEXT_ROWS],
            "characters.",
        )
        print(
            "Inspect expansion against the actual rules, conditions, and neighboring provisions. Character ratios do not measure usefulness."
        )
        print(
            "Whole-unit controls keep long children; short unclassified parents can yield a single equal-size child. No fallback policy is applied."
        )

    def step_7i_validate_relationship_failures_identity_and_reproducibility(self):
        """7i. Validate relationship failures, identity, and reproducibility."""
        expect_value_error(
            lambda: self.resolve_child_parent(self.MANUAL_CHILD_ID),
            "relationship-set ID",
        )
        expect_value_error(
            lambda: self.resolve_child_parent(
                "unknown-child", self.MANUAL_RELATIONSHIP_SET
            ),
            "Unknown child",
        )
        self.wrong_group = next(
            (
                g
                for g in self.PC_GROUPS.values()
                if self.MANUAL_CHILD_ID
                not in [self.PC_LINKS[rid]["child_id"] for rid in g["relationship_ids"]]
            )
        )
        expect_value_error(
            lambda: self.resolve_child_parent(
                self.MANUAL_CHILD_ID, self.wrong_group["id"]
            ),
            "not uniquely linked",
        )
        self.test_group = self.PC_GROUPS[self.MANUAL_RELATIONSHIP_SET]
        self.first_link_id = self.test_group["relationship_ids"][0]
        self.first_link = self.PC_LINKS[self.first_link_id]
        self.first_child = self.PC_CHILDREN[self.first_link["child_id"]]
        self.parent = self.PC_PARENTS[self.test_group["parent_id"]]
        expect_value_error(
            lambda: validate_relationship_group(
                self.test_group,
                self.PC_PARENTS,
                self.PC_CHILDREN,
                {
                    **self.PC_LINKS,
                    self.first_link_id: {
                        **self.first_link,
                        "parent_id": "wrong-parent",
                    },
                },
            ),
            "wrong set/parent",
        )
        expect_value_error(
            lambda: validate_relationship_group(
                self.test_group,
                self.PC_PARENTS,
                {
                    **self.PC_CHILDREN,
                    self.first_child["id"]: {
                        **self.first_child,
                        "start": self.parent["start"] - 1,
                    },
                },
                self.PC_LINKS,
            ),
            "fully contained",
        )
        expect_value_error(
            lambda: validate_relationship_group(
                self.test_group,
                self.PC_PARENTS,
                {
                    **self.PC_CHILDREN,
                    self.first_child["id"]: {
                        **self.first_child,
                        "document_id": "another-document",
                    },
                },
                self.PC_LINKS,
            ),
            "crosses documents",
        )
        expect_value_error(
            lambda: validate_relationship_group(
                self.test_group,
                self.PC_PARENTS,
                self.PC_CHILDREN,
                {
                    **self.PC_LINKS,
                    self.first_link_id: {
                        **self.first_link,
                        "child_id": self.parent["id"],
                    },
                },
            ),
            "Self-link",
        )
        expect_value_error(
            lambda: validate_relationship_group(
                {
                    **self.test_group,
                    "relationship_ids": self.test_group["relationship_ids"][:-1],
                },
                self.PC_PARENTS,
                self.PC_CHILDREN,
                self.PC_LINKS,
            ),
            "reconstruct complete parent",
        )
        self.correct_pc_context = self.PC_GENERATION_CONTEXT
        try:
            self.PC_GENERATION_CONTEXT = {
                **self.correct_pc_context,
                "structural_result": "stale",
            }
            expect_value_error(self.ensure_pc_current, "generation context is stale")
        finally:
            self.PC_GENERATION_CONTEXT = self.correct_pc_context
        require(
            len(self.PC_GROUPS)
            == sum(
                (
                    10 if p["family"] == "section_or_chapter" else 9
                    for p in self.PC_PARENTS.values()
                )
            ),
            "Missing parent/mode/configuration relationship sets.",
        )
        require(
            all((r["coverage_pct"] == 100 for r in self.PC_GROUP_DIAGNOSTICS)),
            "Parent coverage diagnostics failed.",
        )
        require(
            any(
                (
                    r["child_size_max"] > 4000
                    for r in self.PC_GROUP_DIAGNOSTICS
                    if r["mode"] == "whole_contained_units"
                )
            ),
            "Whole-unit children unexpectedly size-capped.",
        )
        require(
            any((r["one_child_equals_parent"] for r in self.PC_GROUP_DIAGNOSTICS)),
            "Short-parent equality case is missing.",
        )
        require(
            len({r["same_child_id"] for r in self.SHARED_CHILD_CONTEXT_ROWS}) == 1
            and len({r["parent_id"] for r in self.SHARED_CHILD_CONTEXT_ROWS}) == 3,
            "Shared-child parent-choice comparison is invalid.",
        )
        require(
            fingerprint(self.build_parent_child_experiment())
            == self.PC_DATA_FINGERPRINT
            == fingerprint(self.PC_DATA),
            "Parent-child IDs, source spans, or links changed on rerun.",
        )
        require(
            fingerprint(self.STRUCTURAL_RESULTS) == self.APPROVED_STRUCTURAL_RESULT
            and self.structural_report_path.read_bytes() == self.STEP6_REPORT_BYTES,
            "Approved structural baseline/report changed.",
        )
        require(
            fingerprint(self.FIXED_RESULTS) == self.STEP5_RESULT_FINGERPRINT
            and self.report_path.read_bytes() == self.STEP7_FIXED_REPORT_BYTES,
            "Approved fixed baseline/report changed.",
        )
        require(
            self.APPROVED_MANIFEST_PATH.read_bytes() == self.approved_manifest_bytes,
            "Frozen samples changed.",
        )
        require(
            hashlib.sha256(self.ARTIFACT.read_bytes()).hexdigest()
            == self.artifact_sha256
            and fingerprint(self.corpus) == self.corpus_fingerprint_before,
            "Stage 1 source changed.",
        )
        print(
            "PASS: contained ordered children, complete parent reconstruction, exact mappings, deterministic links, safe lookup, and unchanged approved artifacts."
        )

    def step_7j_save_relationship_results_and_stop_after_step_7(self):
        """7j. Save relationship results and stop after Step 7."""
        self.PC_REPORT = {
            "report_version": 1,
            "scope": "Step 7 only; parent-child relationship alternatives",
            "run_id": self.PC_RUN_ID,
            "spec": self.PC_SPEC,
            "data_fingerprint": self.PC_DATA_FINGERPRINT,
            "parents": {
                pid: {k: v for k, v in p.items() if k != "text"}
                for pid, p in self.PC_PARENTS.items()
            },
            "children": {
                cid: {k: v for k, v in c.items() if k != "text"}
                for cid, c in self.PC_CHILDREN.items()
            },
            "relationship_sets": self.PC_GROUPS,
            "relationships": self.PC_LINKS,
            "group_diagnostics": self.PC_GROUP_DIAGNOSTICS,
            "relationship_diagnostics": self.PC_LINK_DIAGNOSTICS,
            "sample_coverage": self.PC_SAMPLE_COVERAGE,
            "identical_child_comparisons": self.IDENTICAL_CHILD_COMPARISONS,
            "shared_child_parent_contexts": self.SHARED_CHILD_CONTEXT_ROWS,
            "validation": "PASS: source fidelity, containment, order, full coverage, explicit lookup, stable IDs, immutable baselines",
            "decision": "No final parent policy or chunking strategy selected; waiting for Step 7 review",
        }
        self.pc_report_path = (
            self.OUTPUT_DIR / f"parent_child_report.{fingerprint(self.PC_REPORT)}.json"
        )
        self.pc_report_bytes = (canonical(self.PC_REPORT) + "\n").encode("utf-8")
        if self.pc_report_path.exists():
            require(
                self.pc_report_path.read_bytes() == self.pc_report_bytes,
                "Existing parent-child report differs.",
            )
        else:
            self.pc_report_path.write_bytes(self.pc_report_bytes)
        require(
            json.loads(self.pc_report_path.read_text(encoding="utf-8"))
            == self.PC_REPORT,
            "Parent-child report round-trip failed.",
        )
        print("Parent-child report:", self.pc_report_path.relative_to(self.ROOT))
        print(
            "STOP AFTER STEP 7 — relationship alternatives ready for review; no final parent policy selected."
        )
