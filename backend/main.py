from fastapi import FastAPI
from database_v2 import init_db
from routes import router

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
def startup():
    init_db()
