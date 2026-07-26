"""Token-aware chunking so long fields never silently truncate at the
embedding model's 512-token context window.

Token counts here are an approximation (tiktoken's cl100k_base encoding,
not the exact Arctic Embed tokenizer) - close enough to decide "does this
need chunking," not used for anything requiring exact precision.
"""

import tiktoken

_ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_THRESHOLD_TOKENS = 450
CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 75


def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


def needs_chunking(text: str) -> bool:
    return count_tokens(text) > CHUNK_THRESHOLD_TOKENS


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks of roughly CHUNK_SIZE_TOKENS tokens."""
    tokens = _ENCODING.encode(text)
    if len(tokens) <= CHUNK_SIZE_TOKENS:
        return [text]

    chunks = []
    start = 0
    step = CHUNK_SIZE_TOKENS - CHUNK_OVERLAP_TOKENS
    while start < len(tokens):
        chunk_tokens = tokens[start : start + CHUNK_SIZE_TOKENS]
        chunks.append(_ENCODING.decode(chunk_tokens))
        if start + CHUNK_SIZE_TOKENS >= len(tokens):
            break
        start += step
    return chunks
