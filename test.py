import requests

url = 'http://localhost:35052/query'

questions = [
    "统计各行为类型的数量分布",
    "最受欢迎的前10个商品类别是什么",
    "计算整体的购买转化率",
    "统计每天的用户活跃数",
    "购买次数最多的前20个用户",
]

for question in questions:
    data = {'user_question': question}
    try:
        response = requests.post(url, data=data, timeout=60)
        print(f"问题：{question}")
        print(f"状态码：{response.status_code}")
        result = response.json()
        if 'error' in result:
            print(f"错误：{result['error']}")
        else:
            print(f"SQL：{result.get('sql', 'N/A')[:80]}...")
            print(f"耗时：{result.get('time', 'N/A')}")
        print("-" * 50)
    except Exception as e:
        print(f"请求失败：{e}")
        print("-" * 50)
