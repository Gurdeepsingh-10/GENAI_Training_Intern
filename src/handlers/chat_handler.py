from typing import Iterator, List
from langchain.messages import HumanMessage, AIMessage

from src.agents.chat_agent.graph import create_chat_agent_graph
from src.agents.chat_agent.states.chat_agent_state import ChatAgentState
from src.db.supabase_client import supabase

graph = create_chat_agent_graph()


# =========================
# NORMAL (NON-STREAM) CHAT
# =========================
def chat_agent_handler(thread_id: str, message: str) -> ChatAgentState:
    """
    Handles a full chat turn (non-streaming).
    Saves both user + assistant messages to Supabase.
    """

    # 1️⃣ Save user message
    supabase.table("chat_messages").insert({
        "thread_id": thread_id,
        "sender": "user",
        "content": message
    }).execute()

    # 2️⃣ Invoke graph
    state: ChatAgentState = graph.invoke(
        input={
            "messages": [HumanMessage(content=message)]
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    # 3️⃣ Extract assistant message safely
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage):
        assistant_text = last_msg.content
    else:
        assistant_text = str(last_msg)

    # 4️⃣ Save assistant message
    supabase.table("chat_messages").insert({
        "thread_id": thread_id,
        "sender": "bot",
        "content": assistant_text
    }).execute()

    return state


# =========================
# STREAMING CHAT
# =========================
def chat_streaming_handler(thread_id: str, message: str) -> Iterator[str]:
    """
    Streams tokens from the graph.
    Saves the FULL assistant message only after streaming ends.
    """

    # Save user message immediately
    supabase.table("chat_messages").insert({
        "thread_id": thread_id,
        "sender": "user",
        "content": message
    }).execute()

    collected_chunks: List[str] = []

    for chunk, metadata in graph.stream(
        input={
            "messages": [HumanMessage(content=message)]
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        },
        stream_mode="messages"
    ):
        if chunk and chunk.content:
            collected_chunks.append(chunk.content)
            yield chunk.content

    # After streaming completes → save full assistant message
    final_response = "".join(collected_chunks)

    if final_response.strip():
        supabase.table("chat_messages").insert({
            "thread_id": thread_id,
            "sender": "bot",
            "content": final_response
        }).execute()


# =========================
# THREAD HELPERS
# =========================
def get_all_threads_handler() -> list[str | None]:
    """
    Returns all thread IDs from LangGraph checkpoints.
    """
    all_checkpoints = graph.checkpointer.list(config={})
    threads = set()

    for checkpoint in all_checkpoints:
        threads.add(checkpoint.config["configurable"]["thread_id"])

    return list(threads)


def chat_history_handler(thread_id: str) -> ChatAgentState | dict[None, None]:
    """
    Returns in-memory graph history for a thread.
    """
    return graph.get_state(
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )[0]
