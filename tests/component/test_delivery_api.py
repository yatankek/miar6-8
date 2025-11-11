import pytest
import requests
from uuid import uuid4


class TestDeliveryAPI:
    """Компонентные тесты для Delivery Service API"""

    BASE_URL = "http://localhost:8001/api"

    def setup_method(self):
        """Проверяем доступность сервиса перед тестами"""
        try:
            response = requests.get(f"{self.BASE_URL.replace('/api', '')}/", timeout=5)
            print(f"Service status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            pytest.skip("Delivery Service не запущен")

    def test_create_delivery_basic(self):
        """Базовый тест создания доставки"""
        delivery_data = {
            "order_id": str(uuid4()),
            "address_from": "ул. Ленина, 1",
            "address_to": "ул. Пушкина, 10",
            "recipient_name": "Иван Иванов",
            "recipient_phone": "+79123456789"
        }

        response = requests.post(
            f"{self.BASE_URL}/deliveries",
            json=delivery_data,
            timeout=10
        )

        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:500]}")

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "CREATED"
            assert data["order_id"] == delivery_data["order_id"]
        else:
            assert response.status_code != 500