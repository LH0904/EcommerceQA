"""
测试公共配置 - API 基础地址和工具函数
"""

BASE_URL = "http://localhost:35052"


def get_auth_header(token: str) -> dict:
    """构造 Bearer 认证请求头"""
    return {"Authorization": f"Bearer {token}"}


def print_section(title: str):
    """打印分隔线标题"""
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def print_pass(msg: str):
    print(f"  [PASS] {msg}")


def print_fail(msg: str):
    print(f"  [FAIL] {msg}")
