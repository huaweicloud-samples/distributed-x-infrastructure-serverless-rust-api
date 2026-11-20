# 函数代码构建与部署指南

## 概述

由于华为云 FunctionGraph 不支持 Rust 运行时，本项目将 Rust 函数适配为 Python 实现。

## 目录结构

```
src/functions/
├── get_products.py      # 获取产品列表
├── get_product.py       # 获取单个产品
├── put_product.py       # 创建/更新产品
├── delete_product.py    # 删除产品
├── change_scanner.py  # Cassandra Streams 处理器
└── requirements.txt     # Python 依赖
```

## 依赖项

- cassandra-driver >= 3.29.0

## 构建步骤

### 1. 创建虚拟环境（可选）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 打包函数代码

每个函数需要单独打包为 zip 文件：

```bash
# 为每个函数创建 zip
cd src/functions

# get_products
mkdir -p build/get_products
cp get_products.py build/get_products/index.py
pip install -r requirements.txt -t build/get_products/
cd build/get_products
zip -r ../../../../infra/function-code/get-products.zip .
cd ../../../..

# 重复其他函数...
```

### 4. 上传到 OBS

将生成的 zip 文件上传到 OBS 桶：

```bash
# 使用 obsutil 或控制台上传
obsutil cp get-products.zip obs://your-bucket/function-code/
```

### 5. 更新 Terraform 配置

在 `infra/main.tf` 中更新函数的 `code_url`：

```hcl
resource "huaweicloud_fgs_function" "get_products" {
  # ...
  code_type = "obs"
  code_url  = "https://your-bucket.obs.region.myhuaweicloud.com/function-code/get-products.zip"
}
```

## 环境变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| CASSANDRA_KEYSPACE | keyspace 名 | productsdb |
| REGION | 区域 | cn-north-4 |
| CASSANDRA_HOSTS | GeminiDB 内网地址 | 192.168.x.x |
| SMN_ENDPOINT | SMN 端点 | https://smn.cn-north-4.myhuaweicloud.com |
| SMN_TOPIC_URN | SMN Topic URN | urn:smn:cn-north-4:xxx:serverless-rust-demo-event-bus |

## 事件发布 (SMN/EventGrid)

原架构使用 Cassandra Streams → FunctionGraph → EventBridge，由于 GeminiDB 不支持 Streams，替代方案：

1. **put_product.py** 和 **delete_product.py** 在写入/删除后直接调用 SMN 发布事件
2. **change_scanner.py** 作为定时任务，定期扫描表变更并发布事件

## IAM 委托

FunctionGraph 需要配置 IAM 委托以访问：
- GeminiDB (读写 Cassandra 表)
- SMN (发布事件)

已在 Terraform 中配置 `huaweicloud_identity_agency`。
