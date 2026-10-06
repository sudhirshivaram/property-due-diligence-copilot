import hashlib
import json

import pytest

from property_copilot.chunking import ChunkingExperiments
from property_copilot.chunking import integrity
from property_copilot.cli import main
from property_copilot.config import Settings, find_project_root
from property_copilot.ingestion import IngestionWorkflow


def test_workflow_construction_is_isolated_and_has_no_outputs(tmp_path):
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "notebooks").mkdir()
    first = ChunkingExperiments(tmp_path)
    second = ChunkingExperiments(tmp_path)
    first.VIEWS = {"example": {}}
    assert not hasattr(second, "VIEWS")
    assert IngestionWorkflow(tmp_path).ROOT == tmp_path
    assert not (tmp_path / "data").exists()
    for workflow in (first, second, IngestionWorkflow(tmp_path)):
        assert len(workflow.steps) == len(set(workflow.steps))
        assert all(callable(getattr(workflow, step)) for step in workflow.steps)


def test_project_root_discovery_from_notebooks(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "notebooks").mkdir()
    monkeypatch.chdir(tmp_path / "notebooks")
    assert find_project_root() == tmp_path
    with pytest.raises(FileNotFoundError):
        find_project_root(tmp_path / "missing")


def test_future_cli_commands_do_not_pretend_to_work(capsys):
    with pytest.raises(SystemExit) as result:
        main(["build-index"])
    assert result.value.code == 2
    assert "not implemented" in capsys.readouterr().err


def test_settings_redact_credentials(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://private-example")
    settings = Settings(_env_file=None)
    assert settings.database_url.get_secret_value() == "postgresql://private-example"
    assert "private-example" not in repr(settings)


def test_integrity_rejects_changed_notebook_and_active_package(tmp_path, monkeypatch):
    package = tmp_path / "installed/property_copilot"
    module = package / "chunking/integrity.py"
    module.parent.mkdir(parents=True)
    module.write_text("# fixture")
    notebook = tmp_path / "notebooks/test.ipynb"
    notebook.parent.mkdir()
    notebook.write_text("{}")
    pins = {
        "src/property_copilot/chunking/integrity.py": hashlib.sha256(
            module.read_bytes()
        ).hexdigest(),
        "notebooks/test.ipynb": hashlib.sha256(notebook.read_bytes()).hexdigest(),
    }
    module.with_name("implementation_manifest.json").write_text(json.dumps(pins))
    monkeypatch.setattr(integrity, "__file__", str(module))
    assert integrity.verify_implementation(tmp_path) == pins
    notebook.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="notebooks/test"):
        integrity.verify_implementation(tmp_path)
    notebook.write_text("{}")
    module.write_text("# changed implementation")
    with pytest.raises(ValueError, match="src/property_copilot"):
        integrity.verify_implementation(tmp_path)
