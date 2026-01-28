#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from src.llm_client import LLMClient
print("Creating client...")
client = LLMClient(model="gpt-4o-mini")
print("Calling API...")
response = client.generate_code("Write a Python function that returns 42", temperature=0.5)
print("Success! Response length:", len(response))
print("Response:", response[:200])
