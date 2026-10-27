from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.executor import chat_with_memory


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1)


class Citation(BaseModel):
    source: str
    content: str
    score: float
    tool: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    tool_calls: list[str]
    status: str
    session_id: str


app = FastAPI(title="Agentic RAG 新能源政策助手")


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        result = chat_with_memory(req.session_id, req.message)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}