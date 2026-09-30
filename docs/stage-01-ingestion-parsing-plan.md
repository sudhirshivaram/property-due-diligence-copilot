# Stage 1: Document ingestion and parsing

## Summary and inspection findings

Create `notebooks/01_document_ingestion_parsing.ipynb` as a guided DOCX exploration notebook. Each step will contain an explanation, a small implementation cell, an inspection output, and interpretation notes. Implementation will begin only after your approval.

I inspected the repository and the DOCX in memory; no files were modified.

The source is located inside:

`data/raw/bg_legal_corpus_real.zip` → `bg_legal_corpus_real/full_text/ALL_FULL_TEXTS.docx`

The existing notebook covers synthetic PDF/TXT ingestion. Its page-based representation is unsuitable for this DOCX and will remain as a separate example.

Actual DOCX findings:

| Element | Observed structure |
|---|---|
| Source documents | 21, preceded by a corpus introduction and source list |
| Top-level paragraphs | 31,055 |
| Tables | 21; each has six rows and two columns, containing document metadata |
| Heading 1 | 22: one corpus title and 21 document titles |
| Heading 2 | 509, including full-text/reference markers and legal headings |
| Heading 3 | 195, including sections and EU articles |
| Explicit page breaks | 41 |
| Word sections | One; Word sections do not identify the 21 source documents |
| Footer | A `PAGE` field, without a usable rendered page number |

Bulgarian provisions such as `Чл. 1.` and `Чл. 2а.` occur in ordinary paragraphs. EU provisions include headings such as `Член 1`. Some heading labels and their descriptive titles occupy separate paragraphs.

The DOCX includes reference-rule excerpts and English summaries. Following your choice, all content will be preserved, with reference material labeled separately; later RAG input will be reserved for full-text regions.

## Step-by-step notebook plan

### 1. Locate and load the exact source

**What:** Identify the archive and read only its `ALL_FULL_TEXTS.docx` member into memory.

**Why:** Establish an explicit, reproducible source without accidentally ingesting reference chunks, companion documents, or evaluation data.

**How:** Use `pathlib`, `zipfile`, and `io.BytesIO`. Record the archive-relative path, member name, DOCX byte size, and SHA-256 hash.

**Design choice and trade-off:** Reading the archive member directly avoids duplicate source files. Extracting it to disk would make opening it in Word easier, but is unnecessary for parsing.

**Inspect:** A one-row source manifest and the selected member name. Missing files, duplicate matching members, or invalid ZIP/DOCX content will produce clear errors.

### 2. Inventory the DOCX before extracting content

**What:** Inspect its package parts, body element types, styles, tables, breaks, and auxiliary content.

**Why:** A successful text extraction can silently omit structure. This inventory establishes what the parser must preserve.

**How:** Use `zipfile` and standard-library XML inspection to count actual elements in `word/document.xml`, inspect style definitions, and identify footer fields and any unsupported content.

**Design choice and trade-off:** Inspect styles actually applied to paragraphs, not merely styles defined in the template. Raw XML is precise but verbose, so display selected fragments alongside readable summaries.

**Inspect:**

- Counts matching the findings above.
- Applied-style frequencies.
- The first document title, subtitle, metadata table, reference marker, and full-text marker.
- Representative legal paragraphs and the footer field.
- A list of unexpected elements requiring review.

### 3. Introduce the parsing library

**What:** Use **`python-docx` with standard-library ZIP/XML inspection**.

