from langchain.tools import tool
from src.db.vector.chroma_client import doc_collection

@tool("document_search_tool",return_direct=False)

def document_search_tool(query: str) -> str:
    """Search through uploaded documents."""
    try:
        results = doc_collection.query(
            query_texts=[query],
            n_results=5
        )
        
        if results['documents'] and results['documents'][0]:
            docs = results['documents'][0]
            sources = results['metadatas'][0] if results['metadatas'] else []
            
            response = "Document search results:\n"
            for i, (doc, source) in enumerate(zip(docs[:3], sources[:3])):
                filename = source.get('filename', 'Unknown') if source else 'Unknown'
                response += f"From {filename}: {doc[:200]}...\n"
            
            return response
        else:
            return "No relevant documents found."
    except Exception as e:
        return f"Document search failed: {str(e)}"

