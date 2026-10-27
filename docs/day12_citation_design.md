**表1：citations 结构**

| 字段 | 类型 | 来源 | 示例 |
|------|------|------|------|
| `source` | str | 工具返回的 `d["source"]` | `山东独立储能政策.txt` |
| `content` | str | 工具返回的 `d["content"][:100]` | `三、市场化容量补偿机制...` |
| `score` | float | 工具返回的 `d["score"]` | `0.9147` |
| `tool` | str | 哪个工具返回的 | `vector_search` |
去重维度：按 source 去重，同一 source 保留最高 score 的那条。不加的话，vector_search 返回 3 个 chunk 都来自同一个 山东独立储能政策.txt，citations 里会出现 3 条重复 source。

**表2：`chat_with_memory` 新返回结构**

| 字段 | 类型 | 说明 |
|------|------|------|
| `answer` | str | Agent 最终回答 |
| `citations` | list[dict]【list[Citation]】 | 去重后的 citation 列表，最多 3 条(按 score 升序（距离越小越相关）取前 3。) |
| `tool_calls` | list[str] | 本次调用了哪些工具，如 `["vector_search"]` |
| `status` | str | ok / fallback / degraded / clarify / empty |
| `session_id` | str | 透传 |
Day 12 下午 routes.py 用 Pydantic 的 Citation 模型，chat_with_memory 返回 list[dict]，ChatResponse(**result) 时 Pydantic 会自动转。表2 的 citations 类型建议写 list[dict]（服务层），接口层再转 list[Citation]。 现在表2 写 list[dict] 可以，但要注明“接口层用 Pydantic 转”。

**表3：status 怎么推断**

| 条件 | 接口层 status | 说明 |
| :--- | :--- | :--- |
| 入口空输入 | clarify | 直接返回引导话术，不调 LLM |
| 有 citations 且至少一个工具 status=ok | ok | 正常检索成功 |
| 有 citations 但工具 status=fallback | fallback | 降级成功，接口层新增 fallback 状态 |
| 无 citations 且工具 status=clarify | clarify | 工具让用户补信息 |
| 无 citations 且工具 status=empty/degraded/error | degraded | 没拿到结果 |
| 无 citations 但工具 status=ok（如 price_query） | ok | 结构化工具成功，无 citation 是正常的 |