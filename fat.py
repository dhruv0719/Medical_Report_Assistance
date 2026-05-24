import requests

url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

response = requests.get(url)

print(response.status_code)
print(response.text[:200])