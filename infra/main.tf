# ============================================================================
# Serverless Rust Demo - 华为云 Terraform IaC
# ============================================================================
# 架构: APIG → FunctionGraph → GeminiDB + EventGrid
# ============================================================================

terraform {
  required_version = ">= 1.5"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.70"
    }
  }
}

provider "huaweicloud" {
  region = var.region
}

# ============================================================================
# 变量定义
# ============================================================================

variable "region" {
  description = "华为云区域"
  type        = string
  default     = "cn-north-4"
}

variable "project_name" {
  description = "项目名称"
  type        = string
  default     = "serverless-rust-demo"
}

variable "geminidb_password" {
  description = "GeminiDB 密码"
  type        = string
  sensitive   = true
}

# ============================================================================
# Layer 1: 基础设施与网络
# ============================================================================

resource "huaweicloud_vpc" "main" {
  name                  = "${var.project_name}-vpc"
  cidr                  = "10.0.0.0/16"
  enterprise_project_id = "0"
}

resource "huaweicloud_vpc_subnet" "main" {
  name       = "${var.project_name}-subnet"
  vpc_id     = huaweicloud_vpc.main.id
  cidr       = "10.0.1.0/24"
  gateway_ip = "10.0.1.1"
}

resource "huaweicloud_networking_secgroup" "main" {
  name        = "${var.project_name}-sg"
  description = "Security group for serverless-rust-demo"
}

resource "huaweicloud_networking_secgroup_rule" "allow_apig" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.main.id
}

# ============================================================================
# Layer 2: 数据存储 - GeminiDB Cassandra
# ============================================================================

resource "huaweicloud_geminidb_instance" "main" {
  name              = "${var.project_name}-db"
  mode              = "Cluster"
  password          = var.geminidb_password
  availability_zone = "${var.region}a,${var.region}b"
  vpc_id            = huaweicloud_vpc.main.id
  subnet_id         = huaweicloud_vpc_subnet.main.id
  security_group_id = huaweicloud_networking_secgroup.main.id

  datastore {
    type           = "cassandra"
    storage_engine = "rocksDB"
    version        = "3.11"
  }

  flavor {
    num       = 2
    size      = 100
    spec_code = "geminidb-nosql.xlarge.arm"
    storage   = "cloud"
  }

  tags = {
    project = var.project_name
  }
}

# ============================================================================
# Layer 4: API 接入层 - APIG
# ============================================================================

resource "huaweicloud_apig_instance" "main" {
  name              = "${var.project_name}-apig"
  edition           = "BASIC"
  vpc_id            = huaweicloud_vpc.main.id
  subnet_id         = huaweicloud_vpc_subnet.main.id
  security_group_id = huaweicloud_networking_secgroup.main.id
  maintain_begin    = "02:00:00"

  tags = {
    project = var.project_name
  }
}

resource "huaweicloud_apig_group" "main" {
  name        = "${var.project_name}-api-group"
  instance_id = huaweicloud_apig_instance.main.id
  description = "API group for serverless-rust-demo"
}

# ============================================================================
# Layer 3: 计算层 - FunctionGraph 函数
# ============================================================================

# 函数: GetProducts (获取产品列表)
resource "huaweicloud_fgs_function" "get_products" {
  name        = "${var.project_name}-get-products"
  description = "Get all products"
  handler     = "index.handler"
  memory_size = 128
  timeout     = 5
  runtime     = "Python3.9"
  code_type   = "inline"
  func_code   = base64encode("")
}

# 函数: GetProduct (获取单个产品)
resource "huaweicloud_fgs_function" "get_product" {
  name        = "${var.project_name}-get-product"
  description = "Get a single product by ID"
  handler     = "index.handler"
  memory_size = 128
  timeout     = 5
  runtime     = "Python3.9"
  code_type   = "inline"
  func_code   = base64encode("")
}

# 函数: PutProduct (创建/更新产品)
resource "huaweicloud_fgs_function" "put_product" {
  name        = "${var.project_name}-put-product"
  description = "Create or update a product"
  handler     = "index.handler"
  memory_size = 128
  timeout     = 5
  runtime     = "Python3.9"
  code_type   = "inline"
  func_code   = base64encode("")
}

