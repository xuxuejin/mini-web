SHOW DATABASES;

CREATE DATABASE minics;

SHOW CREATE DATABASE minics;

USE minics;

SELECT DATABASE();

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '商品的唯一标识符',      -- 商品 ID
    name VARCHAR(255) NOT NULL COMMENT '商品名称',                    -- 商品名称
    description TEXT COMMENT '商品的详细描述',                         -- 商品描述
    price DECIMAL(10, 2) NOT NULL COMMENT '商品价格',                 -- 商品价格
    discount_price DECIMAL(10, 2) COMMENT '商品的折扣价格',            -- 商品折扣价（可选）
    image_url VARCHAR(255) COMMENT '商品图片的URL地址',                -- 商品图片路径
    stock INT DEFAULT 0 COMMENT '商品的库存数量',                      -- 库存
    is_active BOOLEAN DEFAULT TRUE COMMENT '商品是否上架',             -- 是否上架
    category_id INT COMMENT '分类ID，引用分类表',                       -- 分类ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '商品的创建时间',  -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '商品的更新时间'  -- 更新时间
) COMMENT='商品表，包含商品的基本信息';

-- 在 MySQL 中，BOOLEAN 实际上是 TINYINT(1) 的一种别名。TINYINT(1) 用来表示一个小整数，通常用 0 表示 FALSE，用 1 表示 TRUE。
-- 虽然上面创建表时定义了 is_active BOOLEAN DEFAULT TRUE，但在 MySQL 的实际存储过程中，它会将 TRUE 存储为 1，而将 FALSE 存储为 0。

DESC products;

# 导入数据
INSERT INTO products (name, description, price, discount_price, image_url, stock, is_active, category_id)
VALUES
('佳能550D', 'Description 1', 3670.00, 90.00, 'https://cdnjson.com/image/p1.ayPE8', 50, TRUE, 1),
('手机无线游戏手柄', 'Description 2', 1500.00, 140.00, 'https://cdnjson.com/image/p2.ayvtZ', 30, TRUE, 2),
('无人机', 'Description 3', 2700.00, 180.00, 'https://cdnjson.com/image/p3.ayGKF', 20, TRUE, 3),
('定焦镜头', 'Description 4', 850.00, 230.00, 'https://cdnjson.com/image/p4.aygAJ', 10, TRUE, 1),
('音响', 'Description 5', 760.00, 230.00, 'https://cdnjson.com/image/p5.ay5NB', 10, TRUE, 4),
('主机游戏手柄', 'Description 6', 1360.00, 230.00, 'https://cdnjson.com/image/p6.ay0F2', 10, TRUE, 2),
('高端白色无人机', 'Description 7', 3800.00, 230.00, 'https://cdnjson.com/image/p7.ayita', 10, TRUE, 3),
('尼康相机', 'Description 8', 3070.00, 230.00, 'https://cdnjson.com/image/p8.ay9cU', 10, TRUE, 1),
('无人摄像头', 'Description 9', 1260.00, 230.00, 'https://cdnjson.com/image/p9.ayb1j', 10, TRUE, 5);

-- 假设还有一个分类表，定义如下：
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,             -- 分类 ID，自动递增主键
    name VARCHAR(255) NOT NULL                     -- 分类名称
);

-- 建立外键关联
ALTER TABLE products ADD CONSTRAINT fk_category
FOREIGN KEY (category_id) REFERENCES categories(id);
