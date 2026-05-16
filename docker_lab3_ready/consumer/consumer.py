import json
import os
import time
import pika

RABBIT_HOST = os.getenv('RABBIT_HOST', 'rabbitmq')
RABBIT_PORT = int(os.getenv('RABBIT_PORT', '5672'))
RABBIT_USER = os.getenv('RABBIT_USER', 'guest')
RABBIT_PASS = os.getenv('RABBIT_PASS', 'guest')
EXCHANGE = os.getenv('USER_EXCHANGE', 'user.exchange')
QUEUE = os.getenv('USER_QUEUE', 'user.events')
BINDING_KEY = os.getenv('USER_BINDING_KEY', 'user.#')


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
            return get_connection()
        except Exception:
            time.sleep(1)
    raise RuntimeError('RabbitMQ is not available')


def callback(ch, method, properties, body):
    try:
        event = json.loads(body.decode('utf-8'))
    except Exception:
        event = {'raw': body.decode('utf-8', errors='replace')}
    print(f'NOTIFICATION SERVICE: received event with routing_key={method.routing_key}: {event}', flush=True)
    print(f'NOTIFICATION SERVICE: send notification to {event.get("email")}', flush=True)
    ch.basic_ack(delivery_tag=method.delivery_tag)


connection = wait_for_rabbitmq()
channel = connection.channel()
channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic', durable=True)
channel.queue_declare(queue=QUEUE, durable=True)
channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=BINDING_KEY)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=QUEUE, on_message_callback=callback)
print('NOTIFICATION SERVICE: waiting for events...', flush=True)
channel.start_consuming()
