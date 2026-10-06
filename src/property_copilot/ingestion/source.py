"""Load and inspect the DOCX source."""

from io import BytesIO
from hashlib import sha256
from zipfile import ZipFile, BadZipFile
from collections import Counter
from itertools import islice
from importlib.metadata import version
import xml.etree.ElementTree as ET
from property_copilot._display import display
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
import sys
from .primitives import load_source, show_rows


class SourceSteps:
    """Source steps; state belongs to the workflow instance."""

    def step_1_locate_and_load_the_exact_source(self):
        """Step 1 — Locate and load the exact source."""
        if self.ROOT is None:
            raise FileNotFoundError(
                "Start Jupyter in the project or notebooks directory"
            )
        self.ARCHIVE = self.ROOT / "data/raw/bg_legal_corpus_real.zip"
        self.MEMBER = "bg_legal_corpus_real/full_text/ALL_FULL_TEXTS.docx"
        self.docx_bytes = load_source(self.ARCHIVE, self.MEMBER)
        self.manifest = {
            "archive": self.ARCHIVE.relative_to(self.ROOT).as_posix(),
            "member": self.MEMBER,
            "docx_bytes": len(self.docx_bytes),
            "sha256": sha256(self.docx_bytes).hexdigest(),
        }
        display(self.manifest)

    def step_1_locate_and_load_the_exact_source_2(self):
        """Step 1 — Locate and load the exact source."""
        self.NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        self.W = "{" + self.NS["w"] + "}"
        try:
            with ZipFile(BytesIO(self.docx_bytes)) as self.package:
                self.part_names = self.package.namelist()
                self.required = [
                    "[Content_Types].xml",
                    "word/document.xml",
                    "word/styles.xml",
                ]
                for self.name in self.required:
                    if self.part_names.count(self.name) != 1:
                        raise ValueError(f"DOCX requires exactly one {self.name}")
                self.document_xml = ET.fromstring(
                    self.package.read("word/document.xml")
                )
                self.styles_xml = ET.fromstring(self.package.read("word/styles.xml"))
                self.auxiliary_xml = {
                    name: ET.fromstring(self.package.read(name))
                    for name in self.part_names
                    if name.startswith(("word/header", "word/footer"))
                    and name.endswith(".xml")
                }
        except (BadZipFile, ET.ParseError) as exc:
            raise ValueError(
                "Selected member is not a readable DOCX XML package"
            ) from exc
        self.body = self.document_xml.find("w:body", self.NS)
        if self.body is None:
            raise ValueError("DOCX has no Word document body")
        self.body_elements = list(self.body)
        print("DOCX package parts:")
        print("\n".join(self.part_names))

    def text_preview(self, element):
        return "".join((node.text or "" for node in element.iter(self.W + "t")))

    def style_id(self, paragraph):
        node = paragraph.find("w:pPr/w:pStyle", self.NS)
        return node.get(self.W + "val") if node is not None else "(default)"

    def step_1_locate_and_load_the_exact_source_3(self):
        """Step 1 — Locate and load the exact source."""
        self.paragraphs_xml = self.body.findall("w:p", self.NS)
        self.tables_xml = self.body.findall("w:tbl", self.NS)
        self.style_names = {
            s.get(self.W + "styleId"): s.find("w:name", self.NS).get(self.W + "val")
            for s in self.styles_xml.findall("w:style", self.NS)
            if s.find("w:name", self.NS) is not None
        }
        self.default_paragraph_style = next(
            (
                s.get(self.W + "styleId")
                for s in self.styles_xml.findall("w:style", self.NS)
                if s.get(self.W + "type") == "paragraph"
                and s.get(self.W + "default") == "1"
            )
        )
        self.style_counts = Counter((self.style_id(p) for p in self.paragraphs_xml))
        self.counts = {
            "top-level paragraphs": len(self.paragraphs_xml),
            "top-level tables": len(self.tables_xml),
            "all body/table paragraphs": len(list(self.body.iter(self.W + "p"))),
            "table rows": len(list(self.body.iter(self.W + "tr"))),
            "table cells": len(list(self.body.iter(self.W + "tc"))),
            "Heading1": self.style_counts["Heading1"],
            "Heading2": self.style_counts["Heading2"],
            "Heading3": self.style_counts["Heading3"],
            "explicit page breaks": sum(
                (
                    b.get(self.W + "type") == "page"
                    for b in self.body.iter(self.W + "br")
                )
            ),
            "section properties": len(list(self.body.iter(self.W + "sectPr"))),
        }
        self.expected = dict(
            zip(self.counts, [31055, 21, 31307, 126, 252, 22, 509, 195, 41, 1])
        )
        show_rows(
            [
                {
                    "measure": k,
                    "observed": v,
                    "inspected snapshot": self.expected[k],
                    "matches": v == self.expected[k],
                }
                for k, v in self.counts.items()
            ]
        )
        print(
            "Top-level XML types:",
            dict(Counter((e.tag.rsplit("}", 1)[-1] for e in self.body))),
        )
        show_rows(
            [
                {
                    "applied style ID": s,
                    "style name": self.style_names.get(s, "default paragraph style"),
                    "paragraph count": count,
                }
                for s, count in self.style_counts.items()
            ]
        )
        if self.counts != self.expected:
            print("REVIEW: source structure differs from the approved plan's snapshot.")

    def step_1_locate_and_load_the_exact_source_4(self):
        """Step 1 — Locate and load the exact source."""
        self.first_table_index = next(
            (i for i, e in enumerate(self.body_elements) if e.tag == self.W + "tbl")
        )
        show_rows(
            [
                {
                    "body index (zero-based)": i,
                    "XML type": self.body_elements[i].tag.rsplit("}", 1)[-1],
                    "style": self.style_id(self.body_elements[i])
                    if self.body_elements[i].tag == self.W + "p"
                    else "—",
                    "preview (220 chars)": self.text_preview(self.body_elements[i])[
                        :220
                    ],
                }
                for i in range(self.first_table_index - 2, self.first_table_index + 2)
            ]
        )
        self.first_table_xml = self.tables_xml[0]
        show_rows(
            [
                {
                    "row": r,
                    "label": self.text_preview(row.findall("w:tc", self.NS)[0]),
                    "value": self.text_preview(row.findall("w:tc", self.NS)[1]),
                }
                for r, row in enumerate(self.first_table_xml.findall("w:tr", self.NS))
            ]
        )
        print("Table shapes (rows, cells per row):")
        print(
            Counter(
                (
                    (
                        len(t.findall("w:tr", self.NS)),
                        tuple(
                            (
                                len(r.findall("w:tc", self.NS))
                                for r in t.findall("w:tr", self.NS)
                            )
                        ),
                    )
                    for t in self.tables_xml
                )
            )
        )
        self.example_prefixes = [
            "Извлечени правила (reference)",
            "Пълен текст / Full text",
            "Част първа",
            "Глава първа",
            "Раздел I",
            "Чл. 1.",
            "Чл. 2а.",
            "Член 1",
            "Приложение",
            "§",
        ]
        self.examples = []
        for self.prefix in self.example_prefixes:
            self.found = next(
                (
                    (i, e)
                    for i, e in enumerate(self.body_elements)
                    if e.tag == self.W + "p"
                    and self.text_preview(e).startswith(self.prefix)
                ),
                None,
            )
            if self.found:
                self.i, self.e = self.found
                self.examples.append(
                    {
                        "example prefix": self.prefix,
                        "body index": self.i,
                        "style": self.style_id(self.e),
                        "preview (350 chars)": self.text_preview(self.e)[:350],
                    }
                )
        show_rows(self.examples)
        print("Representative heading XML:")
        print(
            ET.tostring(
                self.body_elements[self.first_table_index - 2], encoding="unicode"
            )
        )

    def step_1_locate_and_load_the_exact_source_5(self):
        """Step 1 — Locate and load the exact source."""
        self.review_tags = [
            "ins",
            "del",
            "sdt",
            "txbxContent",
            "drawing",
            "pict",
            "altChunk",
            "hyperlink",
            "footnoteReference",
            "endnoteReference",
            "commentReference",
            "fldSimple",
            "fldChar",
            "instrText",
            "numPr",
            "gridSpan",
            "vMerge",
        ]
        show_rows(
            [
                {
                    "feature": tag,
                    "body occurrences": len(list(self.body.iter(self.W + tag))),
                }
                for tag in self.review_tags
            ]
        )
        self.extra_parts = [
            p
            for p in self.part_names
            if p.startswith(
                (
                    "word/footnotes",
                    "word/endnotes",
                    "word/comments",
                    "word/media/",
                    "word/embeddings/",
                )
            )
        ]
        print("Additional content parts requiring review:", self.extra_parts or "none")
        self.unexpected_body = sorted(
            {
                e.tag
                for e in self.body
                if e.tag not in {self.W + "p", self.W + "tbl", self.W + "sectPr"}
            }
        )
        print("Unexpected top-level body elements:", self.unexpected_body or "none")
        print(
            "Nested tables:",
            len(list(self.body.iter(self.W + "tbl"))) - len(self.tables_xml),
        )
        for self.name, self.xml in self.auxiliary_xml.items():
            print("Auxiliary part:", self.name)
            print("Visible text:", repr(self.text_preview(self.xml)))
            print(
                "Field instructions:",
                [e.text for e in self.xml.iter(self.W + "instrText")],
            )
            print(
                "Field events:",
                [
                    e.get(self.W + "fldCharType")
                    for e in self.xml.iter(self.W + "fldChar")
                ],
            )
        print(
            "Review note: this feature scan is not proof of complete Word rendering fidelity."
        )

    def step_1_locate_and_load_the_exact_source_6(self):
        """Step 1 — Locate and load the exact source."""
        print("Python:", sys.version.split()[0])
        print("python-docx:", version("python-docx"))
        print("lxml:", version("lxml"))
        self.parser_document = Document(BytesIO(self.docx_bytes))
        self.sample_start = self.first_table_index - 2
        self.sample_end = self.first_table_index + 2
        self.sample = list(
            islice(
                self.parser_document.iter_inner_content(),
                self.sample_start,
                self.sample_end,
            )
        )
        self.xml_sample = self.body_elements[self.sample_start : self.sample_end]
        self.checks = []
        for self.i, (self.item, self.xml) in enumerate(
            zip(self.sample, self.xml_sample), start=self.sample_start
        ):
            if isinstance(self.item, Paragraph):
                self.text_matches = self.item.text == self.text_preview(self.xml)
                self.explicit_style = self.style_id(self.xml)
                self.expected_style = (
                    self.default_paragraph_style
                    if self.explicit_style == "(default)"
                    else self.explicit_style
                )
                self.style_matches = self.item.style.style_id == self.expected_style
                self.checks.append(
                    {
                        "body index": self.i,
                        "kind": "paragraph",
                        "text matches": self.text_matches,
                        "style/dimensions match": self.style_matches,
                    }
                )
                assert self.text_matches and self.style_matches, (
                    f"Paragraph mismatch at {self.i}"
                )
                print(
                    f"{self.i}: {self.item.style.name} / {self.item.style.style_id}: {self.item.text}"
                )
            elif isinstance(self.item, Table):
                self.xml_rows = self.xml.findall("w:tr", self.NS)
                self.api_cells = [
                    [cell.text for cell in row.cells] for row in self.item.rows
                ]
                self.xml_cells = [
                    [
                        "\n".join(
                            (self.text_preview(p) for p in cell.findall("w:p", self.NS))
                        )
                        for cell in row.findall("w:tc", self.NS)
                    ]
                    for row in self.xml_rows
                ]
                self.dimensions_match = len(self.item.rows) == len(
                    self.xml_rows
                ) and all(
                    (len(a) == len(b) for a, b in zip(self.api_cells, self.xml_cells))
                )
                self.checks.append(
                    {
                        "body index": self.i,
                        "kind": "table",
                        "text matches": self.api_cells == self.xml_cells,
                        "style/dimensions match": self.dimensions_match,
                    }
                )
                assert self.api_cells == self.xml_cells and self.dimensions_match, (
                    "Metadata table mismatch"
                )
                show_rows(
                    [
                        {"row": r, "column": c, "python-docx cell text": value}
                        for r, row in enumerate(self.api_cells)
                        for c, value in enumerate(row)
                    ]
                )
            else:
                raise AssertionError(f"Unexpected sample type: {type(self.item)}")
        assert len(self.sample) == len(self.xml_sample) == 4
        show_rows(self.checks)
        print(
            "Small-region comparison passed: 3 paragraphs and one 6 × 2 metadata table."
        )
