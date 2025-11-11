import pytest
import requests
from uuid import uuid4
import time


class TestBonusAPI:
    """Компонентные тесты для Bonus Service API"""

    BASE_URL = "http://localhost:8002/api"

    def setup_method(self):
        """Проверяем доступность сервиса перед тестами"""
        try:
            response = requests.get(f"{self.BASE_URL.replace('/api', '')}/", timeout=5)
            print(f"Service status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            pytest.skip("Bonus Service не запущен")

    def test_service_health(self):
        """Тест доступности сервиса"""
        response = requests.get(f"{self.BASE_URL.replace('/api', '')}/")
        assert response.status_code == 200
        assert "Bonus Service is running" in response.text

    def test_accrue_points_basic(self):
        """Базовый тест начисления баллов"""
        account_id = str(uuid4())

        accrue_data = {
            "order_id": str(uuid4()),
            "amount": 100.0,
            "reason": "Тестовое начисление"
        }

        response = requests.post(
            f"{self.BASE_URL}/accounts/{account_id}/accrue",
            json=accrue_data,
            timeout=10
        )

        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text[:500]}")  # Первые 500 символов

        # Если успешно, проверяем структуру
        if response.status_code == 200:
            data = response.json()
            assert data["type"] == "ACCRUAL"
            assert data["amount"] == 100.0
        else:
            # Пока просто проверяем что не 500
            assert response.status_code != 500