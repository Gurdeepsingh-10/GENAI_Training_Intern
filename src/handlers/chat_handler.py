from src.agents.chat_agent.graph import create_chat_agent_graph

graph = create_chat_agent_graph()

def chat_agent_handler(message: str) -> dict[str,str]:
    """
    Handles chat agent requests by invoking the chat agent graph with the provided message.
    """
    return graph.invoke({"messages": message})