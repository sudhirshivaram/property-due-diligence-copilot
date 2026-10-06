"""Pin the refactored implementation, including code moved out of notebook cells."""

import hashlib
import json
from pathlib import Path


def verify_implementation(root: Path) -> dict[str, str]:
    """Reject code drift; pins change only with an explicitly reviewed refactor."""
    manifest = Path(__file__).with_name("implementation_manifest.json")
    expected = json.loads(manifest.read_text(encoding="utf-8"))
    for relative, digest in expected.items():
        prefix = "src/property_copilot/"
        path = (
            Path(__file__).resolve().parents[1] / relative.removeprefix(prefix)
            if relative.startswith(prefix)
            else root / relative
        )
        if (
            not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest
        ):
            raise ValueError(
                f"Refactored implementation changed: {relative}. Review before updating the pin."
            )
    return expected
