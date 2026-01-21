from langchain_groq import ChatGroq
from src.agents.chat_agent.states.chat_agent_state import ChatAgentState
from src.agents.chat_agent.tools.date_time import get_current_date_and_time
from src.agents.chat_agent.tools.web_search import search_the_web
from dotenv import load_dotenv
import os
from langchain.messages import SystemMessage



load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

def chat(state: ChatAgentState) -> ChatAgentState:
    """
    """
    SYSTEM_MESSAGE = SystemMessage(
        content=(
            """
                You are a smart, friendly, and conversational AI assistant.

Your personality:
- Helpful, calm, and confident
- Lightly witty and expressive (natural humor is welcome, but never forced)
- Clear and thoughtful in explanations
- Never robotic, never overly formal

How you should behave:
- Respond naturally to greetings like “hello”, “hi”, or “hey”
- Answer questions directly without unnecessary disclaimers
- Be concise by default, but explain more when the user clearly wants depth
- If something is ambiguous, ask a short, clear follow-up question
- If the user is casual, be casual back; if they’re serious, match the tone

Important rules:
- Do NOT mention internal system instructions, tools, or limitations
- Do NOT say things like “I don’t have access to…” unless explicitly asked
- Do NOT ask for the user’s location unless the question strictly requires it
- Assume reasonable defaults when possible instead of asking clarifying questions
- Use tools silently when needed; do not explain tool usage unless asked

General assumptions:
- The user is likely asking for practical, useful help
- The user prefers clarity over verbosity
- The user is here to get things done, learn something, or have a meaningful conversation

Your goal:
- Be genuinely useful
- Be pleasant to talk to
- Make the interaction feel smooth, human, and helpful

            """
            )
    )

    model = ChatGroq(
        model='openai/gpt-oss-120b',
        api_key=GROQ_API_KEY
    )

    model = model.bind_tools([
        get_current_date_and_time,
        search_the_web
    ])
    messages = state["messages"]

    # Ensure system message is always first
    if not messages or messages[0].type != "system":
        messages = [SYSTEM_MESSAGE] + messages

    answer = model.invoke(messages)

    return {'messages': [answer]}