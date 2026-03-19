"""
ZenPlace — Python/Flask backend
================================
Responsibilities:
  - Serve the frontend static files
  - Proxy Gemini API calls (key never reaches the browser)
  - Persist every conversation turn to PostgreSQL (Supabase)
  - Expose REST endpoints for chat history

Routes:
  POST /api/chat              - send a message, get AI reply, save both to DB
  GET  /api/history           - list all sessions (id, created_at, preview)
  GET  /api/history/<session> - full message log for one session
  DELETE /api/history/<session> - delete a session and all its messages
"""

import os
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import google.genai as genai
from google.genai import types
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# -- Config ---------------------------------------------------------------
load_dotenv()

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = BASE_DIR
GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

SYSTEM_PROMPT = """You are a gentle and empathetic emotional support assistant for ZenPlace,
a virtual wellness space. Your role is to listen attentively, welcome people's feelings
without judgment, and offer thoughtful reflections. Always respond in English.

Important guidelines:
- Be warm, present, and human in your writing
- Ask open-ended questions to help the person express themselves
- Validate feelings without minimizing them
- Suggest wellness practices (breathing, meditation, movement) when appropriate
- ALWAYS remind users that you are a complementary support tool, not a substitute for mental health professionals
- If you sense signs of serious crisis or risk, gently encourage the person to seek professional help (988 Suicide & Crisis Lifeline: call or text 988)
- Keep responses appropriately sized - not too short, not excessively long"""

# -- App ------------------------------------------------------------------
app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

gemini_client = genai.Client(api_key=GEMINI_KEY)

# -- Database -------------------------------------------------------------

@contextmanager
def get_db():
    """Yield a psycopg2 connection and auto-commit/rollback."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist yet."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id         TEXT PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id         SERIAL PRIMARY KEY,
                    session_id TEXT        NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    role       TEXT        NOT NULL CHECK(role IN ('user', 'assistant')),
                    content    TEXT        NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id);
            """)


# -- Helpers --------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_or_create_session(session_id: str | None) -> str:
    """Return an existing session id or create a new one."""
    with get_db() as conn:
        with conn.cursor() as cur:
            if session_id:
                cur.execute("SELECT id FROM sessions WHERE id = %s", (session_id,))
                if cur.fetchone():
                    return session_id

            new_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO sessions (id, created_at, updated_at) VALUES (%s, %s, %s)",
                (new_id, now_iso(), now_iso()),
            )
            return new_id


def load_history(session_id: str) -> list[types.Content]:
    """Load all messages for a session as Gemini Content objects."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT role, content FROM messages WHERE session_id = %s ORDER BY id",
                (session_id,),
            )
            rows = cur.fetchall()
    return [
        types.Content(
            role="model" if row["role"] == "assistant" else "user",
            parts=[types.Part(text=row["content"])],
        )
        for row in rows
    ]


def save_message(session_id: str, role: str, content: str) -> None:
    """Persist a single message and bump the session's updated_at."""
    ts = now_iso()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
                (session_id, role, content, ts),
            )
            cur.execute(
                "UPDATE sessions SET updated_at = %s WHERE id = %s",
                (ts, session_id),
            )


# -- API Routes -----------------------------------------------------------

@app.post("/api/chat")
def chat():
    body       = request.get_json(silent=True) or {}
    user_text  = (body.get("message") or "").strip()
    session_id = body.get("session_id")

    if not user_text:
        return jsonify(error="message is required"), 400

    session_id = get_or_create_session(session_id)
    save_message(session_id, "user", user_text)

    try:
        history_for_gemini = load_history(session_id)[:-1]
        chat_session = gemini_client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            history=history_for_gemini,
        )
        response = chat_session.send_message(user_text)
        ai_text  = response.text
    except Exception as exc:
        import traceback
    print(f"CHAT ERROR: {exc}", flush=True)
    traceback.print_exc()
    return jsonify(error=str(exc)), 502

    save_message(session_id, "assistant", ai_text)
    return jsonify(reply=ai_text, session_id=session_id)

    print(f"Session: {session_id}, loading history...", flush=True)
    history_for_gemini = load_history(session_id)
    print(f"History length: {len(history_for_gemini)}", flush=True)
    history_for_gemini = history_for_gemini[:-1]


@app.get("/api/history")
def list_sessions():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    s.id,
                    s.created_at,
                    s.updated_at,
                    (
                        SELECT content FROM messages
                        WHERE session_id = s.id AND role = 'user'
                        ORDER BY id LIMIT 1
                    ) AS preview
                FROM sessions s
                ORDER BY s.updated_at DESC
            """)
            rows = cur.fetchall()

    return jsonify([
        {
            "id":         row["id"],
            "created_at": str(row["created_at"]),
            "updated_at": str(row["updated_at"]),
            "preview":    (row["preview"] or "")[:80],
        }
        for row in rows
    ])


@app.get("/api/history/<session_id>")
def get_session(session_id: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sessions WHERE id = %s", (session_id,))
            if not cur.fetchone():
                return jsonify(error="Session not found"), 404

            cur.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id = %s ORDER BY id",
                (session_id,),
            )
            rows = cur.fetchall()

    return jsonify(
        session_id=session_id,
        messages=[{**row, "created_at": str(row["created_at"])} for row in rows],
    )


@app.delete("/api/history/<session_id>")
def delete_session(session_id: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
            if cur.rowcount == 0:
                return jsonify(error="Session not found"), 404
    return jsonify(deleted=True)


# -- Frontend static files ------------------------------------------------

@app.get("/")
@app.get("/<path:filename>")
def serve_frontend(filename="index.html"):
    return send_from_directory(FRONTEND_DIR, filename)


# -- Entry point ----------------------------------------------------------

if __name__ == "__main__":
    init_db()
    print("ZenPlace backend running at http://localhost:5000")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)