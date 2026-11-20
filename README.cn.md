# 无服务器 Rust CRUD API：华为云最佳实践

[English](./README.md)

![Terraform](https://img.shields.io/badge/Terraform-1.5+-7B42BC?style=flat-square)
![Huawei Cloud](https://img.shields.io/badge/Huawei-Cloud-FF6600?style=flat-square)
![APIG](https://img.shields.io/badge/APIG-Latest-blue?style=flat-square)

## 1. 简介

这是一个基于 Rust 的无服务器 CRUD API 应用程序，已适配到华为云。由于华为云 FunctionGraph 不支持 Rust 运行时，原 Rust 函数已适配为 Python 实现，保持相同的 API 接口和业务逻辑。

### 1.1 功能特性

- 产品 CRUD 操作（创建、读取、更新、删除）
- 事件驱动架构
- 无服务器计算
- RESTful API

### 1.2 架构亮点

- **无服务器**: 使用 FunctionGraph，无需管理服务器
- **高可用**: APIG 专享实例 + GeminiDB 集群
- **事件驱动**: SMN (EventGrid) 实现事件总线
- **日志**: LTS 集中日志管理

## 2. 技术栈

| 组件 | 华为云服务 | 说明 |
|------|------------|------|
| API 网关 | APIG | HTTP API 入口 |
| 计算 | FunctionGraph | 无服务器函数 (Python) |
| 存储 | GeminiDB | Cassandra 兼容 |
| 事件 | SMN (EventGrid) | 事件总线 |
| 日志 | LTS | 日志服务 |

## 3. 前置条件

- 华为云账号
- Terraform CLI (>= 1.5)
- Python 3.9+
- OBS 桶（存储函数代码）

## 4. 快速开始

### 4.1 克隆仓库

```bash
git clone <repository-url>
cd distributed-x-infrastructure-serverless-rust-api
```

### 4.2 配置凭据

```bash
export HW_ACCESS_KEY="your-access-key"
export HW_SECRET_KEY="your-secret-key"
export HW_REGION="cn-north-4"
```

### 4.3 打包函数代码

```bash
cd src/functions

# 创建 OBS 桶并上传函数代码
# 详见 BUILD.md
```

### 4.4 部署

```bash
cd infra
terraform init
terraform plan
terraform apply
```

## 5. 目录结构

```
├── docs/                  # 文档
│   ├── architecture.md    # 架构说明
│   └── deployment-guide.md # 部署指南
├── infra/                 # Terraform IaC
│   ├── main.tf          # 主配置
│   └── function-code/   # 函数代码包
├── src/                  # 函数源代码
│   └── functions/       # Python 函数实现
│       ├── get_products.py
│       ├── get_product.py
│       ├── put_product.py
│       ├── delete_product.py
│       ├── change_scanner.py
│       └── BUILD.md
└── README.md            # 本文件
```

## 6. 使用方法

### 6.1 API 端点

部署后获取 API URL：

```bash
terraform output api_gateway_url
```

### 6.2 API 调用示例

```bash
# 获取产品列表
curl https://<api-gateway-url>/

# 获取单个产品
curl https://<api-gateway-url>/product-1

# 创建产品
curl -X PUT https://<api-gateway-url>/product-1 \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "price": 99.99}'

# 删除产品
curl -X DELETE https://<api-gateway-url>/product-1
```

### 6.3 验证

```bash
# 验证 API 可用性
curl -s https://<api-gateway-url>/ | jq .
```

## 7. 架构详解

### 7.1 Rust → Python 适配

由于 FunctionGraph 不支持 Rust 运行时，Rust 函数已适配为 Python：

| 原 Rust 函数 | Python 实现 |
|--------------|-------------|
| GetProductsFunction | get_products.py |
| GetProductFunction | get_product.py |
| PutProductFunction | put_product.py |
| DeleteProductFunction | delete_product.py |
| DDBStreamsFunction | change_scanner.py |

### 7.2 Cassandra Streams 替代

GeminiDB 不支持 Cassandra Streams，采用以下替代方案：

1. **直接调用**: put_product/delete_product 在写入后直接调用 SMN 发布事件
2. **定时扫描**: change_scanner.py 定期扫描表变更并发布事件

## 8. 清理

```bash
cd infra
terraform destroy
```

## 9. 常见问题

### Q1: 为什么用 Python 而不是 Rust？

华为云 FunctionGraph 不支持 Rust 运行时，因此适配为 Python 实现。

### Q2: Cassandra Streams 如何处理？

GeminiDB 不支持 Streams，使用定时扫描或直接调用替代。

### Q3: 如何更新函数代码？

1. 修改 `src/functions/` 中的 Python 代码
2. 重新打包为 zip
3. 上传到 OBS
4. 更新 Terraform 中的 code_url

## 10. 费用说明

部署以下资源会产生费用：

- APIG 专享实例
- GeminiDB 集群
- FunctionGraph 调用次数
- OBS 存储和流量

具体价格请参考 [华为云定价](https://www.huaweicloud.com/settlement.html)。

## 11. 许可证

本项目基于 MIT No Attribution 许可证。

## 12. 联系方式

- 问题反馈: [Issue Tracker](https://github.com/huaweicloud-samples/distributed-x-infrastructure-serverless-rust-api/issues)
