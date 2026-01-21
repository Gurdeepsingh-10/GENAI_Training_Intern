from typing import Iterator, List
from langchain.messages import HumanMessage, AIMessage

from src.agents.chat_agent.graph import create_chat_agent_graph
from src.agents.chat_agent.states.chat_agent_state import ChatAgentState
from src.db.supabase_client import supabase
from langchain.messages import HumanMessage, AIMessage



graph = create_chat_agent_graph()


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
    """

    # 1️⃣ Load history from DB
    history_messages = load_history_from_db(thread_id)

    # 2️⃣ Append current user message
    history_messages.append(HumanMessage(content=message))

    # 3️⃣ Save user message immediately
    supabase.table("chat_messages").insert({
        "thread_id": thread_id,
        "sender": "user",
        "content": message
    }).execute()

    # 4️⃣ Invoke graph WITH FULL HISTORY
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

    # 5️⃣ Extract assistant reply safely
    messages = state.get("messages", [])
    last_msg = messages[-1]

    assistant_text = (
        last_msg.content
        if hasattr(last_msg, "content")
        else str(last_msg)
    )

    # 6️⃣ Save assistant reply
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
