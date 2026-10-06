"""Validate and save the parsed output."""

from pathlib import Path
from io import BytesIO
from hashlib import sha256
from zipfile import ZipFile, BadZipFile
from collections import Counter
from importlib.metadata import version
import xml.etree.ElementTree as ET
import json
from collections import defaultdict
from copy import deepcopy
from tempfile import NamedTemporaryFile
import os
from .primitives import (
    all_paragraph_records,
    base_record,
    file_sha256,
    heading_level,
    load_source,
    property_xml,
    record_digest,
    require,
    show_full_record,
    show_rows,
    table_paragraphs,
    text_with_evidence,
)


class ValidationSteps:
    """Validation steps; state belongs to the workflow instance."""

    def read_validation_body(self, data):
        with ZipFile(BytesIO(data)) as package:
            root = ET.fromstring(package.read("word/document.xml"))
        result = root.find("w:body", self.NS)
        if result is None:
            raise ValueError("Missing document body")
        return result

    def run_validation(self, name, check):
        try:
            detail = check()
            result = {"check": name, "result": "PASS", "detail": detail}
        except Exception as exc:
            result = {
                "check": name,
                "result": "FAIL",
                "detail": f"{type(exc).__name__}: {exc}",
            }
        self.validation_rows.append(result)
        return result

    def verify_paragraph_at(self, record, xml, part, path, position):
        require(
            record["type"] == "paragraph" and record["position"] == position,
            f"Paragraph position/type: {path}",
        )
        require(
            record["source"] == {"part": part, "path": path},
            f"Paragraph locator: {path}",
        )
        require(
            record["raw_text"] == self.xml_visible_text(xml),
            f"Paragraph text changed: {path}",
        )
        require(
            [
                e["text"]
                for r in record["runs"]
                for e in r["events"]
                if e["type"] == "text"
            ]
            == [e.text or "" for e in xml.iter(self.W + "t")],
            f"Text fragments changed/dropped/duplicated: {path}",
        )
        require(
            record["raw_text"] == "".join((r["raw_text"] for r in record["runs"])),
            f"Run text mismatch: {path}",
        )
        explicit = xml.find("w:pPr/w:pStyle", self.NS)
        require(
            record["style"]["explicit_id"]
            == (explicit.get(self.W + "val") if explicit is not None else None),
            f"Style: {path}",
        )
        require(
            [(m["xml_tag"], m["kind"], m["clear"]) for m in record["break_markers"]]
            == [
                (
                    e.tag.rsplit("}", 1)[-1],
                    e.get(self.W + "type", "textWrapping"),
                    e.get(self.W + "clear"),
                )
                for e in xml.iter()
                if e.tag in {self.W + "br", self.W + "cr"}
            ],
            f"Break events: {path}",
        )

    def step_8_validate_parsing_fidelity_and_persist_stage_1(self):
        """Step 8 — Validate parsing fidelity and persist Stage 1."""
        self.OUTPUT_PATH = self.ROOT / "data/processed/01_parsed_docx_structure.json"
        self.source_archive_sha_before = file_sha256(self.ARCHIVE)
        self.validation_docx_bytes = load_source(self.ARCHIVE, self.MEMBER)
        self.validation_body = self.read_validation_body(self.validation_docx_bytes)
        self.validation_body_elements = list(self.validation_body)
        self.validation_block_by_id = {b["id"]: b for b in self.corpus["blocks"]}
        self.validation_paragraphs = all_paragraph_records(self.corpus["blocks"])
        self.validation_record_by_id = {
            r["id"]: r
            for r in self.corpus["blocks"]
            + [
                p
                for b in self.corpus["blocks"]
                if b["type"] == "table"
                for p in table_paragraphs(b)
            ]
        }
        self.validation_rows = []

    def check_source_identity(self):
        require(
            self.validation_docx_bytes == self.docx_bytes,
            "Source member changed since Step 1",
        )
        require(
            self.corpus["source"]
            == {
                "archive": self.ARCHIVE.relative_to(self.ROOT).as_posix(),
                "member": self.MEMBER,
                "docx_bytes": len(self.validation_docx_bytes),
                "sha256": sha256(self.validation_docx_bytes).hexdigest(),
            },
            "Source provenance mismatch",
        )
        require(
            self.corpus["parser"]["version"] == version("python-docx"),
            "Parser version mismatch",
        )
        return "Exact archive member, byte size, SHA-256 and parser provenance agree"

    def check_order_and_text(self):
        xml_items = [
            (i, e)
            for i, e in enumerate(self.validation_body)
            if e.tag in {self.W + "p", self.W + "tbl"}
        ]
        require(
            len(xml_items) == len(self.corpus["blocks"]), "Body block count mismatch"
        )
        for (position, xml), block in zip(
            xml_items, self.corpus["blocks"], strict=True
        ):
            path = f"/body/children/{position}"
            if xml.tag == self.W + "p":
                self.verify_paragraph_at(
                    block, xml, "word/document.xml", path, position
                )
            else:
                require(
                    block["type"] == "table" and block["position"] == position,
                    f"Table order at {path}",
                )
                require(
                    block["source"] == {"part": "word/document.xml", "path": path},
                    f"Table locator at {path}",
                )
                for row_index, (row, xml_row) in enumerate(
                    zip(block["rows"], xml.findall("w:tr", self.NS), strict=True)
                ):
                    require(row["row_index"] == row_index, f"Row order at {path}")
                    for column_index, (cell, xml_cell) in enumerate(
                        zip(row["cells"], xml_row.findall("w:tc", self.NS), strict=True)
                    ):
                        require(
                            cell["column_index"] == column_index,
                            f"Cell order at {path}",
                        )
                        cell_items = [
                            (i, e)
                            for i, e in enumerate(xml_cell)
                            if e.tag == self.W + "p"
                        ]
                        for paragraph, (child_index, xml_p) in zip(
                            cell["paragraphs"], cell_items, strict=True
                        ):
                            self.verify_paragraph_at(
                                paragraph,
                                xml_p,
                                "word/document.xml",
                                f"{path}/rows/{row_index}/cells/{column_index}/children/{child_index}",
                                child_index,
                            )
        observed = [
            sum((b["type"] == "paragraph" for b in self.corpus["blocks"])),
            sum((b["type"] == "table" for b in self.corpus["blocks"])),
            sum(
                (len(b["rows"]) for b in self.corpus["blocks"] if b["type"] == "table")
            ),
            sum(
                (
                    len(r["cells"])
                    for b in self.corpus["blocks"]
                    if b["type"] == "table"
                    for r in b["rows"]
                )
            ),
            len(self.validation_paragraphs),
            sum(
                (
                    m["kind"] == "page"
                    for p in self.validation_paragraphs
                    for m in p["break_markers"]
                )
            ),
        ]
        require(
            observed == [31055, 21, 126, 252, 31307, 41],
            f"Inspected source inventory changed: {observed}",
        )
        require(
            len(self.corpus["blocks"]) + len(self.corpus["layout_markers"])
            == len(self.validation_body),
            "Unaccounted body element",
        )
        return "31,076 ordered body blocks; 31,307 body/cell paragraphs; 126 rows / 252 cells; 41 page breaks; exact text and locations"

    def check_boundaries_and_regions(self):
        source_starts = []
        for i, xml in enumerate(self.validation_body_elements[:-2]):
            if self.style_id(xml) != "Heading1":
                continue
            subtitle, table = self.validation_body_elements[i + 1 : i + 3]
            if subtitle.tag != self.W + "p" or table.tag != self.W + "tbl":
                continue
            labels = [
                self.text_preview(row.findall("w:tc", self.NS)[0])
                for row in table.findall("w:tr", self.NS)
            ]
            if labels == list(self.METADATA_LABELS):
                source_starts.append(i)
        documents = self.corpus["documents"]
        require(
            len(source_starts) == len(documents) == 21, "Expected 21 source documents"
        )
        body_index_by_position = {
            b["position"]: i for i, b in enumerate(self.corpus["blocks"])
        }
        require(
            len({d["document_id"] for d in documents}) == 21, "Duplicate document IDs"
        )
        for b in self.corpus["blocks"][: body_index_by_position[source_starts[0]]]:
            require(
                b["document_id"] is None and b["region"] == "front_matter",
                "Incorrect corpus front matter",
            )
        full_count = reference_count = 0
        for ordinal, (document, source_start) in enumerate(
            zip(documents, source_starts, strict=True)
        ):
            next_position = (
                source_starts[ordinal + 1]
                if ordinal + 1 < len(source_starts)
                else len(self.validation_body_elements)
            )
            start_index = body_index_by_position[source_start]
            end_index = (
                body_index_by_position[next_position]
                if ordinal + 1 < len(source_starts)
                else len(self.corpus["blocks"])
            )
            require(
                document["block_range"]
                == {
                    "start_index": start_index,
                    "end_index_exclusive": end_index,
                    "first_body_position": source_start,
                    "last_body_position": self.corpus["blocks"][end_index - 1][
                        "position"
                    ],
                },
                "Document range mismatch",
            )
            require(
                document["source_titles"]["title"]["raw_text"]
                == self.text_preview(self.validation_body_elements[source_start]),
                "Document title mismatch",
            )
            source_full = [
                i
                for i in range(source_start, next_position)
                if self.style_id(self.validation_body_elements[i]) == "Heading2"
                and self.text_preview(self.validation_body_elements[i])
                == self.FULL_TEXT_MARKER
            ]
            source_refs = [
                i
                for i in range(source_start, next_position)
                if self.style_id(self.validation_body_elements[i]) == "Heading2"
                and self.text_preview(self.validation_body_elements[i])
                == self.REFERENCE_MARKER
            ]
            require(
                len(source_full) == 1 and len(source_refs) <= 1,
                "Ambiguous source region delimiters",
            )
            require(
                not source_refs or source_refs[0] < source_full[0],
                "Reversed reference/full-text markers",
            )
            full_count += len(source_full)
            reference_count += len(source_refs)
            expected_evidence = {
                "title_block_id": self.corpus["blocks"][start_index]["id"],
                "subtitle_block_id": self.corpus["blocks"][start_index + 1]["id"],
                "metadata_table_block_id": self.corpus["blocks"][start_index + 2]["id"],
                "full_text_marker_block_id": self.corpus["blocks"][
                    body_index_by_position[source_full[0]]
                ]["id"],
                "reference_marker_block_id": self.corpus["blocks"][
                    body_index_by_position[source_refs[0]]
                ]["id"]
                if source_refs
                else None,
            }
            require(
                document["boundary_evidence"] == expected_evidence,
                "Boundary evidence mismatch",
            )
            for b in self.corpus["blocks"][start_index:end_index]:
                region = (
                    "full_text"
                    if b["position"] >= source_full[0]
                    else "reference_rules"
                    if source_refs and b["position"] >= source_refs[0]
                    else "document_metadata"
                )
                require(
                    b["document_id"] == document["document_id"]
                    and b["region"] == region,
                    "Document/region coverage mismatch",
                )
                if b["type"] == "table":
                    require(
                        all(
                            (
                                p["document_id"] == b["document_id"]
                                and p["region"] == region
                                for p in table_paragraphs(b)
                            )
                        ),
                        "Cell membership mismatch",
                    )
        require(
            (full_count, reference_count) == (21, 19), "Region delimiter totals changed"
        )
        require(
            dict(Counter((b["region"] for b in self.corpus["blocks"])))
            == self.corpus["diagnostics"]["region_counts"],
            "Region summary mismatch",
        )
        return "21 contiguous source ranges, 24 front-matter blocks, 21 full-text / 19 reference markers; no gaps or overlaps"

    def check_ids_and_auxiliary(self):
        canonical = (
            list(self.validation_record_by_id.values()) + self.corpus["layout_markers"]
        )
        for auxiliary in self.corpus["auxiliary_content"]:
            canonical += (
                auxiliary["blocks"]
                + [
                    p
                    for b in auxiliary["blocks"]
                    if b["type"] == "table"
                    for p in table_paragraphs(b)
                ]
                + auxiliary["layout_markers"]
            )
            source_xml = self.auxiliary_xml[auxiliary["part"]]
            for record, xml in zip(
                all_paragraph_records(auxiliary["blocks"]),
                source_xml.iter(self.W + "p"),
                strict=True,
            ):
                require(
                    record["raw_text"] == self.xml_visible_text(xml),
                    "Auxiliary text mismatch",
                )
                events = [e for r in record["runs"] for e in r["events"]]
                require(
                    [e["text"] for e in events if e["type"] == "field_instruction"]
                    == [e.text or "" for e in xml.iter(self.W + "instrText")],
                    "Footer field instruction lost",
                )
                require(
                    [e["kind"] for e in events if e["type"] == "field_char"]
                    == [
                        e.get(self.W + "fldCharType")
                        for e in xml.iter(self.W + "fldChar")
                    ],
                    "Footer field order changed",
                )
        expected_body_records = len(self.corpus["blocks"]) + sum(
            (
                len(table_paragraphs(b))
                for b in self.corpus["blocks"]
                if b["type"] == "table"
            )
        )
        require(
            len(self.validation_record_by_id) == expected_body_records,
            "Duplicate body/cell IDs",
        )
        require(
            len({r["id"] for r in canonical}) == len(canonical),
            "Duplicate canonical IDs",
        )
        require(
            len({(r["source"]["part"], r["source"]["path"]) for r in canonical})
            == len(canonical),
            "Duplicate canonical source locations",
        )
        require(
            all(
                (
                    r["id"]
                    == base_record(
                        r["type"],
                        r["position"],
                        r["source"]["part"],
                        r["source"]["path"],
                        self.corpus["source"]["sha256"],
                    )["id"]
                    for r in canonical
                )
            ),
            "Unstable content/location IDs",
        )
        source_sections = [
            (i, e)
            for i, e in enumerate(self.validation_body)
            if e.tag == self.W + "sectPr"
        ]
        for marker, (position, xml) in zip(
            self.corpus["layout_markers"], source_sections, strict=True
        ):
            require(
                marker["position"] == position and marker["xml"] == property_xml(xml),
                "Section properties changed",
            )
        require(
            {a["part"] for a in self.corpus["auxiliary_content"]}
            == set(self.auxiliary_xml),
            "Missing auxiliary part",
        )
        return "Unique stable IDs/locations; footer PAGE events and section properties preserved separately"

    def check_metadata_provenance(self):
        catalog = self.corpus["metadata_provenance"]
        require(
            catalog["generated"]["source_locator_and_fingerprint"]
            == self.corpus["source"],
            "Catalog file provenance mismatch",
        )
        require(
            catalog["generated"]["parser"] == self.corpus["parser"],
            "Catalog parser provenance mismatch",
        )
        row_count = 0
        for document, classified in zip(
            self.corpus["documents"], catalog["documents"], strict=True
        ):
            require(
                document["document_id"] == classified["document_id"],
                "Classified document ID mismatch",
            )
            require(
                document["source_titles"] == classified["source_extracted"]["titles"],
                "Classified titles mismatch",
            )
            for title in document["source_titles"].values():
                require(
                    title
                    == text_with_evidence(
                        self.validation_record_by_id[title["block_id"]]
                    ),
                    "Title evidence mismatch",
                )
            metadata = document["source_metadata"]
            table = self.validation_record_by_id[metadata["table_block_id"]]
            require(
                metadata["table_source"] == table["source"],
                "Metadata table location mismatch",
            )
            require(
                len(metadata["rows"]) == len(table["rows"]) == 6,
                "Missing source metadata row",
            )
            for entry, actual in zip(metadata["rows"], table["rows"], strict=True):
                row_count += 1
                require(
                    entry["row_index"] == actual["row_index"],
                    "Metadata row index mismatch",
                )
                for field, index in [("label", 0), ("value", 1)]:
                    require(
                        entry[field + "_column_index"]
                        == actual["cells"][index]["column_index"],
                        "Metadata column index mismatch",
                    )
                    require(
                        entry[field + "_paragraphs"]
                        == [
                            text_with_evidence(p)
                            for p in actual["cells"][index]["paragraphs"]
                        ],
                        "Source metadata value/evidence modified",
                    )
            require(
                classified["source_extracted"]["metadata_fields"]
                == self.classified_source_rows(document),
                "Categorized source metadata modified",
            )
            require(
                classified["structurally_interpreted"]["boundary_evidence"]
                == document["boundary_evidence"],
                "Interpreted boundary evidence mismatch",
            )
        with ZipFile(BytesIO(self.validation_docx_bytes)) as package:
            core = ET.fromstring(package.read("docProps/core.xml"))
        for index, (record, xml) in enumerate(
            zip(catalog["source_extracted"]["package_properties"], core, strict=True)
        ):
            require(
                record["qualified_name"] == xml.tag
                and record["raw_value"] == xml.text
                and (record["attributes"] == dict(xml.attrib)),
                "Package properties changed",
            )
            require(
                record["source"]
                == {
                    "part": "docProps/core.xml",
                    "path": f"/coreProperties/children/{index}",
                },
                "Package evidence mismatch",
            )
        require(
            all(
                (
                    item["status"] == "deferred"
                    and set(item) == {"field", "status", "reason"}
                    for item in catalog["deferred"]
                )
            ),
            "Deferred metadata was inferred",
        )
        require(
            any(
                (
                    item["field"] == "document_to_chunk_metadata_inheritance"
                    for item in catalog["deferred"]
                )
            ),
            "Chunk inheritance decision missing from deferred list",
        )
        require(row_count == 126, "Expected 126 original metadata rows")
        return "All 126 source metadata rows, titles, raw dates/notes, package properties and evidence agree; deferred decisions remain deferred"

    def check_marker_evidence(self):
        markers = [
            m
            for b in self.corpus["blocks"]
            for m in b["structural_annotations"]["legal_marker_candidates"]
        ]
        kinds = Counter((m["kind"] for m in markers))
        require(
            set(kinds)
            >= {"part", "chapter", "section", "article", "paragraph_sign", "annex"},
            "Missing representative legal-marker kinds",
        )
        for m in markers:
            block = self.validation_record_by_id[m["block_id"]]
            lo, hi = m["character_span"]
            require(
                block["raw_text"][lo:hi] == m["matched_label"]
                and m["source"] == block["source"],
                "Marker source/span mismatch",
            )
            require(
                m["status"] == "candidate"
                and block["region"] == "full_text"
                and (m["document_id"] == block["document_id"]),
                "Marker status/membership mismatch",
            )
            require(
                self.detect_legal_candidate(
                    block,
                    {"region": block["region"], "document_id": block["document_id"]},
                )
                == m,
                "Candidate rule evidence mismatch",
            )
        require(
            dict(kinds) == self.corpus["diagnostics"]["candidate_marker_counts"],
            "Marker count summary mismatch",
        )
        return f"{len(markers)} candidate labels retain source spans/rules; Article, Chapter, Section, § and Annex examples available"

    def check_targeted_failures(self):

        def expect_failure(action, errors):
            try:
                action()
            except errors:
                return
            raise AssertionError("Malformed fixture was silently accepted")

        expect_failure(lambda: self.read_validation_body(b"not a DOCX"), BadZipFile)
        buffer = BytesIO()
        with ZipFile(buffer, "w") as z:
            z.writestr("word/document.xml", "<broken")
        expect_failure(
            lambda: self.read_validation_body(buffer.getvalue()), ET.ParseError
        )
        altered = deepcopy(self.corpus["blocks"][0])
        altered["raw_text"] += " "
        expect_failure(
            lambda: self.verify_paragraph_at(
                altered,
                self.validation_body_elements[0],
                "word/document.xml",
                "/body/children/0",
                0,
            ),
            AssertionError,
        )
        source = self.corpus["documents"][0]
        first = source["block_range"]["start_index"]
        minimal = deepcopy(self.corpus["blocks"][first : first + 3])
        minimal[2]["rows"][0]["cells"][0]["paragraphs"][0]["raw_text"] = (
            "unexpected metadata label"
        )
        expect_failure(lambda: self.discover_document_starts(minimal), ValueError)
        return "Four targeted failures caught: invalid DOCX, malformed XML, changed text, missing metadata pattern; earlier fixture checks also passed"

    def step_8c_validate_metadata_provenance_and_structural_evidence(self):
        """8c. Validate metadata, provenance and structural evidence."""
        for self.name, self.check in [
            ("Source identity/provenance", self.check_source_identity),
            ("Paragraph/table order and exact source text", self.check_order_and_text),
            (
                "21 document boundaries and complete region coverage",
                self.check_boundaries_and_regions,
            ),
            ("Stable IDs, auxiliary fields and layout", self.check_ids_and_auxiliary),
            ("Source metadata and evidence fidelity", self.check_metadata_provenance),
            ("Representative structural-marker evidence", self.check_marker_evidence),
            ("Malformed/missing/changed input guards", self.check_targeted_failures),
        ]:
            self.run_validation(self.name, self.check)
        show_rows(self.validation_rows)

    def step_8d_report_ambiguity_and_show_source_previews(self):
        """8d. Report ambiguity and show source previews."""
        self.stage1_marker_examples = []
        for self.kind in ["article", "chapter", "section", "paragraph_sign", "annex"]:
            self.example = next(
                (
                    m
                    for b in self.corpus["blocks"]
                    for m in b["structural_annotations"]["legal_marker_candidates"]
                    if m["kind"] == self.kind
                ),
                None,
            )
            if self.example:
                self.block = self.validation_block_by_id[self.example["block_id"]]
                self.stage1_marker_examples.append(
                    {
                        "kind": self.kind,
                        "body position": self.block["position"],
                        "source label": self.example["matched_label"],
                        "source text preview": self.block["raw_text"][:350],
                    }
                )
        show_rows(self.stage1_marker_examples)
        self.review_headings = [
            b
            for b in self.corpus["blocks"]
            if b["type"] == "paragraph"
            and b["region"] == "full_text"
            and (heading_level(b) in {2, 3})
            and (b["raw_text"] != self.FULL_TEXT_MARKER)
            and (not b["structural_annotations"]["legal_marker_candidates"])
        ]
        self.heading_groups = defaultdict(list)
        for self.b in self.review_headings:
            self.heading_groups[self.b["raw_text"]].append(self.b["position"])
        show_rows(
            [
                {
                    "unclassified heading": b["raw_text"],
                    "body position": b["position"],
                    "style": b["style"]["resolved_id"],
                }
                for b in self.review_headings[:8]
            ]
        )
        show_rows(
            [
                {
                    "repeated source heading": text,
                    "occurrences": len(positions),
                    "first positions": positions[:6],
                }
                for text, positions in self.heading_groups.items()
                if len(positions) > 1
            ][:5]
        )
        self.long_paragraph = max(
            self.validation_paragraphs, key=lambda p: len(p["raw_text"])
        )
        self.suffix_paragraph = next(
            (
                p
                for p in self.validation_paragraphs
                if p["raw_text"].startswith("Чл. 2а.")
            )
        )
        self.last_document = self.corpus["documents"][-1]
        self.last_span = self.corpus["blocks"][
            self.last_document["block_range"]["start_index"] : self.last_document[
                "block_range"
            ]["end_index_exclusive"]
        ]
        self.last_nonempty = [
            b for b in self.last_span if b["type"] == "paragraph" and b["raw_text"]
        ][-3:]
        show_rows(
            [
                {
                    "sample": label,
                    "body position": p["position"],
                    "characters": len(p["raw_text"]),
                    "preview": p["raw_text"][:500],
                }
                for label, p in [
                    ("long paragraph", self.long_paragraph),
                    ("article suffix/Cyrillic", self.suffix_paragraph),
                ]
                + [("final source ending", p) for p in self.last_nonempty]
            ]
        )
        show_full_record(
            {
                "source": self.long_paragraph["source"],
                "raw_text": self.long_paragraph["raw_text"],
            },
            "Complete longest paragraph, unchanged",
        )
        self.stage1_review_items = [
            {
                "code": "unclassified_headings",
                "count": len(self.review_headings),
                "message": "Preserved without guessing a legal role.",
                "block_ids": [b["id"] for b in self.review_headings],
            },
            {
                "code": "repeated_heading_labels",
                "count": sum((len(v) > 1 for v in self.heading_groups.values())),
                "message": "Repeated labels at distinct source locations are retained; no deduplication or final hierarchy.",
            },
            {
                "code": "candidate_markers_only",
                "message": "Candidate legal labels do not establish provision semantics or legal hierarchy.",
            },
            {
                "code": "source_page_navigation_retained",
                "message": "Source-page navigation/footer-like text remains unchanged; cleaning is deferred.",
            },
            {
                "code": "rendered_layout_not_validated",
                "message": "No physical page numbers or Word visual-layout reconstruction.",
            },
            {
                "code": "legal_accuracy_not_validated",
                "message": "Fidelity is to this DOCX, not current law or completeness of original websites.",
            },
            {
                "code": "chunk_inheritance_undecided",
                "message": "Chunk metadata and document-to-chunk inheritance remain deferred.",
            },
        ]
        show_rows(
            [
                {"review item": item["code"], "detail": item["message"]}
                for item in self.stage1_review_items
            ]
        )
        self.validation_passed = len(self.validation_rows) == 7 and all(
            (row["result"] == "PASS" for row in self.validation_rows)
        )
        self.corpus["diagnostics"]["stage1_validation"] = {
            "result": "PASS" if self.validation_passed else "FAIL",
            "scope": "Stored DOCX text/structure fidelity; not legal accuracy or rendered layout",
            "checks": deepcopy(self.validation_rows),
            "review_items": deepcopy(self.stage1_review_items),
        }
        if not self.validation_passed:
            raise RuntimeError(
                "Stage 1 validation failed. No artifact will be written; inspect FAIL rows above."
            )
        self.validated_corpus_digest = record_digest(self.corpus)
        print(
            "PASS: all required automated checks. Review items retained without inference or repair."
        )

    def step_8e_persist_and_reload_the_validated_representation(self):
        """8e. Persist and reload the validated representation."""
        require(
            self.validation_passed
            and self.corpus["diagnostics"]["stage1_validation"]["result"] == "PASS",
            "Validation must pass before persistence",
        )
        require(
            record_digest(self.corpus) == self.validated_corpus_digest,
            "Corpus changed after validation; rerun Step 8 checks",
        )
        require(
            file_sha256(self.ARCHIVE) == self.source_archive_sha_before,
            "Source archive changed during this run",
        )
        require(
            not self.OUTPUT_PATH.is_symlink(), "Processed output must not be a symlink"
        )
        self.OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.previous_output_sha = (
            file_sha256(self.OUTPUT_PATH) if self.OUTPUT_PATH.exists() else None
        )
        self.temporary_path = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.OUTPUT_PATH.parent,
                prefix=".stage01-",
                suffix=".json.tmp",
                delete=False,
            ) as self.stream:
                self.temporary_path = Path(self.stream.name)
                json.dump(
                    self.corpus,
                    self.stream,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=False,
                )
                self.stream.write("\n")
            os.replace(self.temporary_path, self.OUTPUT_PATH)
        finally:
            if self.temporary_path is not None and self.temporary_path.exists():
                self.temporary_path.unlink()
        with self.OUTPUT_PATH.open("r", encoding="utf-8") as self.stream:
            self.reloaded_corpus = json.load(self.stream)
        require(
            self.reloaded_corpus == self.corpus,
            "FAIL: saved JSON does not exactly equal the in-memory corpus",
        )
        del self.reloaded_corpus
        require(
            file_sha256(self.ARCHIVE) == self.source_archive_sha_before,
            "FAIL: source archive changed during persistence",
        )
        self.output_sha = file_sha256(self.OUTPUT_PATH)
        self.repeatability_result = (
            "NOT CHECKED — first saved artifact"
            if self.previous_output_sha is None
            else "PASS — identical to previous artifact"
            if self.output_sha == self.previous_output_sha
            else "CHANGED — compare source/code/parser versions before claiming repeatability"
        )
        self.persistence_rows = [
            {"check": "UTF-8 JSON save/reload equality", "result": "PASS"},
            {"check": "Original source archive unchanged", "result": "PASS"},
            {
                "check": "Repeat-run output comparison",
                "result": self.repeatability_result,
            },
        ]
        show_rows(self.persistence_rows)
        print("Saved:", self.OUTPUT_PATH.relative_to(self.ROOT))
        print("Bytes:", self.OUTPUT_PATH.stat().st_size, "SHA-256:", self.output_sha)

    def final_stage_1_summary(self):
        """Final Stage 1 summary."""
        self.stage1_summary = {
            "source file": self.corpus["source"]["member"],
            "source archive": self.corpus["source"]["archive"],
            "documents": len(self.corpus["documents"]),
            "structural body blocks": len(self.corpus["blocks"]),
            "body paragraphs / tables": f"{sum((b['type'] == 'paragraph' for b in self.corpus['blocks']))} / {sum((b['type'] == 'table' for b in self.corpus['blocks']))}",
            "metadata preservation": "PASS — all 126 source metadata rows and evidence preserved",
            "output file": self.OUTPUT_PATH.relative_to(self.ROOT).as_posix(),
            "output bytes": self.OUTPUT_PATH.stat().st_size,
            "validation result": "PASS — automated source fidelity and exact JSON reload equality",
            "repeatability": self.repeatability_result,
            "known limitations": f"{len(self.review_headings)} unclassified headings retained; candidate legal roles only; website text retained; no rendered pages or legal accuracy verification",
            "deferred decisions": "Metadata normalization/inference, final legal hierarchy, chunk design and document-to-chunk metadata inheritance",
        }
        show_rows(
            [
                {"Stage 1 item": key, "result": value}
                for key, value in self.stage1_summary.items()
            ]
        )
