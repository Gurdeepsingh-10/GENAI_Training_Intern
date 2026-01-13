from langgraph.graph import START , END , StateGraph
from langgraph.graph.state import CompiledStateGraph
from asyncio import graph
from src.agents.chat_agent.nodes.chat_node import ChatAgentState
from src.agents.chat_agent.nodes.chat_node import chat


def create_chat_agent_graph() -> CompiledStateGraph:
    
    graph_builder = StateGraph(ChatAgentState)
    graph_builder.add_node("chat_node", chat)
    graph_builder.add_edge(START,"chat_node")
    graph_builder.add_edge("chat_node",END)
    return graph_builder.compile()