from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List, Optional, Any, Dict
from backend.llm_interface import parse_prompt
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LLM-Powered SQL DB")

DB_FILE = "database.db"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return sqlite3.connect(DB_FILE)

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    status: str
    result: Optional[List[Dict[str, Any]]] = None
    rows_affected: Optional[int] = None
    error: Optional[str] = None

@app.get("/collections", response_model=List[str])
def get_collections():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cur.fetchall()]
    db.close()
    return tables

@app.get("/columns/{table_name}", response_model=Dict[str, str])
def get_columns(table_name: str):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(f"PRAGMA table_info({table_name})")
        info = cur.fetchall()
        return {col[1]: col[2] for col in info}
    except Exception as e:
        raise HTTPException(400, f"Error fetching columns: {e}")
    finally:
        db.close()

@app.post("/query", response_model=QueryResponse)
def query_sql(req: QueryRequest):
    try:
        sql = parse_prompt(req.prompt)
        print(f"🔍 Generated SQL: {sql}")
    except Exception as e:
        raise HTTPException(400, detail=f"LLM parsing failed: {e}")

    db = get_db()
    cur = db.cursor()

    try:
        if sql.strip().upper().startswith("SELECT"):
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            result = [dict(zip(cols, row)) for row in rows]
            return QueryResponse(status="success", result=result)
        else:
            cur.execute(sql)
            db.commit()
            return QueryResponse(status="success", rows_affected=cur.rowcount)
    except Exception as e:
        raise HTTPException(400, detail=f"SQL execution error: {e}")
    finally:
        db.close()
