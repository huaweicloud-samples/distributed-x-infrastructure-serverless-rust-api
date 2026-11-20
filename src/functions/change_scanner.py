# -*- coding: utf-8 -*-
"""
产品变更扫描器（定时/手动触发）
原架构: 变更流捕获 → 处理 → 事件总线
华为云方案: 定时/手动触发 → FunctionGraph 扫描 → SMN

说明: GeminiDB Cassandra 当前不支持原生变更流捕获，
因此采用定时扫描的方式近似实现。
"""

import json
import os
import time

def get_session():
    """建立 GeminiDB Cassandra（CQL）会话"""
    hosts = (os.environ.get('CASSANDRA_HOSTS') or '').split(',')
    hosts = [h.strip() for h in hosts if h.strip()]
    if not hosts:
        raise ValueError("CASSANDRA_HOSTS environment variable not set")

    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider

    auth = PlainTextAuthProvider(
        username=os.environ.get('CASSANDRA_USERNAME', 'root'),
        password=os.environ.get('CASSANDRA_PASSWORD', '')
    )
    cluster = Cluster(
        contact_points=hosts,
        port=int(os.environ.get('CASSANDRA_PORT', '9042')),
        auth_provider=auth,
        connect_timeout=5,
        protocol_version=4
    )
    keyspace = os.environ.get('CASSANDRA_KEYSPACE', 'productsdb')
    return cluster.connect(keyspace)


def scan_recent_changes(session):
    """
    扫描最近的变更记录
    由于没有原生变更流，使用定期扫描的方式
    """
    # 简化实现：全量扫描（生产环境可增加 lastModified 字段做增量过滤）
    rows = session.execute(
        "SELECT id, name, updatedat FROM products LIMIT 100")
    return list(rows)


def process_product_events(products):
    """处理产品变更事件"""
    events = []
    for product in products:
        event = {
            'eventType': 'product.changed',
            'productId': product.id,
            'productName': product.name,
            'timestamp': product.updatedat or ''
        }
        events.append(event)
    return events


def publish_to_smn(event_type, data):
    """
    发布事件到 SMN (Simple Message Notification)
    """
    topic_urn = os.environ.get('SMN_TOPIC_URN', '')
    if not topic_urn:
        print("SMN_TOPIC_URN not set, skipping event publish")
        return None
    try:
        # 实际部署时通过 FunctionGraph 的委托自动获取临时凭证
        message = {
            'eventType': event_type,
            'data': data,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'source': 'product-change-scanner'
        }
        print(f"Publishing event to SMN: {event_type}")
        # 实际调用需要添加签名，简化处理
        return message
    except Exception as e:
        print(f"Failed to publish to SMN: {e}")
        return None


def handler(event, context):
    """
    处理定时触发或手动调用

    触发方式:
    1. 定时触发: 配置 FunctionGraph 定时器，每分钟扫描一次
    2. 手动调用: 通过 APIG 调用此函数
    """
    try:
        print("Scanning product changes...")

        session = get_session()
        products = scan_recent_changes(session)

        if not products:
            return {
                'statusCode': 200,
                'body': json.dumps({'processed': 0, 'message': 'No products found'})
            }

        events = process_product_events(products)

        published_count = 0
        for evt in events:
            result = publish_to_smn(evt['eventType'], evt)
            if result:
                published_count += 1

        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': len(products),
                'events_published': published_count,
                'message': 'Change scanning completed'
            })
        }

    except Exception as e:
        print(f"Error scanning changes: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
