import chromadb
from chromadb.config import Settings

CHROMA_DB_PATH = "./data/vectordb"
CHAT_HISTORY_COLLECTION = "chat_history"
DOCUMENTS_COLLECTION = "documents"

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DB_PATH,
    settings=Settings(anonymized_telemetry=False)
)

#init vectorstores
try:
    doc_collection = chroma_client.get_collection(DOCUMENTS_COLLECTION)
except:
    doc_collection = chroma_client.create_collection(
        name=DOCUMENTS_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

try:
    memory_collection = chroma_client.get_collection(CHAT_HISTORY_COLLECTION)
except:
    memory_collection = chroma_client.create_collection(
        name=CHAT_HISTORY_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )

