import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="RAG-Bot Client", layout="wide")
st.title("🤖 RAG-Bot Client")

# Sidebar for file upload and session management
with st.sidebar:
    st.header("📁 Document Management")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=['pdf', 'docx', 'doc', 'txt', 'xml'],
        help="Supported formats: PDF, DOCX, TXT, XML"
    )
    
    if uploaded_file and st.button("Upload"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        try:
            response = requests.post(f"{API_BASE_URL}/upload-document/", files=files)
            if response.status_code == 200:
                st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                st.json(response.json())
            else:
                st.error(f"❌ Upload failed: {response.text}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Document list
    if st.button("📋 List Documents"):
        try:
            response = requests.get(f"{API_BASE_URL}/documents/")
            if response.status_code == 200:
                docs = response.json()["documents"]
                st.write("**Uploaded Documents:**")
                for doc in docs:
                    st.write(f"- {doc['filename']} ({doc['chunk_count']} chunks)")
        except Exception as e:
            st.error(f"Error fetching documents: {e}")
    
    # Document search
    search_query = st.text_input("🔍 Search Documents")
    if search_query and st.button("Search"):
        try:
            response = requests.post(f"{API_BASE_URL}/search-documents/?query={search_query}")
            if response.status_code == 200:
                results = response.json()["results"]
                st.write("**Search Results:**")
                for result in results[:3]:
                    st.write(f"📄 {result['filename']}")
                    st.write(result['content'][:200] + "...")
                    st.write("---")
        except Exception as e:
            st.error(f"Search error: {e}")
    
    # Session management
    st.header("💬 Session Management")
    session_id = st.text_input("Session ID", value="default_session")
    
    if st.button("📜 View History"):
        try:
            response = requests.get(f"{API_BASE_URL}/chat-history/{session_id}")
            if response.status_code == 200:
                history = response.json()["history"]
                st.write("**Chat History:**")
                for item in history[-5:]:  # Last 5 items
                    st.text_area("", value=item["content"], height=100, disabled=True)
        except Exception as e:
            st.error(f"Error fetching history: {e}")
    
    if st.button("🗑️ Clear History"):
        try:
            response = requests.delete(f"{API_BASE_URL}/chat-history/{session_id}")
            if response.status_code == 200:
                st.success("History cleared!")
                st.session_state.messages = []
        except Exception as e:
            st.error(f"Error clearing history: {e}")

# Main chat interface
st.header("💭 Chat Interface")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and "sources" in message:
            with st.expander("📚 Sources"):
                for source in message["sources"]:
                    st.write(f"**{source['type'].title()}**: {source.get('content', 'N/A')}")

# Chat input
if prompt := st.chat_input("Ask me anything about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                chat_data = {
                    "message": prompt,
                    "session_id": session_id,
                    "user_id": "streamlit_user"
                }
                
                response = requests.post(
                    f"{API_BASE_URL}/chat/",
                    json=chat_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    bot_response = response.json()
                    st.write(bot_response["response"])
                    
                    # Add assistant message with sources
                    assistant_msg = {
                        "role": "assistant",
                        "content": bot_response["response"],
                        "sources": bot_response.get("sources", [])
                    }
                    st.session_state.messages.append(assistant_msg)
                    
                    # Show sources
                    if bot_response.get("sources"):
                        with st.expander("📚 Sources"):
                            for source in bot_response["sources"]:
                                st.write(f"**{source['type'].title()}**: {source.get('content', 'N/A')}")
                    
                else:
                    error_msg = f"Error: {response.status_code} - {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except Exception as e:
                error_msg = f"Connection error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer with server status
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Test Web Search"):
        test_query = st.text_input("Web search query:", value="latest AI news")
        if test_query:
            try:
                response = requests.get(f"{API_BASE_URL}/test-web-search/?query={test_query}")
                if response.status_code == 200:
                    st.json(response.json())
            except Exception as e:
                st.error(f"Test failed: {e}")

with col2:
    if st.button("🏥 Health Check"):
        try:
            response = requests.get(f"{API_BASE_URL}/health/")
            if response.status_code == 200:
                health_data = response.json()
                st.success(f"Server Status: {health_data['status']}")
                st.write(f"Documents: {health_data.get('document_count', 0)}")
                st.write(f"Memory entries: {health_data.get('memory_count', 0)}")
            else:
                st.error("Server health check failed")
        except Exception as e:
            st.error(f"Cannot connect to server: {e}")

# Usage instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    ### Getting Started:
    
    1. **Upload Documents**: Use the sidebar to upload PDF, DOCX, TXT, or XML files
    2. **Start Chatting**: Ask questions about your uploaded documents
    3. **Web Search**: Ask about current events - the bot will search the web automatically
    4. **Memory**: The bot remembers your conversation within each session
    
    ### Features:
    - **Document Processing**: Supports multiple file formats with intelligent chunking
    - **Semantic Search**: Finds relevant information across all uploaded documents
    - **Web Search**: Automatically searches for current information when needed
    - **Long-term Memory**: Remembers conversations and learns from interactions
    - **Tool Integration**: Date parsing, web search, and document retrieval
    
    ### Example Queries:
    - "Summarize the main points from the uploaded PDF"
    - "What's the latest news about AI today?"
    - "Compare information from different documents"
    - "When was this document created?"
""")
