from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from memory.store import get_or_create, get_history, save_message
from tools.vector_search import vector_search
from tools.policy_search import policy_search
from tools.price_query import price_query
from rag.config import LLM_MODEL, ZAI_API_KEY, ZAI_BASE_URL
import tools.vector_search as vs_module
import tools.policy_search as ps_module
import tools.price_query as pq_module
from tools.error_handler import set_current_session

def build_agent():
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0,
        api_key=ZAI_API_KEY,
        base_url=ZAI_BASE_URL,
        max_retries=5,
    )
    tools = [vector_search, policy_search, price_query]
    system_prompt = (
        "你是新能源政策助手。有三个工具："
        "policy_search 查政策条款，price_query 查电价数字，vector_search 查通用概念。"
        "根据问题类型选对应工具，检索后再回答。检索不到就说不知道，不能硬编。"
        "根据对话历史理解用户问题中的指代（如'它''这个'），结合上文实体回答。"
        "如果工具返回的内容里 status 不是 ok，把 hint 转成自然语言告诉用户，不要原样返回 JSON。"
        "电价数字和价差一律用工具返回的值，不要自己计算。"
    )
    
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )
    return agent

def extract_tool_calls(messages) -> list[str]:
    calls = []
    for m in messages:
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                calls.append(tc["name"])
    return calls

def infer_status(citations, tool_calls, tool_statuses, answer, is_empty_input=False) -> str:
    if is_empty_input:
        return "clarify"
    if not answer:
        return "empty"
    if citations:
        if "fallback" in tool_statuses:
            return "fallback"
        return "ok"
    if not tool_calls:
        return "clarify"
    if "clarify" in tool_statuses:
        return "clarify"
    if "ok" in tool_statuses:
        return "ok"
    return "degraded"

def chat_with_memory(session_id: str, user_input: str) -> dict:
    set_current_session(session_id)
    # 入口校验：空输入直接返回澄清，不调 LLM
    if not user_input or not user_input.strip():
        return {
            "answer": "请提供具体问题，例如：山东独立储能的容量补偿标准是多少？",
            "citations": [],
            "tool_calls": [],
            "status": "clarify",
            "session_id": session_id,
        }
    
    agent = build_agent()
    get_or_create(session_id)
    history = get_history(session_id)
    messages = history + [HumanMessage(content=user_input)]
    result = agent.invoke({"messages": messages})
    answer = result["messages"][-1].content

    # 提取 tool_calls
    tool_calls = extract_tool_calls(result["messages"])

    # 汇总三个工具的 citations 和 status
    all_citations = []
    tool_statuses = []
    tool_map = {"vector_search": vs_module, "policy_search": ps_module, "price_query": pq_module}
    for name, mod in tool_map.items():
        if name in tool_calls:
            all_citations.extend(mod._last_citations)
            tool_statuses.append(mod._last_status)

    # 按 source 去重，保留最高分（距离越小越相关），最多 3 条
    seen = {}
    for c in all_citations:
        src = c["source"]
        if src not in seen or c["score"] < seen[src]["score"]:
            seen[src] = c
    citations = sorted(seen.values(), key=lambda x: x["score"])[:3]

    status = infer_status(citations, tool_calls, tool_statuses, answer)

    save_message(session_id, HumanMessage(content=user_input))
    save_message(session_id, result["messages"][-1])

    return {
        "answer": answer,
        "citations": citations,
        "tool_calls": tool_calls,
        "status": status,
        "session_id": session_id,
    }