from langchain_openai import ChatOpenAI 
import os 

API_KEY = os.getenv("AI_API_KEY")

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    openai_api_key=API_KEY
)

