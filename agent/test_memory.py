from agent.executor import chat_with_memory
import time

SESSION = "test_memory_day10"
DIALOG = [
    "山东独立储能是什么？",
    "它能参与哪些市场？",
    "容量补偿多少钱？",
    "峰谷价差呢？",
    "它和用户侧储能的区别是什么？",
]

def main():
    for i, d in enumerate(DIALOG, 1):
        result = chat_with_memory(SESSION, d)["answer"]
        print(f"\n=== 第{i}轮 ===")
        print (f"[{i}]的答案是{result[:200]}")
        time.sleep(3)

if __name__ == "__main__":
    main()