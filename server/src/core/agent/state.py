from typing import List,Dict,Any 
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    session_id: str
    user_query: str
    context: str
    response: str
    tool_calls: List[Dict[str, Any]]


