import json
import os
import time
import uuid
from flask import Flask, jsonify, request
import pika

app = Flask(__name__)

RABBIT_HOST = os.getenv('RABBIT_HOST', 'rabbitmq')
RABBIT_PORT = int(os.getenv('RABBIT_PORT', '5672'))
RABBIT_USER = os.getenv('RABBIT_USER', 'guest')
RABBIT_PASS = os.getenv('RABBIT_PASS', 'guest')
EXCHANGE = os.getenv('USER_EXCHANGE', 'user.exchange')
ROUTING_KEY = os.getenv('USER_ROUTING_KEY', 'user.created')


def get_connection():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30,
    )
    return pika.BlockingConnection(params)


def wait_for_rabbitmq():
    for _ in range(60):
        try:
            connection = get_connection()
            connection.close()
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError('RabbitMQ is not available')


def publish_event(event: dict):
    connection = get_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)
    channel.queue_declare(queue='user.events', durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue='user.events', routing_key='user.#')
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=ROUTING_KEY,
        body=json.dumps(event, ensure_ascii=False).encode('utf-8'),
        properties=pika.BasicProperties(content_type='application/json', delivery_mode=2),
    )
    connection.close()


@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'lab': 'lab3 RabbitMQ event-driven architecture',
        'try': 'POST /users'
    })


@app.route('/users', methods=['POST'])
def create_user():
    payload = request.get_json(silent=True) or {}
    name = payload.get('name', 'Test User')
    email = payload.get('email', 'test@example.com')
    user_id = str(uuid.uuid4())
    event = {
        'eventType': 'USER_CREATED',
        'id': user_id,
        'name': name,
        'email': email,
    }
    publish_event(event)
    return jsonify({'created': True, 'user': event})


if __name__ == '__main__':
    wait_for_rabbitmq()
    app.run(host='0.0.0.0', port=int(os.getenv('SERVER_PORT', '8080')))
