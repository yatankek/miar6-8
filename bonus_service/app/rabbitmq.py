import aio_pika
import os
import json
import asyncio
from datetime import datetime
from . import models, database

AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@rabbitmq:5672/")


async def process_delivery_completed_message(msg: aio_pika.IncomingMessage):
    async with msg.process():
        try:
            data = json.loads(msg.body.decode())
            print(f"Received RabbitMQ message: {data}")

            account_id = data.get('account_id', data.get('order_id'))

            if not account_id:
                print(f"Error: No account_id found in message")
                return

            db = database.SessionLocal()
            try:
                bonus_amount = 50.0

                # Находим или создаем аккаунт
                account = db.query(models.Account).filter(models.Account.id == account_id).first()
                if not account:
                    account = models.Account(
                        id=account_id,
                        current_balance=bonus_amount,
                        as_of_date=datetime.utcnow()
                    )
                    db.add(account)
                else:
                    account.current_balance += bonus_amount
                    account.as_of_date = datetime.utcnow()

                # Создаем транзакцию
                transaction = models.Transaction(
                    account_id=account_id,
                    type="ACCRUAL",
                    amount=bonus_amount,
                    order_id=data['order_id'],
                    delivery_id=data['delivery_id'],
                    reason="Начисление за завершенную доставку",
                    created_date=datetime.utcnow()
                )

                db.add(transaction)
                db.commit()

                print(f"✅ Bonus {bonus_amount} accrued for delivery {data['delivery_id']}, account {account_id}")

            except Exception as e:
                print(f"❌ Error processing message: {e}")
                db.rollback()
            finally:
                db.close()

        except Exception as e:
            print(f"❌ Error processing message: {e}")


async def consume_delivery_completed_messages():
    while True:  # Бесконечный цикл для переподключения
        try:
            print("🔄 Connecting to RabbitMQ...")
            connection = await aio_pika.connect_robust(AMQP_URL)
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue("delivery_completed", durable=True)

                await queue.consume(process_delivery_completed_message)

                print("✅ Started consuming delivery completed messages...")
                await asyncio.Future()  # Бесконечное ожидание

        except Exception as e:
            print(f"❌ RabbitMQ connection error: {e}")
            print("🔄 Reconnecting in 10 seconds...")
            await asyncio.sleep(10)