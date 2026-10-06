"""Source-span contracts for existing experiments, plus a provisional chunk envelope.

The envelope is additive: it does not select a production metadata policy or
replace the reviewed experiment dictionaries and their content hashes.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    kind: Literal["source", "separator"]
    stream_start: int = Field(ge=0)
    stream_end: int = Field(gt=0)
    block_id: str | None = None
    position: int | None = Field(default=None, ge=0)
    block_start: int | None = Field(default=None, ge=0)
    block_end: int | None = Field(default=None, gt=0)
    source: dict[str, str] | None = None
    text: str | None = None
    left_block_id: str | None = None
    right_block_id: str | None = None

    @model_validator(mode="after")
    def valid_span(self):
        length = self.stream_end - self.stream_start
        if length <= 0:
            raise ValueError("Source spans must be nonempty half-open intervals")
        if self.kind == "source":
            if not self.block_id or self.position is None or not self.source:
                raise ValueError("Source spans require a block and source locator")
            if (
                self.block_start is None
                or self.block_end is None
                or self.block_end - self.block_start != length
            ):
                raise ValueError("Block and stream spans must have equal lengths")
            if (
                self.text is not None
                or self.left_block_id is not None
                or self.right_block_id is not None
            ):
                raise ValueError("Source spans cannot contain separator fields")
        else:
            if (
                self.text != "\n"
                or length != 1
                or not self.left_block_id
                or not self.right_block_id
            ):
                raise ValueError(
                    "Separators must identify an added newline and its neighboring blocks"
                )
            if any(
                value is not None
                for value in (
                    self.block_id,
                    self.position,
                    self.block_start,
                    self.block_end,
                    self.source,
                )
            ):
                raise ValueError("Separators cannot claim source-block offsets")
        return self


class ChunkMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    document_id: str = Field(min_length=1)
    strategy: str = Field(min_length=1)
    parent_id: str | None = None


class Chunk(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    metadata: ChunkMetadata
    source_spans: list[SourceSpan] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_coverage(self):
        if self.end - self.start != len(self.text):
            raise ValueError("Chunk text must match its character interval")
        cursor = self.start
        for span in self.source_spans:
            if span.stream_start != cursor:
                raise ValueError(
                    "Source spans must cover the chunk in order without gaps or overlap"
                )
            cursor = span.stream_end
        if cursor != self.end:
            raise ValueError("Source spans must cover the complete chunk")
        return self
