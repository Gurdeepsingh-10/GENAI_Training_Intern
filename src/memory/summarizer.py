from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2
)

SUMMARY_PROMPT = SystemMessage(
    content="""
You are a memory summarization assistant.

Your task:
- Summarize the conversation briefly
- Preserve important facts, preferences, goals, and decisions
- Remove small talk and filler
- Write in plain sentences, not bullet points
- Do NOT include timestamps or speaker labels
"""
)

def summarize_messages(messages):
    """
    Takes a list of LangChain messages and returns a concise summary string.
    """

    convo_text = []

    for m in messages:
        if isinstance(m, HumanMessage):
            convo_text.append(f"User: {m.content}")
        elif isinstance(m, AIMessage):
            convo_text.append(f"Assistant: {m.content}")

    response = model.invoke(
        [
            SUMMARY_PROMPT,
            HumanMessage(content="\n".join(convo_text))
        ]
    )

    return response.content.strip()
