from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import json

from backend.db.engine import list_collections, insert, find, delete
from backend.llm_interface import parse_prompt

app = FastAPI(title = "LLM-DBMS")

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    status: str
    result: Optional[List[Dict[str, Any]]] = None
    id: Optional[str] = None
    deleted: Optional[str] = None
    error: Optional[str] = None

@app.get("/collections", response_model = List[str])
def get_collections():
    return list_collections()

@app.post("/query", response_model = QueryResponse)
def run_query(req: QueryRequest):
    try:
        cmd = parse_prompt(req.prompt)
    except Exception as e:
        raise HTTPException(status_code = 400, detail = f"Parse error: {e}")
    
    op = cmd.get("operation")
    coll = cmd.get("collection")
    filt = cmd.get("filter", {})
    doc = cmd.get("document", {})

    if op == "insert":
        new_id = insert(coll, doc)
        return QueryResponse(status = "success", id = new_id)
    
    elif op == "find":
        results = find(coll, filt)
        return QueryResponse(status = "success", result = results)
    
    elif op == "delete":
        deleted_count = delete(coll, filt)
        return QueryResponse(status = "success", deleted = deleted_count)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported operation: {op}")