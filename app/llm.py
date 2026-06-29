import requests

def ask_llm(context, query):
    prompt = f"""
You are a strict AI assistant.

Rules:
- Answer ONLY from the context
- Do NOT guess
- If not found → say "Not found in context"
- Return answer in SHORT bullet points only

Context:
{context}

Question: {query}
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3",
            "prompt": prompt,
            "stream": False,
            "temperature": 0
        }
    )

    return response.json().get("response", "")