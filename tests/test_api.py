"""
API 接口测试 - 覆盖所有端点
运行方式: python tests/test_api.py
前提: 后端已启动 (uvicorn new_app:app --port 35052)
"""
import sys
import os
import requests
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
from tests.conftest import BASE_URL, get_auth_header, print_section, print_pass, print_fail

passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        print_pass(name)
        passed += 1
    else:
        print_fail(name)
        failed += 1


# ==================== 1. 基础端点 ====================

print_section("1. 基础端点")

r = requests.get(f"{BASE_URL}/")
check("GET / 返回 200", r.status_code == 200)
check("GET / 返回版本号", "version" in r.json())

r = requests.get(f"{BASE_URL}/health")
check("GET /health 返回 ok", r.json().get("status") == "ok")


# ==================== 2. 认证接口 ====================

print_section("2. 认证接口")

# 管理员登录
r = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin", "password": "admin123"
})
check("管理员登录成功", r.status_code == 200)
admin_token = r.json().get("token", "")
check("返回 JWT token", len(admin_token) > 10)

# 商家登录
r = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "merchant", "password": "merchant123"
})
check("商家登录成功", r.status_code == 200)
merchant_token = r.json().get("token", "")

# 错误密码
r = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin", "password": "wrong"
})
check("错误密码返回 401", r.status_code == 401)

# 获取当前用户
headers = get_auth_header(admin_token)
r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
check("GET /auth/me 返回用户信息", r.json().get("user", {}).get("username") == "admin")

# 未认证访问
r = requests.get(f"{BASE_URL}/auth/me")
check("未认证访问返回 401/403", r.status_code in (401, 403))

# 用户列表（管理员权限）
r = requests.get(f"{BASE_URL}/auth/users", headers=headers)
check("管理员获取用户列表", r.status_code == 200)
check("用户列表包含 admin", any(
    u["username"] == "admin" for u in r.json().get("users", [])
))

# 商家无权获取用户列表
merchant_headers = get_auth_header(merchant_token)
r = requests.get(f"{BASE_URL}/auth/users", headers=merchant_headers)
check("商家无权访问用户列表 (403)", r.status_code == 403)


# ==================== 3. 预设问题 ====================

print_section("3. 预设问题")

r = requests.get(f"{BASE_URL}/presets", headers=headers)
check("获取预设问题成功", r.status_code == 200)
presets = r.json().get("presets", {})
check("预设类别 >= 4", len(presets) >= 4)
total_questions = sum(len(v) for v in presets.values())
check(f"共 {total_questions} 个预设问题", total_questions >= 15)

for cat, questions in presets.items():
    print(f"    {cat}: {len(questions)} 个问题")


# ==================== 4. NL2SQL 查询 ====================

print_section("4. NL2SQL 查询")

test_questions = [
    "各行为类型的数量分布",
    "销量最高的前10个商品",
    "男女用户比例是多少",
]

for q in test_questions:
    start = time.time()
    r = requests.post(f"{BASE_URL}/query", data={"user_question": q}, headers=headers, timeout=120)
    elapsed = time.time() - start

    ok = r.status_code == 200 and "error" not in r.json()
    check(f"查询「{q[:15]}...」({elapsed:.1f}s)", ok)

    if ok:
        data = r.json()
        sql = data.get("sql", "")
        print(f"    SQL: {sql[:80]}{'...' if len(sql) > 80 else ''}")
        result_count = len(data.get("result", []) or [])
        print(f"    结果: {result_count} 行 | 耗时: {data.get('time', 'N/A')}")


# ==================== 5. 缓存命中 ====================

print_section("5. 查询缓存")

q = "各行为类型的数量分布"

# 第一次查询
start = time.time()
r1 = requests.post(f"{BASE_URL}/query", data={"user_question": q}, headers=headers, timeout=120)
t1 = time.time() - start

# 第二次查询（应命中缓存）
start = time.time()
r2 = requests.post(f"{BASE_URL}/query", data={"user_question": q}, headers=headers, timeout=120)
t2 = time.time() - start

check("第二次查询命中缓存", r2.json().get("cached") == True)
check(f"缓存加速: {t1:.2f}s → {t2:.2f}s", t2 < t1)
print(f"    首次: {t1:.2f}s | 缓存: {t2:.2f}s | 加速比: {t1/max(t2, 0.01):.1f}x")


# ==================== 6. 查询历史 ====================

print_section("6. 查询历史")

r = requests.get(f"{BASE_URL}/history?limit=5", headers=headers)
check("获取查询历史成功", r.status_code == 200)
history = r.json().get("history", [])
check(f"历史记录 >= 1 条 (当前 {len(history)} 条)", len(history) >= 1)

if history:
    latest = history[0]
    print(f"    最近: {latest.get('question', '')[:30]} | {latest.get('time_cost', '')} | 缓存={latest.get('cached')}")


# ==================== 汇总 ====================

print_section("测试汇总")
total = passed + failed
print(f"  通过: {passed}/{total}")
print(f"  失败: {failed}/{total}")
if failed == 0:
    print("  全部通过!")
else:
    print(f"  有 {failed} 项失败，请检查后端日志")

sys.exit(0 if failed == 0 else 1)
