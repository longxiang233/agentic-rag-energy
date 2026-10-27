## 1. 存储结构

| 字段 | 类型 | 作用 | 谁写 | 谁读 |
| ---- | ---- | ---- | ---- | ---- |
|session_id | str | 会话唯一标识 | 调用方传入 | store所有方法 |
| messages | list | 历史消息列表(HumanMessage/AIMessage/ToolMessage) | save_message | get_history |
| created_at | float | 创建时间戳 | get_or_create | 清理逻辑 |
| updated_at | float | 最后更新时间 | save_message | 清理逻辑 |

## 2. store方法清单

| 方法 | 签名 | 作用 | 返回 |
| ---- | ---- | ---- | ---- | 
| get_or_create | (session_id) -> dict | 拿会话，没有就建 | 会话dict |
| get_history | (session_id) -> list | 拿历史messages | list |
| save_message | (session_id,message) -> None | 追加一条消息 | None |
| clear | (session_id) -> None | 清空会话 | None |
| list_sessions | () -> list[str] | 列出所有session_id | list |

## 3. 四块对应实现

| 块 | 做什么 | 在哪个方法 |
| --- | --- | --- |
| 存储 | {session_id: {...}}内存dict | get_or_create/save_message |
| 注入 | 新请求拼历史messages | 在executor.py的调用处，不在store |
| 消解 | LLM从历史消解指代("它"指谁) | 靠注入历史+prompt引导，不单独写代码 |
| 清理 | 历史超过N轮截断 | get_history 里 [-MAX_TURNS * 2:] | 