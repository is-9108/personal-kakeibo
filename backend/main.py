from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import models
from .database import engine
from .routers import categories, fixed_cost, reports, transactions, payment_methods
from .scheduler import start_scheduler, stop_scheduler
from .seed import ensure_master_data

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_master_data()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(lifespan=lifespan)

app.include_router(categories.router)
app.include_router(fixed_cost.router)
app.include_router(reports.router)
app.include_router(transactions.router)
app.include_router(payment_methods.router)
