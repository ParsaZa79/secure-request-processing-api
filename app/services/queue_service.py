import time
import pika
import json
from app.models.request import Request
from config import Config

class QueueService:
    def __init__(self, max_retries=5, retry_delay=5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        for attempt in range(self.max_retries):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=Config.RABBITMQ_HOST,
                        port=Config.RABBITMQ_PORT,
                        credentials=pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASS)
                    )
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue='request_queue', durable=True)
                print("Successfully connected to RabbitMQ")
                return
            except pika.exceptions.AMQPConnectionError as e:
                print(f"Connection attempt {attempt + 1} failed. Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        raise Exception("Failed to connect to RabbitMQ after multiple attempts")

    def enqueue(self, request):
        self.channel.basic_publish(
            exchange='',
            routing_key='request_queue',
            body=json.dumps({'id': request.id, 'query': request.user_query}),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))

    def dequeue(self):
        method_frame, header_frame, body = self.channel.basic_get(queue='request_queue')
        if method_frame:
            self.channel.basic_ack(method_frame.delivery_tag)
            data = json.loads(body)
            return Request(id=data['id'], query=data['query'])
        return None

queue_service = QueueService()