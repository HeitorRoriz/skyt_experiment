from .config import OPENAI_API_KEY, MODEL, TEMPERATURE
from typing import Optional
from openai import OpenAI
_client = None
def _get_client():
    global _client
    if _client is None:
        if not OPENAI_API_KEY: raise RuntimeError("OPENAI_API_KEY not set")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client
def call_model(prompt: str, model: Optional[str]=None, temperature: Optional[float]=None) -> str:
    client = _get_client()
    m = model or MODEL
    t = TEMPERATURE if temperature is None else temperature
    resp = client.chat.completions.create(model=m, temperature=t, messages=[{"role":"user","content":prompt}])
    return (resp.choices[0].message.content or "").strip()
