import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("HUGGINGFACE_API_TOKEN")
print("Loaded token:", repr(token))  # Debug check

url = "https://api-inference.huggingface.co/models/google/flan-t5-small"

headers = {"Authorization": f"Bearer {token}"}
payload = {"inputs": "Give feedback on this volleyball play: serve, pass, set, spike."}

response = requests.post(url, headers=headers, json=payload)
print("Status:", response.status_code)
print("Response:", response.text)
