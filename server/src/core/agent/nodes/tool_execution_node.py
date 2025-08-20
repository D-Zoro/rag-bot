from src.core.agent.state import AgentState
from src.core.agent.tools.web_search_tool import web_search_tool
from src.core.agent.tools.date_retrieval_tool import date_retrieval_tool



def tool_execution_node(state: AgentState):
    """Execute tools if needed."""
    query = state["user_query"]
    response = state["response"]
    
    # Simple tool selection logic
    tool_calls = []
    
    # Check if web search is needed
    web_keywords = ["latest", "current", "today", "news", "recent", "2024", "2025"]
    if any(keyword in query.lower() for keyword in web_keywords):
        search_result = web_search_tool(query)
        tool_calls.append({
            "tool": "web_search",
            "query": query,
            "result": search_result
        })
    
    # Check if date info is needed
    date_keywords = ["when", "date", "time", "today", "now"]
    if any(keyword in query.lower() for keyword in date_keywords):
        date_result = date_retrieval_tool(query)
        tool_calls.append({
            "tool": "date_retrieval",
            "query": query,
            "result": date_result
        })
    
    return {
        **state,
        "tool_calls": tool_calls
    }

