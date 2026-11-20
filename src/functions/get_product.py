# -*- coding: utf-8 -*-
"""
获取单个产品（Cassandra CQL 版）
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
        rows = session.execute(
            "SELECT id, name, price, description, updatedat FROM products WHERE id = ?",
            (product_id,)
        )
        row = rows.one()

        if row is None:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Product not found'})
            }

        item = {
            'id': row.id,
            'name': row.name,
            'price': row.price,
            'description': row.description,
            'updatedAt': row.updatedat
        }
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(item)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