# 函数: DeleteProduct (删除产品)
resource "huaweicloud_fgs_function" "delete_product" {
  name        = "${var.project_name}-delete-product"
  description = "Delete a product"
  handler     = "index.handler"
  memory_size = 128
  timeout     = 5
  runtime     = "Python3.9"
  code_type   = "inline"
  func_code   = base64encode("")
}

# 函数: 产品变更扫描器（定时/手动触发）
resource "huaweicloud_fgs_function" "change_scanner" {
  name        = "${var.project_name}-change-scanner"
  description = "Scan product changes and publish events"
  handler     = "index.handler"
  memory_size = 256
  timeout     = 10
  runtime     = "Python3.9"
  code_type   = "inline"
  func_code   = base64encode("")
}

# ============================================================================
# APIG API 定义
# ============================================================================

resource "huaweicloud_apig_api" "get_products" {
  name             = "get-products"
  group_id         = huaweicloud_apig_group.main.id
  instance_id      = huaweicloud_apig_instance.main.id
  type             = "FunctionGraph"
  request_method   = "GET"
  request_path     = "/"
  request_protocol = "HTTPS"

  func_graph {
    function_urn = huaweicloud_fgs_function.get_products.urn
  }

  tags = [var.project_name]
}

resource "huaweicloud_apig_api" "get_product" {
  name             = "get-product"
  group_id         = huaweicloud_apig_group.main.id
  instance_id      = huaweicloud_apig_instance.main.id
  type             = "FunctionGraph"
  request_method   = "GET"
  request_path     = "/{id}"
  request_protocol = "HTTPS"

  func_graph {
    function_urn = huaweicloud_fgs_function.get_product.urn
  }

  tags = [var.project_name]
}

resource "huaweicloud_apig_api" "put_product" {
  name             = "put-product"
  group_id         = huaweicloud_apig_group.main.id
  instance_id      = huaweicloud_apig_instance.main.id
  type             = "FunctionGraph"
  request_method   = "PUT"
  request_path     = "/{id}"
  request_protocol = "HTTPS"

  func_graph {
    function_urn = huaweicloud_fgs_function.put_product.urn
  }

  tags = [var.project_name]
}

resource "huaweicloud_apig_api" "delete_product" {
  name             = "delete-product"
  group_id         = huaweicloud_apig_group.main.id
  instance_id      = huaweicloud_apig_instance.main.id
  type             = "FunctionGraph"
  request_method   = "DELETE"
  request_path     = "/{id}"
  request_protocol = "HTTPS"

  func_graph {
    function_urn = huaweicloud_fgs_function.delete_product.urn
  }

  tags = [var.project_name]
}

# ============================================================================
# Layer 3.5: 事件层 - EventGrid
# ============================================================================

resource "huaweicloud_smn_topic" "event_bus" {
  name         = "${var.project_name}-event-bus"
  display_name = "Serverless Rust Demo Event Bus"
}

# ============================================================================
# 输出
# ============================================================================

output "api_gateway_url" {
  description = "APIG API Gateway URL"
  value       = "https://${huaweicloud_apig_instance.main.ingress_address}"
}

output "geminidb_endpoint" {
  description = "GeminiDB endpoint"
  value       = huaweicloud_geminidb_instance.main.lb_ip_address
  sensitive   = true
}

output "geminidb_port" {
  description = "GeminiDB port"
  value       = huaweicloud_geminidb_instance.main.port
}

output "function_get_products_urn" {
  description = "GetProducts Function URN"
  value       = huaweicloud_fgs_function.get_products.urn
}

output "function_get_product_urn" {
  description = "GetProduct Function URN"
  value       = huaweicloud_fgs_function.get_product.urn
}

output "function_put_product_urn" {
  description = "PutProduct Function URN"
  value       = huaweicloud_fgs_function.put_product.urn
}

output "function_delete_product_urn" {
  description = "DeleteProduct Function URN"
  value       = huaweicloud_fgs_function.delete_product.urn
}

output "function_change_scanner_urn" {
  description = "Change scanner Function URN"
  value       = huaweicloud_fgs_function.change_scanner.urn
}

output "event_topic_urn" {
  description = "EventGrid Topic URN"
  value       = huaweicloud_smn_topic.event_bus.topic_urn
}
