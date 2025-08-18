from fastapi import FastAPI , HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime

server = FastAPI(title="rag bot server",description="FastAPI wraper for LANGCHAIN", version="2.0.0")

server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],

)

class QuerryRequest(BaseModel):
    input : str 

class QuerryResponse(BaseModel):
    output: str 
    timestamp: str 
 
@server.get("/")
async def root():
    return { "message": "Rag bot server Live"}

@server.get("/health")
async def health_check():
    return { "status": "healthy", "timestamp": datetime.now().isoformat()}

@server.get("/query",respo)
