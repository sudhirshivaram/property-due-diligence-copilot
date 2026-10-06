"""Local paths and optional service settings; loading settings opens no connections."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: SecretStr | None = None
    openai_api_key: SecretStr | None = None


def find_project_root(root: str | Path | None = None) -> Path:
    """Resolve an explicit project root, or discover it from the working directory."""
    start = Path(root).expanduser().resolve() if root is not None else Path.cwd()
    candidates = (start,) if root is not None else (start, *start.parents)
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "notebooks"
        ).is_dir():
            return candidate
    raise FileNotFoundError(
        "Use the project/notebooks directory or provide the project root."
    )
