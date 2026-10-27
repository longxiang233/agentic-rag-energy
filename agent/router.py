def route_query(query: str) -> str:
    """规则路由：先按关键词粗分，返回 'policy' / 'price' / 'vector'。
    用于和 LLM 路由对比，MVP 阶段不强制使用。"""
    q = query.lower()

    # 1. 电价类：问数字、价格、价差、补偿金额
    price_kw = ["多少钱", "价格", "价差", "单价", "上浮", "上限", "下限", "元/kwh"]
    if any(k in q for k in price_kw):
        return "price"

    # 2. 政策类：问文件、条款、备案、市场、规定
    policy_kw = ["政策", "规定", "备案", "市场", "文件", "条款", "出自", "依据", "材料"]
    if any(k in q for k in policy_kw):
        return "policy"

    # 3. 其余归通用
    return "vector"