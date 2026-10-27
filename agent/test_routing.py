import time
import os
from agent.executor import build_agent
from langchain_core.messages import HumanMessage

TEST_CASES = [
    ("山东独立储能容量补偿标准是多少？", "price_query"),
    ("山东独立储能可同时参与哪两个市场？", "policy_search"),
    ("什么是AGC？", "vector_search"),
    ("山东2025年峰谷价差多少？", "price_query"),
    ("新型储能项目备案需要什么材料？", "policy_search"),
    ("储能3S分别是什么？", "vector_search"),
    ("用户侧储能怎么赚钱？", "vector_search"),
    ("山东独立储能容量补偿机制的文件依据是什么？", "policy_search"),
    ("尖峰电价上浮多少？", "price_query"),
    ("电源侧和电网侧储能区别？", "vector_search"),
]

def get_called_tools(messages):
    """收集所有工具调用名，返回列表。Agent 可能调用多次"""
    called = []
    for m in messages:
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                called.append(tc["name"])
    return called

def invoke_with_retry(agent, q, max_retries=3):
    for i in range(max_retries):
        try:
            return agent.invoke({"messages": [HumanMessage(content=q)]})
        except Exception as e:
            if "429" in str(e) or "RateLimit" in str(e):
                wait = 10 * (i + 1)
                print(f"  ⏳ 429 限流，等 {wait}s 重试...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"重试 {max_retries} 次仍失败: {q}")

def main():
    agent = build_agent()
    correct = 0
    for i, (q, expected) in enumerate(TEST_CASES, 1):
        result = invoke_with_retry(agent, q)
        called = get_called_tools(result["messages"])
        actual = called[0] if called else "none"
        ok = actual == expected
        correct += ok
        mark = "✅" if ok else "❌"
        print(f"{mark} {i:2d}. 期望={expected:15s} 实际={actual:15s} | {q}")
        time.sleep(3)  # 每题之间歇 3 秒

    total = len(TEST_CASES)
    print(f"\n准确率：{correct}/{total} = {correct/total*100:.0f}%")

if __name__ == "__main__":
    main()