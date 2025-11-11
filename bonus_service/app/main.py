from fastapi import FastAPI
import asyncio
from . import models, database
from .routes import router
from .rabbitmq import consume_delivery_completed_messages

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Bonus Service", version="1.0.0")

app.include_router(router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_delivery_completed_messages())

@app.get("/")
def read_root():
    return {"message": "Bonus Service is running"}