**Why:** `python-docx` provides readable paragraph, run, style, and table objects suitable for learning. Its `iter_inner_content()` preserves the order of body paragraphs and tables. XML inspection complements the higher-level API and supports omission checks. The documentation also identifies limitations such as paragraphs inside revision marks being absent from the paragraph list. [Official document API](https://python-docx.readthedocs.io/en/latest/api/document.html)

**How:** Add `python-docx` as a project dependency when implementation is approved. Record the installed version in notebook output and the parsed artifact. Use public APIs for normal extraction; use XML inspection for explicit breaks, field instructions, and coverage checks.

**Alternatives and trade-offs:**

| Alternative | Benefit | Trade-off for this source |
|---|---|---|
| XML-only parser | Direct access to every stored element | More low-level code and more responsibility for interpreting Word structures |
| `docx2python` | Extracts text, styles, tables, headers, footers, and notes | Its nested representation adds concepts we do not need for these straightforward metadata tables. [Project documentation](https://github.com/ShayHill/docx2python) |
| Mammoth | Produces readable HTML using semantic styles | Conversion intentionally ignores some document details, making it less direct for source-location auditing. [Project documentation](https://github.com/mwilliamson/python-mammoth) |
| Plain-text extraction | Very simple | Discards the boundaries, styles, and table relationships required here |

**Inspect:** Parse one short region with `python-docx` and compare its text, styles, and table cells with the XML inventory.

### 4. Extract ordered structural blocks

**What:** Preserve paragraphs and tables in their original sequence.

**Why:** Reading all paragraphs first and all tables afterward would detach document metadata from its title.

**How:**

- Traverse body paragraphs and tables in order.
- Assign each block a source position and reproducible identifier.
- Preserve paragraph text, style, relevant run formatting, and explicit break markers.
- Preserve table rows, cells, and cell paragraphs.
- Keep empty paragraphs, including those containing page breaks.
- Store footer content separately from body content.

**Design choice and trade-off:** Use an ordered block list with nested table cells. This is easier to inspect than a complete Word XML object model and preserves more structure than one text string. It is not intended to reproduce visual page layout.

No trimming, whitespace normalization, translation, deduplication, or boilerplate removal will occur.

**Inspect:** A compact block table showing position, type, style, text preview, and character count, plus a full-detail viewer for a selected block. Display the first metadata table with row and column coordinates.

### 5. Identify document boundaries and structural markers

**What:** Map blocks to the 21 source documents and annotate their structural roles.

**Why:** The corpus title, document titles, reference material, and full texts have different roles despite sharing some Word heading styles.

**How:**

- Treat the initial title and source list as corpus front matter.
- Recognize document starts using `Heading1` plus the observed subtitle/metadata-table pattern.
- Recognize the explicit reference-rule and full-text markers.
- Assign region labels: `front_matter`, `document_metadata`, `reference_rules`, and `full_text`.
- Preserve heading levels and annotate candidate legal markers such as `Част`, `Глава`, `Раздел`, `Чл.`, `Член`, `§`, and `Приложение`.
- Record marker evidence against the original block without splitting or rewriting its text.

**Design choice and trade-off:** Recover explicit document boundaries now, but keep legal-role annotations conservative. Word heading levels do not consistently encode legal hierarchy: parts and chapters can both use `Heading2`. Do not manufacture a definitive legal tree or infer article boundaries from every inline citation.

**Inspect:** A 21-document inventory, boundary windows around each title, region counts, and examples of Bulgarian articles, EU articles, annexes, and ambiguous headings.

This step identifies structure; it creates no chunks, overlaps, or parent-child retrieval units.

### 6. Assemble a simple intermediate representation

**What:** Build one inspectable corpus record containing provenance, document descriptors, ordered blocks, auxiliary content, and warnings.

**Why:** Later experiments need the same faithful parsed source, without making Stage 1 depend on any chunking strategy.

**How:** Use ordinary Python dictionaries and lists, serialized as UTF-8 JSON:

| Component | Proposed contents |
|---|---|
| Corpus | Schema version, source archive/member, DOCX hash, byte size, parser/version |
| Documents | Internal ID, source titles, block range, source metadata, metadata evidence locations |
| Blocks | ID, position, source locator, document ID, region, type, raw text, style, structural annotations |
| Paragraph details | Ordered runs, relevant formatting, explicit breaks |
| Table details | Ordered rows/cells containing paragraph records |
| Auxiliary content | Footer field instructions and location |
| Diagnostics | Warnings, inventory counts, validation results |

Use zero-based source positions consistently. Build identifiers from the DOCX hash and source location; these remain stable for the same file, but are not permanent legal-document identifiers across revisions.

**Design choice and trade-off:** A flat ordered block list with document references avoids duplicating text inside multiple hierarchies. Nested tables preserve their actual structure. No public API or package refactor is needed yet; the intermediate record is the Stage 1 interface.

**Inspect:** One complete document descriptor, one paragraph record, one table record, and a short contiguous sequence demonstrating their relationships.

### 7. Separate extracted metadata from derived metadata

**What:** Make the provenance of each metadata category explicit.

**Why:** A date written in a source table is different from an ingestion timestamp or an inferred legal effective date.

**How and choices:**

| Category | Fields and treatment |
|---|---|
| Directly available | Source titles, jurisdiction, source URL, official reference, version date, accessed date, notes, paragraph styles, explicit markers |
| Generated during ingestion | Hash, internal IDs, positions, counts, parser/version, schema version |
| Structural interpretation now | Document membership, region labels, candidate legal-marker roles; retain supporting block locations |
| Deferred | Normalized legal hierarchy, effective-date interpretation, language classification, topic labels, property facts, chunk metadata |

Retain metadata-table values verbatim, with links to their source cells. Do not reconcile inconsistencies or infer missing values.

The DOCX core properties contain 2013 creation/modification timestamps and identify `python-docx` as creator. Preserve these as package properties only; they are not evidence of legal publication dates or corpus freshness.

**Trade-off:** Raw strings defer convenient filtering but avoid premature date and jurisdiction normalization. No attempt will be made to reproduce reference-chunk timestamps.

**Inspect:** A metadata table with columns for value, provenance category, and evidence location.

### 8. Validate, save, and stop for review

**What:** Verify that the representation accounts for the source, then save a separate Stage 1 artifact.

**Why:** Nonempty output alone does not establish parsing fidelity.

**How:** Save to `data/processed/01_parsed_docx_structure.json`, leaving the existing PDF/TXT artifact untouched. Reload it and compare it with the in-memory record.

**Design choice and trade-off:** JSON is easy to inspect and preserves nesting. It is adequate for this source; a database or streaming format would add unnecessary complexity.

**Inspect:** A pass/fail validation summary, unresolved warnings, representative full-text previews, and artifact size. Large text remains selectable rather than flooding notebook output.

## Validation and acceptance criteria

- Account for all **31,055 body paragraphs**, **21 tables**, **126 table rows**, and **252 cells**, plus the separately recorded section properties.
- Reconcile **31,307 total body/table paragraphs** without counting table text twice.
- Preserve all **41 explicit page breaks** and distinguish them from rendered page numbers.
- Recover **21 document boundaries** and **21 full-text markers**; distinguish the corpus title from document titles.
- Allow documents without reference-rule sections.
- Compare extracted paragraph and cell text with independently read XML text at matching locations; test break events separately.
- Verify ordered, unique block IDs and valid document references.
- Confirm that no body content is silently unassigned or discarded.
- Manually inspect boundary transitions, long provisions, Cyrillic characters, article suffixes, metadata tables, and the final source document.
- Preserve website navigation and footer-like text occurring inside source full text. Some remains despite source notes claiming removal; cleaning is deferred.
- Exercise small parsing cases covering mixed paragraph/table order, empty paragraphs with breaks, malformed input, missing metadata, and unexpected structures.
- Confirm identical structural output on rerun and exact JSON round-trip equality.

These checks establish fidelity to the supplied DOCX, not completeness or legal correctness of the original websites.

## Assumptions and approval boundary

- The combined DOCX is the sole ingestion input. Reference chunks, golden data, companion TXT/DOCX files, and external URLs will not supply missing content.
- Reference rules will be preserved and labeled separately, as you selected.
- Original Bulgarian and English text will remain unchanged.
- Physical page numbers will remain unavailable; source block locations provide traceability.
- Implementation will remain notebook-first, with small explanatory cells. Production module extraction is deferred.
- Approval will cover this Stage 1 notebook, its DOCX dependency, the separate parsed artifact, and brief setup documentation updates.
- No cleaning, chunking, embeddings, storage for retrieval, retrieval, reranking, generation, evaluation, or agents will be implemented.

No further clarification is required for this Stage 1 design. Code and file changes await your approval.
