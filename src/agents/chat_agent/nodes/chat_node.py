from langchain_groq import ChatGroq
from src.agents.chat_agent.nodes.chat_node import ChatAgentState
from dotenv import load_dotenv
import os 

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def chat(state: ChatAgentState) -> ChatAgentState:
    """A chat node that uses Groq to generate a response based on input messages."""
    model = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama3.1-8b-instant")
    return {"messages": model.invoke(state["messages"]).content}