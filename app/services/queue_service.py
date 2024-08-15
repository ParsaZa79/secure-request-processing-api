import pika
import json
from app.models.request import Request
from config import Config
from threading import Lock
from contextlib import contextmanager

class QueueService:
    def __init__(self, max_connections=5):
        self.max_connections = max_connections
        self.connections = []
        self.lock = Lock()

    def get_connection_params(self):
        return pika.ConnectionParameters(
            host=Config.RABBITMQ_HOST,
            port=Config.RABBITMQ_PORT,
            credentials=pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASS),
            heartbeat=300
        )

    @contextmanager
    def get_connection(self):
        with self.lock:
            if self.connections:
                connection = self.connections.pop()
            else:
                connection = pika.BlockingConnection(self.get_connection_params())

        try:
            yield connection
        finally:
            with self.lock:
                if len(self.connections) < self.max_connections:
                    self.connections.append(connection)
                else:
                    connection.close()

    def enqueue(self, request):
        with self.get_connection() as connection:
            channel = connection.channel()
            channel.queue_declare(queue='request_queue', durable=True)
            channel.basic_publish(
                exchange='',
                routing_key='request_queue',
                body=json.dumps({'id': request.id, 'query': request.user_query}),
                properties=pika.BasicProperties(delivery_mode=2)
            )

    def dequeue(self):
        with self.get_connection() as connection:
            channel = connection.channel()
            channel.queue_declare(queue='request_queue', durable=True)
            method_frame, header_frame, body = channel.basic_get(queue='request_queue')
            if method_frame:
                channel.basic_ack(method_frame.delivery_tag)
                data = json.loads(body)
                return Request(id=data['id'], query=data['query'])
        return None

queue_service = QueueService()