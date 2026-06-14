DDL = [
    """
CREATE TABLE IF NOT EXISTS user_behavior (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL COMMENT '用户唯一标识',
    goods_id VARCHAR(32) NOT NULL COMMENT '商品唯一标识',
    category_id VARCHAR(32) NOT NULL COMMENT '商品类别ID',
    behavior_type VARCHAR(16) NOT NULL COMMENT '行为类型：浏览/收藏/加购/购买',
    timestamp DECIMAL(16,1) COMMENT '行为发生的Unix时间戳',
    gender VARCHAR(8) COMMENT '用户性别：男/女',
    city VARCHAR(64) COMMENT '用户所在城市',
    device VARCHAR(32) COMMENT '用户设备品牌',
    price DECIMAL(12,2) COMMENT '商品价格（元）',
    amount DECIMAL(12,2) COMMENT '购买金额（元）',
    datetime VARCHAR(32) COMMENT '行为发生的完整日期时间',
    date VARCHAR(16) COMMENT '行为日期',
    hour INT COMMENT '行为发生的小时',
    pv_count INT DEFAULT 0 COMMENT '浏览计数',
    cart_count INT DEFAULT 0 COMMENT '加购计数',
    fav_count INT DEFAULT 0 COMMENT '收藏计数',
    buy_count INT DEFAULT 0 COMMENT '购买计数',
    user_type VARCHAR(32) COMMENT '用户类型：窗口购物型/冲动消费型等',
    INDEX idx_user_id (user_id),
    INDEX idx_goods_id (goods_id),
    INDEX idx_category_id (category_id),
    INDEX idx_behavior (behavior_type),
    INDEX idx_date (date),
    INDEX idx_city (city),
    INDEX idx_datetime (datetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户行为表'
""",
    """
CREATE TABLE IF NOT EXISTS goods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    goods_id VARCHAR(32) NOT NULL COMMENT '商品唯一标识',
    sales_count INT DEFAULT 0 COMMENT '商品累计销量',
    goods_name VARCHAR(256) COMMENT '商品名称',
    category_id VARCHAR(32) COMMENT '商品所属类别ID',
    category_name VARCHAR(128) COMMENT '商品类别名称',
    UNIQUE KEY uk_goods_id (goods_id),
    INDEX idx_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品信息表'
""",
    """
CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL COMMENT '用户唯一标识',
    goods_id VARCHAR(32) NOT NULL COMMENT '商品唯一标识',
    category_id VARCHAR(32) COMMENT '商品类别ID',
    comment TEXT COMMENT '评论内容',
    INDEX idx_user_id (user_id),
    INDEX idx_goods_id (goods_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户评论表'
""",
    """
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id VARCHAR(32) NOT NULL COMMENT '类别唯一标识',
    product_count INT DEFAULT 0 COMMENT '该类别下的商品数量',
    category_name VARCHAR(128) COMMENT '类别名称',
    UNIQUE KEY uk_category_id (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品类别表'
""",
    """
CREATE TABLE IF NOT EXISTS user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL COMMENT '用户唯一标识',
    occupation VARCHAR(128) COMMENT '用户职业',
    UNIQUE KEY uk_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表'
""",
]
