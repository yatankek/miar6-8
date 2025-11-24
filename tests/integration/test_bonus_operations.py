import pytest
import requests
from uuid import uuid4


class TestBonusOperations:
    """Интеграционные тесты операций с бонусами"""

    BONUS_URL = "http://localhost:8002/api"

    def setup_method(self):
        """Проверяем доступность Bonus сервиса"""
        try:
            response = requests.get(self.BONUS_URL.replace('/api', ''), timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.fail("Bonus Service не запущен")

    def test_accrue_and_write_off_operations(self):
        """Тест: начисление и списание бонусов"""

        account_id = str(uuid4())

        # 1. Начисляем бонусы
        accrue_data = {
            "order_id": str(uuid4()),
            "amount": 200.0,
            "reason": "Интеграционный тест начисления"
        }

        accrue_response = requests.post(
            f"{self.BONUS_URL}/accounts/{account_id}/accrue",
            json=accrue_data,
            timeout=10
        )
        print(f"Accrue response: {accrue_response.status_code} - {accrue_response.text}")
        assert accrue_response.status_code == 200

        response_data = accrue_response.json()
        assert response_data["type"] == "ACCRUAL"
        assert response_data["amount"] == 200.0

        # 2. Проверяем баланс после начисления
        balance_response = requests.get(
            f"{self.BONUS_URL}/accounts/{account_id}/balance",
            timeout=10
        )
        print(f"Balance response: {balance_response.status_code} - {balance_response.text}")

        # НЕ ПРОПУСКАЕМ, а проверяем что должно работать
        assert balance_response.status_code == 200, f"Balance endpoint failed: {balance_response.text}"

        balance_data = balance_response.json()
        assert "current_balance" in balance_data
        print(f"Balance after accrual: {balance_data['current_balance']}")

        # Баланс должен быть равен сумме начисления (200.0)
        assert balance_data['current_balance'] == 200.0

        # 3. Списание бонусов
        write_off_data = {
            "order_id": str(uuid4()),
            "amount": 50.0,
            "reason": "Интеграционный тест списания"
        }

        write_off_response = requests.post(
            f"{self.BONUS_URL}/accounts/{account_id}/write-off",
            json=write_off_data,
            timeout=10
        )
        print(f"Write-off response: {write_off_response.status_code} - {write_off_response.text}")
        assert write_off_response.status_code == 200

        # 4. Проверяем итоговый баланс
        final_balance_response = requests.get(
            f"{self.BONUS_URL}/accounts/{account_id}/balance",
            timeout=10
        )
        assert final_balance_response.status_code == 200
        final_balance = final_balance_response.json()["current_balance"]

        print(f"Final balance: {final_balance}")
        assert final_balance == 150.0  # 200 - 50 = 150

    def test_insufficient_funds_validation(self):
        """Тест: валидация недостаточных средств при списании"""

        account_id = str(uuid4())

        write_off_data = {
            "order_id": str(uuid4()),
            "amount": 1000.0,
            "reason": "Попытка списания при нулевом балансе"
        }

        write_off_response = requests.post(
            f"{self.BONUS_URL}/accounts/{account_id}/write-off",
            json=write_off_data,
            timeout=10
        )

        print(f"Write-off response: {write_off_response.status_code} - {write_off_response.text}")
        assert write_off_response.status_code == 400
        error_detail = write_off_response.json()["detail"]
        assert "insufficient" in error_detail.lower()