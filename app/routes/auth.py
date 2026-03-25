from fastapi import APIRouter

from app.models import User
from app.schemas import UserReg, UserLog


router = APIRouter(prefix="/api")

@app.get()

@app.get("/hello")
def read_root():
    return {"hello_world": "хеллоу ворлд"}


