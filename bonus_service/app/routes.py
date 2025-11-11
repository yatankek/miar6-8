from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from . import models, schemas, database

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/accounts/{account_id}/accrue", response_model=schemas.TransactionResponse)
def accrue_points(
        account_id: UUID,
        accrue_request: schemas.AccruePointsRequest,
        db: Session = Depends(get_db)
):
    """Начислить баллы на счет"""

    def validate_accrual_amount(amount: float):
        """Валидация суммы для начисления"""
        if amount <= 0:
            raise ValueError("Amount for accrual must be positive")
        if amount > 10000:  # Пример бизнес-правила
            raise ValueError("Amount too large for single accrual")
        return amount

    def calculate_bonus_multiplier(amount: float) -> float:
        """Расчет бонусного множителя (вложенная функция)"""
        if amount > 1000:
            return 1.1
        elif amount > 500:
            return 1.05
        else:
            return 1.0

    def apply_bonus(base_amount: float) -> float:
        """Применение бонуса к сумме (вложенная функция)"""
        multiplier = calculate_bonus_multiplier(base_amount)
        return base_amount * multiplier

    def create_accrual_transaction(final_amount: float):
        """Создание транзакции начисления (вложенная функция)"""
        transaction = models.Transaction(
            account_id=account_id,
            type="ACCRUAL",
            amount=final_amount,
            order_id=accrue_request.order_id,
            delivery_id=accrue_request.delivery_id,
            reason=f"{accrue_request.reason} (с бонусом)" if final_amount > accrue_request.amount else accrue_request.reason,
            created_date=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    try:
        validated_amount = validate_accrual_amount(accrue_request.amount)
        final_amount = apply_bonus(validated_amount)

        account = db.query(models.Account).filter(models.Account.id == account_id).first()
        if not account:
            account = models.Account(
                id=account_id,
                current_balance=final_amount,
                as_of_date=datetime.utcnow()
            )
            db.add(account)
        else:
            account.current_balance += final_amount
            account.as_of_date = datetime.utcnow()

        db.commit()

        transaction = create_accrual_transaction(final_amount)

        return transaction

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/accounts/{account_id}/write-off", response_model=schemas.TransactionResponse)
def write_off_points(
        account_id: UUID,
        write_off_request: schemas.WriteOffPointsRequest,
        db: Session = Depends(get_db)
):
    """Списать баллы со счета"""

    # ВЛОЖЕННЫЕ ФУНКЦИИ внутри write_off_points
    def validate_write_off_amount(amount: float, current_balance: float):
        """Валидация суммы для списания"""
        if amount <= 0:
            raise ValueError("Amount for write-off must be positive")
        if amount > current_balance:
            raise ValueError(f"Insufficient funds. Available: {current_balance}, requested: {amount}")
        if amount < 10:  # Минимальная сумма списания
            raise ValueError("Minimum write-off amount is 10")
        return amount

    def check_transaction_limits(amount: float):
        """Проверка лимитов транзакции (вложенная функция)"""
        daily_limit = 1000
        if amount > daily_limit:
            raise ValueError(f"Transaction amount exceeds daily limit of {daily_limit}")
        return amount

    def create_write_off_transaction():
        """Создание транзакции списания (вложенная функция)"""
        transaction = models.Transaction(
            account_id=account_id,
            type="WRITE_OFF",
            amount=write_off_request.amount,
            order_id=write_off_request.order_id,
            reason=write_off_request.reason,
            created_date=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    try:
        account = db.query(models.Account).filter(models.Account.id == account_id).first()
        if not account:
            raise ValueError("Account not found")

        check_transaction_limits(write_off_request.amount)
        validated_amount = validate_write_off_amount(write_off_request.amount, account.current_balance)

        account.current_balance -= validated_amount
        account.as_of_date = datetime.utcnow()
        db.commit()

        transaction = create_write_off_transaction()

        return transaction

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{account_id}/balance", response_model=schemas.BalanceResponse)
def get_balance(account_id: UUID, db: Session = Depends(get_db)):
    """Получить текущий баланс счета"""

    def format_balance_display(balance: float) -> str:
        """Форматирование баланса для отображения (вложенная функция)"""
        if balance == 0:
            return "Нулевой баланс"
        elif balance < 0:
            return f"Отрицательный баланс: {balance}"
        else:
            return f"Доступно баллов: {balance}"

    def calculate_bonus_projection(balance: float) -> dict:
        """Расчет проекции бонусов (вложенная функция)"""
        projections = {
            "current": balance,
            "next_level": max(0, 1000 - balance),  # До следующего уровня
            "bonus_tier": "basic" if balance < 1000 else "premium" if balance < 5000 else "vip"
        }
        return projections

    try:
        account = db.query(models.Account).filter(models.Account.id == account_id).first()
        if not account:
            # Создаем счет с нулевым балансом
            account = models.Account(
                id=account_id,
                current_balance=0.0,
                as_of_date=datetime.utcnow()
            )
            db.add(account)
            db.commit()
            db.refresh(account)

        # Вызов вложенных функций (для демонстрации)
        balance_display = format_balance_display(account.current_balance)
        bonus_projection = calculate_bonus_projection(account.current_balance)

        print(f"Balance display: {balance_display}")
        print(f"Bonus projection: {bonus_projection}")

        return account

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))