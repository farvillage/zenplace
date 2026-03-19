# ZenPlace

A virtual wellness space where you can vent your feelings to an AI that listens without judgment, and explore mindfulness practices like Zazen, Yoga, Lo-Fi, and ASMR.

---

## Tech stack

| Layer    | Technology |
|----------|------------|
| Frontend | HTML, CSS, JavaScript |
| Backend  | Python + Flask |
| AI       | Google Gemini 2.5 Flash |
| Database | PostgreSQL (Supabase) |
| Hosting  | Render |

---

## Project structure

```
zenplace/
├── index.html        # main page — hero, chat, practices
├── about.html        # about the project + team
├── style.css         # all styling
├── chat.js           # frontend chat logic
├── app.py            # Flask server + all backend logic
├── requirements.txt  # Python dependencies
├── render.yaml       # Render deploy config
├── .env.example      # template for secret keys
└── .gitignore
```

---

## Running locally

**1. Clone the repo**
```bash
git clone https://github.com/farvillage/zenplace.git
cd zenplace
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up your keys**
```bash
cp .env.example .env
```
Open `.env` and fill in:
```
GEMINI_API_KEY=your_key_here
DATABASE_URL=postgresql://...
```

- Get a free Gemini key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- Get a free PostgreSQL database at [supabase.com](https://supabase.com) → Settings → Database → Connection string

**4. Start the server**
```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

---

## Deploying to Render

1. Push the project to GitHub
2. Go to [render.com](https://render.com) → New → Web Service → connect your repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python app.py`
5. Add environment variables:
   - `GEMINI_API_KEY`
   - `DATABASE_URL`
6. Deploy — you'll get a public URL like `https://zenplace.onrender.com`

> Never share or commit your API keys. If a key gets exposed, revoke it immediately and create a new one.

---

## API endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/api/chat` | Send a message, get AI reply |
| `GET` | `/api/history` | List all chat sessions |
| `GET` | `/api/history/<id>` | Get all messages in a session |
| `DELETE` | `/api/history/<id>` | Delete a session |

---

## Important

ZenPlace is a **complementary emotional support tool** and does not replace qualified mental health professionals. In a crisis, call or text **988** (free, 24/7).
