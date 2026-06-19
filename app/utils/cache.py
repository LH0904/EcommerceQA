"""
查询缓存 - LRU 淘汰策略
"""
import hashlib
from collections import OrderedDict

from app.config import settings


class QueryCache:
    """基于 OrderedDict 的 LRU 缓存，容量可配置"""

    def __init__(self, max_size: int = None):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size or settings.CACHE_MAX_SIZE

    def get(self, key: str):
        """获取缓存条目，未命中返回 None"""
        if key in self._cache:
            # 移到末尾（最近使用）
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: dict) -> None:
        """存入缓存，超容量时淘汰最旧条目"""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)  # 淘汰最旧
            self._cache[key] = value

    @staticmethod
    def make_key(question: str) -> str:
        """对问题归一化后生成 MD5 缓存键"""
        normalized = question.strip().lower().replace("\uff1f", "?").replace("\uff0c", ",")
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def __len__(self):
        return len(self._cache)

    def clear(self):
        self._cache.clear()
