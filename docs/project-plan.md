# Historical architecture and incremental plan

> **Superseded structure and numbering:** The mentor’s October 6, 2026 layout
> and the authorized package refactor are documented in [architecture.md](architecture.md).
> Current Stage 1 = DOCX ingestion/parsing; Stage 2 = chunking. The table below
> retains the original Clean/Chunk sequence for historical context only.
> Its module paths, TXT/PDF scaffold and refactor approval gates are historical.

Repository: `property-due-diligence-copilot`; Python import: `property_copilot`.
Use a single Python package with a `src/` layout. This keeps imports tied to
an installed package and gives us module boundaries without microservices.

## Structure

```text
property-due-diligence-copilot/
  pyproject.toml                  # Package, dependencies, test configuration
  README.md                      # Setup and current review gate
  docs/project-plan.md           # Architecture, decisions, acceptance criteria
  notebooks/                     # Numbered experiments and visible outputs
    01_ingestion_and_parsing.ipynb
  data/
    samples/                     # Committed synthetic fixtures
    raw/                         # Local originals; ignored by Git
    processed/                   # Derived local artifacts; ignored by Git
  src/property_copilot/
    __init__.py                  # Package shell; no premature implementation
  tests/README.md                # Test plan for the first production refactor
```

Add modules only when the corresponding notebook is understood and approved:

| Future path under src/property_copilot | Responsibility |
| --- | --- |
| schemas.py | Shared document/page/chunk records and validated contracts |
| ingestion/ | Discovery, validation, format-specific parsers |
| cleaning.py | Reversible text normalization with original text retained |
| chunking.py | Passage boundaries, overlap, IDs and source mapping |
| metadata.py | Property facts with evidence, uncertainty and schema validation |
| embeddings.py | Model adapter, batching and model/version identity |
| vector_store.py | Index write/read adapter and persistence |
| retrieval.py | Query/filter logic and candidate selection |
| reranking.py | Optional candidate scoring after retrieval |
| rag.py | Evidence-grounded prompt construction and cited answers |
| evaluation/ | Labeled fixtures, retrieval and answer quality metrics |
| agents/ | Optional bounded tool orchestration, added only if justified |
| config.py | Central runtime configuration when first needed |
| api/ | Optional service interface after the pipeline is stable |

`tests/unit/` will test pure behavior; `tests/integration/` will test adapters
and component boundaries. Add CI, an exact dependency lock and deployment
configuration when production code is promoted. Avoid a web server, task queue,
agent framework or vector database until the relevant stage needs one.

## Learning sequence and review gates

Each stage follows: explain → run notebook → inspect output → compare alternatives
→ user review → extract reusable code → test → thin notebook → next approval.
No later stage is implemented yet.

| Stage | Visible output / acceptance evidence | Main decision |
| --- | --- | --- |
| 1. Ingest and parse | File manifest, raw page text, IDs, errors and JSONL round-trip | TXT + embedded-text PDF first; OCR/layout parsers if justified |
| 2. Clean | Before/after diffs, retained page references, regression examples | Conservative whitespace/header rules versus aggressive cleanup |
| 3. Chunk | Boundary previews, lengths, overlap and source mapping | Start structural/size-based; compare token-based splitting |
| 4. Extract metadata | Structured facts, supporting quotes, missing/conflicting values | Rules first; schema-validated model extraction where useful |
| 5. Embed | Vector shape, norms, nearest-neighbor sanity examples | Local versus hosted model, cost and document privacy |
| 6. Store vectors | Insert/query/reload results with model/index version | Local persistence first; managed store when scale requires it |
| 7. Retrieve | Ranked passages and recall on labeled questions | Dense search versus hybrid search and explicit filters |
| 8. Rerank | Before/after ranking, quality gain and latency | Keep only if measured benefit warrants cost |
| 9. RAG | Answers linked to document/page evidence and abstention examples | Evidence sufficiency, conflicting facts, prompt-injection handling |
| 10. Evaluate | Retrieval recall, citation correctness, supported claims, latency/cost | Small curated corpus first; evaluation begins in earlier stages |
| 11. Optional agents | Inspectable tool trace, bounded steps and failure cases | Add only for tasks that require dynamic multi-step decisions |

## Stage 1 decisions

Ingestion discovers and validates files. Parsing converts bytes to page text.
Neither step verifies financial statements or interprets investment merit.
SHA-256 identifies file content; relative source paths distinguish occurrences
of identical files. PDF page numbers are one-based physical indices, not printed
page labels. TXT is one logical page. Preserve raw extracted text unchanged.
Only provenance metadata is collected now; property fact extraction comes later.

The initial contract is one document record containing schema version, content ID,
relative source, byte size, parser/version, page records, status and warnings.
Failures are explicit and do not stop other documents. File-level exceptions
are contained at the batch boundary; production will refine error categories.
Empty extracted pages require review: they may be blank, scanned, or failed extraction.
Mixed text/image PDFs can still omit important content despite nonempty text.
No automatic claim that extraction is complete is made.

Use `pypdf` for a small, inspectable starting point. Its text extraction cannot
perform OCR and PDF reading order/layout is inherently imperfect. See the
[official extraction documentation](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).
Consider a layout-aware parser for tables/columns and OCR for scans only after
examining representative documents; added dependencies, runtime and quality
checks must be justified. We intentionally do not reconstruct rent-roll tables.

The notebook imposes a 20 MiB file limit, rejects symlinks and encrypted PDFs,
and uses strict UTF-8 decoding for TXT. These are teaching defaults, not a full
security boundary. Before service deployment add isolated parsing workers,
time/memory limits, access controls, retention policy and structured diagnostics.
No hosted ingestion, OCR, LLM, embedding or vector service is required yet.

## Stage 1 approval checklist

- Restart and run all cells; inspect the manifest and full page previews.
- Verify two synthetic PDF pages and one TXT page preserve their source references.
- Confirm malformed, empty, unsupported and encrypted examples are surfaced.
- Try representative local documents and compare extracted text against originals.
- Decide whether DOCX, scans, tables or printed page labels are required next.
- Approve the stage 1 refactor separately from stage 2 cleaning.

After review, move contracts to `schemas.py` and discovery/parsing functions to
`ingestion/`. Keep sample selection, inspection tables and experiments in the
notebook. Unit-test IDs, UTF-8 decoding, validation, statuses and page numbering;
integration-test actual PDF fixtures and artifact round-trips. Re-run the thin
notebook against package functions to ensure the behavior remains understood.
