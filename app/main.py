from fastapi import FastAPI
from mangum import Mangum

from app import routers

app = FastAPI()

app.include_router(routers.machine)
app.include_router(routers.raspi)

handler = Mangum(app)
