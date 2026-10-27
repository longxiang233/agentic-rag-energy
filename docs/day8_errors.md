# Day8 错题本
# 两个文件的完整内容，直接复制

---

## 文件1：`agentic_rag_energy\docs\day8_errors.md`

```markdown
# Day 8 调试记录：RAG 改智谱 + 建库 + retrieve

日期：2026-10-17
环境：Windows + Python 3.12（.venv312）+ 智谱 GLM

## 问题1：torch c10.dll 初始化失败

**报错：**
```
OSError: [WinError 1114] 动态链接库(DLL)初始化例程失败。
Error loading "...\torch\lib\c10.dll" or one of its dependencies.
```

**根因：** Python 3.14 太新，PyTorch 2.9+ 在 Windows 下 DLL 兼容性差；torch 2.8.0 不支持 Py3.14。

**尝试过：**
- 装 VC++ 2015-2019 x64 → 报 0x80070666，系统已有 14.36 更高版本，无需降级
- pip install torch==2.8.0 → 报找不到版本（Py3.14 最低 2.9.0+cpu）
- pip install torch==2.9.0+cpu / 2.9.1+cpu → 仍报 c10.dll

**解决：** 安装 Python 3.12，在项目内新建 `.venv312`，重装依赖，torch 问题消失。

**命令：**
```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
pip install langchain langchain-openai langchain-community langchain-chroma chromadb python-dotenv torch
```

**教训：** 新项目优先用 PyTorch 官方稳定支持的 Python 版本（3.10-3.12），不要追最新。

---

## 问题2：venv 用错，导致 ModuleNotFoundError

**报错：**
```
ModuleNotFoundError: No module named 'dotenv'
```

**根因：** 当前激活的是 `fastapi_demo\.venv`，不是 `langchain_agent\venv`。

**排查：**
```powershell
python -c "import sys; print(sys.executable)"
# 输出 E:\python_projects\fastapi_demo\.venv\Scripts\python.exe → 错
```

**解决：**
```powershell
deactivate
cd E:\python_projects\langchain_agent
.\venv\Scripts\Activate.ps1
```

**教训：** 每次开终端先确认 `sys.executable` 路径，提示符 `(venv)` 不代表是正确项目的 venv。

---

## 问题3：config.py 变量名不匹配，缺 BASE_URL

**现象：** `ZAI_API_KEY` 读到 None，embedding 会 401。

**根因：**
- `OPENAI_API_KEY = os.getenv("OPEN_API_KEY")` 变量名少 `I`，且 `.env` 里实际叫 `ZAI_API_KEY`
- 没有读 `ZAI_BASE_URL`，ChatOpenAI/OpenAIEmbeddings 默认走 OpenAI 官方

**解决：** `config.py` 改为：
```python
ZAI_API_KEY = os.getenv("ZAI_API_KEY")
ZAI_BASE_URL = os.getenv("ZAI_BASE_URL")
EMBEDDING_MODEL = "embedding-3"
LLM_MODEL = "glm-4.7-flash"
DOCS_DIR = PROJECT_DIR / "rag" / "docs"
PERSIST_DIR = str(PROJECT_DIR / "rag" / "chroma_db")
```

**验证：**
```powershell
python -c "from rag.config import ZAI_API_KEY, ZAI_BASE_URL; print(bool(ZAI_API_KEY), ZAI_BASE_URL)"
```

**教训：** `.env` 变量名和代码读取名必须逐字一致；OpenAI 兼容接口必须显式传 `base_url`。

---

## 问题4：rag_engine.py 导入错误

**报错1：**
```
ImportError: cannot import name 'Path' from 'pydantic'
```
**根因：** `from pydantic import Path` 写错，`Path` 来自 `pathlib`。
**解决：** 改为 `from pathlib import Path`。

**报错2：**
```
ImportError: cannot import name 'DATA_DIR' from 'rag.config'
```
**根因：** `rag_engine.py` 引用 `DATA_DIR`，`config.py` 里叫 `DOCS_DIR`。
**解决：** 全局替换 `DATA_DIR` → `DOCS_DIR`。

**报错3：**
```
ImportError: cannot import name 'AdvancesRagEngine' from 'rag.rag_engine'
```
**根因：** 文件里实际类名是 `RAGEngine`，旧项目叫 `AdvancesRagEngine`。
**解决：** 以实际类名为准，测试命令用 `RAGEngine`。

**教训：** 从旧项目复制代码后，先通读 import 区和类名，再跑。

---

## 问题5：多处拼写错误

**清单：**

| 错误 | 正确 | 位置 |
|------|------|------|
| `vetorstore` | `vectorstore` | 多处 |
| `seach_kwargs` | `search_kwargs` | 多处 |
| `enconding` | `encoding` | DirectoryLoader |
| `from_message` | `from_messages` | ChatPromptTemplate |
| `k:2` | `k: int = 2` | ask 方法签名 |

**解决：** VS Code `Ctrl + H` 全局替换，`Ctrl + F` 逐个确认 0 处。

**教训：** 复制/手写后必须通读变量名，拼写错误在 Python 里不报语法错，只在运行时炸。

---

## 问题6：建库报 unstructured 缺失

**报错：**
```
ImportError: unstructured package not found, please install it with `pip install unstructured`
```

**根因：** `DirectoryLoader` 没传 `loader_cls=TextLoader`，默认走 `UnstructuredFileLoader`。

**解决：**
```python
loader = DirectoryLoader(
    path=str(data_folder),
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
    show_progress=True,
)
```

**教训：** `DirectoryLoader` 必须显式指定 `loader_cls`，否则会引入重量级 `unstructured` 依赖。备选：手动 glob 遍历 + `TextLoader`，更可控。

---

## 问题7：ChromaDB 初始化崩溃 0xC0000005（核心问题）

**现象：**
```powershell
python -u -c "from rag.rag_engine import RAGEngine; e=RAGEngine(); print('ok')"
# 输出 step1、step2，然后进程直接退出，无 traceback
# echo $LASTEXITCODE → -1073741819 (0xC0000005)
```

**根因：** ChromaDB 1.5.9 在 Windows + Python 3.12 下，底层 HNSW C++ 扩展访问冲突，进程静默崩溃。

**尝试过：**
- 降级 `chromadb==1.3.5` → 仍崩
- 降级 `chromadb==0.5.23` + `langchain-chroma==0.2.4` → 仍崩

**解决：切换 FAISS。**

1. `pip install faiss-cpu`
2. `from langchain_community.vectorstores import FAISS`
3. 加载：
```python
self.vectorstore = FAISS.load_local(
    folder_path=PERSIST_DIR,
    embeddings=self.embeddings,
    allow_dangerous_deserialization=True,
)
```
4. 建库：
```python
self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
self.vectorstore.save_local(PERSIST_DIR)
```
5. 向量数：`self.vectorstore.index.ntotal`（不是 `_collection.count()`）

**结果：**
```
向量库加载成功，共9个向量
条数: 5
{'content': '三、市场化容量补偿机制...', 'source': '...山东独立储能政策.txt', 'score': 0.9146572351455688}
```

**教训：** 遇到底层 C++ 扩展在 Windows 崩溃，降级无效时果断换库，不要在 Chroma 上耗时间。FAISS 在 Windows 下更稳，LangChain 支持好，MVP 阶段优先稳定。

---

## 问题8：FAISS 加载/打印 API 差异

**报错1：**
```
TypeError: FAISS.load_local() missing 2 required positional arguments: 'folder_path' and 'embeddings'
```
**解决：** 用关键字参数：
```python
FAISS.load_local(folder_path=PERSIST_DIR, embeddings=self.embeddings, allow_dangerous_deserialization=True)
```

**报错2：**
```
AttributeError: 'FAISS' object has no attribute '_collection'
```
**根因：** `_collection.count()` 是 Chroma 专有 API。
**解决：** 改 `self.vectorstore.index.ntotal`。

**教训：** 换向量库后，加载、保存、计数、检索 API 都要逐一核对，不能沿用旧库写法。

---

## 最终验证结果

```powershell
python -u -c "from rag.rag_engine import RAGEngine; e=RAGEngine(); r=e.retrieve('山东储能容量补偿'); print('条数:', len(r)); print(r[0])"
```

输出：
```
向量库加载成功，共9个向量
条数: 5
{'content': '三、 市场化容量补偿机制...', 'source': '...\\山东独立储能政策.txt', 'score': 0.9146572351455688}
```

**结论：** RAG 层已具备稳定纯检索能力，`retrieve()` 返回 `content/source/score`，可被 `vector_search` 工具封装。
```




