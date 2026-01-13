from src.agents.chat_agent.graph import create_chat_agent_graph
graph = create_chat_agent_graph()
def chat_agent_handler(message: str) -> dict[str,str]:
    """
    Docstring for chat_agent_handler
    
    :return: Description
    :rtype: dict[str, str]

    """
    return graph.invoke({"messages": message}) #{messages: "response from chat agent"}