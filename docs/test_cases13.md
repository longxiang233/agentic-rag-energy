## A 组：直接调 chat_with_memory（用例 1-8、10）

| # | 输入 query | 期望 status | 期望 tool_calls 含 | 期望 citations | 覆盖什么 |
|---|-----------|------------|-------------------|---------------|---------|
| 1 | 新型储能备案需要什么材料 | ok | policy_search | ≥1 | policy 正常 |
| 2 | 山东峰谷价差多少 | ok | price_query | 0 | price 正常 |
| 3 | 什么是虚拟电厂 | ok | vector_search | ≥1 | 边界，先跑看实际 |
| 4 | 山东独立储能可参与哪些市场 | ok | policy_search 或 vector_search | ≥1 | 路由边界，记收尾 |
| 5 | 山东储能容量补偿标准是多少 | ok | price_query 或 policy_search | 0 | 边界，先跑看实际 |
| 6 | 绿电交易是什么 | 先跑定 | vector_search 或 policy_search | ≥1 | 先跑再定期望 |
| 7 | xyz不存在的政策 | degraded | policy_search | 0 | 降级链 |
| 8 | 今天天气怎么样 | clarify | 无 | 0 | 无关问题 |
| 10.1 | 山东独立储能是什么 | ok | 任意 | ≥1 | 多轮起点 | session=e2e_multi |
| 10.2 | 它能参与哪些市场 | clarify | 任意 | 回答含"电能量市场"或"辅助服务市场" | 消解"它" | — |
| 10.3 | 容量补偿多少 | ok | 任意 | 回答含"0.0705" | 消解上下文 | — |
| 10.4 | xyz不存在的政策 | clarify | policy_search | 0 | 多轮中的失败 | — |
| 10.5 | 刚才那个政策再查 | degraded 或 clarify | 任意 | 回答含"xyz" | 消解"刚才那个" | 断言重点在"含xyz"，status 次之 |

## B 组：TestClient 走 HTTP（用例 9、11）

| # | 请求 | 期望 HTTP | 期望 body | 覆盖什么 |
|---|------|----------|----------|---------|
| 9 | POST /chat `{"session_id":"e2e_http","message":""}` | 422 | `detail` 存在，**无 status 字段** | Pydantic 拦截 |
| 11 | POST /chat `{"session_id":"e2e_http","message":"新型储能备案需要什么材料"}` | 200 | 5 key 齐全，status=ok，citations≥1，tool_calls 含 policy_search，session_id=e2e_http | ChatResponse 转换 + 全链路 |

import：pytest
from fastapi.testclient import TestClient
from agent.executor import chat_with_memory
from api.routes import app
被测函数：chat_with_memory
辅助函数：应该是提取tool_name进行判断的工具，但是我没有想到是哪个，收tol_calls，返回tool_name
test_case_01：输入？断言哪 3 样？
test_case_01：输入：新型储能备案需要什么材料
        断言：status == ok、tool_calls含有policy_search、citations≥1
test_case_02：输入：山东峰谷价差多少
        断言：status == ok、tool_calls含有price_query、citations==0
test_case_03：输入：什么是虚拟电厂
        断言：status == ok、tool_calls含有vector_search、citations≥1
test_case_04：输入：山东独立储能可参与哪些市场	
        断言：status == ok、tool_calls含有policy_search、citations≥1
test_case_05：输入：山东储能容量补偿标准是多少	
        断言：status == ok、tool_calls含有price_query、citations==0
test_case_06：输入：绿电交易是什么
        断言：status 跑后定、tool_calls含有vector_search、citations≥1
test_case_07：输入：xyz不存在的政策
        断言：status == degraded、tool_calls含有policy_search、citations==0
test_case_08：输入：今天天气怎么样
        断言：status == clarify、无tool_calls、citations==0
        8直接result["tool_calls"] == []，我感觉这个比较好理解
test_case_09：输入：POST /chat {"session_id":"e2e_http","message":""}
        断言：HTTP：422、body：detail 存在，无 status 字段