# Day 8 后半段（Agent 接入）调试复盘

按和上次一样的格式，三个文件内容直接复制。

---

## 文件1：追加到 `agentic_rag_energy\docs\day8_errors.md`

```markdown
---

# Day 8 后半段调试记录：vector_search + Agent 接入

日期：2026-10-17
环境：Windows + Python 3.12（.venv312）+ 智谱 GLM + LangChain 1.3.15

## 问题9：ModuleNotFoundError: No module named 'agent.executor'

**报错：**
```
ModuleNotFoundError: No module named 'agent.executor'; 'agent' is not a package
```

**根因：**
1. `agent\__init__.py` 缺失，`agent` 目录不是 Python package
2. 从 `agent\` 目录直接 `python test_day8.py`，`agent` 被当成普通模块，无法解析 `agent.executor`

**解决：**
```powershell
# 1. 确认 package 标记
New-Item -ItemType File -Path agent\__init__.py -Force

# 2. 从项目根目录用 -m 运行
cd E:\python_projects\langchain_agent\agentic_rag_energy
python -u -m agent.test_day8
```

**教训：** 用 `python -m 包.模块` 运行时，包目录必须有 `__init__.py`，且要在包的父目录执行。

---

## 问题10：ImportError: cannot import name 'AgentExecutor'

**报错：**
```
ImportError: cannot import name 'AgentExecutor' from 'langchain.agents'
```

**根因：** LangChain 1.3.15 已废弃 `AgentExecutor` / `create_tool_calling_agent`，从 `langchain.agents` 移除，底层迁移到 LangGraph。

**尝试过：**
- `from langchain_classic.agents import AgentExecutor, create_tool_calling_agent` → 可用，但属于兼容层，后续扩展性差

**解决：改用 1.x 标准入口 `create_agent`：**
```python
from langchain.agents import create_agent

