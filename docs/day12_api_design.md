# Day 12 API 设计

## 接口1：`POST /chat`

| 项 | 内容 |
|----|------|
| 路径 | `POST /chat` |
| 请求体 | `{"session_id": "str", "message": "str"}`，message `min_length=1` |
| 响应体 | `{"answer": "str", "citations": [...], "tool_calls": [...], "status": "str", "session_id": "str"}` |
| 空 message | **422**（Pydantic `min_length=1` 自动，不是 400） |
| 服务异常 | 500 + `HTTPException(500, detail=str(e))` |

| 状态码 | 含义 | 谁返回 |
| 422 | 请求体格式对，但字段值不合法（message=""） | Pydantic 自动 |
| 400 | 请求体格式本身错（不是合法 JSON） | FastAPI 自动 |
| 500 | 服务内部异常（chat_with_memory 抛异常） | 你的 try/except |


## 接口2：`GET /health`

| 项 | 内容 |
|----|------|
| 路径 | `GET /health` |
| 响应 | `{"status": "ok"}`（不查库，MVP 最简） |

| chat_with_memory 返回 | ChatResponse 字段 |
| answer |answer: str |
| citations | citations: list[Citation] |
| tool_calls | tool_calls: list[str] |
| status | status: str |
| session_id | session_id: str |

citations 服务层是 list[dict]，接口层 ChatResponse.citations 是 list[Citation]，ChatResponse(**result) 时 Pydantic 自动逐条转换。不要手动写 [Citation(**c) for c in result["citations"]]，多此一举。

Citation 模型的字段名（source/content/score/tool）必须和 dict 的 key 逐字一致。如果 dict 里是 "src" 而模型是 source，Pydantic 转不过去，报 missing field。

接口层只做三件事： 接收请求（Pydantic 解析）、调 chat_with_memory、返回响应（ChatResponse 包装）。不查库、不拼 prompt、不处理 citations 去重——这些都在服务层。

## Pydantic 模型

```python
ChatRequest:
    session_id: str
    message: str = Field(min_length=1)

Citation:
    source: str
    content: str
    score: float
    tool: str

ChatResponse:
    answer: str
    citations: list[Citation]
    tool_calls: list[str]
    status: str
    session_id: str
```