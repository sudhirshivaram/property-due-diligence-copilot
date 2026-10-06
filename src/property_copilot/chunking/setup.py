"""Chunking: setup."""

from collections import Counter
from bisect import bisect_right
import hashlib
import json
from property_copilot._display import HTML, display
from .primitives import (
    build_document_view,
    canonical,
    details_html,
    esc,
    expect_value_error,
    fingerprint,
    highlight_html,
    intersection_length,
    length_summary,
    require,
    show_json,
    show_table,
    table_html,
    validate_stage1,
)


class SetupSteps:
    """Setup steps; state belongs to the workflow instance."""

    def step_2_load_and_verify_the_stage_1_interface(self):
        """Step 2 — Load and verify the Stage 1 interface."""
        self.ARTIFACT = self.ROOT / "data/processed/01_parsed_docx_structure.json"
        self.EXPECTED_ARTIFACT_SHA256 = (
            "caa696a76ea403bf1ddf074aa503fd4362162d128e32a2c755570464bc95ebdc"
        )
        require(
            self.ARTIFACT.is_file(),
            "Run and validate Stage 1 first: the parsed artifact is missing.",
        )
        self.artifact_bytes = self.ARTIFACT.read_bytes()
        self.artifact_sha256 = hashlib.sha256(self.artifact_bytes).hexdigest()
        require(
            self.artifact_sha256 == self.EXPECTED_ARTIFACT_SHA256,
            "Stage 1 artifact changed. Review source identity and sample positions before updating the pin.",
        )
        try:
            self.corpus = json.loads(self.artifact_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Stage 1 artifact is not valid UTF-8 JSON.") from exc

    def step_2_load_and_verify_the_stage_1_interface_2(self):
        """Step 2 — Load and verify the Stage 1 interface."""
        self.validation = validate_stage1(self.corpus)
        self.corpus_fingerprint_before = fingerprint(self.corpus)
        self.DOCUMENTS = {d["document_id"]: d for d in self.corpus["documents"]}
        self.DOC_BY_ORDINAL = {d["ordinal"]: d for d in self.corpus["documents"]}
        self.BLOCKS = {b["id"]: b for b in self.corpus["blocks"]}
        self.BY_POSITION = {b["position"]: b for b in self.corpus["blocks"]}
        print(self.validation)
        print("Artifact SHA-256:", self.artifact_sha256)
        print("Original DOCX SHA-256 (stored):", self.corpus["source"]["sha256"])
        print(
            "Schema:",
            self.corpus["schema_version"],
            "| recorded Stage 1 result:",
            self.corpus["diagnostics"]["stage1_validation"]["result"],
        )

    def step_2a_inspect_the_inventory_and_preserved_evidence(self):
        """2a. Inspect the inventory and preserved evidence."""
        show_table(
            [
                {
                    "document": d["ordinal"],
                    "title": d["source_titles"]["title"]["raw_text"],
                    "full_text_blocks_including_delimiter": sum(
                        (
                            b["document_id"] == d["document_id"]
                            and b["region"] == "full_text"
                            for b in self.corpus["blocks"]
                        )
                    ),
                }
                for d in self.corpus["documents"]
            ]
        )
        show_table(
            [
                {"candidate_kind": k, "count": v}
                for k, v in self.corpus["diagnostics"][
                    "candidate_marker_counts"
                ].items()
            ]
        )
        show_table(self.corpus["diagnostics"]["warnings"])
        show_json(
            "Complete Document 1 descriptor: source values and evidence locations",
            self.DOC_BY_ORDINAL[1],
        )
        for self.position in (56, 57, 59, 61, 112, 2051, 2848, 25783):
            self.b = self.BY_POSITION[self.position]
            show_json(
                f"Block {self.position}: source text and unchanged Stage 1 annotations",
                {
                    k: self.b[k]
                    for k in (
                        "id",
                        "position",
                        "document_id",
                        "region",
                        "source",
                        "raw_text",
                        "structural_annotations",
                    )
                },
            )

    def source_map(self, document_id, start, end):
        view = self.VIEWS[document_id]
        require(
            isinstance(start, int)
            and isinstance(end, int)
            and (0 <= start <= end <= len(view["text"])),
            "Invalid document character span.",
        )
        if start == end:
            return []
        rows = []
        for seg in view["segments"][
            bisect_right(self.SEGMENT_ENDS[document_id], start) :
        ]:
            if seg["start"] >= end:
                break
            lo, hi = (max(start, seg["start"]), min(end, seg["end"]))
            if lo >= hi:
                continue
            if seg["kind"] == "source":
                b = self.BLOCKS[seg["block_id"]]
                rows.append(
                    {
                        "kind": "source",
                        "stream_start": lo,
                        "stream_end": hi,
                        "block_id": b["id"],
                        "position": b["position"],
                        "block_start": lo - seg["start"],
                        "block_end": hi - seg["start"],
                        "source": b["source"],
                    }
                )
            else:
                rows.append(
                    {
                        "kind": "separator",
                        "stream_start": lo,
                        "stream_end": hi,
                        "text": "\n",
                        "left_block_id": seg["left_block_id"],
                        "right_block_id": seg["right_block_id"],
                    }
                )
        return rows

    def reconstruct(self, mapped):
        return "".join(
            (
                self.BLOCKS[r["block_id"]]["raw_text"][
                    r["block_start"] : r["block_end"]
                ]
                if r["kind"] == "source"
                else r["text"]
                for r in mapped
            )
        )

    def step_2b_build_reversible_document_views_not_chunks(self):
        """2b. Build reversible document views — not chunks."""
        self.VIEWS = {
            did: build_document_view(d, self.corpus["blocks"])
            for did, d in self.DOCUMENTS.items()
        }
        self.BLOCK_SPANS = {
            seg["block_id"]: (did, seg["start"], seg["end"])
            for did, view in self.VIEWS.items()
            for seg in view["segments"]
            if seg["kind"] == "source"
        }
        self.SEGMENT_ENDS = {
            did: [seg["end"] for seg in view["segments"]]
            for did, view in self.VIEWS.items()
        }
        self.EXCLUDED_DELIMITERS = [
            {
                "document_id": did,
                "block_id": v["delimiter_block_id"],
                "text": self.BLOCKS[v["delimiter_block_id"]]["raw_text"],
                "reason": "Stage 1 evidence-linked standalone full-text delimiter",
            }
            for did, v in self.VIEWS.items()
        ]
        for self.did, self.view in self.VIEWS.items():
            require(
                self.reconstruct(self.source_map(self.did, 0, len(self.view["text"])))
                == self.view["text"],
                "Full-document reconstruction failed.",
            )
            for self.seg in self.view["segments"]:
                if self.seg["kind"] == "source":
                    require(
                        self.view["text"][self.seg["start"] : self.seg["end"]]
                        == self.BLOCKS[self.seg["block_id"]]["raw_text"],
                        "Source paragraph changed in view.",
                    )
            require(
                len(self.view["segments"])
                == max(0, 2 * len(self.view["block_ids"]) - 1),
                "Missing map entries.",
            )
        show_table(
            [
                {
                    "region": k,
                    "blocks": v,
                    "view_policy": "Retain all except evidence-linked delimiter"
                    if k == "full_text"
                    else "Retain in artifact only",
                }
                for k, v in Counter(
                    (b["region"] for b in self.corpus["blocks"])
                ).items()
            ]
        )
        show_table(
            [
                {
                    "document": self.DOCUMENTS[did]["ordinal"],
                    "characters": len(v["text"]),
                    "source_blocks": len(v["block_ids"]),
                    "added_newlines": max(0, len(v["block_ids"]) - 1),
                    "empty_blocks_preserved": sum(
                        (self.BLOCKS[bid]["raw_text"] == "" for bid in v["block_ids"])
                    ),
                }
                for did, v in self.VIEWS.items()
            ]
        )
        show_json(
            "Excluded delimiter ledger (only these full-text blocks are omitted)",
            self.EXCLUDED_DELIMITERS,
        )
        self.did, self.start, self._ = self.BLOCK_SPANS[self.BY_POSITION[61]["id"]]
        self.end = self.BLOCK_SPANS[self.BY_POSITION[63]["id"]][2]
        show_json(
            "Article boundary map: original blocks versus added newlines",
            self.source_map(self.did, self.start, self.end),
        )
        print(
            "PASS: every document view reconstructs exactly from source blocks plus documented separators."
        )

    def step_3_select_and_freeze_representative_content(self):
        """Step 3 — Select and freeze representative content."""
        self.paragraph_inventory = [
            {
                "document": self.DOCUMENTS[did]["ordinal"],
                "position": self.BLOCKS[bid]["position"],
                "characters": len(self.BLOCKS[bid]["raw_text"]),
                "preview": self.BLOCKS[bid]["raw_text"][:140],
            }
            for did, v in self.VIEWS.items()
            for bid in v["block_ids"]
        ]
        self.candidate_inventory = []
        for self.did, self.view in self.VIEWS.items():
            self.source_blocks = [self.BLOCKS[bid] for bid in self.view["block_ids"]]
            self.stops = [
                i
                for i, b in enumerate(self.source_blocks)
                if b["structural_annotations"]["legal_marker_candidates"]
                or b["structural_annotations"]["word_heading_level"] is not None
            ]
            for self.i, self.b in enumerate(self.source_blocks):
                self.markers = self.b["structural_annotations"][
                    "legal_marker_candidates"
                ]
                if not self.markers:
                    continue
                self.later = bisect_right(self.stops, self.i)
                self.next_index = (
                    self.stops[self.later]
                    if self.later < len(self.stops)
                    else len(self.source_blocks)
                )
                self.first, self.last = (
                    self.b,
                    self.source_blocks[self.next_index - 1],
                )
                self.lo, self.hi = (
                    self.BLOCK_SPANS[self.first["id"]][1],
                    self.BLOCK_SPANS[self.last["id"]][2],
                )
                for self.marker in self.markers:
                    self.candidate_inventory.append(
                        {
                            "document": self.DOCUMENTS[self.did]["ordinal"],
                            "kind": self.marker["kind"],
                            "label": self.marker["matched_label"],
                            "first_position": self.first["position"],
                            "last_position": self.last["position"],
                            "estimated_characters": self.hi - self.lo,
                            "status": "unreviewed marker-to-next-anchor estimate; not a chunk",
                        }
                    )
        show_table(
            [
                {
                    "inventory": "all source paragraphs",
                    **length_summary(
                        (r["characters"] for r in self.paragraph_inventory)
                    ),
                }
            ]
        )
        show_table(
            [
                {
                    "candidate_kind": kind,
                    **length_summary(
                        (
                            r["estimated_characters"]
                            for r in self.candidate_inventory
                            if r["kind"] == kind
                        )
                    ),
                }
                for kind in sorted({r["kind"] for r in self.candidate_inventory})
            ]
        )
        show_table(
            sorted(
                self.paragraph_inventory,
                key=lambda r: (-r["characters"], r["position"]),
            ),
            limit=8,
        )
        show_table(
            sorted(
                self.candidate_inventory,
                key=lambda r: (-r["estimated_characters"], r["first_position"]),
            ),
            limit=8,
        )

    def step_3b_explicit_source_window_selection(self):
        """3b. Explicit source-window selection."""
        self.SAMPLE_SPECS = [
            (
                "normal_article",
                1,
                61,
                62,
                "Чл. 1.",
                "Complete two-paragraph Article with inline amendment note.",
                "Check whether both paragraphs provide enough legal context; cross-references may need more.",
            ),
            (
                "short_neighbors",
                1,
                63,
                65,
                "Чл. 2.",
                "Short Article and Cyrillic-suffixed Чл. 2а expose merging and label risks.",
                "This comparison window deliberately contains two Articles; it is not one legal unit.",
            ),
            (
                "nested_structure",
                1,
                110,
                116,
                "Глава трета.",
                "Chapter/Section labels, separate titles, and Article 10.",
                "Heading-title adjacency is observed; no automatic ancestor tree has been assigned.",
            ),
            (
                "long_article",
                2,
                2779,
                2810,
                "Чл. 7.",
                "Long list-bearing Article ends immediately before Чл. 8 at 2811.",
                "Review numbered subitems and exceptions; boundary fidelity is not legal interpretation.",
            ),
            (
                "additional_provision",
                1,
                2051,
                2055,
                "Допълнителни разпоредби",
                "Additional-provision heading plus § 1.",
                "Heading is unclassified by Stage 1; distinguish this scope from later amendment sections.",
            ),
            (
                "transitional_provision",
                1,
                2158,
                2166,
                "Преходни разпоредби",
                "Transitional heading plus § 6 before § 7 at 2167.",
                "Do not identify § 6 globally or infer effective legal status from these source words.",
            ),
            (
                "annex",
                2,
                2848,
                2893,
                "Приложение № 1",
                "Complete form-like Annex before Annex 2 at 2894.",
                "Form blanks and numbered entries are preserved; they are not automatically Articles.",
            ),
            (
                "long_paragraph",
                11,
                25737,
                25737,
                "Понастоящем",
                "A 3,600-character prose paragraph exceeds small candidate sizes.",
                "The paragraph is an excerpt in a wider recital sequence, not an independent provision.",
            ),
            (
                "publication_history",
                1,
                56,
                56,
                "Обн. ДВ.",
                "A 4,077-character publication list can dominate a future chunk.",
                "No history text is removed and dates are not interpreted as verified legal status.",
            ),
            (
                "eu_article",
                11,
                25783,
                25785,
                "Член 1",
                "EU Article heading, separate subject title, and body before Член 2.",
                "Different heading convention; verify that the separate title remains attached.",
            ),
            (
                "unclassified_heading",
                1,
                2051,
                2051,
                "Допълнителни разпоредби",
                "Isolate a real unclassified Stage 1 heading.",
                "Text suggests a role but Stage 1 has no legal-marker candidate here; keep uncertainty explicit.",
            ),
        ]
        self.weak_doc = self.DOC_BY_ORDINAL[16]
        self.weak_blocks = self.VIEWS[self.weak_doc["document_id"]]["block_ids"]
        self.SAMPLE_SPECS.append(
            (
                "weak_structure",
                16,
                self.BLOCKS[self.weak_blocks[0]]["position"],
                self.BLOCKS[self.weak_blocks[-1]]["position"],
                "Начало",
                "Entire weakly structured source-page text including navigation.",
                "No Article hierarchy; navigation remains present and no cleaning decision is made.",
            )
        )
        self.article_estimates = [
            r for r in self.candidate_inventory if r["kind"] == "article"
        ]
        self.article_distribution = length_summary(
            (r["estimated_characters"] for r in self.article_estimates)
        )
        self.normal_size = (
            self.BLOCK_SPANS[self.BY_POSITION[62]["id"]][2]
            - self.BLOCK_SPANS[self.BY_POSITION[61]["id"]][1]
        )
        self.normal_is_atypical = (
            not self.article_distribution["p25"]
            <= self.normal_size
            <= self.article_distribution["p75"]
        )
        self.median_selection = {
            "rule": "add nearest median estimate if normal Article is outside [p25, p75]",
            "normal_characters": self.normal_size,
            "distribution": self.article_distribution,
            "additional_sample_needed": self.normal_is_atypical,
        }
        if self.normal_is_atypical:
            self.median_row = min(
                self.article_estimates,
                key=lambda r: (
                    abs(
                        r["estimated_characters"]
                        - self.article_distribution["median_p50"]
                    ),
                    r["first_position"],
                ),
            )
            self.SAMPLE_SPECS.append(
                (
                    "median_article_candidate",
                    self.median_row["document"],
                    self.median_row["first_position"],
                    self.median_row["last_position"],
                    self.median_row["label"],
                    "Deterministic near-median Article candidate balances unusually sized examples.",
                    "Endpoint comes from the scouting estimate and requires human boundary review.",
                )
            )
        show_json("Is an additional median Article needed?", self.median_selection)

    def observed_context(self, document_id, position, limit=6):
        blocks = [
            self.BLOCKS[bid]
            for bid in self.VIEWS[document_id]["block_ids"]
            if self.BLOCKS[bid]["position"] <= position
            and (
                self.BLOCKS[bid]["structural_annotations"]["word_heading_level"]
                is not None
                or self.BLOCKS[bid]["structural_annotations"]["legal_marker_candidates"]
            )
        ]
        return [
            {
                "block_id": b["id"],
                "position": b["position"],
                "text": b["raw_text"][:180],
                "heading_level": b["structural_annotations"]["word_heading_level"],
                "candidate_labels": [
                    c["matched_label"]
                    for c in b["structural_annotations"]["legal_marker_candidates"]
                ],
            }
            for b in blocks[-limit:]
        ]

    def select_sample(self, spec):
        name, ordinal, first, last, prefix, why, question = spec
        document = self.DOC_BY_ORDINAL[ordinal]
        did = document["document_id"]
        blocks = [b for b in self.corpus["blocks"] if first <= b["position"] <= last]
        require(
            blocks
            and blocks[0]["position"] == first
            and (blocks[-1]["position"] == last),
            f"Missing endpoint for {name}.",
        )
        require(
            all(
                (
                    b["document_id"] == did and b["id"] in self.BLOCK_SPANS
                    for b in blocks
                )
            ),
            f"Sample {name} crosses a document or includes non-corpus content.",
        )
        require(
            blocks[0]["raw_text"].startswith(prefix), f"Start label changed for {name}."
        )
        lo, hi = (
            self.BLOCK_SPANS[blocks[0]["id"]][1],
            self.BLOCK_SPANS[blocks[-1]["id"]][2],
        )
        return {
            "sample_id": name,
            "document_id": did,
            "document_ordinal": ordinal,
            "first_position": first,
            "last_position_inclusive": last,
            "start": lo,
            "end": hi,
            "characters": hi - lo,
            "block_ids": [b["id"] for b in blocks],
            "source_spans": self.source_map(did, lo, hi),
            "source_text_sha256": hashlib.sha256(
                self.VIEWS[did]["text"][lo:hi].encode("utf-8")
            ).hexdigest(),
            "selection_rationale": why,
            "unresolved_boundary_question": question,
            "review_status": "source-window identity checked; human review pending",
            "observed_context_not_ancestry": self.observed_context(did, first),
        }

    def window_rows(self, sample, padding=2):
        view = self.VIEWS[sample["document_id"]]
        ids = view["block_ids"]
        first = ids.index(sample["block_ids"][0])
        last = ids.index(sample["block_ids"][-1])
        indices = sorted(
            set(range(max(0, first - padding), min(len(ids), first + padding + 1)))
            | set(range(max(0, last - padding), min(len(ids), last + padding + 1)))
        )
        return [
            {
                "position": self.BLOCKS[ids[i]]["position"],
                "within_sample": first <= i <= last,
                "characters": len(self.BLOCKS[ids[i]]["raw_text"]),
                "style": self.BLOCKS[ids[i]]["style"]["name"],
                "candidate_labels": [
                    c["matched_label"]
                    for c in self.BLOCKS[ids[i]]["structural_annotations"][
                        "legal_marker_candidates"
                    ]
                ],
                "preview": self.BLOCKS[ids[i]]["raw_text"][:220],
            }
            for i in indices
        ]

    def step_3b_explicit_source_window_selection_2(self):
        """3b. Explicit source-window selection."""
        self.samples = [self.select_sample(spec) for spec in self.SAMPLE_SPECS]
        require(
            len({s["sample_id"] for s in self.samples}) == len(self.samples),
            "Duplicate sample names.",
        )
        require(
            not self.BY_POSITION[2051]["structural_annotations"][
                "legal_marker_candidates"
            ],
            "Unclassified-heading sample no longer matches its purpose.",
        )
        for self.position, self.prefix in (
            (63, "Чл. 2."),
            (66, "Чл. 3."),
            (117, "Чл. 11."),
            (2811, "Чл. 8."),
            (2056, "§ 1а."),
            (2167, "§ 7."),
            (2894, "Приложение № 2"),
            (25786, "Член 2"),
        ):
            require(
                self.BY_POSITION[self.position]["raw_text"].startswith(self.prefix),
                "Expected following boundary changed.",
            )
        show_table(
            [
                {
                    "sample": s["sample_id"],
                    "document": s["document_ordinal"],
                    "positions_inclusive": f"{s['first_position']}–{s['last_position_inclusive']}",
                    "characters": s["characters"],
                    "why": s["selection_rationale"],
                }
                for s in self.samples
            ]
        )
        for self.s in self.samples:
            self.text = self.VIEWS[self.s["document_id"]]["text"][
                self.s["start"] : self.s["end"]
            ]
            display(
                HTML(
                    f"<h4>{esc(self.s['sample_id'])} — source selection, not a chunk</h4><p>{esc(self.s['unresolved_boundary_question'])}</p>"
                )
            )
            show_table(self.window_rows(self.s))
            show_json(
                "Nearby heading/marker evidence — not inferred ancestry",
                self.s["observed_context_not_ancestry"],
            )
            display(
                HTML(
                    details_html(
                        f"Complete sample: {len(self.text):,} characters; no truncation",
                        self.text,
                    )
                )
            )

    def frozen_samples(self):
        return json.loads(self.FROZEN_MANIFEST_JSON)["samples"]

    def step_3c_freeze_the_manifest_and_full_document_inputs(self):
        """3c. Freeze the manifest and full-document inputs."""
        self.selected_document_ids = sorted(
            {s["document_id"] for s in self.samples},
            key=lambda did: self.DOCUMENTS[did]["ordinal"],
        )
        self.manifest = {
            "manifest_version": 1,
            "scope": "Stage 2 Steps 1–4: source selections only; no chunks",
            "artifact_path": str(self.ARTIFACT.relative_to(self.ROOT)),
            "artifact_sha256": self.artifact_sha256,
            "source_docx_sha256": self.corpus["source"]["sha256"],
            "offset_convention": "zero-based half-open Python Unicode characters",
            "view_policy": "full_text paragraphs; one added newline; omit only evidence-linked delimiter",
            "median_selection": self.median_selection,
            "samples": self.samples,
            "complete_document_inputs": [
                {
                    "document_id": did,
                    "ordinal": self.DOCUMENTS[did]["ordinal"],
                    "characters": len(self.VIEWS[did]["text"]),
                    "block_ids": self.VIEWS[did]["block_ids"],
                    "text_sha256": hashlib.sha256(
                        self.VIEWS[did]["text"].encode("utf-8")
                    ).hexdigest(),
                }
                for did in self.selected_document_ids
            ],
            "review_status": "pending user review after Step 4",
        }
        self.FROZEN_MANIFEST_JSON = canonical(self.manifest)
        self.SETUP_ID = hashlib.sha256(
            self.FROZEN_MANIFEST_JSON.encode("utf-8")
        ).hexdigest()
        print("Frozen setup SHA-256:", self.SETUP_ID)
        print(
            "Sample count:",
            len(self.frozen_samples()),
            "| complete documents reserved:",
            len(self.selected_document_ids),
        )
        show_table(
            self.manifest["complete_document_inputs"],
            ["ordinal", "document_id", "characters", "text_sha256"],
        )
        show_json(
            "Complete frozen manifest: expand to inspect all block IDs and source spans",
            json.loads(self.FROZEN_MANIFEST_JSON),
        )

    def check_display_record(self, record):
        require(
            record.get("setup_id") == self.SETUP_ID,
            "Stale display record: recreate it for the current frozen setup.",
        )
        require(
            record.get("document_id") in self.VIEWS,
            "Display record references an unknown document.",
        )
        require(
            isinstance(record.get("start"), int) and isinstance(record.get("end"), int),
            "Offsets must be integers.",
        )
        require(
            0
            <= record["start"]
            <= record["end"]
            <= len(self.VIEWS[record["document_id"]]["text"]),
            "Display span is outside its source document.",
        )
        for key in ("id", "ordinal", "configuration", "record_kind"):
            require(key in record, f"Missing display field: {key}")

    def span_diagnostics(self, record, neighbors=(), reviewed_units=None):
        self.check_display_record(record)
        did, lo, hi = (record["document_id"], record["start"], record["end"])
        for other in neighbors:
            self.check_display_record(other)
        peers = [
            other
            for other in neighbors
            if other["document_id"] == did and other["id"] != record["id"]
        ]
        peers.append(record)
        require(
            len({p["id"] for p in peers}) == len(peers),
            "Duplicate display IDs in neighbor list.",
        )
        peers.sort(key=lambda p: (p["start"], p["ordinal"], p["id"]))
        index = next((i for i, p in enumerate(peers) if p["id"] == record["id"]))
        before = peers[index - 1] if index else None
        after = peers[index + 1] if index + 1 < len(peers) else None
        previous = (
            intersection_length((lo, hi), (before["start"], before["end"]))
            if before
            else 0
        )
        following = (
            intersection_length((lo, hi), (after["start"], after["end"]))
            if after
            else 0
        )
        overlaps = [
            (max(lo, other["start"]), min(hi, other["end"]))
            for other in (before, after)
            if other is not None
            and intersection_length((lo, hi), (other["start"], other["end"]))
        ]
        mapped = self.source_map(did, lo, hi)
        paragraphs_cut = sorted(
            {
                r["position"]
                for r in mapped
                if r["kind"] == "source"
                and (
                    r["block_start"] > 0
                    or r["block_end"] < len(self.BLOCKS[r["block_id"]]["raw_text"])
                )
            }
        )
        split_units, touched_units = ([], [])
        if reviewed_units is not None:
            for unit in reviewed_units:
                require(
                    unit.get("review_status") == "reviewed"
                    and unit.get("setup_id") == self.SETUP_ID,
                    "Legal-unit diagnostics require explicit current-setup reviewed units.",
                )
                require(
                    unit["document_id"] in self.VIEWS
                    and 0
                    <= unit["start"]
                    < unit["end"]
                    <= len(self.VIEWS[unit["document_id"]]["text"]),
                    "Reviewed unit has an invalid source span.",
                )
                if unit["document_id"] == did and intersection_length(
                    (lo, hi), (unit["start"], unit["end"])
                ):
                    touched_units.append(unit["id"])
                    if (
                        unit["start"] < lo < unit["end"]
                        or unit["start"] < hi < unit["end"]
                    ):
                        split_units.append(unit["id"])
        return {
            "actual_previous_overlap": previous,
            "actual_next_overlap": following,
            "overlap_ranges": overlaps,
            "paragraph_positions_cut": paragraphs_cut,
            "reviewed_legal_units_cut (supplied ledger only)": split_units
            if reviewed_units is not None
            else "unknown — no reviewed unit ledger supplied",
            "combines_reviewed_units (supplied ledger only)": len(touched_units) > 1
            if reviewed_units is not None
            else "unknown — no reviewed unit ledger supplied",
        }

    def span_card(self, record, sample=None, neighbors=(), reviewed_units=None):
        self.check_display_record(record)
        did, lo, hi = (record["document_id"], record["start"], record["end"])
        text = self.VIEWS[did]["text"][lo:hi]
        diagnostic = self.span_diagnostics(record, neighbors, reviewed_units)
        focus = None
        outside = "not applicable"
        if sample is not None:
            require(
                sample["document_id"] == did,
                "Sample and display record belong to different documents.",
            )
            focus = (sample["start"], sample["end"])
            outside = len(text) - intersection_length((lo, hi), focus)
        mapped = self.source_map(did, lo, hi)
        positions = [r["position"] for r in mapped if r["kind"] == "source"]
        fields = {
            "kind": record["record_kind"],
            "configuration": record["configuration"],
            "sample": sample["sample_id"] if sample else "not supplied",
            "ordinal": record["ordinal"],
            "ID": record["id"],
            "document ID": did,
            "document title": self.DOCUMENTS[did]["source_titles"]["title"]["raw_text"],
            "characters": len(text),
            "span [start, end)": [lo, hi],
            "outside sample characters": outside,
            "beginning": text[:180],
            "end": text[-180:],
            **diagnostic,
        }
        context = self.observed_context(did, positions[0]) if positions else []
        body = table_html(
            [
                {"field": k, "value": v}
                for k, v in fields.items()
                if k != "overlap_ranges"
            ]
        )
        body += "<details><summary>Complete text with display-only boundary/overlap highlights</summary>"
        body += (
            highlight_html(text, lo, (lo, hi), diagnostic["overlap_ranges"], focus)
            + "</details>"
        )
        body += details_html(
            "Reversible source map", json.dumps(mapped, ensure_ascii=False, indent=2)
        )
        body += details_html(
            "Observed context — not inferred ancestry",
            json.dumps(context, ensure_ascii=False, indent=2),
        )
        body += "<p>Legal hierarchy remains uncertain; candidate labels are source evidence only.</p>"
        return (
            "<section style='border:1px solid #aaa;padding:10px;min-width:0'>"
            + body
            + "</section>"
        )

    def comparison_html(self, sample, panels, reviewed_units=None):
        frozen = {s["sample_id"]: s for s in self.frozen_samples()}
        require(
            sample == frozen.get(sample["sample_id"]),
            "Sample differs from frozen manifest.",
        )
        did = sample["document_id"]
        text = self.VIEWS[did]["text"][sample["start"] : sample["end"]]
        source = f"<h4>Same source: {esc(sample['sample_id'])}</h4>" + details_html(
            "Full selected source", text
        )
        columns = []
        for label, records in panels.items():
            for record in records:
                self.check_display_record(record)
                require(
                    record["document_id"] == did, "Comparison panel mixes documents."
                )
            shown = [
                r
                for r in records
                if intersection_length(
                    (r["start"], r["end"]), (sample["start"], sample["end"])
                )
            ]
            cards = "".join(
                (self.span_card(r, sample, records, reviewed_units) for r in shown)
            )
            columns.append(
                f"<div style='flex:1;min-width:280px'><h4>{esc(label)}</h4>"
                + (cards or "<p>No strategy results supplied — not implemented.</p>")
                + "</div>"
            )
        return (
            source
            + "<div style='display:flex;gap:12px;overflow:auto'>"
            + "".join(columns)
            + "</div>"
        )

    def relationship_html(self, parent, children, sample=None, reviewed_units=None):
        self.check_display_record(parent)
        require(
            not parent.get("parent_id"),
            "This display accepts one explicit parent level only.",
        )
        require(
            len({c["id"] for c in children}) == len(children), "Duplicate child IDs."
        )
        rows = []
        for child in children:
            self.check_display_record(child)
            require(
                child.get("parent_id") == parent["id"] and child["id"] != parent["id"],
                "Invalid parent link.",
            )
            require(
                child["document_id"] == parent["document_id"]
                and parent["start"] <= child["start"] <= child["end"] <= parent["end"],
                "Child is not contained within supplied parent.",
            )
            size = child["end"] - child["start"]
            rows.append(
                {
                    "parent ID": parent["id"],
                    "child ID": child["id"],
                    "child order": child["ordinal"],
                    "parent characters": parent["end"] - parent["start"],
                    "child characters": size,
                    "expansion ratio": round(
                        (parent["end"] - parent["start"]) / size, 2
                    )
                    if size
                    else "undefined: empty child",
                }
            )
        ordered = sorted(children, key=lambda c: (c["start"], c["ordinal"]))
        return (
            table_html(rows)
            + "<div style='display:flex;gap:12px;overflow:auto'><div style='flex:1;min-width:280px'>"
            + self.span_card(parent, sample)
            + "</div><div style='flex:1;min-width:280px'>"
            + "".join(
                (self.span_card(c, sample, ordered, reviewed_units) for c in ordered)
            )
            + "</div></div>"
        )

    def step_4a_demonstrate_source_inspection_leave_strategy_panels_empty(self):
        """4a. Demonstrate source inspection; leave strategy panels empty."""
        self.SAMPLE_ID = "normal_article"
        self.selected_sample = next(
            (s for s in self.frozen_samples() if s["sample_id"] == self.SAMPLE_ID)
        )
        self.source_record = {
            "id": "source-selection:" + fingerprint([self.SETUP_ID, self.SAMPLE_ID]),
            "ordinal": 1,
            "document_id": self.selected_sample["document_id"],
            "start": self.selected_sample["start"],
            "end": self.selected_sample["end"],
            "setup_id": self.SETUP_ID,
            "configuration": "Steps 1–4 source inspection; no strategy parameters",
            "record_kind": "source selection, not a chunk",
        }
        display(HTML(self.span_card(self.source_record, self.selected_sample)))
        display(
            HTML(
                self.comparison_html(
                    self.selected_sample,
                    {
                        "Fixed-length (future)": [],
                        "Structural (future)": [],
                        "Parent-child (future)": [],
                    },
                )
            )
        )
        display(
            HTML(
                "<h4>Synthetic renderer fixture — not corpus output</h4><p>Gold: supplied overlap; bars: supplied cuts.</p>"
                + highlight_html("АБ <пример> ВГ", cuts=(3, 10), overlaps=((3, 10),))
            )
        )

    def step_4b_validate_setup_fidelity_and_display_edge_cases(self):
        """4b. Validate setup fidelity and display edge cases."""
        expect_value_error(
            lambda: validate_stage1({**self.corpus, "schema_version": 999}),
            "schema version",
        )
        expect_value_error(
            lambda: validate_stage1(
                {
                    **self.corpus,
                    "diagnostics": {
                        **self.corpus["diagnostics"],
                        "stage1_validation": {"result": "FAIL"},
                    },
                }
            ),
            "must report PASS",
        )
        expect_value_error(
            lambda: validate_stage1(
                {
                    **self.corpus,
                    "blocks": self.corpus["blocks"] + [self.corpus["blocks"][0]],
                }
            ),
            "Duplicate body",
        )
        expect_value_error(
            lambda: validate_stage1(
                {**self.corpus, "blocks": list(reversed(self.corpus["blocks"]))}
            ),
            "increasing",
        )
        self.changed_membership = dict(
            self.corpus["blocks"][61], document_id="missing-document"
        )
        expect_value_error(
            lambda: validate_stage1(
                {
                    **self.corpus,
                    "blocks": self.corpus["blocks"][:61]
                    + [self.changed_membership]
                    + self.corpus["blocks"][62:],
                }
            ),
            "membership",
        )
        self.kept_ids = {bid for v in self.VIEWS.values() for bid in v["block_ids"]}
        self.removed_ids = {r["block_id"] for r in self.EXCLUDED_DELIMITERS}
        self.full_text_ids = {
            b["id"] for b in self.corpus["blocks"] if b["region"] == "full_text"
        }
        require(
            not self.kept_ids.intersection(self.removed_ids)
            and self.kept_ids | self.removed_ids == self.full_text_ids,
            "Full-text coverage mismatch.",
        )
        require(
            all((self.BLOCKS[bid]["region"] == "full_text" for bid in self.kept_ids)),
            "Reference/metadata contamination.",
        )
        for self.sample in self.frozen_samples():
            self.text = self.VIEWS[self.sample["document_id"]]["text"][
                self.sample["start"] : self.sample["end"]
            ]
            require(
                self.reconstruct(self.sample["source_spans"]) == self.text,
                "Sample source-map reconstruction failed.",
            )
            require(
                hashlib.sha256(self.text.encode("utf-8")).hexdigest()
                == self.sample["source_text_sha256"],
                "Sample text changed.",
            )
            require(
                len(self.text) == self.sample["characters"],
                "Sample character count changed.",
            )
        require(
            [self.select_sample(spec) for spec in self.SAMPLE_SPECS]
            == self.frozen_samples(),
            "Sample selection is not reproducible.",
        )
        require(
            canonical(self.manifest) == self.FROZEN_MANIFEST_JSON,
            "Manifest mutated after freeze.",
        )
        require(
            fingerprint({**self.manifest, "view_policy": "changed"}) != self.SETUP_ID,
            "Setup fingerprint ignores configuration.",
        )
        expect_value_error(
            lambda: self.check_display_record(
                {**self.source_record, "setup_id": "old-setup"}
            ),
            "Stale",
        )
        expect_value_error(
            lambda: self.source_map(self.source_record["document_id"], -1, 0), "Invalid"
        )
        require(
            self.source_map(self.source_record["document_id"], 0, 0) == [],
            "Empty span map must be empty.",
        )
        require(
            self.span_diagnostics(self.source_record)["paragraph_positions_cut"] == [],
            "Whole-block sample unexpectedly cuts paragraphs.",
        )
        (
            self.real_views,
            self.real_blocks,
            self.real_spans,
            self.real_ends,
            self.real_documents,
        ) = (
            self.VIEWS,
            self.BLOCKS,
            self.BLOCK_SPANS,
            self.SEGMENT_ENDS,
            self.DOCUMENTS,
        )
        try:
            self.fixture_doc = {
                "document_id": "fixture",
                "ordinal": 0,
                "source_titles": {"title": {"raw_text": "Synthetic display fixture"}},
                "boundary_evidence": {"full_text_marker_block_id": "delimiter"},
            }
            self.fixture_texts = [
                ("delimiter", "Пълен текст / Full text"),
                ("a", "Чл. 2а. <x>"),
                ("empty", ""),
                ("b", "§ 1. (Изм.)"),
            ]
            self.fixture_blocks = [
                {
                    "id": bid,
                    "position": i,
                    "document_id": "fixture",
                    "region": "full_text",
                    "raw_text": text,
                    "source": {"part": "fixture", "path": str(i)},
                    "structural_annotations": {
                        "word_heading_level": None,
                        "legal_marker_candidates": [],
                    },
                }
                for i, (bid, text) in enumerate(self.fixture_texts)
            ]
            self.fixture_view = build_document_view(
                self.fixture_doc, self.fixture_blocks
            )
            require(
                self.fixture_view["text"] == "Чл. 2а. <x>\n\n§ 1. (Изм.)",
                "Empty source block or separator lost.",
            )
            require(
                sum(
                    (
                        seg["kind"] == "source" and seg["start"] == seg["end"]
                        for seg in self.fixture_view["segments"]
                    )
                )
                == 1,
                "Zero-length block evidence lost.",
            )
            self.VIEWS = {"fixture": self.fixture_view}
            self.BLOCKS = {b["id"]: b for b in self.fixture_blocks}
            self.DOCUMENTS = {"fixture": self.fixture_doc}
            self.SEGMENT_ENDS = {
                "fixture": [seg["end"] for seg in self.fixture_view["segments"]]
            }
            for self.lo in range(len(self.fixture_view["text"]) + 1):
                for self.hi in range(self.lo, len(self.fixture_view["text"]) + 1):
                    require(
                        self.reconstruct(self.source_map("fixture", self.lo, self.hi))
                        == self.fixture_view["text"][self.lo : self.hi],
                        "Partial map mismatch.",
                    )
            self.base = {
                "document_id": "fixture",
                "setup_id": self.SETUP_ID,
                "configuration": "synthetic display test",
                "record_kind": "supplied fixture span",
            }
            self.parent = {
                **self.base,
                "id": "p",
                "ordinal": 0,
                "start": 0,
                "end": len(self.fixture_view["text"]),
            }
            self.left = {
                **self.base,
                "id": "a",
                "ordinal": 1,
                "start": 0,
                "end": 8,
                "parent_id": "p",
            }
            self.right = {
                **self.base,
                "id": "b",
                "ordinal": 2,
                "start": 6,
                "end": 12,
                "parent_id": "p",
            }
            require(
                self.span_diagnostics(self.left, [self.left, self.right])[
                    "actual_next_overlap"
                ]
                == 2,
                "Overlap calculation failed.",
            )
            require(
                self.span_diagnostics(self.right, [self.left, self.right])[
                    "actual_previous_overlap"
                ]
                == 2,
                "Previous overlap failed.",
            )
            require(
                self.span_diagnostics(self.left)["paragraph_positions_cut"] == [1],
                "Partial paragraph not flagged.",
            )
            self.reviewed = [
                {
                    "id": "fixture-unit",
                    "document_id": "fixture",
                    "start": 0,
                    "end": 10,
                    "setup_id": self.SETUP_ID,
                    "review_status": "reviewed",
                }
            ]
            require(
                self.span_diagnostics(self.left, reviewed_units=self.reviewed)[
                    "reviewed_legal_units_cut (supplied ledger only)"
                ]
                == ["fixture-unit"],
                "Reviewed-unit split not flagged.",
            )
            self.rendered = self.relationship_html(self.parent, [self.left, self.right])
            require(
                "expansion ratio" in self.rendered
                and "&lt;x&gt;" in self.rendered
                and ("<x>" not in self.rendered),
                "Unsafe or incomplete display.",
            )
            expect_value_error(
                lambda: self.relationship_html(
                    self.parent, [{**self.left, "parent_id": "wrong"}]
                ),
                "parent link",
            )
            expect_value_error(
                lambda: self.relationship_html(
                    self.parent, [{**self.left, "end": self.parent["end"] + 1}]
                ),
                "outside",
            )
        finally:
            (
                self.VIEWS,
                self.BLOCKS,
                self.BLOCK_SPANS,
                self.SEGMENT_ENDS,
                self.DOCUMENTS,
            ) = (
                self.real_views,
                self.real_blocks,
                self.real_spans,
                self.real_ends,
                self.real_documents,
            )
        require(
            fingerprint(self.corpus) == self.corpus_fingerprint_before,
            "In-memory Stage 1 representation mutated.",
        )
        require(
            hashlib.sha256(self.ARTIFACT.read_bytes()).hexdigest()
            == self.artifact_sha256,
            "Stage 1 artifact changed on disk.",
        )
        print(
            "PASS: source fidelity, region exclusion, complete-document coverage, sample freezing, error guards, and display fixtures."
        )
        print(
            "Setup validation complete. The approved Step 5 fixed-length baseline follows below."
        )

    def step_4c_preserve_the_approved_frozen_setup(self):
        """4c. Preserve the approved frozen setup."""
        self.OUTPUT_DIR = (
            self.ROOT / "data/processed/02_chunking_experiments/package_refactor_v1"
        )
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.OUTPUT_DIR / f"sample_manifest.{self.SETUP_ID}.json"
        self.manifest_bytes = (self.FROZEN_MANIFEST_JSON + "\n").encode("utf-8")
        if self.manifest_path.exists():
            require(
                self.manifest_path.read_bytes() == self.manifest_bytes,
                "Existing content-addressed manifest differs; investigate before overwriting.",
            )
        else:
            self.manifest_path.write_bytes(self.manifest_bytes)
        require(
            json.loads(self.manifest_path.read_text(encoding="utf-8"))
            == json.loads(self.FROZEN_MANIFEST_JSON),
            "Manifest round-trip failed.",
        )
        print("Frozen manifest:", self.manifest_path.relative_to(self.ROOT))
        print("Setup fingerprint:", self.SETUP_ID)
        print("Approved Steps 1–4 setup verified. Proceeding only to Step 5 below.")
