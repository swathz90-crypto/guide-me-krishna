#!/usr/bin/env python3
"""
Download the real Bhagavad Gita corpus from github.com/gita/gita
and build a properly formatted JSON corpus for Geetopadesha.

Uses:
  - verse.json  → Sanskrit text, transliteration
  - translation.json → English translations (Swami Sivananda, author_id=16)
"""
import json
import os
import urllib.request

VERSE_URL = "https://raw.githubusercontent.com/gita/gita/master/data/verse.json"
TRANSLATION_URL = "https://raw.githubusercontent.com/gita/gita/master/data/translation.json"

# Prefer Swami Sivananda (16) → fallback to Swami Gambirananda (19) → any English
PREFERRED_AUTHORS = [16, 19, 18, 20, 21]


def fetch_json(url: str):
    print(f"Fetching {url} ...")
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read().decode())


def main():
    verses = fetch_json(VERSE_URL)
    translations = fetch_json(TRANSLATION_URL)

    # Build a map: verse_id → {author_id: description}
    trans_map: dict[int, dict[int, str]] = {}
    for t in translations:
        if t.get("lang") != "english":
            continue
        vid = t["verse_id"]
        aid = t["author_id"]
        trans_map.setdefault(vid, {})[aid] = t["description"].strip()

    corpus = []
    missing = 0

    for v in verses:
        vid = v["id"]
        chapter = v["chapter_number"]
        verse_num = v["verse_number"]
        verse_id = f"{chapter}.{verse_num}"

        # Pick best available English translation
        translation = ""
        author_trans = trans_map.get(vid, {})
        for aid in PREFERRED_AUTHORS:
            if aid in author_trans:
                translation = author_trans[aid]
                break
        if not translation and author_trans:
            translation = next(iter(author_trans.values()))
        if not translation:
            missing += 1
            translation = f"Verse {verse_id} of the Bhagavad Gita."

        # Clean up Sanskrit text (remove verse number suffix like "।।1.1।।")
        sanskrit = v.get("text", "").strip()

        corpus.append({
            "verseId": verse_id,
            "chapter": chapter,
            "verse": verse_num,
            "sanskrit": sanskrit,
            "transliteration": v.get("transliteration", "").strip(),
            "translation": translation,
            "commentary": v.get("word_meanings", "").strip(),
        })

    print(f"Total verses: {len(corpus)}, missing translations: {missing}")

    os.makedirs("data", exist_ok=True)
    out_path = "data/gita_corpus.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    print(f"Saved → {out_path}")


if __name__ == "__main__":
    main()
