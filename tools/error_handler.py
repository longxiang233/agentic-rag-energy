import time
import logging
from pathlib import Path

# ---------- 日志配置 ----------
# 用 Path(__file__) 定位，不管从哪个目录跑，都写到项目 logs/ 下
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("tool")
logger.setLevel(logging.INFO)

# 避免重复添加 handler（模块被多次 import 时）
if not logger.handlers:
    fh = logging.FileHandler(LOG_DIR / "agent.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(fh)

_current_session = "default"

def set_current_session(session_id: str):
    global _current_session
    _current_session = session_id

def get_current_session() -> str:
    return _current_session

class ToolErrorHandler:
    """统一处理工具调用的异常、重试和日志"""
    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    # ---------- 1. 统一构造失败返回 ----------
    def make_failure_response(self, status: str, hint: str, retryable: bool = False,
                            retry_count: int = 0, data: str = None) -> dict:
        """统一构造失败返回 dict。
        status: degraded / fallback / clarify / empty / error
        data: 只有 fallback 时传（降级后的替代结果）
        """
        resp = {
            "status": status,
            "hint": hint,
            "retryable": retryable,
            "retry_count": retry_count,
        }
        if data is not None:
            resp["data"] = data
        return resp

    # ---------- 2. 判空 ----------
    def is_empty_result(self, result) -> bool:
        """只判原始数据空，不判已包装的失败 dict。
        传入的应该是 retrieve() 的 list 或工具的原始输出。
        """
        if result is None:
            return True
        if isinstance(result, str):
            return not result.strip()
        if isinstance(result, (list, dict)):
            return len(result) == 0
        return False


    # ---------- 3. 写结构化日志 ----------
    def log_tool_call(self, session_id: str = None, tool: str = "", status: str = "",
                    retry_count: int = 0, latency_ms: int = 0,
                    error: str = None, user_query: str = None) -> None:
        """按表3 字段写一条日志。user_query 截断前 50 字。"""
        if session_id is None:
            session_id = get_current_session()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        q = (user_query or "")[:50]
        err = error or "-"
        logger.info(
            f"{ts} | session={session_id} | tool={tool} | status={status} | "
            f"retry={retry_count} | latency={latency_ms}ms | error={err} | query={q}"
        )


    # ---------- 4. 重试包装 ----------
    def call_with_retry(self, func, args: dict, session_id: str = "default",
                        tool_name: str = None, max_retries: int = 2) -> dict:
        """包装工具调用，支持两条重试路径：
        1. 工具正常返回 {"retryable": True}
        2. 工具抛 TimeoutError
        重试耗尽后返回 degraded。
        """
        if tool_name is None:
            tool_name = getattr(func, "__name__", "unknown")
        user_query = args.get("query", "")

        for i in range(max_retries + 1):   # 第一次正常调 + max_retries 次重试
            start = time.time()
            try:
                result = func(**args)      # 参数是 dict，用 ** 展开
                latency = int((time.time() - start) * 1000)

                # 路径1：工具正常返回，但标记 retryable=True
                if isinstance(result, dict) and result.get("retryable") is True:
                    if i < max_retries:
                        # 还能重试
                        self.log_tool_call(session_id, tool_name, "retry", i, latency,
                                    error="retryable", user_query=user_query)
                        time.sleep(1)
                        continue
                    else:
                        # 最后一次还是 retryable，重试耗尽 → degraded
                        self.log_tool_call(session_id, tool_name, "degraded", i, latency,
                                    error="retryable", user_query=user_query)
                        return self.make_failure_response(
                            "degraded", f"重试{max_retries}次仍失败",
                            retryable=False, retry_count=i,
                        )

                # 正常返回，原样返回
                status = result.get("status", "ok") if isinstance(result, dict) else "ok"
                self.log_tool_call(session_id, tool_name, status, i, latency, user_query=user_query)
                return result

            except Exception as e:
                latency = int((time.time() - start) * 1000)

                # 路径2：抛 TimeoutError，且还有重试次数
                if isinstance(e, TimeoutError):
                    if i < max_retries:
                        # 还能重试
                        self.log_tool_call(session_id, tool_name, "retry", i, latency,
                                    error="timeout", user_query=user_query)
                        time.sleep(1)
                        continue
                    else:
                        # 最后一次还是超时，重试耗尽 → degraded（不是 error）
                        self.log_tool_call(session_id, tool_name, "degraded", i, latency,
                                    error="timeout", user_query=user_query)
                        return self.make_failure_response(
                            "degraded", f"重试{max_retries}次仍失败",
                            retryable=False, retry_count=i,
                        )

                # 其他异常（非超时），直接 error
                self.log_tool_call(session_id, tool_name, "error", i, latency,
                            error=type(e).__name__, user_query=user_query)
                return self.make_failure_response(
                    "error", f"工具执行出错：{type(e).__name__}",
                    retryable=False, retry_count=i,
                )

        # 循环外：重试耗尽
        self.log_tool_call(session_id, tool_name, "degraded", max_retries, 0,
                    error="max_retries", user_query=user_query)
        return self.make_failure_response(
            "degraded", f"重试{max_retries}次仍失败",
            retryable=False, retry_count=max_retries,
        )