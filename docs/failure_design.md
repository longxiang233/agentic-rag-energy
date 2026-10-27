## 1. 三个工具的失败场景

| 工具 | 失败类型 | 触发条件 | retryable | 处理动作 | 返回结构 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| vector_search | 超时重试中 | 第1/2次重试 | True | sleep(1) 后重试 | 仅日志 {"status":"retry","retry_count":i}，不返回 Agent |
| vector_search | 超时耗尽 | 重试2次仍超时 | True | 降级 | {"status":"degraded","hint":"检索服务暂时不可用，请稍后重试"} |
| vector_search | 返回空 | retrieve 返回 [] | False | 降级提示 | {"status":"empty","hint":"未找到相关文档，建议换关键词"} |
| policy_search | 返回空 | 过滤后 policy_docs == [] | False | 降级到 vector_search | {"status":"fallback","hint":"已切换通用检索","data":"<vector结果摘要>"} |
| policy_search | 降级后仍空 | policy 空 → vector 也空 | False | 最终兜底 | {"status":"degraded","hint":"未找到相关政策或通用信息，建议换关键词"} |
| price_query | 未匹配关键词 | 三个 if 都没命中 | False | 澄清：列支持查询 | {"status":"clarify","hint":"支持查询：峰谷价差、容量补偿、现货价格"} |
| 任一工具 | 参数缺失 | query 为空或全空格 | False | 澄清：追问 | {"status":"clarify","hint":"请提供查询关键词"} |
| 任一工具 | 执行异常 | 非超时的 Exception | False | 记 error 日志 | {"status":"error","hint":"工具执行出错，请稍后重试"} |


degraded：回答降级，重试了但失败
fallback：工具降级（到通用）
empty：空
clarify：澄清
error：直接抛异常没重试

## 2. 返回结构统一
| 字段 | 类型 | 何时有 | 含义 |
| :--- | :--- | :--- | :--- |
| status | str | 必有 | ok / retry / degraded / fallback / clarify / empty / error |
| data | str | ok 或 fallback 时 | 正常返回内容 / 降级后的替代结果 |
| hint | str | 非 ok 时 | 给用户或 LLM 的提示 |
| retryable | bool | 非 ok 时 | 是否值得重试 |
| retry_count | int | 非 ok 时 | 实际重试次数 |

## 3. 日志字段
| 字段 | 类型 | 示例 | 作用 |
| :--- | :--- | :--- | :--- |
| ts | str | 2026-10-19 15:30:12 | 时间戳 |
| session_id | str | test_memory_day10 | 会话追踪 |
| tool | str | vector_search | 哪个工具 |
| status | str | degraded | 结果状态 |
| retry_count | int | 2 | 重试次数 |
| latency_ms | int | 1234 | 耗时（每次重试记一条）单次耗时 |
| error | str | timeout | 错误类型（可选） |
