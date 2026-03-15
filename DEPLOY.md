# Deploy Guide Me Krishna to Play Store

## Step 1 — Push to GitHub

Open a terminal in this folder and run:

```bash
git init
git add .
git commit -m "Guide Me Krishna — initial release"
```

Then go to github.com → New repository → name it `guide-me-krishna` → copy the push commands shown and run them.

---

## Step 2 — Deploy to Render

1. Go to https://render.com and sign up (free)
2. Click **New → Web Service**
3. Connect your GitHub account and select the `guide-me-krishna` repo
4. Render auto-detects the `Dockerfile` — no changes needed
5. Under **Environment Variables**, add:
   - `GROQ_API_KEY` = your actual Groq API key
6. Click **Deploy**
7. Wait ~5 minutes — you'll get a URL like `https://guide-me-krishna.onrender.com`

---

## Step 3 — Generate Play Store bundle via PWABuilder

1. Go to https://www.pwabuilder.com
2. Enter your Render URL (e.g. `https://guide-me-krishna.onrender.com`)
3. Click **Start** — it will score your PWA (should be 100% with our manifest)
4. Click **Package for stores → Android**
5. Fill in:
   - App name: `Guide Me Krishna`
   - Package ID: `com.guidemekrishna.app` (or your own)
   - Version: `1.0.0`
6. Click **Generate** — downloads a zip with your signed `.aab` and keystore
7. **Save the keystore file safely** — you need it for every future update

---

## Step 4 — Upload to Google Play Store

1. Go to https://play.google.com/console
2. Create a developer account ($25 one-time fee)
3. Click **Create app**
4. Fill in app details, screenshots, description
5. Go to **Production → Releases → Create release**
6. Upload the `.aab` file from Step 3
7. Submit for review (usually 1-3 days)

---

## Notes

- The free Render tier sleeps after 15 min of inactivity — first load after sleep takes ~30s
- Upgrade to Render's $7/month plan to keep it always-on
- Your GROQ_API_KEY is never exposed to users — it stays server-side
