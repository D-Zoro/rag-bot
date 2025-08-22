from fastapi import APIRouter
from src.models.schemas import ChatMessage,ChatResponse
from src.core.memory.MemoryManager import MemoryManager
from src.core.agent.graph import agent as graph

router=APIRouter()

@router.post("/chat/", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint with RAG and memory integration."""
    
    try:
        # Get chat history for context
        chat_history = MemoryManager.get_session_history(message.session_id)
        
        # Prepare messages for the graph
        messages = []
        for hist in chat_history[-5:]:  # Last 5 interactions
            if "User:" in hist["content"] and "Assistant:" in hist["content"]:
                parts = hist["content"].split("Assistant:", 1)
                if len(parts) == 2:
                    user_part = parts[0].replace("User:", "").strip()
                    assistant_part = parts[1].strip()
                    messages.extend([
                        {"role": "user", "content": user_part},
                        {"role": "assistant", "content": assistant_part}
                    ])
        
        # Add current message
        messages.append({"role": "user", "content": message.message})
        
        # Run the LangGraph workflow
        initial_state = AgentState(
            messages=messages,
            session_id=message.session_id,
            user_query=message.message,
            context="",
            response="",
            tool_calls=[]
        )
        
        # Execute the graph
        final_state = graph.invoke(initial_state)
        
        # Extract sources from tool calls and document retrieval
        sources = []
        for tool_call in final_state.get("tool_calls", []):
            sources.append({
                "type": "tool",
                "tool_name": tool_call["tool"],
                "content": tool_call["result"][:200] + "..." if len(tool_call["result"]) > 200 else tool_call["result"]
            })
        
        # Add document sources from context
        if "Document Context:" in final_state.get("context", ""):
            sources.append({
                "type": "document",
                "content": "Retrieved from uploaded documents"
            })
        
        # Store interaction in memory
        MemoryManager.store_interaction(
            session_id=message.session_id,
            user_message=message.message,
            bot_response=final_state["response"],
            user_id=message.user_id
        )
        
        return ChatResponse(
            response=final_state["response"],
            session_id=message.session_id,
            sources=sources,
            timestamp=datetime.now()
        )

