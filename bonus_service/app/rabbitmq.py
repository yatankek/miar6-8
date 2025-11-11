import aio_pika
import os
import json
import asyncio
from . import models, database

AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@rabbitmq:5672/")


async def process_delivery_completed_message(msg: aio_pika.IncomingMessage):
    async with msg.process():
        try:
            data = json.loads(msg.body.decode())

            db = database.SessionLocal()
            try:
                bonus_amount = 50.0

                transaction = models.Transaction(
                    account_id=data.get('account_id', '00000000-0000-0000-0000-000000000000'),
                    type="ACCRUAL",
                    amount=bonus_amount,
                    order_id=data['order_id'],
                    delivery_id=data['delivery_id'],
                    reason="Начисление за завершенную доставку",
                    created_date=asyncio.get_event_loop().time()
                )

                db.add(transaction)
                db.commit()

                print(f"Bonus accrued for delivery {data['delivery_id']}")

            except Exception as e:
                print(f"Error processing message: {e}")
                db.rollback()
            finally:
                db.close()

        except Exception as e:
            print(f"Error processing message: {e}")


async def consume_delivery_completed_messages():
    try:
        connection = await aio_pika.connect_robust(AMQP_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("delivery_completed", durable=True)

            await queue.consume(process_delivery_completed_message)

            print("Started consuming delivery completed messages...")
            await asyncio.Future()
    except Exception as e:
        print(f"RabbitMQ connection error: {e}")