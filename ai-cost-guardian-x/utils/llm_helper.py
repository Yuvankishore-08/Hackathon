import anthropic
import streamlit as st


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 1500) -> str:
    api_key = st.session_state.get("anthropic_api_key", "")
    if not api_key:
        return "⚠️ No API key provided. Please enter your Anthropic API key in the sidebar."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return message.content[0].text
    except Exception as e:
        return f"⚠️ LLM Error: {str(e)}"