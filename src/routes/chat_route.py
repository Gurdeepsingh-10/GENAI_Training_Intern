from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.handlers.chat_handler import chat_agent_handler, get_all_threads_handler, chat_history_handler
from src.agents.chat_agent.states.chat_agent_state import ChatAgentState
from fastapi.responses import StreamingResponse
import json
import time
from fastapi.responses import StreamingResponse
from src.db.supabase_client import supabase
from fastapi import Body


router = APIRouter()


@router.post("/chat/{thread_id}")
def chat_agent_route(thread_id: str, message: str)-> ChatAgentState:
    """
    """
    return chat_agent_handler(thread_id=thread_id, message=message)

@router.get("/chat/threads")
def get_all_threads() -> list[str | None]:
    """
    Docstring for get_all_threads
    """
    return get_all_threads_handler()

@router.post('/chat/{thread_id}')
def chat_stream_route(thread_id: str, message: str) ->ChatAgentState:
    """
    Docstring for chat_agent_route
    
    :param thread_id: Description
    :type thread_id: str
    :param message: Description
    :type message: str
    :return: Description
    :rtype: ChatAgentState
    """

    return chat_agent_handler(thread_id=thread_id, message=message)


@router.get('/chat/history/{thread_id}')
def get_chat_history(thread_id: str) -> ChatAgentState | dict[None, None]:
    """
    Docstring for get_chat_history
    
    :param thread_id: Description
    :type thread_id: str
    """
    return chat_history_handler(thread_id = thread_id)



@router.post("/chat/stream/{thread_id}")
def chat_stream(thread_id: str, message: str):

    full_state = chat_agent_handler(thread_id=thread_id, message=message)

    # ----- Extract last message safely -----
    if isinstance(full_state, dict):
        last_obj = full_state["messages"][-1]
        last_message = (
            last_obj["content"] 
            if isinstance(last_obj, dict) 
            else last_obj.content
        )
    else:
        last_message = full_state.messages[-1].content
    # ---------------------------------------

    def word_generator():
        for word in last_message.split(" "):
            time.sleep(0.08)          # <-- CRITICAL for visible streaming
            yield word + " "

    return StreamingResponse(word_generator(), media_type="text/plain")



@router.get("/chat/history/db/{thread_id}")
def get_chat_history_db(thread_id: str):
    res = (
    supabase
    .table("chat_messages")
    .select("sender, content, approved")
    .eq("thread_id", thread_id)
    .or_("approved.is.null,approved.eq.true")
    .order("created_at")
    .execute()
)

    return res.data


@router.post("/chat/feedback")
def chat_feedback(
    message_id: int = Body(...),
    approved: bool = Body(...)
):
    """
    Approve / Reject an AI response
    """
    from src.handlers.chat_handler import mark_message_feedback
    mark_message_feedback(message_id, approved)
    return {"status": "ok"}