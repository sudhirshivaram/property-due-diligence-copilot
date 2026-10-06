"""Private-corpus regression, opt in with PROPERTY_COPILOT_CORPUS_TESTS=1."""

import json
import os
import shutil
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.corpus,
    pytest.mark.skipif(
        os.environ.get("PROPERTY_COPILOT_CORPUS_TESTS") != "1",
        reason="Set PROPERTY_COPILOT_CORPUS_TESTS=1 to run the private corpus workflows",
    ),
]


def test_thin_notebooks_match_original_results(tmp_path, monkeypatch):
    import property_copilot._display as presentation

    root = Path(__file__).resolve().parents[2]
    archive = root / "data/raw/bg_legal_corpus_real.zip"
    if not archive.is_file():
        pytest.skip("Private source archive is unavailable")
    for directory in ("notebooks", "docs", "src"):
        shutil.copytree(root / directory, tmp_path / directory)
    shutil.copy2(root / "pyproject.toml", tmp_path / "pyproject.toml")
    (tmp_path / "data/raw").mkdir(parents=True)
    shutil.copy2(archive, tmp_path / "data/raw" / archive.name)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(presentation, "display", lambda *args, **kwargs: None)
    expected = json.loads(
        (root / "tests/fixtures/refactor_fingerprints.json").read_text()
    )
    for notebook_name, fingerprints in expected.items():
        notebook = json.loads((tmp_path / "notebooks" / notebook_name).read_text())
        namespace = {}
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                # Execute the actual thin cells, not a second implementation of the sequence.
                exec(compile("".join(cell["source"]), notebook_name, "exec"), namespace)
        workflow = namespace["workflow"]
        for name, value in fingerprints.items():
            assert getattr(workflow, name) == value, f"{notebook_name}: {name}"
