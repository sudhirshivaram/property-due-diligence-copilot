# Tests

Run `python -m pytest` for synthetic unit tests covering exact ZIP-member loading,
source identities, Unicode/overlap preservation, source-map separators,
parent-child containment and reconstruction, schema validation, isolated workflow
state, configuration and implementation-integrity guards. No network is used.

The complete private-corpus regression is opt-in:

```bash
PROPERTY_COPILOT_CORPUS_TESTS=1 python -m pytest tests/integration -q
```

It copies the source archive to a temporary project, runs the actual thin notebook
cells in order, retains their embedded validation cases, and compares the Stage 1
artifact and every recorded experiment/result fingerprint against the independently
executed original notebooks. It requires `data/raw/bg_legal_corpus_real.zip`; the
archive and derived artifacts are never committed. This test runs Python cells
directly; Jupyter kernel execution is a separate smoke check.

`tests/eval/` is reserved for later golden-set retrieval metrics. Database/API
integration and Act 16 tests belong here when those components are implemented.
