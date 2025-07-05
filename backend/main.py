from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List
import os, json

from backend.db.engine import list_collections, insert, find, delete, update
from backend.llm_interface import parse_prompt
from backend.schema.schema_manager import (
    list_schemas, load_schema, save_schema, validate_document
)
from jsonschema import ValidationError

app = FastAPI(title="LLM-DBMS")

# CORS
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Ensure schemas dir
SCHEMA_DIR = os.path.join(os.getcwd(), "backend", "schema", "schemas")
os.makedirs(SCHEMA_DIR, exist_ok=True)

class RawSchema(BaseModel):
    schema: Dict[str, Any]

# Schema endpoints
@app.get("/schemas", response_model=List[str])
def api_list_schemas():
    return list_schemas()

@app.get("/schemas/{collection}")
def api_get_schema(collection: str):
    try:
        return load_schema(collection)
    except FileNotFoundError:
        raise HTTPException(404, f"Schema {collection} not found")

@app.post("/schemas/{collection}")
def api_save_schema(collection: str, body: RawSchema):
    save_schema(collection, body.schema)
    return {"status": "success", "collection": collection}

# Collection list
@app.get("/collections", response_model=List[str])
def api_list_collections():
    return list_collections()

# Document listing
@app.get("/documents/{collection}")
def list_documents(
    collection: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1)
):
    all_docs = find(collection, {})
    return {
        "total": len(all_docs),
        "skip": skip,
        "limit": limit,
        "documents": all_docs[skip : skip + limit]
    }

# Delete document
class DocID(BaseModel):
    id: str

@app.post("/documents/{collection}/delete")
def delete_document(collection: str, body: DocID):
    count = delete(collection, {"_id": body.id})
    if count == 0:
        raise HTTPException(404, "Document not found")
    return {"status": "success", "deleted": count}

# Update document
class UpdateDoc(BaseModel):
    id: str
    document: Dict[str, Any]

@app.post("/documents/{collection}/update")
def update_document(collection: str, body: UpdateDoc):
    count = update(collection, {"_id": body.id}, body.document)
    if count == 0:
        raise HTTPException(404, "Document not found or no change")
    return {"status": "success", "updated": count}

# Natural‑Language query
class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    status: str
    result: List[Dict[str, Any]] = []
    id: str = ""
    deleted: int = 0
    error: str = ""

@app.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    try:
        cmd = parse_prompt(req.prompt)
    except Exception as e:
        raise HTTPException(400, f"Parse error: {e}")

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

    if op == "find":
        return QueryResponse(status="success", result=find(coll, filt))

    if op == "delete":
        deleted_count = delete(coll, filt)
        return QueryResponse(status="success", deleted=deleted_count)

    raise HTTPException(400, f"Unsupported operation: {op}")
