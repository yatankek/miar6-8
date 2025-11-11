import pytest
from uuid import uuid4


class TestBusinessLogic:
    """Основные тесты бизнес-логики"""

    def test_delivery_status_transitions(self):
        """Тест валидных переходов статусов доставки"""

        def validate_status_transition(current_status, new_status):
            valid_transitions = {
                "CREATED": ["ASSIGNED"],
                "ASSIGNED": ["DELIVERED"]
            }
            return new_status in valid_transitions.get(current_status, [])

        # Валидные переходы
        assert validate_status_transition("CREATED", "ASSIGNED") == True
        assert validate_status_transition("ASSIGNED", "DELIVERED") == True

        # Невалидные переходы
        assert validate_status_transition("CREATED", "DELIVERED") == False
        assert validate_status_transition("DELIVERED", "ASSIGNED") == False

    def test_bonus_balance_calculation(self):
        """Тест расчета баланса бонусов"""

        def calculate_balance(transactions):
            balance = 0.0
            for tx in transactions:
                if tx["type"] == "ACCRUAL":
                    balance += tx["amount"]
                else:  # WRITE_OFF
                    balance -= tx["amount"]
            return balance

        transactions = [
            {"type": "ACCRUAL", "amount": 100.0},
            {"type": "WRITE_OFF", "amount": 30.0},
            {"type": "ACCRUAL", "amount": 50.0},
        ]

        assert calculate_balance(transactions) == 120.0