import pika
import json
import time
from app.models.request import Request
from config import Config
from threading import Lock
from contextlib import contextmanager


# class QueueService:

#     def get_connection_params(self):
#         pass

#     def create_connection(self):
#         pass

#     @contextmanager
#     def get_connection(self):
#         pass

#     def enqueue(self, request):
#         pass

#     def dequeue(self):
#         return None

class QueueService:
    def __init__(self, max_connections=5, max_retries=3, retry_delay=5):
        self.max_connections = max_connections
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connections = []
        self.lock = Lock()

    def get_connection_params(self):
        return pika.ConnectionParameters(
            host=Config.RABBITMQ_HOST,
            port=Config.RABBITMQ_PORT,
            credentials=pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASS),
            heartbeat=60,  # Reduced heartbeat interval
            blocked_connection_timeout=300
        )

    def create_connection(self):
        for attempt in range(self.max_retries):
            try:
                return pika.BlockingConnection(self.get_connection_params())
            except pika.exceptions.AMQPConnectionError as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay)

    @contextmanager
    def get_connection(self):
        with self.lock:
            if self.connections:
                connection = self.connections.pop()
            else:
                connection = self.create_connection()

        try:
            if not connection.is_open:
                connection = self.create_connection()
            yield connection
        except pika.exceptions.AMQPConnectionError:
            connection = self.create_connection()
            yield connection
        finally:
            with self.lock:
                if len(self.connections) < self.max_connections:
                    if connection.is_open:
                        self.connections.append(connection)
                    else:
                        connection = self.create_connection()
                        self.connections.append(connection)
                else:
                    connection.close()

    def enqueue(self, request):
        for _ in range(self.max_retries):
            try:
                with self.get_connection() as connection:
                    channel = connection.channel()
                    channel.queue_declare(queue='request_queue', durable=True)
                    channel.basic_publish(
                        exchange='',
                        routing_key='request_queue',
                        body=json.dumps({'id': request.id, 'query': request.user_query}),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                return
            except pika.exceptions.AMQPConnectionError:
                time.sleep(self.retry_delay)
        raise Exception("Failed to enqueue request after multiple attempts")

    def dequeue(self):
        for _ in range(self.max_retries):
            try:
                with self.get_connection() as connection:
                    channel = connection.channel()
                    channel.queue_declare(queue='request_queue', durable=True)
                    method_frame, header_frame, body = channel.basic_get(queue='request_queue')
                    if method_frame:
                        channel.basic_ack(method_frame.delivery_tag)
                        data = json.loads(body)
                        return Request(id=data['id'], query=data['query'])
                return None
            except pika.exceptions.AMQPConnectionError:
                time.sleep(self.retry_delay)
        raise Exception("Failed to dequeue request after multiple attempts")

queue_service = QueueService()