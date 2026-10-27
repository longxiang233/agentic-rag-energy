import os
from fastapi import FastAPI, HTTPException, UploadFile, Request,File, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import shutil
from pathlib import Path
from .models import AskResponse, AskRequest
from .rag_engine import RAGEngine
from .config import DATA_DIR

try:
    engine = RAGEngine
    print("RAGEngine加载成功")
except FileNotFoundError as e:
    print(f"j加载失败{e}")
    engine = None

app = FastAPI(tetil = "RAG 知识库问答系统")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request:Request,exc:RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail":"请求参数校验失败","errors":"exc_errors()"}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request:Request, exc:Exception):
    print(f"全局捕获异常：{type(exc).__name__} - {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail":"服务器内部错误，请稍后重试或联系管理员"}
    )

@app.get("/")
def root():
    return{"message":"RAG 系统已启动，请POST / ask 提问"}

@app.post("/ask", response_model = AskResponse)
def ask_question(req:AskRequest):
    if engine is None or not engine.ready:
        raise HTTPException(status_code=503,detail="RAG Engine未初始化，请先构建向量库")
    try:
        response = engine.ask(question=req.question, k=req.k)
        return response
    except Exception as e:
        raise HTTPException(status_code = 500,detail=f"处理失败：{str(e)}")

@app.post("/upload", status_code=202)
async def upload_file(
    background_tasks:BackgroundTasks,
    file:UploadFile = File(...)
) :
    temp_dir = Path("./temp")
    temp_dir.mkdir(exist_ok = True)
    temp_path = temp_dir / file.filename

    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file,buffer)

    background_tasks.add_task(engine.rebuild_from_file,str(temp_path))

    return {"message":"文件已接到，正在后台重建向量库，请稍后查询"}