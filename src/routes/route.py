from fastapi import APIRouter
from src.handlers.handler import hello
router = APIRouter()


@router.get("/")
def hello_route():
    return hello()