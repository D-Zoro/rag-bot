from fastapi import FastAPI, File , UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from src.utils.document_processor import extract_text_from_file
from src.models.schemas import ChatMessage, DocumentInfo, ChatResponse
from src.utils.text_splitter import text_splitter
import uuid
from src.core.agent.graph import agent as graph
from datetime import datetime
import os
from src.db.vector.chroma_client import doc_collection,memory_collection
from src.core.memory.MemoryManager import MemoryManager
from src.core.agent.state import AgentState
from src.core.agent.tools.date_retrieval_tool import date_retrieval_tool
from src.core.agent.tools.web_search_tool import web_search_tool


CHROMA_DB_PATH = "./chroma_db"
CHAT_HISTORY_COLLECTION = "chat_history"
DOCUMENTS_COLLECTION = "documents"



app = FastAPI(title="RAG-Bot Server", version="1.0.0")



# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "RAG-Bot Server is running", "status": "healthy"}

@app.post("/upload-document/", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process documents (PDF, DOCX, TXT, XML)."""
    
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.xml']
    file_ext = '.' + file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Extract text
        text_content = extract_text_from_file(tmp_file_path, file.filename)
        
        # Split into chunks
        chunks = text_splitter.split_text(text_content)
        
        # Create documents with metadata
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            doc_id = f"{file.filename}_{i}_{uuid.uuid4()}"
            documents.append(chunk)
            metadatas.append({
                "filename": file.filename,
                "chunk_index": i,
                "upload_time": datetime.now().isoformat(),
                "file_type": file_ext[1:]  # Remove the dot
            })
            ids.append(doc_id)
        
        # Store in vector database
        doc_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        return DocumentInfo(
            filename=file.filename,
            doc_type=file_ext[1:],
            chunk_count=len(chunks),
            upload_time=datetime.now()
        )
        
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/", response_model=ChatResponse)
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    try:
        history = MemoryManager.get_session_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat-history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session."""
    try:
        # Delete from memory collection
        # ChromaDB doesn't have a direct delete by metadata, so we need to query first
        results = memory_collection.query(
            query_texts=[""],
            n_results=1000,
            where={"session_id": session_id}
        )
        
        if results['ids']:
            memory_collection.delete(ids=results['ids'][0])
        
        return {"message": f"Chat history cleared for session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/")
async def list_documents():
    """List all uploaded documents."""
    try:
        # Get all documents
        results = doc_collection.get()
        
        # Group by filename
        documents = {}
        if results['metadatas']:
            for metadata in results['metadatas']:
                filename = metadata.get('filename', 'Unknown')
                if filename not in documents:
                    documents[filename] = {
                        "filename": filename,
                        "file_type": metadata.get('file_type', 'unknown'),
                        "upload_time": metadata.get('upload_time'),
                        "chunk_count": 0
                    }
                documents[filename]["chunk_count"] += 1
        
        return {"documents": list(documents.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a specific document and all its chunks."""
    try:
        # Query for document chunks
        results = doc_collection.query(
            query_texts=[""],
            n_results=1000,
            where={"filename": filename}
        )
        
        if results['ids'] and results['ids'][0]:
            doc_collection.delete(ids=results['ids'][0])
            return {"message": f"Document {filename} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search-documents/")
async def search_documents(query: str):
    """Search through uploaded documents."""
    try:
        results = doc_collection.query(
            query_texts=[query],
            n_results=10
        )
        
        search_results = []
        if results['documents'] and results['documents'][0]:
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                search_results.append({
                    "content": doc,
                    "filename": metadata.get('filename'),
                    "chunk_index": metadata.get('chunk_index'),
                    "relevance_score": "N/A"  # ChromaDB doesn't return scores directly
                })
        
        return {"query": query, "results": search_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/")
async def list_sessions():
    """List all chat sessions."""
    try:
        results = memory_collection.get()
        
        sessions = set()
        if results['metadatas']:
            for metadata in results['metadatas']:
                session_id = metadata.get('session_id')
                if session_id:
                    sessions.add(session_id)
        
        return {"sessions": list(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/")
async def health_check():
    """Detailed health check."""
    try:
        # Check database connections
        doc_count = doc_collection.count()
        memory_count = memory_collection.count()
        
        return {
            "status": "healthy",
            "document_count": doc_count,
            "memory_count": memory_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Tool testing endpoints
@app.get("/test-web-search/")
async def test_web_search(query: str):
    """Test web search functionality."""
    result = web_search_tool(query)
    return {"query": query, "result": result}

@app.get("/test-date-tool/")
async def test_date_tool(date_string: str = "today"):
    """Test date retrieval functionality."""
    result = date_retrieval_tool(date_string)
    return {"input": date_string, "result": result}

# Configuration endpoints
@app.get("/config/")
async def get_config():
    """Get current configuration."""
    return {
        "chroma_db_path": CHROMA_DB_PATH,
        "collections": {
            "documents": DOCUMENTS_COLLECTION,
            "chat_history": CHAT_HISTORY_COLLECTION
        },
        "supported_formats": ["pdf", "docx", "doc", "txt", "xml"],
        "chunk_size": text_splitter._chunk_size,
        "chunk_overlap": text_splitter._chunk_overlap
    }

if __name__ == "__main__":
    import uvicorn
    
    # Ensure directories exist
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    
    print("Starting RAG-Bot Server...")
    print(f"Documents collection: {DOCUMENTS_COLLECTION}")
    print(f"Memory collection: {CHAT_HISTORY_COLLECTION}")
    print("Supported formats: PDF, DOCX, TXT, XML")
    print("Features: Document upload, Chat with memory, Web search, Date tools")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        
    )


