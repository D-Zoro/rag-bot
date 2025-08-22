from src.core.agent.nodes.final_response_node import final_response_node
from src.core.agent.nodes.retrival_node import retrieval_node
from src.core.agent.nodes.reasoning_node import reasoning_node
from src.core.agent.nodes.tool_execution_node import tool_execution_node

from src.core.agent.state import AgentState

from langgraph.graph import StateGraph, END 


graph = StateGraph(AgentState)

#nodes->
graph.add_node("retriveal",retrieval_node)
graph.add_node("reasoning",reasoning_node)
graph.add_node("tool_execution",tool_execution_node)
graph.add_node("final_response",final_response_node)

#edges(connecting nodes)->
graph.set_entry_point("retriveal")
graph.add_edge("retriveal","reasoning")
graph.add_edge("reasoning","tool_execution")
graph.add_edge("tool_execution","final_response")
graph.add_edge("final_response",END)


agent = graph.compile()