test_case_11：输入：新型储能备案需要什么材料
        断言：HTTP：200；5 key 齐全，status=ok，citations≥1，tool_calls 含 policy_search，session_id=e2e_http
test_multi_turn：session_id="e2e_multi"
        第一轮：输入：山东独立储能是什么
                断言：status=ok，citations≥1
        第二轮：输入：它能参与哪些市场
                断言：status=clarify，回答含"电能量市场"或"辅助服务市场"
        第三轮：输入：容量补偿多少
                断言：status=ok，回答含"0.0705" 
        第四轮：输入：xyz不存在的政策
                断言：status=clarify，policy_search
        第五轮：输入：刚才那个政策再查
                断言：status=degraded，回答含xyz

1.测试文件路径：agentic_rag_energy/agent/test_e2e.py
2.被测对象：
        - A组：（用例1-8，10）：chat_with_memory，直接调函数
        - B组：（用例9，11）：app，用TestClient（app）发HTTP
3.辅助函数：不需要（extract_tool_calls已在被测函数内完成）
4.用例组织方式：一个test_函数一个用例，共11个 + 1 个多轮函数
  跑测命令：pytest agent/test_e2e.py -v
        或者：pytest E:\python_projects\langchain_agent\agentic_rag_energy\agent\test_e2e.py -v -s

def test_multi_turn():
    固定 session_id = e2e_10

    第1轮：调 chat_with_memory("e2e_10", "山东独立储能是什么")
           断言：status=ok，citations≥1
    第2轮：调 chat_with_memory("e2e_10", "它能参与哪些市场")
           断言：status=clarify，回答含"电能量市场"或"辅助服务市场"
    第3轮：调 chat_with_memory("e2e_10", "容量补偿多少")
           断言：status=ok，回答含"0.0705" 
    第4轮：调 chat_with_memory("e2e_10", "xyz不存在的政策")
           断言：status=clarify，policy_search
    第5轮：调 chat_with_memory("e2e_10", "刚才那个政策再查")
           断言：status=degraded，回答含xyz



以下可直接粘贴进 `day13_special.md`，作为“方法论复盘”一节。

---

# Day 13 方法论复盘：从零写 test_e2e.py 的完整思路链

## 一、一开始是怎么想的（写代码前的 4 个决策）

**第1步：先定测试对象，再定用例。**
问的不是“要测什么功能”，而是“**测哪一层**”。选 A（直接调 `chat_with_memory`）还是 B（`TestClient` 走 HTTP），决定了 import 什么、断言什么。最终定的是**A 为主 + B 补两条**——因为 e2e 要覆盖服务层逻辑，但“入口校验 422”只能在接口层测。

**第2步：用例表不是“列场景”，是“列可断言的期望”。**
一开始列“输入 query / 期望 status / tool_calls / citations”，写代码时才发现：**“A 或 B”这种期望没法写成断言**。所以写表阶段就要逼自己二选一，选不了的标“跑后定”，而不是留“或”。

**第3步：先算成本，再决定批次。**
单条用例 29 秒 + 花钱 → 不能 12 条一次写完再跑。定的批次是：**不花钱的先跑（8、9）→ 探针批量跑拿实际值（3/4/5/6）→ 确定性的单条跑（11、10）**。

**第4步：断言顺序固定为 status → tool_calls → citations。**
先粗后细，挂了能一眼看出是哪层错。这个顺序今天一次都没乱。

---

## 二、今天实际踩的坑（每个坑的“症状→原因→改法→下次预判”）

### 坑1：路径写重复 → `file or directory not found`
- **症状**：pytest 收集到 0 个用例，直接报文件不存在
- **原因**：已在项目根目录，命令里又写了 `agentic_rag_energy/` 前缀
- **改法**：`pytest agent/test_e2e.py`，或直接绝对路径
- **下次预判**：**报“找不到文件”时，第一反应是看提示符当前目录，不是看代码**

