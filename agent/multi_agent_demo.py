from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from rag.config import LLM_MODEL, ZAI_API_KEY, ZAI_BASE_URL

llm = ChatOpenAI(
    model=LLM_MODEL, 
    api_key=ZAI_API_KEY,
    base_url=ZAI_BASE_URL,
    temperature=0.7
)

# 1. 定义多智能体的共享状态
class MultiAgentState(TypedDict):
    task: str        # 用户的原始任务
    draft: str       # 写手 Agent 的草稿
    feedback: str    # 审核 Agent 的意见
    revision: int    # 修改次数

# 2. 定义节点：写手 Agent
def writer_node(state: MultiAgentState):
    print("\n---> [写手 Agent] 正在生成/修改内容...")
    task = state["task"]
    feedback = state.get("feedback", "")
    
    prompt = f"请根据要求写一段话：{task}。"
    if feedback:
        prompt += f"\n注意！根据之前的审核意见进行修改：{feedback}"
        
    response = llm.invoke(prompt)
    print(f"【草稿】: {response.content}")
    return {"draft": response.content}

# 3. 定义节点：审核 Agent
def reviewer_node(state: MultiAgentState):
    print("\n---> [审核 Agent] 正在评估内容...")
    draft = state["draft"]
    revision = state.get("revision", 0)
    
    prompt = f"""
    你是一个严格的审核员。请检查以下内容是否包含了“新能源”和“储能”这两个词。
    内容：{draft}
    如果包含，请只回复“通过”。如果不包含，请回复具体缺失了什么词。
    """
    response = llm.invoke(prompt)
    result = response.content.strip()
    
    if "通过" in result:
        print("【审核结果】通过！")
        return {"feedback": "通过", "revision": revision + 1}
    else:
        print(f"【审核结果】未通过。意见：{result}")
        return {"feedback": result, "revision": revision + 1}

# 4. 定义路由（主管决策）
def supervisor_route(state: MultiAgentState):
    print("\n---> [主管 Supervisor] 进行决策...")
    if state["feedback"] == "通过":
        return "end"
    if state["revision"] >= 2:
        print("【主管决策】重试超过 2 次，强制结束（防死循环）")
        return "end"
    print("【主管决策】打回写手重写")
    return "retry"

# 5. 构建 LangGraph
workflow = StateGraph(MultiAgentState)
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", reviewer_node)

workflow.set_entry_point("writer")
workflow.add_edge("writer", "reviewer")

workflow.add_conditional_edges(
    "reviewer",
    supervisor_route,
    {"end": END, "retry": "writer"}
)

app = workflow.compile()

if __name__ == "__main__":
    print("====== 开始运行多智能体协作 Demo ======")
    # 故意给一个刁钻的任务：只说“写一句话”，大概率第一遍不会包含“新能源”和“储能”
    inputs = {"task": "随便写一句关于科技的话。", "draft": "", "feedback": "", "revision": 0}
    
    # 执行（限制最大递归 4 次）
    result = app.invoke(inputs, {"recursion_limit": 10})
    print("\n====== 最终输出结果 ======")
    print(result["draft"])