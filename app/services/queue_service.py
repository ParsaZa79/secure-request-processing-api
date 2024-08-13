import pika
import json
from app.models.request import Request

class QueueService:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='request_queue', durable=True)

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