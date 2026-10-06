# Package refactor validation — October 6, 2026

The original notebooks were executed in an isolated project copy before extracting
their implementation. Their measured result fingerprints are recorded in
`tests/integration/refactor_fingerprints.json` without private source text.

The refactored thin notebook cells were then executed from a fresh temporary
project with a copy of the same archive. All recorded experiment IDs and result
fingerprints matched, including the hybrid result.

- **33 unit tests passed**: parsing inputs, stable IDs, splitters, Unicode coverage,
  source spans, parent-child links, schemas, configuration and integrity checks.
- **Full corpus integration test passed**: both notebooks' code cells, all embedded
  assertions, and all baseline fingerprint comparisons (152 seconds).
- **Stage 1 JSON is byte-for-byte identical**: SHA-256
  `caa696a76ea403bf1ddf074aa503fd4362162d128e32a2c755570464bc95ebdc`.
- **Eight pre-hybrid JSON artifacts are byte-for-byte identical**: frozen sample
  manifest and fixed, structural, parent-child, oversized, history, metadata and
  strategy-comparison reports.
- **Hybrid result fingerprint is unchanged**:
  `da3636e8da34e024008fe60c43529e8cb68077012bfbebb3e78e62abc7754600`.
  Its audit report changes intentionally to identify the refactored package and
  notebook files and the separate report directory.
- **Real Jupyter kernel smoke check passed**: both notebooks' entry cells imported
  the installed package from the notebooks directory; rich display worked.
- Editable package installation, CLI help, API OpenAPI `/health` registration,
  dependency consistency, Ruff undefined-name/import checks and `git diff --check`
  passed. Committed notebook sources have no stored outputs.

The complete notebook-cell regression runs directly in Python. The Jupyter check
covers kernel startup, imports and rich output, not a second full corpus run.
Legal correctness, retrieval quality and production readiness are not established
by these refactor checks.

Run instructions are in [tests/README.md](../tests/README.md). The current structure
and data flow are in [Architecture.md](Architecture.md).
