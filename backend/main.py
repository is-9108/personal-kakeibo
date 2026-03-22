from fastapi import FastAPI
from . import models
from .database import engine
from .routers import categories, fixed_cost, reports, transactions

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(categories.router)
app.include_router(fixed_cost.router)
app.include_router(reports.router)
app.include_router(transactions.router)



