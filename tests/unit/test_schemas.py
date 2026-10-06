import pytest
from pydantic import ValidationError

from property_copilot.schemas import Chunk, ChunkMetadata, SourceSpan


def span(**changes):
    return (
        dict(
            kind="source",
            stream_start=0,
            stream_end=3,
            block_id="b",
            position=0,
            block_start=0,
            block_end=3,
            source={"part": "word/document.xml", "path": "/body/0"},
        )
        | changes
    )


def test_chunk_contract_checks_interval_and_coverage():
    fields = dict(
        id="c",
        text="abc",
        start=0,
        end=3,
        metadata=ChunkMetadata(document_id="d", strategy="fixed"),
        source_spans=[span()],
    )
    assert Chunk.model_validate(fields).text == "abc"
    with pytest.raises(ValidationError, match="character interval"):
        Chunk.model_validate(fields | {"end": 4})
    with pytest.raises(ValidationError, match="without gaps"):
        Chunk.model_validate(
            fields | {"source_spans": [span(stream_start=1, block_start=1)]}
        )


@pytest.mark.parametrize(
    "changes",
    [{"stream_start": -1}, {"block_end": 4}, {"text": "\n"}, {"stream_end": 0}],
)
def test_source_span_rejects_false_provenance(changes):
    with pytest.raises(ValidationError):
        SourceSpan.model_validate(span(**changes))
