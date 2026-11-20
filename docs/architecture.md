# 架构说明

## 1. 架构概述

本项目是一个基于 Rust 的无服务器 CRUD API 应用程序，现已适配到华为云。由于 FunctionGraph 不支持 Rust 运行时，Rust 函数已适配为 Python 实现。

## 2. 架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         华为云                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────┐     ┌──────────────────────────────┐           │
│   │   APIG      │────▶│   FunctionGraph              │           │
│   │ (HTTP API)  │     │   • get-products (Python)   │           │
│   └──────────────┘     │   • get-product (Python)    │           │
│          │              │   • put-product (Python)    │           │
│          │              │   • delete-product (Python) │           │
│          │              │   • change-scanner (定时) │           │
│          │              └──────────────┬───────────────┘           │
│          │                             │                           │
│          │                             ▼                           │
│          │              ┌───────────────────────────────┐          │
│          │              │   GeminiDB                   │          │
│          │              │   (Cassandra 兼容模式)        │          │
│          │              └───────────────────────────────┘          │
│          │                             │                           │
│          │              ┌──────────────┴───────────────┐          │
│          │              │   SMN (EventGrid)          │          │
│          │              │   事件发布                   │          │
│          │              └─────────────────────────────┘          │
│          │                                                     │
│          ▼                                                     │
│   ┌──────────────┐                                           │
│   │   LTS        │                                           │
│   │  (日志服务)  │                                           │
│   └──────────────┘                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. 组件说明

### 3.1 APIG (API Gateway)

- **作用**: 接收 HTTP 请求路由到对应的 FunctionGraph 函数
- **配置**:
  - `GET /` → get-products
  - `GET /{id}` → get-product
  - `PUT /{id}` → put-product
  - `DELETE /{id}` → delete-product
- **类型**: 专享实例 (BASIC)

### 3.2 FunctionGraph

| 函数名 | 用途 | 实现语言 | 超时 |
|--------|------|----------|------|
| get-products | 获取产品列表 | Python | 5s |
| get-product | 获取单个产品 | Python | 5s |
| put-product | 创建/更新产品 | Python | 5s |
| delete-product | 删除产品 | Python | 5s |
| change-scanner | 处理数据变更事件 | Python | 10s |

### 3.3 GeminiDB

- **模式**: Cassandra 兼容
- **存储引擎**: rocksDB
- **副本数**: 2

### 3.4 SMN (Simple Message Notification)

- **作用**: 事件驱动，替代原 EventBridge
- **用途**: 接收产品变更事件

## 4. 事件流设计

### 4.1 原架构

```
Cassandra Streams → FunctionGraph → EventBridge
```

### 4.2 华为云架构

**方案A (推荐)**: 直接调用
```
PUT/DELETE → FunctionGraph → GeminiDB + SMN
```

**方案B**: 定时扫描
```
定时触发 → FunctionGraph → 扫描 GeminiDB → SMN
```

## 5. 部署说明

部署使用 Terraform IaC，详情见 `infra/` 目录。

函数代码在 `src/functions/` 目录，打包后上传到 OBS。

## 6. 注意事项

1. **Python 适配**: FunctionGraph 不支持 Rust，函数已适配为 Python
2. **Cassandra Streams**: GeminiDB 不支持 Streams，使用定时扫描或直接调用替代
3. **IAM 委托**: FunctionGraph 需要配置 Agency 访问 GeminiDB 和 SMN
4. **依赖打包**: 函数依赖 cassandra-driver，需要打包到 zip 中
