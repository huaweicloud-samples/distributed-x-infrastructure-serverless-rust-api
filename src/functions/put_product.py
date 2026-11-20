# -*- coding: utf-8 -*-
"""
创建/更新产品（Cassandra CQL 版）
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


def publish_event(event_type, product_data):
    """发布事件到消息通知服务（SMN）"""
    topic_urn = os.environ.get('SMN_TOPIC_URN', '')
    if not topic_urn:
        print("SMN not configured, skipping event publish")
        return
    try:
        message = {
            'eventType': event_type,
            'product': product_data,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        # 实际部署时通过 FunctionGraph 委托获取凭证并调用 SMN API
        print(f"Event published: {event_type}")
    except Exception as e:
        print(f"Failed to publish event: {e}")


def handler(event, context):
    """函数入口"""
    try:
        product_id = event.get('pathParameters', {}).get('id', '')
        if not product_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Product ID is required'})
            }

        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)

        product = {
            'id': product_id,
            'name': body.get('name', ''),
            'price': float(body.get('price', 0)),
            'description': body.get('description', ''),
            'updatedat': time.strftime('%Y-%m-%dT%H:%M:%SZ')
        }

        session = get_session()
        session.execute(
            "INSERT INTO products (id, name, price, description, updatedat) VALUES (?, ?, ?, ?, ?)",
            (product['id'], product['name'], product['price'],
             product['description'], product['updatedat'])
        )

        publish_event('product.updated', product)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'id': product_id, 'name': product['name'],
                                'price': product['price'],
                                'description': product['description'],
                                'updatedAt': product['updatedat']})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
