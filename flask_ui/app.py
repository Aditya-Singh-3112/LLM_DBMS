from flask import Flask, render_template, request, redirect, url_for, flash
import requests, json
from math import ceil
from json import dumps, loads

API = "http://localhost:8000"

app = Flask(__name__)
app.secret_key = "dev"


@app.route("/")
def index():
    cols = requests.get(f"{API}/collections").json()
    return render_template("index.html", collections=cols)


@app.route("/insert/<collection>", methods=["GET", "POST"])
def insert(collection):
    resp = requests.get(f"{API}/schemas/{collection}")
    if resp.status_code != 200:
        flash(f"Schema for {collection} not found.", "error")
        return redirect(url_for("index"))
    schema_props = resp.json().get("properties", {})

    if request.method == "POST":
        doc = {}
        for name, prop in schema_props.items():
            if prop.get("type") == "boolean":
                doc[name] = name in request.form
            else:
                val = request.form.get(name, "")
                if prop.get("type") == "number":
                    try: val = float(val)
                    except: val = None
                doc[name] = val
        prompt = f"Insert into {collection}: {json.dumps(doc)}"
        res = requests.post(f"{API}/query", json={"prompt": prompt}).json()
        if res.get("status") == "success":
            flash(f"Inserted ID: {res.get('id')}", "success")
        else:
            flash(f"Error: {res.get('error')}", "error")
        return redirect(url_for("insert", collection=collection))

    return render_template("insert.html", collection=collection, schema=schema_props)


@app.route("/view/<collection>")
def view(collection):
    skip = int(request.args.get("skip", 0))
    limit = int(request.args.get("limit", 20))

    resp = requests.get(f"{API}/documents/{collection}", params={"skip": skip, "limit": limit})
    if resp.status_code != 200:
        flash(f"Failed to load documents for {collection}", "error")
        return redirect(url_for("index"))

    data = resp.json()
    docs = data["documents"]
    total = data["total"]
    pages = ceil(total / limit)
    page = (skip // limit) + 1

    return render_template(
        "view.html",
        collection=collection,
        documents=docs,
        skip=skip,
        limit=limit,
        total=total,
        page=page,
        pages=pages
    )


@app.route("/documents/<collection>/delete", methods=["POST"])
def delete_doc(collection):
    doc_id = request.form.get("id")
    resp = requests.post(f"{API}/documents/{collection}/delete", json={"id": doc_id})
    if resp.status_code == 200:
        flash("Document deleted", "success")
    else:
        flash(f"Delete failed: {resp.text}", "error")
    return redirect(url_for("view", collection=collection))


@app.route("/documents/<collection>/edit", methods=["GET", "POST"])
def edit(collection):
    doc_id = request.args.get("doc_id") or request.form.get("id")
    # load all docs to find one by id (or implement single‐doc fetch)
    all_docs = requests.get(f"{API}/documents/{collection}", params={"skip":0, "limit":9999}).json()["documents"]
    doc = next((d for d in all_docs if d["_id"] == doc_id), None)
    if not doc:
        flash("Document not found", "error")
        return redirect(url_for("view", collection=collection))

    resp = requests.get(f"{API}/schemas/{collection}")
    schema_props = resp.json().get("properties", {})

    if request.method == "POST":
        updated = {}
        for name, prop in schema_props.items():
            if prop.get("type") == "boolean":
                updated[name] = name in request.form
            else:
                val = request.form.get(name, "")
                if prop.get("type") == "number":
                    try: val = float(val)
                    except: val = None
                updated[name] = val
        resp2 = requests.post(f"{API}/documents/{collection}/update",
                              json={"id": doc_id, "document": updated})
        if resp2.status_code == 200:
            flash("Document updated", "success")
            return redirect(url_for("view", collection=collection))
        else:
            flash(f"Update failed: {resp2.text}", "error")

    return render_template("edit.html", collection=collection, schema=schema_props, doc=doc)


@app.route("/schema/<collection>", methods=["GET", "POST"])
def edit_schema(collection):
    """
    Display and edit the raw JSON Schema for a collection.
    GET: load from FastAPI and show in textarea.
    POST: send updated JSON back to FastAPI to save.
    """
    api_url = f"{API}/schemas/{collection}"

    if request.method == "POST":
        # Read the JSON string from form
        raw = request.form.get("schema_json", "")
        try:
            # Validate that it’s valid JSON
            parsed = loads(raw)
        except Exception as e:
            flash(f"Invalid JSON: {e}", "error")
            return redirect(url_for("edit_schema", collection=collection))

        # Send to FastAPI to save
        resp = requests.post(api_url, json={"schema": parsed})
        if resp.status_code == 200:
            flash("Schema saved successfully.", "success")
        else:
            flash(f"Save failed: {resp.text}", "error")
        return redirect(url_for("edit_schema", collection=collection))

    # GET: Load existing schema
    resp = requests.get(api_url)
    if resp.status_code != 200:
        flash(f"Schema for {collection} not found.", "error")
        return redirect(url_for("index"))

    schema_obj = resp.json()
    # Pretty‑print it for the textarea
    schema_str = dumps(schema_obj, indent=2)
    return render_template(
        "schema.html",
        collection=collection,
        schema_json=schema_str
    )

@app.route("/nlq", methods=["GET", "POST"])
def nlq():
    """
    Natural‑Language Query page.
    GET: show an input box.
    POST: send the prompt to FastAPI /query and display the response.
    """
    result = None
    error = None
    prompt = ""

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        if prompt:
            try:
                resp = requests.post(f"{API}/query", json={"prompt": prompt})
                data = resp.json()
                if resp.status_code == 200 and data.get("status") == "success":
                    # choose which field to render
                    if data.get("result") is not None:
                        result = data["result"]
                    elif data.get("id"):
                        result = f"Inserted ID: {data['id']}"
                    elif data.get("deleted") is not None:
                        result = f"Deleted count: {data['deleted']}"
                    else:
                        result = data
                else:
                    error = data.get("detail") or data.get("error") or resp.text
            except Exception as e:
                error = str(e)

    return render_template(
        "nlq.html",
        prompt=prompt,
        result=result,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
