class RetrievalServiceError(Exception):
    """Raised when the retrieval (embedding/reranking) subsystem fails to contact the inference backend."""
    pass
