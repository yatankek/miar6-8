from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import asyncio

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
        if amount > 10000:
            raise ValueError("Amount too large for single accrual")
        return amount

    def calculate_bonus_multiplier(amount: float) -> float:
        """Расчет бонусного множителя"""
        if amount > 1000:
            return 1.1
        elif amount > 500:
            return 1.05
        else:
            return 1.0

    def apply_bonus(base_amount: float) -> float:
        """Применение бонуса к сумме"""
        multiplier = calculate_bonus_multiplier(base_amount)
        return base_amount * multiplier

    def create_accrual_transaction(final_amount: float):
        """Создание транзакции начисления"""
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
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/accounts/{account_id}/balance", response_model=schemas.BalanceResponse)
def get_balance(account_id: UUID, db: Session = Depends(get_db)):
    """Получить текущий баланс счета"""
    try:
        account = db.query(models.Account).filter(models.Account.id == account_id).first()

        if not account:
            account = models.Account(
                id=account_id,
                current_balance=0.0,
                as_of_date=datetime.utcnow()
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            print(f"Created new account with zero balance: {account_id}")

        return {
            "id": account.id,
            "current_balance": account.current_balance,
            "as_of_date": account.as_of_date
        }

    except Exception as e:
        print(f"Error in get_balance for account {account_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/accounts/{account_id}/write-off", response_model=schemas.TransactionResponse)
def write_off_points(
        account_id: UUID,
        write_off_request: schemas.WriteOffPointsRequest,
        db: Session = Depends(get_db)
):
    """Списать баллы со счета"""

    def validate_write_off_amount(amount: float, current_balance: float):
        """Валидация суммы для списания"""
        if amount <= 0:
            raise ValueError("Amount for write-off must be positive")
        if amount > current_balance:
            raise ValueError(f"Insufficient funds. Available: {current_balance}, requested: {amount}")
        return amount

    def create_write_off_transaction():
        """Создание транзакции списания"""
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
            # Создаем счет с нулевым балансом вместо ошибки
            account = models.Account(
                id=account_id,
                current_balance=0.0,
                as_of_date=datetime.utcnow()
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            print(f"Created new account with zero balance: {account_id}")

        # Теперь проверяем достаточно ли средств
        validated_amount = validate_write_off_amount(write_off_request.amount, account.current_balance)

        account.current_balance -= validated_amount
        account.as_of_date = datetime.utcnow()
        db.commit()

        transaction = create_write_off_transaction()

        return transaction

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")