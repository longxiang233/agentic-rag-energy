import pytest
from agent.executor import chat_with_memory
from fastapi.testclient import TestClient
from api.routes import app

def test_case_01():
    result = chat_with_memory("e2e_01", "新型储能备案需要什么材料")
    print(result["status"], result["tool_calls"], len(result["citations"]))
    assert result["status"] == "ok","01错了，status不是ok"
    assert "policy_search" in result["tool_calls"],"01错了，工具不是policy"
    assert len(result["citations"]) >= 1,"错了，引用不大于1"
    print("01通过")

def test_case_02():
    result = chat_with_memory("e2e_02", "山东峰谷价差多少")
    print(result["status"], result["tool_calls"], len(result["citations"]))
    assert result["status"] == "ok", "status错"
    assert "price_query" in result["tool_calls"], "工具错"
    assert len(result["citations"]) == 0, "引用错"
    print ("02通过")

def test_case_03():
    result = chat_with_memory("e2e_03", "什么是虚拟电厂")
    print("03实际:", result["status"], result["tool_calls"], len(result["citations"]))
    assert result["status"] == "ok"
    assert "vector_search" in result["tool_calls"]
    assert len(result["citations"]) >= 1

def test_case_04():
    result = chat_with_memory("e2e_04", "山东独立储能可参与哪些市场")
    print("04实际:", result["status"], result["tool_calls"], len(result["citations"]))
    assert result["status"] == "ok"
    assert "policy_search" in result["tool_calls"]
    assert len(result["citations"]) >= 1

def test_case_05():
    result = chat_with_memory("e2e_05", "山东储能容量补偿标准是多少")
    print("05实际:", result["status"], result["tool_calls"], len(result["citations"]))
    assert result["status"] == "ok"
    assert "price_query" in result["tool_calls"]
    assert len(result["citations"]) == 0

def test_case_06():
    result = chat_with_memory("e2e_06", "绿电交易是什么")
    print("06实际:", result["status"], result["tool_calls"], len(result["citations"]))
    assert result["status"] == "ok"
    assert "vector_search" in result["tool_calls"]
    assert len(result["citations"]) >= 1

def test_case_07():
    result = chat_with_memory("e2e_07", "xyz不存在的政策")
    print(result["status"], result["tool_calls"], len(result["citations"]))
    assert result["status"] == "degraded", "status错"
    assert "policy_search" in result["tool_calls"], "工具错"
    assert len(result["citations"]) == 0, "引用错"
    print ("07通过")

def test_case_08():
    result = chat_with_memory("e2e_08", "今天天气怎么样")
    assert result["status"] in ["clarify", "degraded"]
    assert len(result["citations"]) == 0, "引用错"
    print("08通过")

def test_case_09():
    client = TestClient(app)
    resp = client.post("/chat", json={"session_id": "e2e_09", "message": ""})
    assert resp.status_code == 422, "HTTP码错"
    body = resp.json()
    assert "detail" in body, "缺detail"
    assert "status" not in body, "不该有status"
    print("09通过")

def test_multi_turn():
    sid = "e2e_10"

    r1 = chat_with_memory(sid, "山东独立储能是什么")
    print("第1轮:", r1["status"], r1["tool_calls"], len(r1["citations"]), "|", r1["answer"][:80])
    assert r1["status"] == "ok"
    assert len(r1["citations"]) >= 1

    # 第2轮
    r2 = chat_with_memory(sid, "它能参与哪些市场")
    print("第2轮:", r2["status"], r2["tool_calls"], len(r2["citations"]), "|", r2["answer"][:80])
    assert r2["status"] in ["ok", "clarify"]
    assert "电能量市场" in r2["answer"] or "辅助服务市场" in r2["answer"]

    # 第3轮
    r3 = chat_with_memory(sid, "容量补偿多少")
    print("第3轮:", r3["status"], r3["tool_calls"], len(r3["citations"]), "|", r3["answer"][:80])
    assert r3["status"] in ["ok", "clarify"]
    assert "0.0705" in r3["answer"]

    # 第4轮
    r4 = chat_with_memory(sid, "xyz不存在的政策")
    print("第4轮:", r4["status"], r4["tool_calls"], len(r4["citations"]), "|", r4["answer"][:80])
    assert r4["status"] in ["clarify", "degraded"]
    assert len(r4["citations"]) == 0

    # 第5轮
    r5 = chat_with_memory(sid, "刚才那个政策再查")
    print("第5轮:", r5["status"], r5["tool_calls"], len(r5["citations"]), "|", r5["answer"][:80])
    assert r5["status"] in ["degraded", "clarify"]
    assert "xyz" in r5["answer"]

def test_case_11():
    client = TestClient(app)
    resp = client.post("/chat", json = {
        "session_id" : "e2e_11",
        "message": "新型储能备案需要什么材料",
    })
    assert resp.status_code == 200
    body = resp.json()
    for k in ["answer", "citations", "status", "session_id", "tool_calls"]:
        assert k in body, f"缺 {k}"
    assert body["status"] == "ok"
    assert len(body["citations"]) >= 1
    assert "policy_search" in body["tool_calls"]
    assert body["session_id"] == "e2e_11"
    print("11通过")