# Property Investment Due-Diligence Copilot

An incremental, notebook-first project. **Stage 1: document ingestion and parsing**
is complete. All later stages require separate review and approval.

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
Word page rendering. No cleaning, chunking, embeddings, vector storage, retrieval,
RAG, or evaluation is implemented. Chunk metadata inheritance remains undecided.

See [the approved Stage 1 plan](docs/stage-01-ingestion-parsing-plan.md).
The next stage requires review and approval of the notebook results and artifact.
The [broader project plan](docs/project-plan.md) records the original scaffold
and future architecture; the approved Stage 1 plan describes the current DOCX work.

## Files kept local

Git ignores `.venv/`, source archives, processed artifacts, evaluation data and
local environment files. Synthetic samples under `data/samples/` are included
as examples from the earlier scaffold; they are not inputs to the DOCX notebook.

The committed notebook has no saved outputs. Run it locally to recreate them;
clear notebook outputs before committing changes. A local executed copy, when
present, is `data/processed/01_document_ingestion_parsing.executed.ipynb` and is
ignored by Git. Do not commit private source content or credentials.

Dependencies have compatibility ranges; capture an exact tested lock before
CI/deployment. This is a learning implementation, not a production ingestion service.