agent = create_agent(
    model=llm,
    tools=[vector_search],
    system_prompt="你是新能源政策助手。优先调用 vector_search 检索政策文件，再基于检索结果回答。",
)
```

**关键差异：**
- `create_agent` 不需要 `ChatPromptTemplate`、`agent_scratchpad`
- 输入是 `messages` 列表，不是 `input` 字符串
- 输出是 LangGraph 状态，取 `result["messages"][-1].content`

**教训：** 装包后先看主版本号，1.x 的 Agent API 和 0.x 完全不同，教程代码大概率跑不通。

---

## 问题11：SyntaxWarning: 'tuple' object is not callable

**报错：**
```
SyntaxWarning: 'tuple' object is not callable; perhaps you missed a comma?
("systen", "你是新能源政策助手...")
```

**根因：**
1. `systen` 拼错（应为 `system`）
2. 字符串末尾缺逗号，相邻字符串被 Python 隐式拼接后，`(...)` 被解析成 tuple 调用
3. 旧写法 `ChatPromptTemplate.from_messages([("systen", "..."), ("human", ...)])` 里，tuple 内字符串拼接出问题

**解决：** 改用 `create_agent` 的 `system_prompt` 参数，直接传字符串，不再手写 message tuple，问题消失。

**教训：** `SyntaxWarning` 不要忽略，它经常是"少逗号 / 拼写错 / 括号错位"的早期信号。

---

## 问题12：智谱 400 code 1214 messages 参数非法（核心问题）

**报错：**
```
openai.BadRequestError: Error code: 400 - {'error': {'code': '1214', 'message': 'messages 参数非法。请检查文档。'}}
```

**根因：** `create_agent` 返回的是 LangGraph 对象，期望输入 `{"messages": [...]}`。之前传 `{"input": "..."}`，键名不匹配，导致 `user` 消息没被正确注入，发给智谱的只有 `system` 消息，触发 1214 校验。

**排查过程：**
1. 先怀疑 `ChatOpenAI` 兼容层对 `tool_calls` 序列化不符合智谱要求
2. 分步确认：`RAGEngine()` 初始化正常 → `vector_search` 单独调用正常 → 问题定位在 `agent.invoke()` 入参
3. 对照 `create_agent` 文档，确认输入 schema 是 `messages`

**解决：**
```python
from langchain_core.messages import HumanMessage

result = agent.invoke({
    "messages": [HumanMessage(content="山东独立储能容量补偿标准是多少？")]
})
```

**教训：**
- LangGraph 系 Agent 的输入是状态 dict，键名必须和 State schema 对齐
- 智谱对 `messages` 序列校验比 OpenAI 严：必须至少一条 `user`，`system` 后不能直接跟 `assistant`/`tool`
- 400 + 业务错误码（1214）优先查请求体结构，不是 key/网络问题

---

## 问题13：KeyError: 'output'

**报错：**
```
KeyError: 'output'
```

**根因：** `create_agent` 返回 LangGraph 状态，键是 `messages`，没有 `output`。旧 `AgentExecutor` 才返回 `{"output": ...}`。

**解决：**
```python
# 旧写法（AgentExecutor）
print(result["output"])

# 新写法（create_agent）
print(result["messages"][-1].content)
```

**教训：** 换 Agent 框架后，返回结构要重新确认；LangGraph 统一用 `messages` 承载对话历史。

---

## 最终验证结果

```powershell
python -u -m agent.test_day8
```

输出：
```
向量库加载成功，共9个向量
=== OUTPUT ===
根据检索到的山东独立储能相关政策文件，目前未明确列出具体的容量补偿金额标准...
### 1. 市场化容量补偿机制
- 补偿分配：发电侧主体市场化容量补偿费用按照月度市场化可用容量占比进行分配。
- 可用容量计算：独立新型储能电站日市场化可用容量 = 储能电站核定放电功率 × K × H / 24
...
```

**结论：** 单 Agent 调用 `vector_search` → FAISS 检索 → 智谱生成，闭环跑通。Agent 未硬编金额，基于检索结果作答并主动给出建议。
