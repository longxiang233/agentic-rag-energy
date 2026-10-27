from agent.executor import build_agent
from langchain_core.messages import HumanMessage

agent = build_agent()
result = agent.invoke({
    "messages": [HumanMessage(content="山东独立储能容量补偿标准是多少？")]
})
print("===OUTPUT===")
print(result["messages"][-1].content or result["messages"][-1])