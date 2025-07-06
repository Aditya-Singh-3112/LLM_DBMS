import requests

LLM_URL = "http://localhost:8080/generate"

def parse_prompt(prompt: str) -> str:
    template = f"""
You are a helpful assistant that converts natural language into valid SQLite SQL queries.

Rules:
- Only output the final SQL query.
- Do not add explanation or multiple choices.
- Use appropriate SQL syntax with correct table and column names.

Examples:

Prompt: Create a table to store users with name, age, and city.
SQL: CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, city TEXT);

Prompt: Insert a new user named Aditya, age 23, from Bhopal.
SQL: INSERT INTO users (name, age, city) VALUES ('Aditya', 23, 'Bhopal');

Prompt: Show all users older than 20.
SQL: SELECT * FROM users WHERE age > 20;

Prompt: {prompt}
SQL:
    """.strip()

    response = requests.post(LLM_URL, json={"inputs": template})
    sql = response.json()["generated_text"]
    return extract_sql(sql)

def extract_sql(text: str) -> str:
    lines = text.strip().splitlines()
    for line in lines:
        if line.strip().upper().startswith(("SELECT", "INSERT", "CREATE", "UPDATE", "DELETE", "DROP", "ALTER")):
            return line.strip().rstrip(";") + ";"
    raise ValueError("No valid SQL found in LLM output.")
