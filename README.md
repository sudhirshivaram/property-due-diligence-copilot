# Property Investment Due-Diligence Copilot

An incremental project following the mentor’s package structure. **Stage 1:
document ingestion/parsing** and **Stage 2: chunking experiments** now run from
`src/property_copilot/` through thin notebooks. Later application stages remain
planned. See [the architecture and current folder layout](docs/architecture.md).

## Run locally

Use Python 3.11 or newer. From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m jupyterlab
```

Place your supplied `bg_legal_corpus_real.zip` in `data/raw/`. The notebook reads
only `bg_legal_corpus_real/full_text/ALL_FULL_TEXTS.docx` inside that archive.
The source archive and golden evaluation dataset are not included in this repository.
Reference chunks and evaluation data are not used as parsing input.

Open `notebooks/01_document_ingestion_parsing.ipynb`, select the project `.venv`
kernel, then restart and run all cells. Jupyter may start from the project or
notebooks directory. Explanations and intermediate outputs guide each step.
No external model or service is called.

## Stage 1 behavior and output

The notebook loads the DOCX, inventories its structure, preserves ordered
paragraphs/tables and explicit breaks, identifies source-document boundaries
and candidate legal markers, and assembles an evidence-linked corpus.
Metadata categories distinguish source values, generated provenance, structural
interpretations and deferred decisions. The Black Sea Coast Act is source
Document #9 in the supplied corpus.

Step 8 reports PASS/FAIL fidelity checks and unresolved review items. After
validation passes it writes `data/processed/01_parsed_docx_structure.json`,
reloads the JSON to check exact equality, and checks that the original archive
is unchanged. Rerunning replaces only this derived artifact. Two complete runs
were verified to produce identical artifact bytes.

The inspected source contains 21 documents, 31,055 body paragraphs, 21 tables,
and 126 source metadata rows. Unclassified headings and source-page navigation
are retained. Validation establishes fidelity to the DOCX, not legal accuracy or
Word page rendering. Stage 1 performs no cleaning, chunking, embeddings, vector storage, retrieval,
RAG, or evaluation. Chunk metadata inheritance remains undecided.

See [the approved Stage 1 plan](docs/stage-01-ingestion-parsing-plan.md).
The [broader project plan](docs/project-plan.md) preserves the historical learning
sequence; [architecture.md](docs/architecture.md) is authoritative for the current
mentor-aligned layout and Stage 1/Stage 2 numbering.

## Files kept local

Git ignores `.venv/`, source archives, processed artifacts, evaluation data and
local environment files. Obsolete TXT/PDF scaffold samples were removed; the
current workflow uses the local DOCX corpus archive.

The committed notebook has no saved outputs. Run it locally to recreate them;
clear notebook outputs before committing changes. A local executed copy, when
present, is `data/processed/01_document_ingestion_parsing.executed.ipynb` and is
ignored by Git. Do not commit private source content or credentials.

Dependencies have compatibility ranges; capture an exact tested lock before
CI/deployment. This is a learning implementation, not a production ingestion service.

## Stage 2 — Steps 1–12: chunking experiments

Open `notebooks/02_chunking_experiments.ipynb` with the project kernel, then restart
and run all cells. Steps 1–7 retain the frozen setup, fixed-length and uncapped
structural baselines, and parent-child alternatives. Step 8 compares exact and
paragraph/whitespace-aware children inside complete oversized structural parents.

The experiment tests 2,000/4,000/8,000-character triggers, 1,000/2,000-character
child targets and 0%/10% overlap. It displays affected unit types, measured overlap,
source maps, cut reasons and matched diagnostics on the same four complete documents.
Complete parents remain visible as the control. These parameters are experimental
probes; Step 12 records a provisional shortlist rather than a production strategy. Step 9 adds separate candidate annotations for publication lists and inline amendment
notes, character-share measurements, and existing-boundary witnesses. Original text
remains unchanged; no effective-date or legal-status assertions are made.
Step 10 preserves all document metadata in a source-backed registry and displays
minimal and selectively joined views of an existing child, with explicit structural,
relationship and provenance evidence. No production metadata schema is selected.
Step 11 aligns the frozen samples across existing strategies, records an explicit
reviewer rubric, then reads mentor excerpts separately for citation/text correspondence.
Mentor references never enter chunk builders and are not exhaustive ground truth.
Step 12 tests an evidence-gated hybrid composed from the original structural units
and Step 8 child spans, with a provisional lead and sensitivity shortlist. It reports
regressions, validates exact preservation, and writes a local Stage 2 decision summary.
The notebook stops after Step 12 for review. Embeddings, vector storage, retrieval,
reranking, RAG, LLM calls and agents remain unimplemented.

Frozen manifests, separate deterministic reports and executed notebooks belong in
the ignored `data/processed/02_chunking_experiments/package_refactor_v1/` directory.
Pre-refactor reports and notebook recovery copies were archived outside the repository
during cleanup; current reports are regenerated by the package workflow. Source notebook
outputs remain cleared. See the [Stage 2 plan](docs/stage-02-chunking-experiments-plan.md).


## Package and command-line use

Install the package with the setup command above after pulling this refactor.
The workflows discover the project from the project/notebooks directory, or
accept an explicit root:

```python
from property_copilot.ingestion import IngestionWorkflow
from property_copilot.chunking import ChunkingExperiments, fixed_length_windows

windows = fixed_length_windows("Example source text", length=10, overlap=2)
# Full reviewed corpus workflows (require the local source archive):
# ingestion = IngestionWorkflow(root="/path/to/project").run()
# experiments = ChunkingExperiments(root="/path/to/project").run()
```

```bash
property-copilot ingest
property-copilot chunk
python -m pytest
```

`python -m property_copilot.cli` is equivalent to the installed command.
`build-index` and `run-query` report that those stages are not implemented.
Copy `.env.example` to `.env` when service credentials are needed; the current
workflows need none. The optional API shell can be installed with `.[api]` and
served with `uvicorn property_copilot.api.main:app`; it exposes `/health` only.

See [tests/README.md](tests/README.md) for the optional full private-corpus
regression. Keep notebook outputs cleared in Git; running cells still displays
the existing inspection tables and examples.
