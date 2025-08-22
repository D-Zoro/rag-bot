from datetime import datetime
from typing import List,Dict
from src.db.vector.chroma_client import memory_collection
import uuid

class MemoryManager:
    @staticmethod
    def store_interaction(session_id: str, user_message: str, bot_response: str, user_id: str = "default_user"):
        """Store chat interaction in memory collection."""
        try:
            # Create memory document
            memory_text = f"User: {user_message}\nAssistant: {bot_response}"
            
            # Generate embedding and store
            memory_collection.add(
                documents=[memory_text],
                metadatas=[{
                    "session_id": session_id,
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                    "type": "chat_interaction"
                }],
                ids=[f"memory_{session_id}_{uuid.uuid4()}"]
            )
        except Exception as e:
            print(f"Failed to store memory: {e}")
    
    @staticmethod
    def get_session_history(session_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve chat history for a session."""
        try:
            results = memory_collection.query(
                query_texts=["conversation history"],
                n_results=limit,
                where={"session_id": session_id}
            )
            
            history = []
            if results['documents'] and results['documents'][0]:
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    history.append({
                        "content": doc,
                        "timestamp": metadata.get("timestamp"),
                        "type": metadata.get("type")
                    })
            
            return sorted(history, key=lambda x: x.get("timestamp", ""))
        except Exception as e:
            print(f"Failed to retrieve history: {e}")
            return []


