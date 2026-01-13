from fastapi import APIRouter
from src.handlers.chat_handler import chat_agent_handler
router = APIRouter()


@router.get("/chat")
def chat_agent_route(message: str) -> dict[str,str]:
    """
    Docstring for chat_agent_route
    
    :param message: Description
    :type message: str
    :return: Description
    :rtype: dict[str, str]
    """
    return chat_agent_handler(message)