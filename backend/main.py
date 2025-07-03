from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import json

from backend.db.engine import list_collections, insert, find, delete
from fastapi.middleware.cors import CORSMiddleware
from backend.llm_interface import parse_prompt
from backend.schema.schema_manager import (
    list_schemas, load_schema, save_schema, validate_document
)
from jsonschema import ValidationError

app = FastAPI(title="LLM-DBMS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to just your frontend origin later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Schema API -----

class RawSchema(BaseModel):
    schema: Dict[str, Any]

@app.get("/schema", response_model=List[str])
def api_list_schemas():
    return list_schemas()

@app.get("/schema/{collection}")
def api_get_schema(collection: str):
    try:
        return load_schema(collection)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Schema {collection} not found")

@app.post("/schema/{collection}")
def api_post_schema(collection: str, schema: RawSchema):
    print(f"Saving schema via /schema/{collection}")
    save_schema(collection, schema.schema)
    return {"status": "saved via /schema"}

@app.post("/schemas/{collection}")
def api_save_schema(collection: str, schema: RawSchema):
    print(f"Saving schema via /schemas/{collection}")
    save_schema(collection, schema.schema)
    return {"status": "saved via /schemas"}

# ----- Query API -----

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    status: str
    result: Optional[List[Dict[str, Any]]] = None
    id: Optional[str] = None
    deleted: Optional[int] = None
    error: Optional[str] = None

@app.get("/collections", response_model=List[str])
def get_collections():
    return list_collections()

@app.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    try:
        cmd = parse_prompt(req.prompt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    op = cmd.get("operation")
    coll = cmd.get("collection")
    filt = cmd.get("filter", {})
    doc = cmd.get("document", {})

    if op == "insert":
        try:
            validate_document(coll, doc)
        except ValidationError as ve:
            raise HTTPException(400, f"Schema validation failed: {ve.message}")
        new_id = insert(coll, doc)
        return QueryResponse(status="success", id=new_id)

    elif op == "find":
        results = find(coll, filt)
        return QueryResponse(status="success", result=results)

    elif op == "delete":
        deleted_count = delete(coll, filt)
        return QueryResponse(status="success", deleted=deleted_count)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported operation: {op}")
