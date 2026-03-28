import os
from groq import Groq

def call_llm(system_prompt, user_message, max_tokens=1000):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key: return "Error: API Key missing"
    client = Groq(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=max_tokens,
            temperature=0.1
        )
        return str(completion.choices[0].message.content or "")
    except Exception as e:
        return f"LLM Error: {str(e)}"