from src.core.agent.state import AgentState
from src.core.agent.tools.memory_retrival_tool import memory_search_tool
from src.core.agent.tools.document_search_tool import document_search_tool

def retrieval_node(state: AgentState):
    """Retrieve relevant context from documents and memory."""
    query = state["user_query"]
    session_id = state["session_id"]
    
    # Search documents
    doc_context = document_search_tool(query)
    
    # Search memory
    memory_context = memory_search_tool(query, session_id)
    
    # Combine contexts
    context = f"Document Context:\n{doc_context}\n\nMemory Context:\n{memory_context}"
    
    return {
        **state,
        "context": context
    }

