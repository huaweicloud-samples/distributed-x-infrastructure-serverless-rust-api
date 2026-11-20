# -*- coding: utf-8 -*-
"""
删除产品（Cassandra CQL 版）
"""

import json
import os

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


def publish_event(event_type, product_id):
    """发布事件到消息通知服务（SMN）"""
    print(f"Event would be published: {event_type} for product {product_id}")


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

        session = get_session()

        # 检查产品是否存在
        rows = session.execute(
            "SELECT id FROM products WHERE id = ?", (product_id,))
        if rows.one() is None:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Product not found'})
            }

        # 删除产品
        session.execute("DELETE FROM products WHERE id = ?", (product_id,))

        # 发布事件
        publish_event('product.deleted', product_id)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Product deleted', 'id': product_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
