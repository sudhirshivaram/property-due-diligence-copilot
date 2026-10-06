"""Chunking: history."""

from pathlib import Path
import hashlib
import json
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
    require,
    show_table,
    table_html,
)


class HistorySteps:
    """History steps; state belongs to the workflow instance."""

    def history_candidates(self, text):
        stack, pairs, unresolved = ([], [], [])
        for i, char in enumerate(text):
            if char == "(":
                stack.append(i)
            elif char == ")":
                if stack:
                    pairs.append((stack.pop(), i + 1))
                else:
                    unresolved.append(
                        {"offset": i, "reason": "unmatched closing parenthesis"}
                    )
        unresolved.extend(
            ({"offset": i, "reason": "unmatched opening parenthesis"} for i in stack)
        )
        candidates = [
            (a, b)
            for a, b in sorted(pairs)
            if self.H_CUE.search(text[a:b]) and self.H_DV.search(text[a:b])
        ]
        outer = [
            (a, b)
            for a, b in candidates
            if not any(
                (c <= a and b <= d and ((c, d) != (a, b)) for c, d in candidates)
            )
        ]
        return (outer, unresolved)

    def step_9_amendment_and_publication_history_investigation(self):
        """Step 9 — Amendment and publication-history investigation."""
        self.ensure_os_current()
        self.H_APPROVED_PATHS = [
            self.APPROVED_MANIFEST_PATH,
            self.report_path,
            self.structural_report_path,
            self.pc_report_path,
            self.os_report_path,
        ]
        self.H_APPROVED_BYTES = {str(p): p.read_bytes() for p in self.H_APPROVED_PATHS}
        self.H_SOURCE_FINGERPRINT = fingerprint(
            {did: self.VIEWS[did]["text"] for did in self.BASELINE_DOCUMENT_IDS}
        )
        self.H_BASELINE_FINGERPRINTS = [
            fingerprint(self.FIXED_RESULTS),
            fingerprint(self.STRUCTURAL_RESULTS),
            fingerprint(self.PC_DATA),
            self.OS_DATA_FINGERPRINT,
        ]
        self.H_SPEC = {
            "version": 1,
            "setup_id": self.SETUP_ID,
            "artifact_sha256": self.artifact_sha256,
            "source_fingerprint": self.H_SOURCE_FINGERPRINT,
            "fixed_run": self.BASELINE_ID,
            "structural_run": self.STRUCTURAL_ID,
            "reviewed_publication_positions": [56, 2739],
            "inline_rule": "balanced block-local parentheses with amendment cue and ДВ; outermost qualifying span",
            "scope_rule": "same-block adjacent excerpt and containing provisional structural unit; no legal attribution",
            "coverage_limit": "Bulgarian pattern candidates in four baseline documents; not exhaustive",
            "text_transformation": None,
            "legal_status_assertions": False,
        }
        self.H_RUN_ID = fingerprint(self.H_SPEC)
        self.H_CUE = re.compile(
            "(?i)(?:\\b(?:изм|доп|отм|обн|попр)\\.|\\bнов(?:а|о|и)?\\b)"
        )
        self.H_DV = re.compile("\\bДВ\\b", re.I)
        self.H_ANNOTATIONS, self.H_UNCERTAINTY = ([], [])
        for self.did in self.BASELINE_DOCUMENT_IDS:
            for self.bid in self.VIEWS[self.did]["block_ids"]:
                self.block = self.BLOCKS[self.bid]
                self.text = self.block["raw_text"]
                self._, self.origin, self._ = self.BLOCK_SPANS[self.bid]
                self.candidates, self.unresolved = self.history_candidates(self.text)
                self.reviewed_list = (
                    self.block["position"]
                    in self.H_SPEC["reviewed_publication_positions"]
                )
                self.spans = (
                    [(0, len(self.text))] if self.reviewed_list else self.candidates
                )
                for self.a, self.b in self.spans:
                    self.start, self.end = (self.origin + self.a, self.origin + self.b)
                    self.units = [
                        u
                        for u in self.STRUCTURAL_RESULTS[self.did]
                        if u["start"] <= self.start and self.end <= u["end"]
                    ]
                    self.annotation = {
                        "id": "history:"
                        + fingerprint(
                            [self.H_RUN_ID, self.did, self.bid, self.a, self.b]
                        ),
                        "document_id": self.did,
                        "block_id": self.bid,
                        "position": self.block["position"],
                        "block_start": self.a,
                        "block_end": self.b,
                        "start": self.start,
                        "end": self.end,
                        "verbatim_text": self.text[self.a : self.b],
                        "source_spans": self.source_map(self.did, self.start, self.end),
                        "kind": "document_publication_list"
                        if self.reviewed_list
                        else "inline_history_candidate",
                        "review_basis": "reviewed list block and surrounding title/provision context"
                        if self.reviewed_list
                        else "pattern candidate; requires manual review",
                        "proposed_scope": "document publication/amendment list"
                        if self.reviewed_list
                        else "nearby clause or provision; exact scope unresolved",
                        "containing_structural_unit_ids": [u["id"] for u in self.units],
                        "uncertainty": "Source placement is evidence only; attribution, completeness, effective dates and legal status are not verified.",
                    }
                    self.H_ANNOTATIONS.append(self.annotation)
                for self.match in self.H_DV.finditer(self.text):
                    if not any((a <= self.match.start() < b for a, b in self.spans)):
                        self.H_UNCERTAINTY.append(
                            {
                                "document_id": self.did,
                                "block_id": self.bid,
                                "position": self.block["position"],
                                "block_offset": self.match.start(),
                                "reason": "uncovered ДВ reference: citation, nonparenthesized history or missed candidate",
                                "context": self.text[
                                    max(0, self.match.start() - 70) : self.match.end()
                                    + 100
                                ],
                            }
                        )
                if self.H_DV.search(self.text):
                    self.H_UNCERTAINTY.extend(
                        (
                            {
                                "document_id": self.did,
                                "block_id": self.bid,
                                "position": self.block["position"],
                                "block_offset": r["offset"],
                                "reason": r["reason"],
                                "context": self.text[:180],
                            }
                            for r in self.unresolved
                        )
                    )
        self.H_ANNOTATIONS.sort(
            key=lambda a: (
                self.DOCUMENTS[a["document_id"]]["ordinal"],
                a["start"],
                a["end"],
            )
        )
        self.H_ANNOTATION_FINGERPRINT = fingerprint(self.H_ANNOTATIONS)
        self.H_BY_ID = {a["id"]: a for a in self.H_ANNOTATIONS}
        show_table(
            [
                {
                    "document": self.DOCUMENTS[did]["ordinal"],
                    "publication_lists": sum(
                        (
                            a["document_id"] == did
                            and a["kind"] == "document_publication_list"
                            for a in self.H_ANNOTATIONS
                        )
                    ),
                    "inline_candidates": sum(
                        (
                            a["document_id"] == did
                            and a["kind"] == "inline_history_candidate"
                            for a in self.H_ANNOTATIONS
                        )
                    ),
                    "uncertainty_entries": sum(
                        (a["document_id"] == did for a in self.H_UNCERTAINTY)
                    ),
                    "coverage": "No matches is not evidence of no history",
                }
                for did in self.BASELINE_DOCUMENT_IDS
            ]
        )
        show_table(
            [
                {
                    k: a[k]
                    for k in (
                        "id",
                        "position",
                        "block_start",
                        "block_end",
                        "kind",
                        "verbatim_text",
                        "proposed_scope",
                        "uncertainty",
                    )
                }
                for a in self.H_ANNOTATIONS
                if a["position"] in (56, 61, 64, 2739, 2779)
            ]
        )
        display(
            HTML(
                "<details><summary>Uncovered references and unresolved punctuation (all entries)</summary>"
                + table_html(self.H_UNCERTAINTY)
                + "</details>"
            )
        )

    def ensure_history_current(self):
        self.ensure_os_current()
        require(
            fingerprint(self.H_SPEC) == self.H_RUN_ID
            and fingerprint(self.H_ANNOTATIONS) == self.H_ANNOTATION_FINGERPRINT,
            "History configuration/annotations changed; rebuild Step 9 diagnostics.",
        )
        require(
            fingerprint(
                {did: self.VIEWS[did]["text"] for did in self.BASELINE_DOCUMENT_IDS}
            )
            == self.H_SOURCE_FINGERPRINT,
            "Source views changed; rebuild history experiment.",
        )

    def history_representation(self, record, annotated=False):
        text = self.VIEWS[record["document_id"]]["text"][
            record["start"] : record["end"]
        ]
        return {
            "text": text,
            "annotation_ids": [
                a["id"]
                for a in self.H_ANNOTATIONS
                if annotated
                and a["document_id"] == record["document_id"]
                and intersection_length(
                    (record["start"], record["end"]), (a["start"], a["end"])
                )
            ],
        }

    def show_history_block(self, position):
        self.ensure_history_current()
        block = self.BY_POSITION[position]
        did, start, end = self.BLOCK_SPANS[block["id"]]
        record = {"document_id": did, "start": start, "end": end}
        original = self.history_representation(record)
        annotated = self.history_representation(record, True)
        require(
            original["text"] == annotated["text"] == block["raw_text"],
            "Representation changed source.",
        )
        annotations = [self.H_BY_ID[aid] for aid in annotated["annotation_ids"]]
        left = "<h4>Original unchanged</h4>" + highlight_html(original["text"], start)
        right = "<h4>Original unchanged + annotation overlay</h4>" + highlight_html(
            annotated["text"],
            start,
            overlaps=[(a["start"], a["end"]) for a in annotations],
        )
        display(
            HTML(
                f"<h4>Source body position {position}</h4><div style='display:grid;grid-template-columns:1fr 1fr;gap:16px'>"
                + "<section>"
                + left
                + "</section><section>"
                + right
                + "</section></div>"
                + details_html(
                    "Separate annotation records — proposed scope, uncertainty and exact mappings",
                    json.dumps(annotations, ensure_ascii=False, indent=2),
                )
            )
        )

    def step_9a_original_versus_original_plus_annotations(self):
        """9a. Original versus original plus annotations."""
        for self.position in (56, 61, 64, 2739, 2779):
            self.show_history_block(self.position)

    def history_share(self, record):
        did, lo, hi = (record["document_id"], record["start"], record["end"])
        hits = [
            a
            for a in self.H_ANNOTATIONS
            if a["document_id"] == did
            and intersection_length((lo, hi), (a["start"], a["end"]))
        ]
        intervals = [(max(lo, a["start"]), min(hi, a["end"])) for a in hits]
        count = interval_union_length(intervals)
        return {
            "characters": hi - lo,
            "annotated_characters": count,
            "annotated_share_pct": round(100 * count / (hi - lo), 2)
            if hi > lo
            else None,
            "publication_list_characters": interval_union_length(
                [
                    (max(lo, a["start"]), min(hi, a["end"]))
                    for a in hits
                    if a["kind"] == "document_publication_list"
                ]
            ),
            "inline_candidate_characters": interval_union_length(
                [
                    (max(lo, a["start"]), min(hi, a["end"]))
                    for a in hits
                    if a["kind"] == "inline_history_candidate"
                ]
            ),
            "annotation_ids": [a["id"] for a in hits],
            "annotations_cut": [
                a["id"] for a in hits if lo > a["start"] or hi < a["end"]
            ],
        }

    def step_9b_how_much_text_is_annotated(self):
        """9b. How much text is annotated?."""
        self.H_SAMPLE_SHARES = [
            {"sample_id": s["sample_id"], **self.history_share(s)}
            for s in self.BASELINE_SAMPLES
        ]
        self.H_UNIT_SHARES = []
        self.H_FIXED_SHARES = []
        for self.sample in self.BASELINE_SAMPLES:
            self.did = self.sample["document_id"]
            for self.unit in self.STRUCTURAL_RESULTS[self.did]:
                if intersection_length(
                    (self.sample["start"], self.sample["end"]),
                    (self.unit["start"], self.unit["end"]),
                ):
                    self.H_UNIT_SHARES.append(
                        {
                            "sample_id": self.sample["sample_id"],
                            "unit_id": self.unit["id"],
                            "unit_kind": self.unit["unit_kind"],
                            **self.history_share(self.unit),
                        }
                    )
            for self.setting in self.CONFIGURATIONS:
                for self.chunk in self.FIXED_RESULTS[self.setting["id"]][self.did]:
                    if intersection_length(
                        (self.sample["start"], self.sample["end"]),
                        (self.chunk["start"], self.chunk["end"]),
                    ):
                        self.H_FIXED_SHARES.append(
                            {
                                "sample_id": self.sample["sample_id"],
                                "configuration": self.setting["id"],
                                "chunk_id": self.chunk["id"],
                                **self.history_share(self.chunk),
                            }
                        )
        self.share_columns = [
            "sample_id",
            "characters",
            "annotated_characters",
            "annotated_share_pct",
            "publication_list_characters",
            "inline_candidate_characters",
        ]
        show_table(self.H_SAMPLE_SHARES, self.share_columns)
        show_table(
            self.H_UNIT_SHARES, ["sample_id", "unit_kind", *self.share_columns[1:]]
        )
        display(
            HTML(
                "<details><summary>Representative fixed-length chunks: shares and cut annotation IDs across all nine settings</summary>"
                + table_html(self.H_FIXED_SHARES)
                + "</details>"
            )
        )

    def step_9c_boundary_witnesses_split_note_versus_separated_nearby_text(self):
        """9c. Boundary witnesses: split note versus separated nearby text."""
        self.H_ANCHORS = {}
        for self.a in self.H_ANNOTATIONS:
            if self.a["kind"] != "inline_history_candidate":
                continue
            self.text = self.BLOCKS[self.a["block_id"]]["raw_text"]
            self.origin = self.a["start"] - self.a["block_start"]
            self.end_limit = min(
                [
                    other["block_start"]
                    for other in self.H_ANNOTATIONS
                    if other["block_id"] == self.a["block_id"]
                    and other["block_start"] >= self.a["block_end"]
                ]
                or [len(self.text)]
            )
            self.start = self.a["block_end"]
            while self.start < self.end_limit and self.text[self.start].isspace():
                self.start += 1
            self.end = min(self.start + 60, self.end_limit)
            if self.start < self.end:
                self.H_ANCHORS[self.a["id"]] = {
                    "start": self.origin + self.start,
                    "end": self.origin + self.end,
                    "verbatim_text": self.text[self.start : self.end],
                    "scope": "following same-block context proxy; legal attachment unverified",
                }
        self.H_WITNESSES = []
        for self.kind in ("document_publication_list", "inline_history_candidate"):
            for self.event in (
                ("annotation_cut",)
                if self.kind == "document_publication_list"
                else ("annotation_cut", "nearby_context_separated")
            ):
                self.found = None
                for self.setting in self.CONFIGURATIONS:
                    if self.found:
                        break
                    for self.a in self.H_ANNOTATIONS:
                        if self.a["kind"] != self.kind:
                            continue
                        self.chunks = self.FIXED_RESULTS[self.setting["id"]][
                            self.a["document_id"]
                        ]
                        self.anchor = self.H_ANCHORS.get(self.a["id"])
                        for self.chunk in self.chunks:
                            self.hit = intersection_length(
                                (self.chunk["start"], self.chunk["end"]),
                                (self.a["start"], self.a["end"]),
                            )
                            self.cut = 0 < self.hit < self.a["end"] - self.a["start"]
                            self.separated = (
                                self.hit == self.a["end"] - self.a["start"]
                                and self.anchor is not None
                                and (
                                    not (
                                        self.chunk["start"] <= self.anchor["start"]
                                        and self.anchor["end"] <= self.chunk["end"]
                                    )
                                )
                            )
                            if (
                                self.event == "annotation_cut"
                                and self.cut
                                or (
                                    self.event == "nearby_context_separated"
                                    and self.separated
                                )
                            ):
                                self.recovered = bool(
                                    self.anchor
                                    and any(
                                        (
                                            c["start"]
                                            <= min(
                                                self.a["start"], self.anchor["start"]
                                            )
                                            and max(self.a["end"], self.anchor["end"])
                                            <= c["end"]
                                            for c in self.chunks
                                        )
                                    )
                                )
                                self.found = {
                                    "kind": self.kind,
                                    "event": self.event,
                                    "configuration": self.setting["id"],
                                    "annotation_id": self.a["id"],
                                    "chunk_id": self.chunk["id"],
                                    "position": self.a["position"],
                                    "context_anchor": self.anchor,
                                    "another_chunk_contains_full_note_and_anchor": self.recovered,
                                }
                                break
                        if self.found:
                            break
                if self.found:
                    self.H_WITNESSES.append(self.found)
                else:
                    self.H_WITNESSES.append(
                        {
                            "kind": self.kind,
                            "event": self.event,
                            "status": "No witness found in current tested settings; not proof of absence elsewhere",
                        }
                    )
        show_table(self.H_WITNESSES)
        for self.witness in self.H_WITNESSES:
            if "chunk_id" not in self.witness:
                continue
            self.a = self.H_BY_ID[self.witness["annotation_id"]]
            self.chunks = self.FIXED_RESULTS[self.witness["configuration"]][
                self.a["document_id"]
            ]
            self.index = next(
                (
                    i
                    for i, c in enumerate(self.chunks)
                    if c["id"] == self.witness["chunk_id"]
                )
            )
            self.peers = self.chunks[max(0, self.index - 1) : self.index + 2]
            self.body = details_html(
                "Verbatim history note / list and uncertain scope",
                json.dumps(self.a, ensure_ascii=False, indent=2),
            )
            self.anchor = self.witness["context_anchor"]
            if self.anchor:
                self.body += details_html(
                    "Nearby source anchor — not verified legal scope",
                    json.dumps(self.anchor, ensure_ascii=False, indent=2),
                )
            for self.chunk in self.peers:
                self.body += self.span_card(
                    self.chunk,
                    neighbors=self.peers,
                    reviewed_units=self.REVIEWED_PROVISIONS,
                )
            for self.uid in self.a["containing_structural_unit_ids"]:
                self.body += (
                    "<details><summary>Complete unchanged structural context</summary>"
                    + self.span_card(
                        self.STRUCTURAL_BY_ID[self.uid],
                        reviewed_units=self.REVIEWED_PROVISIONS,
                    )
                    + "</details>"
                )
            display(
                HTML(
                    "<details><summary>"
                    + esc(
                        self.witness["event"]
                        + " / "
                        + self.witness["kind"]
                        + " / "
                        + self.witness["configuration"]
                    )
                    + "</summary>"
                    + self.body
                    + "</details>"
                )
            )

    def step_9d_future_policy_hypotheses_no_policy_implemented(self):
        """9d. Future policy hypotheses — no policy implemented."""
        self.positive = "Чл. 1. (Изм. - ДВ, бр. 65 от 2003 г.) Текст."
        self.pairs, self._ = self.history_candidates(self.positive)
        require(
            len(self.pairs) == 1
            and self.positive[self.pairs[0][0] : self.pairs[0][1]]
            == "(Изм. - ДВ, бр. 65 от 2003 г.)",
            "Inline-note detection failed.",
        )
        for self.text in (
            "",
            "(1) Текст",
            "(чл. 7, ал. 3)",
            "(2003 г.)",
            "(ДВ, бр. 65 от 2003 г.)",
        ):
            require(
                not self.history_candidates(self.text)[0],
                "Ordinary numbering/citation/date incorrectly asserted as history.",
            )
        self.nested = "(Изм. (уточнение) - ДВ, бр. 1)"
        require(
            self.history_candidates(self.nested)[0] == [(0, len(self.nested))],
            "Nested note boundaries changed.",
        )
        require(
            not self.history_candidates("(Изм. - ДВ, бр. 1")[0]
            and self.history_candidates("(Изм. - ДВ, бр. 1")[1],
            "Unclosed note silently accepted.",
        )
        require(
            len(self.history_candidates("(Нов - ДВ, бр. 1) (Доп. - ДВ, бр. 2)")[0])
            == 2,
            "Adjacent notes merged.",
        )
        require(
            len(self.H_BY_ID) == len(self.H_ANNOTATIONS), "Duplicate annotation IDs."
        )
        for self.a in self.H_ANNOTATIONS:
            self.block = self.BLOCKS[self.a["block_id"]]
            require(
                self.a["verbatim_text"]
                == self.block["raw_text"][self.a["block_start"] : self.a["block_end"]]
                == self.VIEWS[self.a["document_id"]]["text"][
                    self.a["start"] : self.a["end"]
                ]
                == self.reconstruct(self.a["source_spans"]),
                "Annotation source mismatch.",
            )
            require(
                self.a["id"]
                == "history:"
                + fingerprint(
                    [
                        self.H_RUN_ID,
                        self.a["document_id"],
                        self.a["block_id"],
                        self.a["block_start"],
                        self.a["block_end"],
                    ]
                ),
                "Annotation identity changed.",
            )
        for self.did in self.BASELINE_DOCUMENT_IDS:
            self.view = {
                "document_id": self.did,
                "start": 0,
                "end": len(self.VIEWS[self.did]["text"]),
            }
            require(
                self.history_representation(self.view)["text"]
                == self.history_representation(self.view, True)["text"]
                == self.VIEWS[self.did]["text"],
                "Representation changed legal text.",
            )
        for self.rows in (
            self.H_SAMPLE_SHARES,
            self.H_UNIT_SHARES,
            self.H_FIXED_SHARES,
        ):
            require(
                all(
                    (
                        0 <= r["annotated_characters"] <= r["characters"]
                        for r in self.rows
                    )
                ),
                "Share double counts characters.",
            )
        require(
            interval_union_length([(0, 4), (2, 6)]) == 6,
            "Union share accounting changed.",
        )
        require(
            all(
                (
                    Path(path).read_bytes() == data
                    for path, data in self.H_APPROVED_BYTES.items()
                )
            ),
            "Approved report or manifest changed.",
        )
        require(
            self.H_BASELINE_FINGERPRINTS
            == [
                fingerprint(self.FIXED_RESULTS),
                fingerprint(self.STRUCTURAL_RESULTS),
                fingerprint(self.PC_DATA),
                fingerprint(list(self.OS_GROUPS.values())),
            ],
            "Approved chunk results changed.",
        )
        require(
            hashlib.sha256(self.ARTIFACT.read_bytes()).hexdigest()
            == self.artifact_sha256
            and fingerprint(self.corpus) == self.corpus_fingerprint_before,
            "Stage 1 changed.",
        )
        self.old = self.H_SPEC["version"]
        try:
            self.H_SPEC["version"] = 999
            expect_value_error(
                self.ensure_history_current, "History configuration/annotations changed"
            )
        finally:
            self.H_SPEC["version"] = self.old
        self.ensure_history_current()
        print(
            "PASS:",
            len(self.H_ANNOTATIONS),
            "exact annotations; unchanged representations, source maps, IDs, union shares, candidate edge cases and approved artifacts.",
        )

    def step_9e_review_and_stop_after_step_9(self):
        """9e. Review and stop after Step 9."""
        self.ensure_history_current()
        self.H_REPORT = {
            "report_version": 1,
            "scope": "Step 9 only — non-destructive history investigation",
            "run_id": self.H_RUN_ID,
            "spec": self.H_SPEC,
            "annotation_fingerprint": self.H_ANNOTATION_FINGERPRINT,
            "annotations": self.H_ANNOTATIONS,
            "uncertainty_ledger": self.H_UNCERTAINTY,
            "sample_shares": self.H_SAMPLE_SHARES,
            "structural_unit_shares": self.H_UNIT_SHARES,
            "fixed_chunk_shares": self.H_FIXED_SHARES,
            "boundary_witnesses": self.H_WITNESSES,
            "validation": "PASS: unchanged original text, exact source mappings, union shares, deterministic annotation IDs",
            "decision": "No history policy selected; scope and legal interpretation require review",
        }
        self.history_report_path = (
            self.OUTPUT_DIR
            / f"history_annotation_report.{fingerprint(self.H_REPORT)}.json"
        )
        self.history_bytes = (canonical(self.H_REPORT) + "\n").encode("utf-8")
        if self.history_report_path.exists():
            require(
                self.history_report_path.read_bytes() == self.history_bytes,
                "History report differs.",
            )
        else:
            self.history_report_path.write_bytes(self.history_bytes)
        require(
            json.loads(self.history_report_path.read_text(encoding="utf-8"))
            == self.H_REPORT,
            "History report round trip failed.",
        )
        print(
            "History investigation report:",
            self.history_report_path.relative_to(self.ROOT),
        )
        print(
            "STOP AFTER STEP 9 — unchanged text and separate candidate annotations ready for review."
        )
