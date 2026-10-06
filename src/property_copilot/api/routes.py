"""Service liveness only; retrieval and legal analysis remain future work."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "pipeline": "ingestion-and-chunking-experiments"}
