"""Chunking: fixed."""

import hashlib
import json
import math
from property_copilot._display import HTML, display
from .primitives import (
    canonical,
    details_html,
    esc,
    expect_value_error,
    fingerprint,
    fixed_length_windows,
    highlight_html,
    intersection_length,
    interval_union_length,
    length_summary,
    offsets,
    require,
    show_json,
    show_table,
    table_html,
)


class FixedSteps:
    """Fixed steps; state belongs to the workflow instance."""

    def step_5a_load_the_approved_manifest_and_lock_the_experiment_inputs(self):
        """5a. Load the approved manifest and lock the experiment inputs."""
        self.APPROVED_SETUP_ID = (
            "9282d70912c3c61977502ae88016482ba790e93f324da78806d12d3bfdda7043"
        )
        self.APPROVED_MANIFEST_PATH = (
            self.OUTPUT_DIR / f"sample_manifest.{self.APPROVED_SETUP_ID}.json"
        )
        require(
            self.APPROVED_MANIFEST_PATH.is_file(),
            "Approved Stage 2 manifest is missing; restore the frozen setup first.",
        )
        self.approved_manifest_bytes = self.APPROVED_MANIFEST_PATH.read_bytes()
        self.APPROVED_MANIFEST = json.loads(self.approved_manifest_bytes)
        require(
            fingerprint(self.APPROVED_MANIFEST)
            == self.APPROVED_SETUP_ID
            == self.SETUP_ID,
            "Setup changed since approval. Review the new sample manifest before running Step 5.",
        )
        require(
            canonical(self.APPROVED_MANIFEST) == self.FROZEN_MANIFEST_JSON,
            "In-memory setup differs from approved manifest.",
        )
        require(
            self.APPROVED_MANIFEST["artifact_sha256"] == self.artifact_sha256,
            "Manifest points to another Stage 1 artifact.",
        )
        self.SETUP_APPROVAL = {
            "setup_id": self.APPROVED_SETUP_ID,
            "scope": "Steps 1–4 approved; Step 5 only authorized",
            "legal_validity": "not assessed",
        }
        self.BASELINE_DOCUMENT_IDS = tuple(
            (
                d["document_id"]
                for d in self.APPROVED_MANIFEST["complete_document_inputs"]
            )
        )
        self.BASELINE_SAMPLES = self.APPROVED_MANIFEST["samples"]
        for self.entry in self.APPROVED_MANIFEST["complete_document_inputs"]:
            self.view = self.VIEWS[self.entry["document_id"]]
            require(
                len(self.view["text"]) == self.entry["characters"]
                and self.view["block_ids"] == self.entry["block_ids"],
                "Complete-document input differs from the frozen manifest.",
            )
            require(
                hashlib.sha256(self.view["text"].encode("utf-8")).hexdigest()
                == self.entry["text_sha256"],
                "Complete-document text hash mismatch.",
            )
        self.CONFIGURATIONS = [
            {
                "id": f"chars-{length}-overlap-{percent}pct",
                "length": length,
                "overlap_percent": percent,
                "overlap_characters": length * percent // 100,
                "stride": length - length * percent // 100,
            }
            for length in (1000, 2000, 4000)
            for percent in (0, 10, 20)
        ]
        self.CONFIGURATIONS_JSON = canonical(self.CONFIGURATIONS)
        self.CONFIG_BY_ID = {c["id"]: c for c in self.CONFIGURATIONS}
        self.BASELINE_SPEC = {
            "setup_id": self.SETUP_ID,
            "algorithm": "strict_character_windows_v1",
            "configurations": self.CONFIGURATIONS,
            "boundary_policy": "start at document zero; stop on first window reaching document end",
        }
        self.BASELINE_ID = fingerprint(self.BASELINE_SPEC)
        print("Fixed-length experiment:", self.BASELINE_ID)
        print(
            "Frozen scope:",
            len(self.BASELINE_DOCUMENT_IDS),
            "complete documents;",
            len(self.BASELINE_SAMPLES),
            "inspection samples",
        )
        show_table(self.CONFIGURATIONS)
        show_table(
            self.APPROVED_MANIFEST["complete_document_inputs"],
            ["ordinal", "characters", "text_sha256"],
        )

    def step_5b_strict_splitter_and_independent_boundary_checks(self):
        """5b. Strict splitter and independent boundary checks."""
        require(offsets("", 4, 1) == [], "Empty text must produce no chunks.")
        require(
            offsets("АБВГ", 4, 1) == [(0, 4)],
            "Exact-size input must not create a duplicate tail.",
        )
        require(
            offsets("АБВГД", 4, 0) == [(0, 4), (4, 5)],
            "One-character final chunk lost.",
        )
        require(
            offsets("АБВГД", 4, 1) == [(0, 4), (3, 5)],
            "Overlapped final chunk is wrong.",
        )
        require(
            offsets("АБВГД", 4, 3) == [(0, 4), (1, 5)],
            "High overlap failed to terminate.",
        )
        require(
            offsets("Чл. 1.\nдългадума § 2.", 7, 2)
            == [(0, 7), (5, 12), (10, 17), (15, 21)],
            "Whitespace/labels changed strict offsets.",
        )
        self.fixture = "Чл. 2а.\n(Изм. - ДВ) дългадума"
        require(
            offsets(self.fixture, 9, 2) == offsets("Ж" * len(self.fixture), 9, 2),
            "Content affected fixed boundaries.",
        )
        require(
            fixed_length_windows("дългадума", 4, 0)[0]["text"] == "дълг",
            "Splitter adjusted a word boundary.",
        )
        for self.length, self.overlap in (
            (0, 0),
            (-1, 0),
            (4, -1),
            (4, 4),
            (4, 5),
            (True, 0),
            (4, 1.5),
        ):
            expect_value_error(
                lambda length=self.length, overlap=self.overlap: fixed_length_windows(
                    "x", length, overlap
                ),
                "Length"
                if type(self.length) is not int or self.length <= 0
                else "Overlap",
            )
        print(
            "PASS: strict splitter fixtures; boundaries depend only on character count and numeric settings."
        )

    def baseline_chunk_id(self, config_id, document_id, start, end):
        return "fixed:" + fingerprint(
            [self.BASELINE_ID, config_id, document_id, start, end]
        )

    def build_fixed_baseline(self):
        result = {}
        for config in self.CONFIGURATIONS:
            result[config["id"]] = {}
            for did in self.BASELINE_DOCUMENT_IDS:
                windows = fixed_length_windows(
                    self.VIEWS[did]["text"],
                    config["length"],
                    config["overlap_characters"],
                )
                result[config["id"]][did] = [
                    {
                        **window,
                        "id": self.baseline_chunk_id(
                            config["id"], did, window["start"], window["end"]
                        ),
                        "ordinal": ordinal,
                        "document_id": did,
                        "configuration": config["id"],
                        "setup_id": self.SETUP_ID,
                        "baseline_id": self.BASELINE_ID,
                        "record_kind": "strict fixed-length character chunk",
                    }
                    for ordinal, window in enumerate(windows, 1)
                ]
        return result

    def validate_fixed_baseline(self, results):
        require(
            set(results) == set(self.CONFIG_BY_ID),
            "Missing/extra baseline configurations.",
        )
        all_ids = set()
        for config in self.CONFIGURATIONS:
            require(
                set(results[config["id"]]) == set(self.BASELINE_DOCUMENT_IDS),
                "Wrong document population.",
            )
            for did, records in results[config["id"]].items():
                source = self.VIEWS[did]["text"]
                expected_count = (
                    0
                    if not source
                    else 1
                    + max(
                        0,
                        math.ceil((len(source) - config["length"]) / config["stride"]),
                    )
                )
                require(
                    len(records) == expected_count,
                    "Unexpected chunk count or redundant tail.",
                )
                rebuilt, covered_end = ([], 0)
                for index, record in enumerate(records):
                    self.check_display_record(record)
                    lo, hi = (record["start"], record["end"])
                    require(
                        record["ordinal"] == index + 1
                        and record["document_id"] == did
                        and (record["configuration"] == config["id"])
                        and (record["baseline_id"] == self.BASELINE_ID),
                        "Chunk identity/configuration mismatch.",
                    )
                    require(
                        lo == index * config["stride"]
                        and hi == min(lo + config["length"], len(source)),
                        "A boundary deviated from strict arithmetic.",
                    )
                    require(
                        record["id"]
                        == self.baseline_chunk_id(config["id"], did, lo, hi),
                        "Unstable chunk ID.",
                    )
                    require(record["id"] not in all_ids, "Duplicate chunk ID.")
                    all_ids.add(record["id"])
                    require(
                        record["text"]
                        == source[lo:hi]
                        == self.reconstruct(self.source_map(did, lo, hi)),
                        "Chunk text or source mapping differs from source.",
                    )
                    require(
                        lo <= covered_end and hi > covered_end,
                        "Gap or wholly redundant chunk.",
                    )
                    if index:
                        previous = records[index - 1]
                        require(
                            previous["end"] - lo == config["overlap_characters"],
                            "Actual overlap differs from configured overlap.",
                        )
                        require(
                            previous["text"][-config["overlap_characters"] :]
                            == record["text"][: config["overlap_characters"]]
                            if config["overlap_characters"]
                            else True,
                            "Overlap text does not match.",
                        )
                    rebuilt.append(record["text"][covered_end - lo :])
                    covered_end = hi
                require(
                    covered_end == len(source) and "".join(rebuilt) == source,
                    "Complete-document reconstruction failed.",
                )
        return len(all_ids)

    def step_5c_generate_all_nine_baselines_on_complete_document_inputs(self):
        """5c. Generate all nine baselines on complete-document inputs."""
        self.FIXED_RESULTS = self.build_fixed_baseline()
        self.fixed_chunk_count = self.validate_fixed_baseline(self.FIXED_RESULTS)
        self.FIXED_RESULTS_FINGERPRINT = fingerprint(self.FIXED_RESULTS)
        print(
            "PASS:",
            self.fixed_chunk_count,
            "configuration-specific chunks; complete coverage and exact mappings for all nine runs.",
        )

    def step_5d_evaluation_only_provision_ledger_never_used_by_the_splitter(self):
        """5d. Evaluation-only provision ledger — never used by the splitter."""
        self.PROVISION_SPECS = [
            ("normal_article", "Article", "Чл. 1.", 61, 62),
            ("short_neighbors", "Article", "Чл. 2.", 63, 63),
            ("short_neighbors", "Article", "Чл. 2а.", 64, 65),
            ("nested_structure", "Article", "Чл. 10.", 114, 116),
            ("long_article", "Article", "Чл. 7.", 2779, 2810),
            ("additional_provision", "§ provision", "§ 1.", 2052, 2055),
            ("transitional_provision", "§ provision", "§ 6.", 2159, 2166),
            ("annex", "Annex", "Приложение № 1", 2848, 2893),
            ("eu_article", "Article", "Член 1", 25783, 25785),
        ]
        self.SAMPLE_BY_ID = {s["sample_id"]: s for s in self.BASELINE_SAMPLES}
        self.REVIEWED_PROVISIONS = []
        for (
            self.sample_id,
            self.kind,
            self.label,
            self.first,
            self.last,
        ) in self.PROVISION_SPECS:
            self.sample = self.SAMPLE_BY_ID[self.sample_id]
            self.did, self.lo, self._ = self.BLOCK_SPANS[
                self.BY_POSITION[self.first]["id"]
            ]
            self.end_did, self._, self.hi = self.BLOCK_SPANS[
                self.BY_POSITION[self.last]["id"]
            ]
            require(
                self.did == self.end_did == self.sample["document_id"]
                and self.sample["start"] <= self.lo < self.hi <= self.sample["end"],
                "Diagnostic provision falls outside its approved sample.",
            )
            require(
                self.BY_POSITION[self.first]["raw_text"].startswith(self.label),
                "Diagnostic label changed.",
            )
            self.REVIEWED_PROVISIONS.append(
                {
                    "id": f"source-unit:{self.first}:{self.last}",
                    "kind": self.kind,
                    "label": self.label,
                    "sample_id": self.sample_id,
                    "document_id": self.did,
                    "start": self.lo,
                    "end": self.hi,
                    "setup_id": self.SETUP_ID,
                    "first_position": self.first,
                    "last_position": self.last,
                    "review_status": "reviewed",
                    "review_scope": "Explicit source-boundary inspection only; not legal validity or a corpus-wide segmentation",
                }
            )
        show_table(
            self.REVIEWED_PROVISIONS,
            ["id", "kind", "label", "sample_id", "first_position", "last_position"],
        )

    def paragraph_cuts(self, record):
        mapped = self.source_map(record["document_id"], record["start"], record["end"])
        return sorted(
            {
                r["block_id"]
                for r in mapped
                if r["kind"] == "source"
                and (
                    r["block_start"] > 0
                    or r["block_end"] < len(self.BLOCKS[r["block_id"]]["raw_text"])
                )
            }
        )

    def legal_diagnostic(self, record):
        lo, hi, did = (record["start"], record["end"], record["document_id"])
        touched = [
            u
            for u in self.REVIEWED_PROVISIONS
            if u["document_id"] == did
            and intersection_length((lo, hi), (u["start"], u["end"]))
        ]
        return {
            "touched": [u["id"] for u in touched],
            "cut": [
                u["id"]
                for u in touched
                if u["start"] < lo < u["end"] or u["start"] < hi < u["end"]
            ],
            "contained": [
                u["id"] for u in touched if lo <= u["start"] and u["end"] <= hi
            ],
        }

    def step_5e_corpus_level_and_sample_level_diagnostics(self):
        """5e. Corpus-level and sample-level diagnostics."""
        self.CHUNK_DIAGNOSTICS = {
            r["id"]: {
                "paragraphs_cut": self.paragraph_cuts(r),
                **self.legal_diagnostic(r),
            }
            for docs in self.FIXED_RESULTS.values()
            for records in docs.values()
            for r in records
        }
        self.CORPUS_DIAGNOSTICS, self.DOCUMENT_DIAGNOSTICS, self.SAMPLE_DIAGNOSTICS = (
            [],
            [],
            [],
        )
        for self.config in self.CONFIGURATIONS:
            self.config_id = self.config["id"]
            self.records = [
                r
                for did in self.BASELINE_DOCUMENT_IDS
                for r in self.FIXED_RESULTS[self.config_id][did]
            ]
            self.sizes = [r["end"] - r["start"] for r in self.records]
            self.unique = sum(
                (len(self.VIEWS[did]["text"]) for did in self.BASELINE_DOCUMENT_IDS)
            )
            self.actual_overlaps = [
                a["end"] - b["start"]
                for did in self.BASELINE_DOCUMENT_IDS
                for a, b in zip(
                    self.FIXED_RESULTS[self.config_id][did],
                    self.FIXED_RESULTS[self.config_id][did][1:],
                )
            ]
            self.corpus_row = {
                "configuration": self.config_id,
                "documents": len(self.BASELINE_DOCUMENT_IDS),
                "chunks": len(self.records),
                "size_min": min(self.sizes),
                "size_median": length_summary(self.sizes)["median_p50"],
                "size_max": max(self.sizes),
                "coverage_pct": 100.0,
                "extra_characters": sum(self.sizes) - self.unique,
                "extra_character_pct": round(
                    100 * (sum(self.sizes) - self.unique) / self.unique, 2
                ),
                "actual_overlap_min_max": [
                    min(self.actual_overlaps),
                    max(self.actual_overlaps),
                ],
                "paragraphs_cut": len(
                    {
                        bid
                        for r in self.records
                        for bid in self.CHUNK_DIAGNOSTICS[r["id"]]["paragraphs_cut"]
                    }
                ),
                "ledger_units_cut_of_9": len(
                    {
                        uid
                        for r in self.records
                        for uid in self.CHUNK_DIAGNOSTICS[r["id"]]["cut"]
                    }
                ),
                "ledger_units_contained_somewhere_of_9": len(
                    {
                        uid
                        for r in self.records
                        for uid in self.CHUNK_DIAGNOSTICS[r["id"]]["contained"]
                    }
                ),
                "chunks_combining_ledger_units": sum(
                    (
                        len(self.CHUNK_DIAGNOSTICS[r["id"]]["touched"]) > 1
                        for r in self.records
                    )
                ),
            }
            self.covered = sum(
                (
                    interval_union_length(
                        (
                            (r["start"], r["end"])
                            for r in self.FIXED_RESULTS[self.config_id][did]
                        )
                    )
                    for did in self.BASELINE_DOCUMENT_IDS
                )
            )
            require(self.covered == self.unique, "Corpus coverage is incomplete.")
            self.corpus_row["coverage_pct"] = round(100 * self.covered / self.unique, 2)
            self.CORPUS_DIAGNOSTICS.append(self.corpus_row)
            for self.did in self.BASELINE_DOCUMENT_IDS:
                self.doc_records = self.FIXED_RESULTS[self.config_id][self.did]
                self.DOCUMENT_DIAGNOSTICS.append(
                    {
                        "configuration": self.config_id,
                        "document": self.DOCUMENTS[self.did]["ordinal"],
                        "characters": len(self.VIEWS[self.did]["text"]),
                        "chunks": len(self.doc_records),
                        "last_chunk_characters": self.doc_records[-1]["end"]
                        - self.doc_records[-1]["start"],
                    }
                )
            for self.sample in self.BASELINE_SAMPLES:
                self.lo, self.hi = (self.sample["start"], self.sample["end"])
                self.hits = [
                    r
                    for r in self.FIXED_RESULTS[self.config_id][
                        self.sample["document_id"]
                    ]
                    if intersection_length((self.lo, self.hi), (r["start"], r["end"]))
                ]
                self.clipped = [
                    (max(self.lo, r["start"]), min(self.hi, r["end"]))
                    for r in self.hits
                ]
                self.covered = interval_union_length(self.clipped)
                require(
                    self.covered == self.hi - self.lo, "Sample is not fully covered."
                )
                self.sample_units = {
                    u["id"]
                    for u in self.REVIEWED_PROVISIONS
                    if u["document_id"] == self.sample["document_id"]
                    and intersection_length((self.lo, self.hi), (u["start"], u["end"]))
                }
                self.units_cut = {
                    uid
                    for r in self.hits
                    for uid in self.CHUNK_DIAGNOSTICS[r["id"]]["cut"]
                } & self.sample_units
                self.units_contained = {
                    uid
                    for r in self.hits
                    for uid in self.CHUNK_DIAGNOSTICS[r["id"]]["contained"]
                } & self.sample_units
                self.cut_paragraphs = {
                    bid
                    for r in self.hits
                    for bid in self.CHUNK_DIAGNOSTICS[r["id"]]["paragraphs_cut"]
                }
                self.internal_cuts = {
                    cut
                    for r in self.hits
                    for cut in (r["start"], r["end"])
                    if self.lo < cut < self.hi
                }
                self.cut_paragraphs = {
                    bid
                    for bid in self.cut_paragraphs
                    if any(
                        (
                            self.BLOCK_SPANS[bid][1] < c < self.BLOCK_SPANS[bid][2]
                            for c in self.internal_cuts
                        )
                    )
                }
                self.SAMPLE_DIAGNOSTICS.append(
                    {
                        "sample": self.sample["sample_id"],
                        "configuration": self.config_id,
                        "intersecting_chunks": len(self.hits),
                        "sample_coverage_pct": round(
                            100 * self.covered / (self.hi - self.lo), 2
                        ),
                        "extra_character_pct_in_sample": round(
                            100
                            * (sum((b - a for a, b in self.clipped)) - self.covered)
                            / self.covered,
                            2,
                        ),
                        "whole_sample_in_one_chunk": any(
                            (
                                r["start"] <= self.lo and self.hi <= r["end"]
                                for r in self.hits
                            )
                        ),
                        "internal_cut_points": len(self.internal_cuts),
                        "paragraphs_cut_inside_sample": len(self.cut_paragraphs),
                        "ledger_units_cut": len(self.units_cut)
                        if self.sample_units
                        else "unassessed",
                        "ledger_units_contained": len(self.units_contained)
                        if self.sample_units
                        else "unassessed",
                        "hit_chunks_combining_ledger_units": sum(
                            (
                                len(self.CHUNK_DIAGNOSTICS[r["id"]]["touched"]) > 1
                                for r in self.hits
                            )
                        ),
                        "outside_sample_characters": interval_union_length(
                            ((r["start"], r["end"]) for r in self.hits)
                        )
                        - self.covered,
                    }
                )
        print(
            "Experiment corpus characters:",
            sum((len(self.VIEWS[did]["text"]) for did in self.BASELINE_DOCUMENT_IDS)),
        )
        show_table(self.CORPUS_DIAGNOSTICS)
        display(
            HTML(
                "<details><summary>Per-document counts and tail sizes (36 rows)</summary>"
                + table_html(self.DOCUMENT_DIAGNOSTICS)
                + "</details>"
            )
        )
        for self.sample in self.BASELINE_SAMPLES:
            self.rows = [
                r
                for r in self.SAMPLE_DIAGNOSTICS
                if r["sample"] == self.sample["sample_id"]
            ]
            display(
                HTML(
                    f"<details><summary>{esc(self.sample['sample_id'])}: all nine configurations</summary>"
                    + table_html(self.rows)
                    + "</details>"
                )
            )

    def ensure_baseline_current(self):
        require(
            self.SETUP_ID == self.APPROVED_SETUP_ID
            and fingerprint(json.loads(self.FROZEN_MANIFEST_JSON))
            == self.APPROVED_SETUP_ID,
            "Frozen setup changed; rerun and review setup before using these results.",
        )
        require(
            canonical(self.CONFIGURATIONS) == self.CONFIGURATIONS_JSON
            and fingerprint(self.BASELINE_SPEC) == self.BASELINE_ID,
            "Configuration changed; rerun Step 5 generation and diagnostics.",
        )

    def show_fixed_sample(self, sample_id, config_id, max_cards=3):
        self.ensure_baseline_current()
        require(
            config_id in self.CONFIG_BY_ID and sample_id in self.SAMPLE_BY_ID,
            "Unknown sample/configuration.",
        )
        require(
            max_cards is None or (type(max_cards) is int and max_cards > 0),
            "max_cards must be positive or None.",
        )
        sample = self.SAMPLE_BY_ID[sample_id]
        lo, hi, did = (sample["start"], sample["end"], sample["document_id"])
        records = self.FIXED_RESULTS[config_id][did]
        hits = [
            r for r in records if intersection_length((lo, hi), (r["start"], r["end"]))
        ]
        cuts = sorted(
            {c for r in hits for c in (r["start"], r["end"]) if lo <= c <= hi}
        )
        overlap_ranges = [
            (b["start"], a["end"])
            for a, b in zip(records, records[1:])
            if b["start"] < a["end"] and b["start"] < hi and (a["end"] > lo)
        ]
        cut_rows = []
        for cut in cuts:
            paragraph = next(
                (
                    self.BLOCKS[r["block_id"]]["position"]
                    for r in self.source_map(
                        did, max(0, cut - 1), min(len(self.VIEWS[did]["text"]), cut + 1)
                    )
                    if r["kind"] == "source"
                    and self.BLOCK_SPANS[r["block_id"]][1]
                    < cut
                    < self.BLOCK_SPANS[r["block_id"]][2]
                ),
                None,
            )
            source = self.VIEWS[did]["text"]
            cut_rows.append(
                {
                    "offset": cut,
                    "left_context": source[max(0, cut - 45) : cut],
                    "right_context": source[cut : cut + 45],
                    "paragraph_cut_position": paragraph,
                    "inside_alphanumeric_run": 0 < cut < len(source)
                    and source[cut - 1].isalnum()
                    and source[cut].isalnum(),
                    "ledger_units_cut": [
                        u["id"]
                        for u in self.REVIEWED_PROVISIONS
                        if u["document_id"] == did and u["start"] < cut < u["end"]
                    ],
                }
            )
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
        body = f"<p>{len(hits)} intersecting chunks; showing {len(chosen)}; {len(hits) - len(chosen)} omitted. Use max_cards=None for all.</p>"
        body += "<details><summary>Complete sample with ALL intersecting chunk cuts/overlap</summary>"
        body += (
            highlight_html(
                self.VIEWS[did]["text"][lo:hi], lo, cuts, overlap_ranges, (lo, hi)
            )
            + "</details>"
        )
        body += (
            "<details><summary>Exact cut offsets and source context</summary>"
            + table_html(cut_rows)
            + "</details>"
        )
        for record in chosen:
            require(
                record["baseline_id"] == self.BASELINE_ID
                and record["text"]
                == self.VIEWS[did]["text"][record["start"] : record["end"]],
                "Stale chunk record.",
            )
            index = record["ordinal"] - 1
            neighbors = records[max(0, index - 1) : index + 2]
            body += self.span_card(record, sample, neighbors, self.REVIEWED_PROVISIONS)
            legal = self.CHUNK_DIAGNOSTICS[record["id"]]
            body += details_html(
                "Evaluation ledger: units touched / cut / fully contained (not exhaustive)",
                json.dumps(legal, ensure_ascii=False, indent=2),
            )
        display(
            HTML(
                f"<details><summary>{esc(sample_id)} — {esc(config_id)}</summary>{body}</details>"
            )
        )

    def step_5f_inspect_real_chunks_cut_points_overlap_and_source_maps(self):
        """5f. Inspect real chunks, cut points, overlap, and source maps."""
        self.GALLERY_CONFIGURATION = "chars-2000-overlap-10pct"
        for self.sample in self.BASELINE_SAMPLES:
            self.show_fixed_sample(
                self.sample["sample_id"], self.GALLERY_CONFIGURATION, max_cards=3
            )

    def step_5f_inspect_real_chunks_cut_points_overlap_and_source_maps_2(self):
        """5f. Inspect real chunks, cut points, overlap, and source maps."""
        self.INSPECT_SAMPLE = "short_neighbors"
        for self.config in self.CONFIGURATIONS:
            self.show_fixed_sample(self.INSPECT_SAMPLE, self.config["id"], max_cards=3)

    def step_5g_concrete_boundary_witnesses_and_interpretation(self):
        """5g. Concrete boundary witnesses and interpretation."""
        self.WITNESSES = []
        for self.config in self.CONFIGURATIONS:
            self.population = [
                r
                for did in self.BASELINE_DOCUMENT_IDS
                for r in self.FIXED_RESULTS[self.config["id"]][did]
                if any(
                    (
                        s["document_id"] == did
                        and intersection_length(
                            (s["start"], s["end"]), (r["start"], r["end"])
                        )
                        for s in self.BASELINE_SAMPLES
                    )
                )
            ]
            for self.phenomenon in (
                "paragraph cut",
                "provision cut",
                "multiple provisions combined",
            ):

                def matches(record):
                    d = self.CHUNK_DIAGNOSTICS[record["id"]]
                    return (
                        bool(d["paragraphs_cut"])
                        if self.phenomenon == "paragraph cut"
                        else bool(d["cut"])
                        if self.phenomenon == "provision cut"
                        else len(d["touched"]) > 1
                    )

                self.matches = matches
                self.witness = next(
                    (r for r in self.population if self.matches(r)), None
                )
                self.WITNESSES.append(
                    {
                        "configuration": self.config["id"],
                        "phenomenon": self.phenomenon,
                        "chunk_id": self.witness["id"] if self.witness else None,
                        "document": self.DOCUMENTS[self.witness["document_id"]][
                            "ordinal"
                        ]
                        if self.witness
                        else None,
                        "ordinal": self.witness["ordinal"] if self.witness else None,
                        "sample": next(
                            (
                                s["sample_id"]
                                for s in self.BASELINE_SAMPLES
                                if self.witness
                                and s["document_id"] == self.witness["document_id"]
                                and intersection_length(
                                    (s["start"], s["end"]),
                                    (self.witness["start"], self.witness["end"]),
                                )
                            )
                        )
                        if self.witness
                        else None,
                        "evidence": self.CHUNK_DIAGNOSTICS[self.witness["id"]]
                        if self.witness
                        else "No witness in annotated sample intersections",
                    }
                )
        show_table(
            self.WITNESSES,
            [
                "configuration",
                "phenomenon",
                "document",
                "ordinal",
                "sample",
                "chunk_id",
            ],
        )
        for self.phenomenon in ("provision cut", "multiple provisions combined"):
            self.witness = next(
                (
                    w
                    for w in self.WITNESSES
                    if w["phenomenon"] == self.phenomenon and w["chunk_id"]
                ),
                None,
            )
            if self.witness:
                self.did = self.DOC_BY_ORDINAL[self.witness["document"]]["document_id"]
                self.records = self.FIXED_RESULTS[self.witness["configuration"]][
                    self.did
                ]
                self.record = self.records[self.witness["ordinal"] - 1]
                display(
                    HTML(
                        f"<h4>Witness: {esc(self.phenomenon)}</h4>"
                        + self.span_card(
                            self.record,
                            self.SAMPLE_BY_ID[self.witness["sample"]],
                            self.records[
                                max(0, self.witness["ordinal"] - 2) : self.witness[
                                    "ordinal"
                                ]
                                + 1
                            ],
                            self.REVIEWED_PROVISIONS,
                        )
                    )
                )
                show_json(
                    "Witness diagnostics (source ledger only)", self.witness["evidence"]
                )
        print("Observed across the nine runs:")
        print("- Every configuration covers the same frozen document text completely.")
        print(
            "- Actual adjacent overlaps match each requested character overlap exactly."
        )
        print(
            "- Chunks with multiple ledger units:",
            [r["chunks_combining_ledger_units"] for r in self.CORPUS_DIAGNOSTICS],
        )
        print(
            "- Distinct ledger units cut (out of nine):",
            [r["ledger_units_cut_of_9"] for r in self.CORPUS_DIAGNOSTICS],
        )
        print(
            "- The long Article is",
            self.SAMPLE_BY_ID["long_article"]["characters"],
            "characters; none of the tested lengths can contain it in one chunk.",
        )
        print(
            "No configuration has been selected. Meaning preservation requires inspecting the actual text."
        )

    def step_5h_final_fidelity_checks_reproducible_report_and_approved_checkpoint(self):
        """5h. Final fidelity checks, reproducible report, and approved checkpoint."""
        self.ensure_baseline_current()
        require(
            interval_union_length([]) == 0
            and interval_union_length([(0, 4), (2, 6), (6, 7)]) == 7,
            "Overlap union calculation failed.",
        )
        require(
            interval_union_length([(0, 10), (2, 3), (12, 14)]) == 12,
            "Contained/disjoint interval union failed.",
        )
        require(
            len(self.CORPUS_DIAGNOSTICS) == 9
            and len(self.SAMPLE_DIAGNOSTICS) == 9 * len(self.BASELINE_SAMPLES),
            "Incomplete diagnostics grid.",
        )
        require(
            all(
                (
                    row["extra_characters"] == 0
                    for row in self.CORPUS_DIAGNOSTICS
                    if "overlap-0pct" in row["configuration"]
                )
            ),
            "Zero-overlap baseline unexpectedly duplicates characters.",
        )
        require(
            all((row["sample_coverage_pct"] == 100 for row in self.SAMPLE_DIAGNOSTICS)),
            "Sample coverage incomplete.",
        )
        require(
            all(
                (
                    row["ledger_units_contained"] == 0
                    for row in self.SAMPLE_DIAGNOSTICS
                    if row["sample"] == "long_article"
                )
            ),
            "Oversized Article reported as fully contained.",
        )
        for self.witness in self.WITNESSES:
            if not self.witness["chunk_id"]:
                continue
            self.records = self.FIXED_RESULTS[self.witness["configuration"]][
                self.DOC_BY_ORDINAL[self.witness["document"]]["document_id"]
            ]
            self.record = self.records[self.witness["ordinal"] - 1]
            self.shared = self.span_diagnostics(
                self.record,
                self.records[
                    max(0, self.witness["ordinal"] - 2) : self.witness["ordinal"] + 1
                ],
                self.REVIEWED_PROVISIONS,
            )
            self.local = self.CHUNK_DIAGNOSTICS[self.record["id"]]
            require(
                self.shared["reviewed_legal_units_cut (supplied ledger only)"]
                == self.local["cut"],
                "Display/report legal cuts disagree.",
            )
            require(
                self.shared["combines_reviewed_units (supplied ledger only)"]
                == (len(self.local["touched"]) > 1),
                "Combined-unit diagnostics disagree.",
            )
            require(
                self.shared["paragraph_positions_cut"]
                == sorted(
                    (
                        self.BLOCKS[bid]["position"]
                        for bid in self.local["paragraphs_cut"]
                    )
                ),
                "Display/report paragraph cuts disagree.",
            )
        require(
            fingerprint(self.build_fixed_baseline())
            == self.FIXED_RESULTS_FINGERPRINT
            == fingerprint(self.FIXED_RESULTS),
            "Baseline rerun changed IDs/text, or stored results were mutated.",
        )
        require(
            self.APPROVED_MANIFEST_PATH.read_bytes() == self.approved_manifest_bytes,
            "Approved sample manifest changed.",
        )
        require(
            hashlib.sha256(self.ARTIFACT.read_bytes()).hexdigest()
            == self.artifact_sha256
            and fingerprint(self.corpus) == self.corpus_fingerprint_before,
            "Stage 1 source changed.",
        )
        self.FIXED_REPORT = {
            "report_version": 1,
            "scope": "Step 5 only; four frozen complete-document inputs",
            "setup_approval": self.SETUP_APPROVAL,
            "baseline_spec": self.BASELINE_SPEC,
            "baseline_id": self.BASELINE_ID,
            "source_artifact_sha256": self.artifact_sha256,
            "result_fingerprint": self.FIXED_RESULTS_FINGERPRINT,
            "configuration_specific_chunk_count": self.fixed_chunk_count,
            "diagnostic_ledger": self.REVIEWED_PROVISIONS,
            "corpus_diagnostics": self.CORPUS_DIAGNOSTICS,
            "document_diagnostics": self.DOCUMENT_DIAGNOSTICS,
            "sample_diagnostics": self.SAMPLE_DIAGNOSTICS,
            "witnesses": self.WITNESSES,
            "validation": "PASS: strict arithmetic, exact reconstruction, complete coverage, overlap, IDs, metrics, immutable inputs",
            "decision": "No winner selected; waiting for Step 5 review",
        }
        self.report_path = (
            self.OUTPUT_DIR
            / f"fixed_length_report.{fingerprint(self.FIXED_REPORT)}.json"
        )
        self.report_bytes = (canonical(self.FIXED_REPORT) + "\n").encode("utf-8")
        if self.report_path.exists():
            require(
                self.report_path.read_bytes() == self.report_bytes,
                "Existing content-addressed report differs.",
            )
        else:
            self.report_path.write_bytes(self.report_bytes)
        require(
            json.loads(self.report_path.read_text(encoding="utf-8"))
            == self.FIXED_REPORT,
            "Report round-trip failed.",
        )
        print(
            "PASS: all Step 5 checks. Report:", self.report_path.relative_to(self.ROOT)
        )
        print(
            "Approved Step 5 baseline verified. Step 6 follows; no winning configuration selected."
        )
