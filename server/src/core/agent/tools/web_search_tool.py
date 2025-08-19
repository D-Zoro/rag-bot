from langchain.tools import tool 
import requests

@tool("websearch_tool",return_direct=False)

def web_search_tool(query: str) -> str:
    """Search the web for current information."""
    try:
        # Using DuckDuckGo instant answer API (free)
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('AbstractText'):
            return f"Search result: {data['AbstractText']}"
        elif data.get('Answer'):
            return f"Answer: {data['Answer']}"
        else:
            return f"No specific answer found for: {query}"
    except Exception as e:
        return f"Search failed: {str(e)}"

