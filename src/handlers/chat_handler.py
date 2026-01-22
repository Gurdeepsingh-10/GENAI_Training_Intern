from typing import Iterator, List

from langchain.messages import HumanMessage, AIMessage

from src.agents.chat_agent.graph import create_chat_agent_graph
from src.agents.chat_agent.states.chat_agent_state import ChatAgentState
from src.db.supabase_client import supabase
from langchain.messages import SystemMessage
from src.memory.summarizer import summarize_messages
from fastapi import Request


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



MAX_RECENT_MESSAGES = 6  # 👈 important

def chat_agent_handler(thread_id: str, message: str):

    # 1️⃣ Load summary
    summary = load_summary(thread_id)

    messages = []

    # 2️⃣ Inject summary as system memory (NOT visible)
    if summary:
        messages.append(
            SystemMessage(content=f"Conversation memory: {summary}")
        )

    # 3️⃣ Load last N messages only
    history = (
        supabase
        .table("chat_messages")
        .select("sender, content")
        .eq("thread_id", thread_id)
        .order("created_at", desc=True)
        .limit(MAX_RECENT_MESSAGES)
        .execute()
    )

    for row in reversed(history.data):
        if row["sender"] == "user":
            messages.append(HumanMessage(content=row["content"]))
        else:
            messages.append(AIMessage(content=row["content"]))

    # 4️⃣ Append new user message
    messages.append(HumanMessage(content=message))

    # 5️⃣ Save user message
    supabase.table("chat_messages").insert({
        "thread_id": thread_id,
        "sender": "user",
        "content": message
    }).execute()

    # 6️⃣ Call graph
    state = graph.invoke(
        {"messages": messages},
        config={"configurable": {"thread_id": thread_id}}
    )

    assistant_msg = state["messages"][-1].content

    # 7️⃣ Save assistant reply
    supabase.table("chat_messages").insert({
        "thread_id": thread_id,
        "sender": "bot",
        "content": assistant_msg
    }).execute()

    # 8️⃣ Periodically summarize (every ~8 messages)
    total = (
        supabase
        .table("chat_messages")
        .select("id", count="exact")
        .eq("thread_id", thread_id)
        .execute()
    )

    if total.count % 8 == 0:
        recent_msgs = messages[-12:]
        summary = summarize_messages(recent_msgs)
        save_summary(thread_id, summary)

    return state



# =========================
# STREAMING CHAT
# =========================

def chat_streaming_handler(request: Request,
    thread_id: str,
    message: str) -> Iterator[str]:
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

def load_summary(thread_id: str) -> str | None:
    res = (
        supabase
        .table("chat_summaries")
        .select("summary")
        .eq("thread_id", thread_id)
        .execute()
    )

    if not res.data:
        return None

    return res.data[0]["summary"]



def save_summary(thread_id: str, summary: str):
    supabase.table("chat_summaries").upsert({
        "thread_id": thread_id,
        "summary": summary
    }).execute()

def mark_message_feedback(message_id: int, approved: bool):
    """
    Human-in-the-loop feedback for AI answers.
    """
    supabase.table("chat_messages").update(
        {"approved": approved}
    ).eq("id", message_id).execute()
