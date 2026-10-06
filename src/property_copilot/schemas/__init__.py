"""Shared contracts. Experimental dictionaries retain their original serialized form."""

from .chunk import Chunk, ChunkMetadata, SourceSpan

__all__ = ["Chunk", "ChunkMetadata", "SourceSpan"]
