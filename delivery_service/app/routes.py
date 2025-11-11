from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import asyncio

from . import models, schemas, database, rabbitmq

router = APIRouter()


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/deliveries", response_model=schemas.DeliveryResponse)
async def create_delivery(delivery: schemas.DeliveryCreate, db: Session = Depends(get_db)):
    new_delivery = models.Delivery(
        **delivery.dict(),
        created_date=datetime.utcnow()
    )
    db.add(new_delivery)
    db.commit()
    db.refresh(new_delivery)
    return new_delivery


@router.patch("/deliveries/{delivery_id}", response_model=schemas.DeliveryResponse)
async def update_delivery(delivery_id: UUID, delivery_update: schemas.DeliveryUpdate, db: Session = Depends(get_db)):
    delivery = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    # Вложенные функции для бизнес-логики
    def validate_status_transition(current_status, new_status):
        valid_transitions = {
            "CREATED": ["ASSIGNED"],
            "ASSIGNED": ["DELIVERED"]
        }
        if current_status in valid_transitions and new_status in valid_transitions[current_status]:
            return True
        return False

    def update_delivery_dates(delivery_obj, status):
        if status == "ASSIGNED" and not delivery_obj.assigned_date:
            delivery_obj.assigned_date = datetime.utcnow()
        elif status == "DELIVERED" and not delivery_obj.delivered_date:
            delivery_obj.delivered_date = datetime.utcnow()

    if delivery_update.courier_id is not None:
        delivery.courier_id = delivery_update.courier_id

    if delivery_update.status:
        if not validate_status_transition(delivery.status.value, delivery_update.status):
            raise HTTPException(status_code=400, detail="Invalid status transition")

        update_delivery_dates(delivery, delivery_update.status)
        delivery.status = delivery_update.status

        if delivery_update.status == "DELIVERED":
            asyncio.create_task(rabbitmq.send_delivery_completed_message({
                "delivery_id": str(delivery.id),
                "order_id": str(delivery.order_id),
                "completed_at": delivery.delivered_date.isoformat()
            }))

    db.commit()
    db.refresh(delivery)
    return delivery


@router.get("/deliveries/{delivery_id}", response_model=schemas.DeliveryResponse)
def get_delivery(delivery_id: UUID, db: Session = Depends(get_db)):
    delivery = db.query(models.Delivery).filter(models.Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.get("/deliveries", response_model=list[schemas.DeliveryResponse])
def get_deliveries(db: Session = Depends(get_db)):
    return db.query(models.Delivery).all()