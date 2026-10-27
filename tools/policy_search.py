import time
from langchain_core.tools import tool
from rag_bridge import get_rag_engine
from tools.error_handler import make_failure_response, is_empty_result, log_tool_call

SCORE_THRESHOLD = 1.02
_last_citations = []   # list[dict]，每次调用前清空
_last_status = "ok"    # 本次调用的原始状态

@tool
def policy_search(query:str, top_k:int = 5) -> str:
    """查询新能源政策条款、补贴标准、并网规则、市场参与规则、备案要求、政策文件出处。
    输入：政策相关问题，如"独立储能可参与哪些市场"、"新型储能备案材料"、"某条款出自哪个文件"。
    返回：政策原文片段+来源文件。
    触发场景：问题涉及政策文件、规定、备案、市场规则、条款出处时，优先用本工具。
    不适用：只查具体电价数字用 price_query，只查术语解释/行业概念用 vector_search。"""

    global _last_citations, _last_status
    _last_citations = []
    _last_status = "ok"

    start = time.time()
    if not query or not query.strip():
        _last_status = "clarify"
        return str(make_failure_response("clarify", "请提供查询关键词"))
    
    engine = get_rag_engine()
    docs = engine.retrieve(query, top_k=top_k)
    latency = int((time.time() - start) * 1000)

    policy_docs = [d for d in docs
               if ("政策" in d["source"] or "管理" in d["source"])
               and d["score"] <= SCORE_THRESHOLD]

    if is_empty_result(policy_docs):
        log_tool_call(None, "policy_search", "empty", 0, latency, user_query=query)
        # 降级到 vector_search，函数内 import 防循环
        from tools.vector_search import vector_search
        import tools.vector_search as vs_module   # ← 新加，为了拿 vector 的 citations
        
        fallback = vector_search.invoke({"query": query, "top_k": top_k})
        
        # fallback 是 str，判断是否也是空/失败
        if fallback.startswith("{'status'") or fallback.startswith('{"status"'):
            # 降级后 vector 也失败
            _last_status = "degraded"
            _last_citations = []
            log_tool_call(None, "policy_search", "degraded", 0, latency, user_query=query)
            return str(make_failure_response(
                "degraded", "未找到相关政策或通用信息，建议换关键词"))

        # 降级成功，citations 来自 vector
        _last_status = "fallback"
        _last_citations = vs_module._last_citations   # ← 关键：复制 vector 的 citations
        log_tool_call(None, "policy_search", "fallback", 0, latency, user_query=query)
        return str(make_failure_response(
            "fallback", "未找到政策条款，已切换通用检索",
            data=fallback[:200]))

    _last_status = "ok"
    _last_citations = [
        {"source": d["source"], "content": d["content"][:100],
         "score": d["score"], "tool": "policy_search"}
        for d in policy_docs[:3]
    ]
    log_tool_call(None, "policy_search", "ok", 0, latency, user_query=query)
    lines = [f"[{i}] 来源: {d['source']}\n{d['content']}\n" for i, d in enumerate(policy_docs, 1)]
    return "\n".join(lines)