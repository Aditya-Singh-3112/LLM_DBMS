import os
import json
import uuid

BASE_PATH = "./data"

def list_collections():
    return [d for d in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, d))]

def insert(collection, document):
    col_path = os.path.join(BASE_PATH, collection)
    os.makedirs(col_path, exist_ok=True)

    doc_id = str(uuid.uuid4())
    document["_id"] = doc_id

    with open(os.path.join(col_path, f"{doc_id}.json"), "w") as f:
        json.dump(document, f, indent=2)
    
    return doc_id

def find(collection, filters):
    col_path = os.path.join(BASE_PATH, collection)
    if not os.path.exists(col_path):
        return []
    
    results = []
    for file in os.listdir(col_path):
        with open(os.path.join(col_path, file), "r") as f:
            doc = json.load(f)
            if all(doc.get(k) == v for k, v in filters.items()):
                results.append(doc)
    
    return results

def delete(collection, filters):
    col_path = os.path.join(BASE_PATH, collection)
    deleted = 0

    for file in os.listdir(col_path):
        file_path = os.path.join(col_path, file)
        try:
            with open(file_path, "r") as f:
                doc = json.load(f)

            if all(doc.get(k) == v for k, v in filters.items()):
                os.remove(file_path)
                deleted += 1
        except Exception as e:
            print(f"Error deleting file {file}: {e}")

    return deleted