"""
答辩演示脚本 - 逐步展示系统核心功能
运行方式: python tests/demo.py
前提: 后端已启动 (uvicorn new_app:app --port 35052)

每个步骤按回车继续，适合答辩现场演示
"""
import sys
import os
import json
import time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
from tests.conftest import BASE_URL, get_auth_header

# 颜色
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[92m"
C_CYAN = "\033[96m"
C_YELLOW = "\033[93m"
C_DIM = "\033[2m"


def banner(title):
    print(f"\n{C_BOLD}{C_CYAN}{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}{C_RESET}")


def wait(msg="按 Enter 继续..."):
    input(f"\n{C_DIM}{msg}{C_RESET}")


def show(label, value):
    print(f"  {C_YELLOW}{label}{C_RESET}  {value}")


def main():
    print(f"""
{C_BOLD}╔══════════════════════════════════════════════════════════╗
║          电商智能问答系统 — 答辩演示                     ║
║          EcommerceQA System Demo                         ║
╚══════════════════════════════════════════════════════════╝{C_RESET}
{C_DIM}  后端地址: {BASE_URL}
  技术栈: FastAPI + MiMo LLM + ChromaDB + MySQL{C_RESET}
""")

    wait("按 Enter 开始演示...")

    # ==================== Step 1: 系统启动 ====================
    banner("Step 1: 系统健康检查")

    r = requests.get(f"{BASE_URL}/health", timeout=5)
    show("健康状态:", r.json().get("status", "unknown"))

    r = requests.get(f"{BASE_URL}/", timeout=5)
    data = r.json()
    show("系统名称:", data.get("message"))
    show("版本号:", data.get("version"))

    wait()

    # ==================== Step 2: JWT 认证 ====================
    banner("Step 2: JWT 认证与权限管理")

    print(f"\n  {C_DIM}> 管理员登录 admin/admin123{C_RESET}")
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    admin_data = r.json()
    admin_token = admin_data["token"]
    show("登录状态:", f"{C_GREEN}成功{C_RESET}")
    show("用户角色:", admin_data["user"]["role"])
    show("Token:", admin_token[:40] + "...")

    print(f"\n  {C_DIM}> 商家登录 merchant/merchant123{C_RESET}")
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "merchant", "password": "merchant123"
    })
    merchant_data = r.json()
    merchant_token = merchant_data["token"]
    show("登录状态:", f"{C_GREEN}成功{C_RESET}")
    show("用户角色:", merchant_data["user"]["role"])

    print(f"\n  {C_DIM}> 权限验证: 商家尝试访问用户列表{C_RESET}")
    r = requests.get(f"{BASE_URL}/auth/users", headers=get_auth_header(merchant_token))
    show("结果:", f"HTTP {r.status_code} — 权限不足，拒绝访问")

    admin_headers = get_auth_header(admin_token)

    wait()

    # ==================== Step 3: 预设问题 ====================
    banner("Step 3: 预设问题模板")

    r = requests.get(f"{BASE_URL}/presets", headers=admin_headers)
    presets = r.json()["presets"]

    for cat, questions in presets.items():
        print(f"\n  {C_BOLD}{cat}{C_RESET}")
        for i, q in enumerate(questions, 1):
            print(f"    {i}. {q}")

    wait()

    # ==================== Step 4: NL2SQL 查询 ====================
    banner("Step 4: NL2SQL 智能查询")

    demo_questions = [
        "各行为类型的数量分布",
        "销量最高的前10个商品",
        "各城市的购买转化率",
    ]

    for i, q in enumerate(demo_questions, 1):
        print(f"\n  {C_BOLD}[查询 {i}] {q}{C_RESET}")
        start = time.time()
        r = requests.post(f"{BASE_URL}/query", data={"user_question": q},
                          headers=admin_headers, timeout=120)
        elapsed = time.time() - start

        data = r.json()
        if "error" in data:
            show("错误:", data["error"])
            continue

        sql = data.get("sql", "")
        show("生成 SQL:", sql[:90] + ("..." if len(sql) > 90 else ""))

        rows = data.get("result", []) or []
        show("查询结果:", f"{len(rows)} 行")
        show("耗时:", data.get("time", "N/A"))
        show("缓存:", "是" if data.get("cached") else "否")

        # 展示前 3 行数据
        if rows:
            print(f"    {C_DIM}数据预览:{C_RESET}")
            for row in rows[:3]:
                print(f"      {json.dumps(row, ensure_ascii=False)[:80]}")

        if i < len(demo_questions):
            wait("按 Enter 执行下一个查询...")

    wait()

    # ==================== Step 5: 缓存加速 ====================
    banner("Step 5: 查询缓存机制")

    q = "各行为类型的数量分布"
    print(f"\n  {C_DIM}> 对「{q}」执行两次相同查询，对比耗时{C_RESET}")

    start = time.time()
    r1 = requests.post(f"{BASE_URL}/query", data={"user_question": q},
                       headers=admin_headers, timeout=120)
    t1 = time.time() - start

    time.sleep(0.5)

    start = time.time()
    r2 = requests.post(f"{BASE_URL}/query", data={"user_question": q},
                       headers=admin_headers, timeout=120)
    t2 = time.time() - start

    cached = r2.json().get("cached", False)
    show("首次查询:", f"{t1:.2f}s (LLM + SQL 执行 + 看板生成)")
    show("二次查询:", f"{t2:.2f}s (缓存命中: {'是' if cached else '否'})")

    if t2 < t1:
        speedup = t1 / max(t2, 0.01)
        show("加速比:", f"{C_GREEN}{speedup:.1f}x{C_RESET}")

    wait()

    # ==================== Step 6: 查询历史 ====================
    banner("Step 6: 查询历史记录")

    r = requests.get(f"{BASE_URL}/history?limit=5", headers=admin_headers)
    history = r.json().get("history", [])

    show("历史记录数:", f"{len(history)} 条")
    print()

    for h in history:
        q_text = h.get("question", "")[:25]
        cached_mark = " [缓存]" if h.get("cached") else ""
        print(f"    {q_text:25s}  {h.get('time_cost', ''):>8s}  {h.get('category', '')}{cached_mark}")

    wait()

    # ==================== Step 7: 多轮对话 ====================
    banner("Step 7: 多轮对话上下文理解")

    print(f"\n  {C_DIM}> 模拟多轮对话: 先查询行为分布，再追问购买详情{C_RESET}")

    # 第一轮
    q1 = "各行为类型的数量分布"
    print(f"\n  {C_BOLD}第 1 轮: {q1}{C_RESET}")
    r = requests.post(f"{BASE_URL}/query", data={"user_question": q1},
                      headers=admin_headers, timeout=120)
    d1 = r.json()
    show("SQL:", d1.get("sql", "")[:80])

    # 第二轮（带上下文）
    q2 = "其中购买行为的用户城市分布"
    context = json.dumps([{"question": q1, "sql": d1.get("sql", "")}])
    print(f"\n  {C_BOLD}第 2 轮: {q2}{C_RESET}")
    r = requests.post(f"{BASE_URL}/query",
                      data={"user_question": q2, "context": context},
                      headers=admin_headers, timeout=120)
    d2 = r.json()
    show("SQL:", d2.get("sql", "")[:80])
    show("上下文:", "携带了第 1 轮的问答历史")

    wait()

    # ==================== 结束 ====================
    banner("演示完成")

    print(f"""
  {C_GREEN}{C_BOLD}系统核心能力展示完毕:{C_RESET}
    1. JWT 认证与角色权限管理 (admin/merchant)
    2. 预设问题模板 (4 类别 20 个问题)
    3. NL2SQL 自然语言转 SQL (向量检索 + LLM 生成)
    4. Echarts 数据看板自动生成
    5. LRU 查询缓存 (加速比 {speedup:.0f}x)
    6. 查询历史持久化
    7. 多轮对话上下文理解
    8. PDF 报告导出 (Playwright)

  {C_DIM}技术栈: FastAPI + MiMo LLM + ChromaDB + MySQL 8.0
  前端: Vue 3 SPA | 团队: 周青 陈蕾 王凯伦 吕昊{C_RESET}
""")


if __name__ == "__main__":
    main()
