from fastapi import FastAPI
from . import models, database
from .routes import router

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Delivery Service", version="1.0.0")

app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Delivery Service is running"}