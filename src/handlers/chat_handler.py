from typing import Iterator, List

from langchain.messages import HumanMessage, AIMessage

from src.agents.chat_agent.graph import create_chat_agent_graph
from src.agents.chat_agent.states.chat_agent_state import ChatAgentState
from src.db.supabase_client import supabase


# =========================
# CONFIG
# =========================

MAX_CONTEXT_MESSAGES = 8  # SAFE for 8k TPM models


# =========================
# GRAPH
# =========================

graph = create_chat_agent_graph()


# =========================
# HELPERS
# =========================

def trim_history(messages: List):
    """
    Keep only the last N messages to avoid token overflow.
    """
    return messages[-MAX_CONTEXT_MESSAGES:]


def load_history_from_db(thread_id: str):
    """
    Load chat history from Supabase and convert to LangChain messages.
    """
    res = (
        supabase
        .table("chat_messages")
        .select("sender, content")
        .eq("thread_id", thread_id)
        .order("created_at")
        .execute()
    )

    messages = []

    for row in res.data:
        if row["sender"] == "user":
            messages.append(HumanMessage(content=row["content"]))
        elif row["sender"] == "bot":
            messages.append(AIMessage(content=row["content"]))

    return messages


# =========================
# NORMAL (NON-STREAM) CHAT
# =========================

def chat_agent_handler(thread_id: str, message: str):
    """
    Chat handler with persistent memory (Supabase-backed).
    Sends only trimmed context to the LLM.
    """

    # 1️⃣ Load FULL history from DB
    history_messages = load_history_from_db(thread_id)

    # 2️⃣ Trim history for LLM context
    history_messages = trim_history(history_messages)

    # 3️⃣ Append current user message
    history_messages.append(HumanMessage(content=message))

    # 4️⃣ Save user message immediately
    supabase.table("chat_messages").insert({
        "thread_id": thread_id,
        "sender": "user",
        "content": message
    }).execute()

    # 5️⃣ Invoke graph
    state = graph.invoke(
        input={
            "messages": history_messages
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    # 6️⃣ Extract assistant reply safely
    messages = state.get("messages", [])
    last_msg = messages[-1]

    assistant_text = (
        last_msg.content.strip()
        if hasattr(last_msg, "content")
        else str(last_msg)
    )

    # 7️⃣ Save assistant reply
    if assistant_text.strip():
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
    Uses trimmed context to avoid token overflow.
    """

    # 1️⃣ Save user message immediately
    supabase.table("chat_messages").insert({
        "thread_id": thread_id,
        "sender": "user",
        "content": message
    }).execute()

    # 2️⃣ Load FULL history
    history_messages = load_history_from_db(thread_id)

    # 3️⃣ Trim history for LLM
    history_messages = trim_history(history_messages)

    # 4️⃣ Append current user message
    history_messages.append(HumanMessage(content=message))

    collected_chunks: List[str] = []

    # 5️⃣ Stream from graph
    for chunk, metadata in graph.stream(
        input={
            "messages": history_messages
        },
        config={
            "configurable": {
                "thread_id": thread_id
            }
        },
        stream_mode="messages"
    ):
        if chunk and getattr(chunk, "content", None):
            collected_chunks.append(chunk.content)
            yield chunk.content

    # 6️⃣ Save full assistant response after streaming
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
