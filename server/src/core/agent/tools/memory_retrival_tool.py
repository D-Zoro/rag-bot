from src.db.vector.chroma_client import memory_collection



def memory_search_tool(query: str, session_id: str) -> str:
    """Search through chat history and memory."""
    try:
        # Search in memory collection
        results = memory_collection.query(
            query_texts=[query],
            n_results=5,
            where={"session_id": session_id}
        )
        
        if results['documents'] and results['documents'][0]:
            memories = results['documents'][0]
            return f"Relevant memories: {'; '.join(memories[:3])}"
        else:
            return "No relevant memories found."
    except Exception as e:
        return f"Memory search failed: {str(e)}"

