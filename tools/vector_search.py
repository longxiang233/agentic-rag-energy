import time
from langchain_core.tools import tool
from rag_bridge import get_rag_engine
from tools.error_handler import make_failure_response, is_empty_result, log_tool_call

SCORE_THRESHOLD = 1.02   # 低于这个分数的相关
_last_citations = []    # list[dict]，每次调用前清空
_last_status = "ok"    # 本次调用的原始状态

@tool
def vector_search(query:str, top_k:int = 5) -> str:
    """在新能源政策知识库中检索相关文档。输入自然语言查询，返回文档片段和来源"""
    global _last_citations, _last_status
    _last_citations = []
    _last_status = "ok"
    
    start = time.time()
    if not query or not query.strip():
        _last_status = "clarify"
        return str(make_failure_response("clarify", "请提供查询关键词"))
    
    engine = get_rag_engine()
    docs = engine.retrieve(query, top_k=top_k)
    docs = [d for d in docs if d["score"] <= SCORE_THRESHOLD]
    latency = int((time.time() - start) * 1000)

    if is_empty_result(docs):
        _last_status = "empty"
        log_tool_call(None, "vector_search", "empty", 0, latency, user_query=query)
        return str(make_failure_response("empty", "未找到相关文档，建议换关键词"))

    _last_status = "ok"
    _last_citations = [
        {"source": d["source"], "content": d["content"][:100],
        "score": d["score"], "tool": "vector_search"}
        for d in docs[:3]
    ]
    log_tool_call(None, "vector_search", "ok", 0, latency, user_query=query)
    lines = [f"[{i}] 来源: {d['source']}\n{d['content']}\n" for i, d in enumerate(docs, 1)]
    return "\n".join(lines)