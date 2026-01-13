from fastapi import APIRouter
from src.handlers.chat_handler import chat_agent_handler
router = APIRouter()

@router.post("/chat")
def hello_route(message: str) -> dict[str, str]:
    return chat_agent_handler(message=message)