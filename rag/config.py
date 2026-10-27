import os
from pathlib import Path
from dotenv import load_dotenv

def find_env_file(maker_file=".env"):
    current = Path(__file__).parent
    for _ in range(5):
        if (current / maker_file).exists():
            return current / maker_file
        current = current.parent
    return Path(__file__).parent / maker_file

# .env 在 langchain_agent 根目录
ENV_PATH = find_env_file()
load_dotenv(dotenv_path=ENV_PATH)

# 智谱配置
ZAI_API_KEY = os.getenv("ZAI_API_KEY")
ZAI_BASE_URL = os.getenv("ZAI_BASE_URL")

# 模型
EMBEDDING_MODEL = "embedding-3"
LLM_MODEL = "glm-4-flash"

# 切分
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 项目根 = agentic_rag_energy
PROJECT_DIR = Path(__file__).parent.parent

# 知识库文档目录（待建）
DOCS_DIR = PROJECT_DIR / "rag" / "docs"

# 向量库持久化目录（待建）
PERSIST_DIR = str(PROJECT_DIR / "rag" / "faiss_db")