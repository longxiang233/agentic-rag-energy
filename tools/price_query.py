import time
from langchain_core.tools import tool
from tools.error_handler import make_failure_response, log_tool_call

PRICE_DATA = {
    "峰谷价差": {"尖峰": 1.2, "高峰": 1.0, "平段": 0.7, "低谷": 0.3, "价差": 0.9, "单位": "元/kWh", "来源": "山东2025电价政策"},
    "容量补偿": {"独立储能": 0.0705, "单位": "元/kWh", "来源": "山东独立储能政策"},
    "现货价格": {"上限": 1.5, "下限": 0.0, "单位": "元/kWh", "来源": "山东现货市场规则"},
}

_last_citations = []   # price_query 不走向量检索，恒为空
_last_status = "ok"

@tool
def price_query(query: str) -> str:
    """查询山东峰谷电价、容量补偿单价、现货价格上限下限。
    输入：电价相关问题，如"峰谷价差"、"容量补偿多少钱"、"现货价格上限"。
    返回：结构化电价数字+来源。
    不适用：查政策条款原文用 policy_search，查通用概念用 vector_search。"""
    start = time.time()

    global _last_citations, _last_status
    _last_citations = []
    _last_status = "ok"

    if not query or not query.strip():
        _last_status = "clarify"
        return str(make_failure_response("clarify", "请提供查询关键词"))

    q = query.lower()

    if "容量补偿" in q or "补偿" in q:
        d = PRICE_DATA["容量补偿"]
        latency = int((time.time() - start) * 1000)
        log_tool_call(None, "price_query", "ok", 0, latency, user_query=query)
        _last_status = "ok"
        #_last_citations 保持空，price_query 不产生 citation
        log_tool_call(None, "price_query", "ok", 0, latency, user_query=query)
        return f"独立储能容量补偿：{d['独立储能']} {d['单位']}，来源：{d['来源']}"

    if "峰谷" in q or "尖峰" in q or "价差" in q:
        d = PRICE_DATA["峰谷价差"]
        latency = int((time.time() - start) * 1000)
        _last_status = "ok"
        # _last_citations 保持空，price_query 不产生 citation
        log_tool_call(None, "price_query", "ok", 0, latency, user_query=query)
        return (f"峰谷电价：尖峰{d['尖峰']}、高峰{d['高峰']}、平段{d['平段']}、低谷{d['低谷']} {d['单位']}，"
            f"峰谷价差{d['价差']} {d['单位']}，来源：{d['来源']}")

    if "现货" in q:
        d = PRICE_DATA["现货价格"]
        latency = int((time.time() - start) * 1000)
        log_tool_call(None, "price_query", "ok", 0, latency, user_query=query)
        _last_status = "ok"
        # _last_citations 保持空，price_query 不产生 citation
        log_tool_call(None, "price_query", "ok", 0, latency, user_query=query)
        return f"现货价格：上限{d['上限']}、下限{d['下限']} {d['单位']}，来源：{d['来源']}"

    latency = int((time.time() - start) * 1000)
    log_tool_call(None, "price_query", "clarify", 0, latency, user_query=query)
    _last_status = "clarify"
    log_tool_call(None, "price_query", "clarify", 0, latency, user_query=query)
    return str(make_failure_response(
        "clarify", "支持查询：峰谷价差、容量补偿、现货价格"))