import requests, json

LLM_URL = "http://localhost:8080/generate"

SYSTEM_PROMPT = """You are an assistant that converts natural language into structured database commands.
Use the following JSON format:
{
  "operation": "find" | "insert" | "update" | "delete",
  "collection": "string",
  "filter": { … },
  "document": { … }  // only for insert or update
}
Respond with ONLY valid JSON for the one command.
"""

def extract_first_json(text: str) -> str:
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return text[start : i + 1]
    raise ValueError("No balanced JSON object found")

def parse_prompt(user_prompt: str) -> dict:
    full_prompt = SYSTEM_PROMPT + f'\nUser: "{user_prompt}"\nJSON:\n'
    payload = {
        "inputs": full_prompt,
        "parameters": {"max_new_tokens": 300, "temperature": 0.2}
    }

    resp = requests.post(LLM_URL, json=payload)
    resp.raise_for_status()
    generated = resp.json()["generated_text"]

    # Extract only the first JSON block
    json_str = extract_first_json(generated)
    return json.loads(json_str)
