import os

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

_EMBEDDER = None
_EMBEDDER_READY = False
_EMBEDDER_FAILED = False


def _load_embedder():
    global _EMBEDDER, _EMBEDDER_READY, _EMBEDDER_FAILED
    if _EMBEDDER_READY:
        return _EMBEDDER
    if _EMBEDDER_FAILED:
        return None
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        _EMBEDDER_FAILED = True
        return None

    try:
        _EMBEDDER = SentenceTransformer(EMBEDDING_MODEL)
        _EMBEDDER_READY = True
        return _EMBEDDER
    except Exception:
        _EMBEDDER_FAILED = True
        return None


def is_embedding_ready() -> bool:
    return _EMBEDDER_READY


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    if not texts:
        return []
    model = _load_embedder()
    if model is None:
        return None
    try:
        vectors = model.encode(texts, normalize_embeddings=True)
    except Exception:
        return None

    return [[float(value) for value in vector] for vector in vectors]
