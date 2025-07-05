import os
import json
import uuid
from typing import Dict, Any, List

BASE_PATH = "./data"

def list_collections() -> List[str]:
    """
    Return a list of all collection names (subdirectories under BASE_PATH).
    """
    if not os.path.exists(BASE_PATH):
        return []
    return [
        d for d in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, d))
    ]

def insert(collection: str, document: Dict[str, Any]) -> str:
    """
    Insert a new document into the specified collection.
    Generates a UUID for `_id`, writes to disk, and returns the new ID.
    """
    col_path = os.path.join(BASE_PATH, collection)
    os.makedirs(col_path, exist_ok=True)

    doc_id = str(uuid.uuid4())
    document["_id"] = doc_id

    with open(os.path.join(col_path, f"{doc_id}.json"), "w") as f:
        json.dump(document, f, indent=2)

    return doc_id

def find(collection: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find all documents in a collection matching the exact key/value filters.
    """
    col_path = os.path.join(BASE_PATH, collection)
    if not os.path.exists(col_path):
        return []

    results: List[Dict[str, Any]] = []
    for filename in os.listdir(col_path):
        file_path = os.path.join(col_path, filename)
        try:
            with open(file_path, "r") as f:
                doc = json.load(f)
            if all(doc.get(k) == v for k, v in filters.items()):
                results.append(doc)
        except Exception:
            # skip unreadable files
            continue

    return results

def delete(collection: str, filters: Dict[str, Any]) -> int:
    """
    Delete all documents matching the filters. Returns the number deleted.
    """
    col_path = os.path.join(BASE_PATH, collection)
    if not os.path.exists(col_path):
        return 0

    deleted = 0
    for filename in os.listdir(col_path):
        file_path = os.path.join(col_path, filename)
        try:
            with open(file_path, "r") as f:
                doc = json.load(f)
            if all(doc.get(k) == v for k, v in filters.items()):
                os.remove(file_path)
                deleted += 1
        except Exception:
            continue

    return deleted

def update(collection: str, filters: Dict[str, Any], new_doc: Dict[str, Any]) -> int:
    """
    Update all documents matching `filters` by replacing their contents
    with `new_doc` (preserving the original `_id`). Returns number updated.
    """
    col_path = os.path.join(BASE_PATH, collection)
    if not os.path.exists(col_path):
        return 0

    updated_count = 0
    for filename in os.listdir(col_path):
        file_path = os.path.join(col_path, filename)
        try:
            with open(file_path, "r") as f:
                doc = json.load(f)
            if all(doc.get(k) == v for k, v in filters.items()):
                # preserve the original ID
                new_doc_copy = new_doc.copy()
                new_doc_copy["_id"] = doc["_id"]
                with open(file_path, "w") as f:
                    json.dump(new_doc_copy, f, indent=2)
                updated_count += 1
        except Exception:
            continue

    return updated_count
