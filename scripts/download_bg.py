"""Download Krishna-Arjuna background image for the UI."""
import urllib.request, os

urls = [
    ("https://upload.wikimedia.org/wikipedia/commons/a/a5/Krishna_and_Arjuna.jpg", "src/static/krishna_arjuna.jpg"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Krishna_and_Arjuna.jpg/800px-Krishna_and_Arjuna.jpg", "src/static/krishna_arjuna.jpg"),
]

headers = {
    "User-Agent": "GuideMeKrishna/1.0 (educational project; https://github.com) Python-urllib/3"
}

for url, dest in urls:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        print(f"Downloaded {len(data)} bytes -> {dest}")
        break
    except Exception as e:
        print(f"Failed {url}: {e}")
