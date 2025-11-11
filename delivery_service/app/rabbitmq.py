import aio_pika
import os
import json

AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@rabbitmq:5672/")

async def send_delivery_completed_message(delivery_data: dict):
    try:
        connection = await aio_pika.connect_robust(AMQP_URL)
        async with connection:
            channel = await connection.channel()
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(delivery_data).encode()
                ),
                routing_key="delivery_completed"
            )
    except Exception as e:
        print(f"Failed to send message: {e}")