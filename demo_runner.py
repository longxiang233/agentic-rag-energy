"""演示视频用的交互脚本，按回车逐步展示 4 个功能。"""
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

from agent.executor import chat_with_memory

def pause(msg="按回车继续"):
    input(f"\n[{msg}] ")

def main():
    print("=" * 60)
    print("Agentic RAG 新能源政策问答助手 - 功能演示")
    print("=" * 60)

    # ---------- 场景1：多轮对话 ----------
    print("\n### 功能1：多轮对话 - 连续3轮不丢上下文 ###")
    pause("开始第1轮")

    print("\n[第1轮] 山东独立储能是什么？")
    r1 = chat_with_memory("demo", "山东独立储能是什么")
    print(f"答：{r1['answer'][:150]}")
    pause("继续第2轮")

    print("\n[第2轮] 它能参与哪些市场？（消解'它'）")
    r2 = chat_with_memory("demo", "它能参与哪些市场")
    print(f"答：{r2['answer'][:150]}")
    pause("继续第3轮")

    print("\n[第3轮] 容量补偿多少？（消解上下文）")
    r3 = chat_with_memory("demo", "容量补偿多少")
    print(f"答：{r3['answer'][:150]}")
    pause("进入功能2")

    # ---------- 场景2：失败降级 ----------
    print("\n### 功能2：失败降级 - 无结果不返空 ###")
    print("\n[查询] xyz不存在的政策")
    r4 = chat_with_memory("demo_fail", "xyz不存在的政策")
    print(f"status: {r4['status']}")
    print(f"答：{r4['answer'][:150]}")
    pause("进入功能3")

    # ---------- 场景3：工具路由 ----------
    print("\n### 功能3：工具路由 - 政策vs电价 ###")
    print("\n[政策问题] 新型储能备案需要什么材料")
    r5 = chat_with_memory("route1", "新型储能备案需要什么材料")
    print(f"tools: {r5['tool_calls']}")
    pause("继续")

    print("\n[电价问题] 山东峰谷价差多少")
    r6 = chat_with_memory("route2", "山东峰谷价差多少")
    print(f"tools: {r6['tool_calls']}")
    pause("进入功能4")

    # ---------- 场景4：引用输出 ----------
    print("\n### 功能4：引用输出 - 每条回答带source ###")
    print("\n[查询] 新型储能备案需要什么材料")
    r7 = chat_with_memory("demo_citation", "新型储能备案需要什么材料")
    print(f"答：{r7['answer'][:100]}")
    print(f"\ncitations ({len(r7['citations'])} 条):")
    for i, c in enumerate(r7["citations"], 1):
        print(f"  [{i}] source: {c['source'].split(chr(92))[-1]}")
        print(f"      score:  {round(c['score'], 3)}")
        print(f"      tool:   {c['tool']}")
        print(f"      content: {c['content'][:60]}...")

    print("\n" + "=" * 60)
    print("演示结束")
    print("=" * 60)

if __name__ == "__main__":
    main()