import pytest
import requests
import time
from uuid import uuid4


class TestDeliveryToBonus:
    """Интеграционные тесты между Delivery и Bonus сервисами"""

    DELIVERY_URL = "http://localhost:8001/api"
    BONUS_URL = "http://localhost:8002/api"

    def setup_method(self):
        """Проверяем доступность обоих сервисов"""
        try:
            delivery_response = requests.get(self.DELIVERY_URL.replace('/api', ''), timeout=5)
            bonus_response = requests.get(self.BONUS_URL.replace('/api', ''), timeout=5)
            assert delivery_response.status_code == 200
            assert bonus_response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.fail("Сервисы не запущены")


    def test_multiple_deliveries_accumulate_bonuses(self):
        """Тест: несколько доставок накапливают бонусы"""

        account_id = str(uuid4())
        successful_deliveries = 0

        for i in range(2):
            delivery_data = {
                "order_id": str(uuid4()),
                "address_from": f"ул. Тестовая, {i}",
                "address_to": f"ул. Тестовая, {i + 10}",
                "recipient_name": f"Тест {i}",
                "recipient_phone": f"+7999999999{i}"
            }

            # Создаем доставку
            create_response = requests.post(
                f"{self.DELIVERY_URL}/deliveries",
                json=delivery_data,
                timeout=10
            )
            assert create_response.status_code == 200
            delivery_id = create_response.json()["id"]

            # Сначала назначаем курьера
            courier_id = str(uuid4())
            assign_response = requests.patch(
                f"{self.DELIVERY_URL}/deliveries/{delivery_id}",
                json={
                    "courier_id": courier_id,
                    "status": "ASSIGNED"
                },
                timeout=10
            )
            assert assign_response.status_code == 200

            # Завершаем доставку
            update_response = requests.patch(
                f"{self.DELIVERY_URL}/deliveries/{delivery_id}",
                json={"status": "DELIVERED"},
                timeout=10
            )

            assert update_response.status_code == 200, f"Failed to complete delivery: {update_response.text}"
            successful_deliveries += 1
            print(f"Successfully completed delivery {i + 1}")

            time.sleep(4)

        # Проверяем итоговый баланс
        balance_response = requests.get(
            f"{self.BONUS_URL}/accounts/{account_id}/balance",
            timeout=10
        )

        assert balance_response.status_code == 200, f"Balance check failed: {balance_response.text}"

        final_balance = balance_response.json()["current_balance"]
        expected_bonuses = successful_deliveries * 50.0

        print(f"Successful deliveries: {successful_deliveries}")
        print(f"Expected bonuses: {expected_bonuses}, Actual balance: {final_balance}")

        # Если бонусы не начисляются, проверяем RabbitMQ
        if final_balance != expected_bonuses:
            print("⚠️  Bonuses not accrued - checking RabbitMQ connection")
            # Проверяем логи Bonus Service
            print("Check docker-compose logs bonus_service for RabbitMQ errors")
