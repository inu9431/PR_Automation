from fastapi import FastAPI
from app.api.webhook import router
from app.database import Base, engine

# Base.metadata.create_all(engine)

app = FastAPI()
app.include_router(router)