### 坑2：断言里的类型错误 → 会炸但没跑到
- `result["tool.calls"]`：key 用点不用下划线 → `KeyError`
- `result["tool_calls"] == "policy_search"`：list 和 str 比 → 恒 False
- `result["citations"] >= 1`：list 和 int 比 → `TypeError`
- **下次预判**：**写断言前先问“这个值的类型是什么”**。dict 取值用 `[]`、成员判断用 `in`、数量判断先 `len()`

### 坑3：429 余额不足被误认为“测试挂了”
- **症状**：跑了 2 分半才 FAILED，堆栈 50 行
- **原因**：embedding API 429，重试退避后才抛出，根本没走到断言
- **改法**：看堆栈**最底部**的异常类型和 message，`RateLimitError` + “余额不足” → 不是代码问题
- **下次预判**：**FAILED 先分两类——“断言失败”（AssertionError）和“异常中断”（其他异常）**。后者先查环境，别改断言

### 坑4：用例3 的期望写错（预期 policy，实际 vector）
- **原因**：把“通用概念题”当成“政策题”
- **改法**：跑出实际值，回填用例表，注释“概念题正确路由”
- **下次预判**：**用例表里“路由期望”最容易拍脑袋错**。先跑探针拿实际值，再定死断言，别一开始就硬断言

### 坑5：多轮第2轮 status=clarify，回答却是对的
- **症状**：`tool_calls=[]` → `infer_status` 命中 `if not tool_calls: return "clarify"`，但 answer 已经列全了市场
- **原因**：**代码缺陷**——把“没调工具”和“需要用户澄清”混成一件事
- **改法**（今天）：放宽断言 `in ["ok", "clarify"]`，记入待回炉
- **改法**（明天）：写 `test_case_14_infer_status_unit`，先写失败用例暴露它，再改 `infer_status` 的判断条件
- **下次预判**：**e2e 挂的时候，先分清“测试期望错了”还是“代码行为错了”**。问自己：这个 status 按语义对吗？不对就是代码的锅，测试放宽只是临时手段

### 坑6：`policy_query` 拼写错误（两工具名混拼）
- **下次预判**：工具名只有三个——`vector_search`、`policy_search`、`price_query`。**写断言前把这三个名字念一遍**

---

## 三、今天验证有效的做法（以后照做）

| 做法 | 为什么有效 |
|---|---|
| **先写一条跑通，再铺开** | 用例1 通过才证明 import、路径、断言格式全对，后面 11 条都是复制结构 |
| **探针版：print 实际值 + 宽松断言** | 3/4/5/6 一次跑拿 4 条实际值，省 3 次跑（约 1.5 分钟 + 钱） |
| **不花钱的用例优先跑** | 8、9 验证了入口校验和 422 拦截，零成本 |
| **`-k` 精确选用例** | 每次只跑改动的那几条，不重跑全量 |
| **每轮 print `status / tool_calls / len(citations) / answer[:80]`** | 挂了立刻能判是改断言还是查代码 |
| **session_id 每条用例不同** | 避免历史串味；多轮测试共用同一个 |
| **断言带失败消息** | `"01错了，status不是ok"` 比裸 assert 好排查 |

---

## 四、以后遇到“从零写一个测试文件”，直接套这个流程

```
1. 定测哪层：服务层函数 / 接口层 HTTP / 两者都要
2. 列用例表：每条必须有“可断言的期望”，写不了“或”
3. 算成本：哪些不花钱先跑，哪些要探针
4. 写文件头 + 第1条 → 跑通 → 再铺开
5. 不确定性高的用例：print 实际值 + 宽松断言，跑完回填硬断言
6. FAILED 先分类：AssertionError（断言错或代码错）vs 其他异常（环境/依赖）
7. 断言错先问“类型对吗”，代码错先问“语义对吗”
8. 全绿后回填用例表，把“实际和设计不符”的点写成“已知偏差”，不删
```

**一句话**：**测试代码的错误分三种——语法/类型错（写的时候自查）、期望错（跑完回填）、代码缺陷（放宽断言 + 记待回炉开 fix）。三者处理方式完全不同，先分类再动手。**