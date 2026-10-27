from rag.rag_engine import RAGEngine

_engine = None

def get_rag_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine