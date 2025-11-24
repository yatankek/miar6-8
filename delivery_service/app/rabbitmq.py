import aio_pika
import os
import json

AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@rabbitmq:5672/")


async def send_delivery_completed_message(delivery_data: dict):
    try:
        connection = await aio_pika.connect_robust(AMQP_URL)
        async with connection:
            channel = await connection.channel()

            required_fields = ["delivery_id", "order_id", "account_id", "completed_at"]
            for field in required_fields:
                if field not in delivery_data:
                    print(f"Warning: Missing required field {field} in delivery data")

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(delivery_data).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="delivery_completed"
            )
            print(f"Message sent to RabbitMQ: {delivery_data}")
    except Exception as e:
        print(f"Failed to send message: {e}")