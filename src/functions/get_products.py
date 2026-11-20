# -*- coding: utf-8 -*-
"""
查询全部产品（Cassandra CQL 版）
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
        session = get_session()
        rows = session.execute("SELECT id, name, price, description, updatedat FROM products")

        items = [
            {
                'id': r.id,
                'name': r.name,
                'price': r.price,
                'description': r.description,
                'updatedAt': r.updatedat
            }
            for r in rows
        ]

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'items': items, 'count': len(items)})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
