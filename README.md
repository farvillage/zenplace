# ZenPlace

A virtual wellness space for venting and exploring mindfulness practices.  
Built with HTML/CSS/JS (frontend) + Python/Flask + SQLite (backend).

---

## Project structure

```
zenplace/
├── index.html          # Main page (hero + chat + practices)
├── about.html          # About the project + team
├── style.css           # Unified stylesheet
├── chat.js             # Frontend chat logic
│
└── backend/
    ├── app.py          # Flask server + SQLite logic
    ├── requirements.txt
    ├── .env.example    # Copy to .env and add your API key
    └── zenplace.db     # Created automatically on first run
```

---

## Setup

### 1. Clone / download the project

### 2. Create the `.env` file

```bash
cd backend
cp .env.example .env
```

Open `.env` and set your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run the server

```bash
python app.py
```

Open your browser at **http://localhost:5000**.

---

## API endpoints

| Method   | Path                        | Description                          |
|----------|-----------------------------|--------------------------------------|
| `POST`   | `/api/chat`                 | Send a message, receive AI reply     |
| `GET`    | `/api/history`              | List all chat sessions               |
| `GET`    | `/api/history/<session_id>` | Get all messages in a session        |
| `DELETE` | `/api/history/<session_id>` | Delete a session and its messages    |

### `POST /api/chat` — request body

```json
{
  "message": "I've been feeling really anxious lately.",
  "session_id": null
}
```

Pass `null` (or omit `session_id`) to start a new session.  
Pass the returned `session_id` in subsequent requests to continue the same conversation.

### `POST /api/chat` — response

```json
{
  "reply": "I hear you. Can you tell me more about what's been triggering that anxiety?",
  "session_id": "a3f2b1c4-..."
}
```

---

## Important

ZenPlace is a **complementary emotional support tool** and does not replace
qualified mental health professionals. In a crisis, call or text **988**
(Suicide & Crisis Lifeline, free, 24/7).
