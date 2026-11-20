# 部署指南

## 1. 前置条件

- 华为云账号
- Terraform CLI (>= 1.5)
- Python 3.9+
- OBS 桶（存储函数代码）

## 2. 配置步骤

### 2.1 配置华为云凭据

```bash
export HW_ACCESS_KEY="your-access-key"
export HW_SECRET_KEY="your-secret-key"
export HW_REGION="cn-north-4"
```

### 2.2 创建 OBS 桶

在华为云控制台创建 OBS 桶，用于存储函数代码：

```bash
# 或使用 Terraform
resource "huaweicloud_obs_bucket" "functions" {
  bucket = "your-function-bucket"
}
```

### 2.3 打包函数代码

```bash
cd src/functions

# 为每个函数创建独立目录并打包
for func in get_products get_product put_product delete_product change_scanner; do
  mkdir -p build/$func
  cp $func.py build/$func/index.py
  pip install -r requirements.txt -t build/$func/
  cd build/$func
  zip -r ../../../../infra/function-code/$func.zip .
  cd ../../..
done
```

### 2.4 上传到 OBS

```bash
obsutil cp infra/function-code/*.zip obs://your-bucket/function-code/
```

### 2.5 配置变量

编辑 `infra/terraform.tfvars`：

```hcl
region            = "cn-north-4"
project_name      = "serverless-rust-demo"
geminidb_password = "YourSecurePassword123!"
domain_name       = "your-huaweicloud-domain"
obs_bucket        = "your-function-bucket"
```

### 2.6 更新函数代码 URL

在 `infra/main.tf` 中更新每个函数的 `code_url`：

```hcl
resource "huaweicloud_fgs_function" "get_products" {
  # ...
  code_type = "obs"
  code_url  = "https://your-bucket.obs.cn-north-4.myhuaweicloud.com/function-code/get_products.zip"
}
```

### 2.7 部署资源

```bash
cd infra
terraform init
terraform validate
terraform plan
terraform apply
```

## 3. 验证部署

### 3.1 获取 API URL

```bash
terraform output api_gateway_url
```

### 3.2 测试 API

```bash
API_URL="https://<your-api-gateway-url>"

# 获取产品列表
curl $API_URL/

# 获取单个产品
curl $API_URL/product-1

# 创建产品
curl -X PUT $API_URL/product-1 \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "price": 99.99}'

# 删除产品
curl -X DELETE $API_URL/product-1
```

## 4. 清理资源

```bash
terraform destroy
```

## 5. 费用说明

部署以下资源会产生费用：

- APIG 专享实例 (BASIC)
- GeminiDB 集群 (2 节点)
- FunctionGraph 调用次数
- OBS 存储和流量

具体价格请参考 [华为云定价](https://www.huaweicloud.com/settlement.html)。

## 6. 故障排查

### 6.1 函数调用失败

1. 检查函数日志：LTS → 函数日志
2. 验证环境变量：CASSANDRA_HOSTS, CASSANDRA_KEYSPACE 等
3. 检查 IAM 委托是否正确配置

### 6.2 Cassandra 连接失败

1. 确认 GeminiDB 实例正常运行
2. 检查安全组规则
3. 验证 endpoint 地址正确

### 6.3 事件发布失败

1. 检查 SMN Topic 存在
2. 验证 IAM 委托包含 SMN 权限
