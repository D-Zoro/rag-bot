from dateutil import parser as date_parser
from langchain.tools import tool
from  datetime import datetime


@tool("date_retrieval_tool")
def date_retrieval_tool(date_string: str) -> str:
    """Parse and format dates, get current date info."""
    try:
        if date_string.lower() in ['today', 'now', 'current']:
            return f"Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        parsed_date = date_parser.parse(date_string)
        return f"Parsed date: {parsed_date.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"Date parsing failed: {str(e)}"

