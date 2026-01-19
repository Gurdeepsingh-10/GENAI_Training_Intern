from typing import Literal
from langgraph.graph import END
from src.agents.chat_agent.states.chat_agent_state import ChatAgentState

def should_continue(state: ChatAgentState) -> Literal['tool_executer_node', END]:
    """
    Docstring for should_continue

    Decide if we should continue the loop or stop based upon whether the LLM made a tool call
    
    :param state: Description
    :type state: ChatAgentState
    :return: Description
    :rtype: Any | Literal['tool_executer_node']
    """
    messages = state['messages']
    last_message = messages[-1]

    #if the LLM  makes a tool call, then perform an action
    if last_message.tool_calls:
        return 'tool_executer_node'
    
    #Otherwise, we stop (reply to the user)
    return END