"""Run the local reviewed workflows without opening a notebook."""

import argparse
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, help="Project directory (defaults to discovery from cwd)"
    )
    parser.add_argument(
        "command", choices=("ingest", "chunk", "build-index", "run-query")
    )
    args = parser.parse_args(argv)
    if args.command in {"build-index", "run-query"}:
        parser.error(
            f"{args.command} is planned; embeddings, storage and retrieval are not implemented"
        )
    if args.command == "ingest":
        from .ingestion import IngestionWorkflow

        IngestionWorkflow(args.root).run()
    else:
        from .chunking import ChunkingExperiments

        ChunkingExperiments(args.root).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
