from config import OPENAI_API_KEY, MODEL, TEMPERATURE
import openai

# For openai>=1.0.0
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def query_llm(prompt: str, model: str, temperature: float) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def call_llm(contract):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": contract["system_message"]},
            {"role": "user", "content": contract["user_prompt"]},
        ],
    )
    return response.choices[0].message.content.strip()

def call_llm_simple(prompt: str) -> str:
    """Call LLM with a simple prompt without contract structure"""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content.strip()
