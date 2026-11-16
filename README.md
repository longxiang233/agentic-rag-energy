# Agentic RAG 新能源政策问答系统

## 💡 项目背景与解决的痛点

新能源（光伏、储能）行业的政策和电价机制更新非常频繁。以前业务员查个文件，得在几百页的 PDF 里翻半天，不仅容易漏看条款导致合规风险，单轮问答也根本问不清具体的补贴细节。

基于这个真实的业务背景，我开发了这套系统，主要想解决三个实际问题：
*   **查政策防踩坑**：把海量政策文件转化为秒级响应的智能知识库。最核心的是**强制要求大模型输出引用出处（Citations）**，防止它瞎编政策，把人工查文件的时间直接压缩到几秒钟。
*   **算电价辅助决策**：储能赚钱主要靠峰谷套利。系统能精准提取和计算电价差，帮业务员找最优的充放电策略，而不是让大模型自己去做算术。
*   **降本增效**：这套 RAG 架构不仅能查政策，也能无缝平移到偏远风光电站的“设备维修手册问答”上，相当于给现场工人配了个随身专家，省去了专家到处跑的差旅成本。

## 🚀 核心功能

1. **多轮对话**：基于 `session_id` 注入历史，连续 5 轮对话不丢上下文，支持指代消解（如“它”、“刚才那个政策”）。
2. **工具路由**：基于 LLM 和 docstring，自动将问题分流到 `policy_search`（政策条款）、`price_query`（电价数字）或 `vector_search`（通用概念）。
3. **失败降级**：结构化处理超时、返回空等异常。无结果时返回自然语言兜底话术，绝不把裸 JSON 抛给用户。
4. **引用输出**：每条基于文档的回答强制附带 `citations` 列表，包含来源文件（source）、相似度分数（score）和内容摘要。

## 🛠 技术栈

- **语言**：Python 3.12
- **接口**：FastAPI + Pydantic (提供 422/500 校验)
- **框架**：LangChain 1.x + LangGraph (Agent 执行图)
- **向量库**：FAISS (基于 Windows 兼容性决策，由 Chroma 迁移)
- **大模型**：智谱 GLM-4.7-flash (对话) + embedding-3 (向量化)
- **测试**：pytest (11个端到端用例)

### 🤖 进阶扩展：多智能体协作 Demo (Multi-Agent)

在 agent/multi_agent_demo.py 中，实现了一个基于 LangGraph 的 Supervisor（主管）模式多智能体 Demo。它定义了 Writer（生成）和 Reviewer（审核）两个独立 Agent，通过 TypedDict 共享全局状态。并且利用了条件边实现了“审核不通过自动打回重写”，为了防止两个 Agent 互相扯皮死循环，还专门设计了 revision >= 2 的强制退出机制。

## 🏗 架构图

```mermaid
%%{init: {"theme": "neutral"}}%%
graph TD
    U["用户请求"] --> API["API层 FastAPI POST chat"]
    API --> AG["Agent层 LangGraph 图结构循环"]
    
    AG -->|"意图路由"| T1["Tool层 policy_search"]
    AG -->|"意图路由"| T2["Tool层 price_query"]
    AG -->|"意图路由"| T3["Tool层 vector_search"]
    
    T1 --> RAG["RAG层 FAISS 检索 + 阈值过滤 + 引用溯源"]
    T2 --> DB["结构化数据 PRICE_DATA 字典"]
    T3 --> RAG
    
    AG --> M["Memory层 session_id 历史消息列表"]
    AG --> L["日志层 logs agent.log 记录耗时和状态"]
```

## 💻 怎么跑

### 1. 安装依赖
```powershell
cd E:\python_projects\langchain_agent\agentic_rag_energy
python -m venv .venv312
.\.venv312\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 配置环境变量
在项目根目录（或主项目根目录）创建 `.env`，填入：
```env
ZAI_API_KEY=你的智谱API_KEY
ZAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

### 3. 建库（首次运行）
```powershell
python -c "from rag.rag_engine import RAGEngine; e = RAGEngine(); e.build_vectorstore()"
```

### 4. 启动服务
```powershell
uvicorn api.routes:app --host 127.0.0.1 --port 8000
```

### 5. 接口测试示例 (PowerShell)
```powershell
$body = @{session_id="demo"; message="新型储能备案需要什么材料"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method Post -Body $body -ContentType "application/json; charset=utf-8"
```

## ✅ 测试与验收

- **端到端测试**：`pytest agent/test_e2e.py -q`，**11/11 全部通过**，覆盖正常路由、边界查询、降级拦截和 422 接口校验。
- **演示视频**：见 `day13\demo_video.mp4`（展示了多轮、路由、降级、引用 4 个核心功能）。

## ⚠️ 已知限制

1. **Memory 存储**：目前使用单进程内存 dict 存储历史，重启服务丢失，未来计划迁移至 Redis。
2. **阈值召回**：FAISS 检索使用硬阈值（1.02），部分语义相近词可能被过滤，后续引入 Reranker 优化。
3. **LLM 算术**：大模型直接做数学计算不可靠，目前电价差值由工具硬编返回，并禁止 LLM 自行计算。