import urllib.request, json

data = json.dumps({
    "query": "What does the Gita say about fear and courage?",
    "language": "en",
    "topK": 2
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:8000/query",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = json.loads(urllib.request.urlopen(req).read())
print("Confidence:", resp["confidence"])
for v in resp["citedVerses"]:
    print("BG", v["verseId"], ":", v["translation"][:120])
