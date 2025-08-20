from src.core.agent.state import AgentState
from src.external.llm_client import llm



def final_response_node(state: AgentState):
    """Generate final response incorporating tool results."""
    original_response = state["response"]
    tool_calls = state["tool_calls"]
    
    if tool_calls:
        # Enhance response with tool results
        tool_context = "\n".join([
            f"Tool {call['tool']}: {call['result']}" 
            for call in tool_calls
        ])
        
        enhanced_prompt = f"""
        Original response: {original_response}
        
        Additional tool results:
        {tool_context}
        
        Please provide a final comprehensive response incorporating all available information.
        """
        
        try:
            final_response = llm.invoke(enhanced_prompt)
            return {
                **state,
                "response": final_response.content
            }
        except Exception as e:
            return {
                **state,
                "response": f"{original_response}\n\nNote: Tool enhancement failed: {str(e)}"
            }
    
    return state


