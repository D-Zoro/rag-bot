from src.core.agent.state import AgentState
from src.external.llm_client import llm


def reasoning_node(state: AgentState):
    """Main reasoning and response generation."""
    query = state["user_query"]
    context = state["context"]
    messages = state["messages"]
    
    # Prepare chat history for context
    chat_context = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in messages[-5:]  # Last 5 messages
    ])
    
    # Create prompt
    prompt = f"""
    You are a helpful AI assistant with access to uploaded documents and chat history.
    
    User Query: {query}
    
    Retrieved Context:
    {context}
    
    Recent Chat History:
    {chat_context}
    
    Please provide a comprehensive response based on the available context and your knowledge.
    If you need additional current information, you can use tools.
    """
    
    try:
        response = llm.invoke(prompt)
        return {
            **state,
            "response": response.content
        }
    except Exception as e:
        return {
            **state,
            "response": f"Error generating response: {str(e)}"
        }


