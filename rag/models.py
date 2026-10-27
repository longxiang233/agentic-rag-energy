from pydantic import BaseModel, Field
from typing import List, Optional

class AskRequest(BaseModel):
    question:str = Field(..., description="用户的问题", min_length=1)
    k:int = Field(2, description = "检索相关的k个文档块", ge=1, le=10)

class AskResponse(BaseModel):
    answer:str = Field(..., description = "基于文档生成的答案")
    sources:List[str] = Field(..., description = "引用的原文片段")
