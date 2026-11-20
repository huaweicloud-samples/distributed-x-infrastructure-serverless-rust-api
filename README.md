# Serverless Rust CRUD API: Huawei Cloud Best Practice

[中文版](./README.cn.md)

![Terraform](https://img.shields.io/badge/Terraform-1.5+-7B42BC?style=flat-square)
![Huawei Cloud](https://img.shields.io/badge/Huawei-Cloud-FF6600?style=flat-square)
![APIG](https://img.shields.io/badge/APIG-Latest-blue?style=flat-square)

## 1. Introduction

This is a serverless CRUD API application originally written in Rust, now adapted for Huawei Cloud. Since Huawei Cloud FunctionGraph does not support Rust runtime, the original Rust functions have been adapted to Python while maintaining the same API interfaces and business logic.

### 1.1 Features

- Product CRUD operations (Create, Read, Update, Delete)
- Event-driven architecture
- Serverless computing
- RESTful API

### 1.2 Architecture Highlights

- **Serverless**: Using FunctionGraph, no server management required
- **High availability**: APIG dedicated instance + GeminiDB cluster
- **Event-driven**: SMN (EventGrid) for event bus
- **Logging**: LTS for centralized log management

## 2. Technology Stack

| Component | Huawei Cloud Service | Description |
|-----------|---------------------|-------------|
| API Gateway | APIG | HTTP API entry point |
| Compute | FunctionGraph | Serverless functions (Python) |
| Storage | GeminiDB | Cassandra compatible |
| Events | SMN (EventGrid) | Event bus |
| Logging | LTS | Log service |

## 3. Prerequisites

- Huawei Cloud account
- Terraform CLI (>= 1.5)
- Python 3.9+
- OBS bucket (for storing function code)

## 4. Quick Start

### 4.1 Clone the Repository

```bash
git clone <repository-url>
cd distributed-x-infrastructure-serverless-rust-api
```

### 4.2 Configure Credentials

```bash
export HW_ACCESS_KEY="your-access-key"
export HW_SECRET_KEY="your-secret-key"
export HW_REGION="cn-north-4"
```

### 4.3 Package Function Code

```bash
cd src/functions

# Create OBS bucket and upload function code
# See BUILD.md for details
```

### 4.4 Deploy

```bash
cd infra
terraform init
terraform plan
terraform apply
```

## 5. Directory Structure

```
├── docs/                  # Documentation
│   ├── architecture.md    # Architecture documentation
│   └── deployment-guide.md # Deployment guide
├── infra/                 # Terraform IaC
│   ├── main.tf          # Main configuration
│   └── function-code/   # Function code packages
├── src/                  # Function source code
│   └── functions/       # Python function implementations
│       ├── get_products.py
│       ├── get_product.py
│       ├── put_product.py
│       ├── delete_product.py
│       ├── change_scanner.py
│       └── BUILD.md
└── README.md            # This file (English)
```

## 6. Usage

### 6.1 API Endpoints

Get API URL after deployment:

```bash
terraform output api_gateway_url
```

### 6.2 API Examples

```bash
# Get product list
curl https://<api-gateway-url>/

# Get single product
curl https://<api-gateway-url>/product-1

# Create product
curl -X PUT https://<api-gateway-url>/product-1 \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "price": 99.99}'

# Delete product
curl -X DELETE https://<api-gateway-url>/product-1
```

### 6.3 Verification

```bash
# Verify API availability
curl -s https://<api-gateway-url>/ | jq .
```

## 7. Architecture Details

### 7.1 Rust → Python Adaptation

Since FunctionGraph does not support Rust runtime, Rust functions have been adapted to Python:

| Original Rust Function | Python Implementation |
|----------------------|---------------------|
| GetProductsFunction | get_products.py |
| GetProductFunction | get_product.py |
| PutProductFunction | put_product.py |
| DeleteProductFunction | delete_product.py |
| DDBStreamsFunction | change_scanner.py |

### 7.2 Cassandra Streams Alternative

GeminiDB does not support Cassandra Streams. Alternative solutions:

1. **Direct Call**: put_product/delete_product publish events to SMN directly after write operations
2. **Scheduled Scan**: change_scanner.py periodically scans table changes and publishes events

## 8. Cleanup

```bash
cd infra
terraform destroy
```

## 9. FAQ

### Q1: Why Python instead of Rust?

Huawei Cloud FunctionGraph does not support Rust runtime, so we adapted to Python.

### Q2: How to handle Cassandra Streams?

GeminiDB does not support Streams. We use scheduled scan or direct call as alternatives.

### Q3: How to update function code?

1. Modify Python code in `src/functions/`
2. Repackage as zip
3. Upload to OBS
4. Update code_url in Terraform

## 10. spend

Deploying the following resources will incur charges:

- APIG dedicated instance
- GeminiDB cluster
- FunctionGraph invocation fees
- OBS storage and traffic

For settlement details, refer to the Huawei Cloud billing overview in the console.

## 11. License

This project is licensed under MIT No Attribution.

## 12. Contact

- Issue Tracker: [GitHub Issues](https://github.com/huaweicloud-samples/distributed-x-infrastructure-serverless-rust-api/issues)
