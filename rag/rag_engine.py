import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

from .config import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, LLM_MODEL, DOCS_DIR, PERSIST_DIR, ZAI_API_KEY, ZAI_BASE_URL
from .models import AskResponse

from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings,ChatOpenAI
# from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

class RAGEngine:
    """封装了加载、分割、建库、检索的 RAG 核心引擎（基于 create_retrieval_chain）"""
    def __init__(self):
        """初始化时自动加载向量库和模型，如果库不存在则标记为未就绪"""
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=ZAI_API_KEY,
            base_url=ZAI_BASE_URL,
            max_retries=5,
        )
        self.llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=0,
            api_key=ZAI_API_KEY,
            base_url=ZAI_BASE_URL,
            max_retries=5,
        )

        # 检查硬盘上是否有持久化的向量库
        if not Path(PERSIST_DIR).exists():
            self.ready = False
            self.vectorstore = None
            self.retriever = None
            print(f"向量库不存在，请先调用 build_vectorstore() 构建")
        else:
            self.vectorstore = FAISS.load_local(
                #persist_directory = PERSIST_DIR,
                folder_path=PERSIST_DIR,
                embeddings=self.embeddings,
                #embedding_function=self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k":3})
            self.ready = True
            print(f"向量库加载成功，共{self.vectorstore.index.ntotal}个向量")
            #print(f"向量库加载成功，共{self.vectorstore._collection.count()}个向量")

    def build_vectorstore(self, data_folder:str = DOCS_DIR):
        loader = DirectoryLoader(
            path = str(data_folder),
            glob = "**/*.txt",
            loader_cls=TextLoader,
            loader_kwargs = {"encoding":"utf-8"},
            show_progress = True
        )
        raw_docs = loader.load()
        print(f"加载了{len(raw_docs)}个原文档")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size = CHUNK_SIZE,
            chunk_overlap = CHUNK_OVERLAP,
            length_function = len,
            separators = ["\n\n", "\n", "。", "！", "？", " ", ""]
        )

        chunks = splitter.split_documents(raw_docs)
        print(f"分割为{len(chunks)}个文件块")

        #vectorstore = Chroma.from_documents(
        #    documents = chunks,
        #    embedding = self.embeddings,
        #   persist_directory=PERSIST_DIR
        #)
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        vectorstore.save_local(PERSIST_DIR)  # 保存到 rag/chroma_db 目录
        self.ready = True
        print(f"向量库已加载，保存在{PERSIST_DIR}")

        self.vectorstore = vectorstore
        self.retriever = vectorstore.as_retriever(search_kwargs={"k":3})
        self.ready = True

    def retrieve(self, query: str, top_k: int = 5) -> list:
        if not self.ready:
            return []
        results = self.vectorstore.similarity_search_with_score(query, k=top_k)
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": float(score),
            }
            for doc, score in results
        ]

    def rebuild_from_file(self, file_path:str):
        if self.vectorstore:
            self.vectorstore.delete_collection()

        loader = TextLoader(file_path)
        docs = loader.load()
        self.retriever = self.vectorstore.as_retriever()
        self.ready = True

    def ask(self, question:str, k:int=2) -> AskResponse:
        if not self.ready:
            raise RuntimeError("RAG Engine 未就绪， 请先调用 build_vectorstore()")

        temp_retriever = self.vectorstore.as_retriever(search_kwargs={"k":k})
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
            "你是一个基于知识库的问答助手。请根据以下提供的上下文片段回答用户的问题。"
            "如果上下文不足以回答问题，请直接说'根据现有信息无法回答'，严禁捏造信息。\n\n"
            "上下文：\n{context}"),
            ("human","{input}")
        ])
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        retrieval_chain = create_retrieval_chain(temp_retriever,document_chain)
        result = retrieval_chain.invoke({"input":question})
        sources = [doc.page_content for doc in result['context']]
        return AskResponse(answer=result['answer'], sources=sources)