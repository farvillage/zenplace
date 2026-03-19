/**
 * ZenPlace — Vent chat
 *
 * - Modern chat UI (message bubbles)
 * - Calls the local Flask backend (/api/chat) — API key never touches the browser
 * - Session ID stored in sessionStorage so the conversation persists on refresh
 *   but starts fresh when the tab is closed
 * - Friendly error handling
 * - Auto-resize textarea
 */

// ── DOM Elements ──────────────────────────────────────────────────
const chatWindow    = document.getElementById('chatWindow');
const inputQuestion = document.getElementById('inputQuestion');
const sendBtn       = document.getElementById('sendBtn');

// ── Session state ─────────────────────────────────────────────────
// Persist the session_id for the tab's lifetime so the backend can
// look up the full conversation history from SQLite on every request.
let sessionId = sessionStorage.getItem('zenplace_session_id') || null;
let isLoading = false;

// ── On load: restore previous messages from the backend ──────────
async function restoreSession() {
  if (!sessionId) return;

  try {
    const res = await fetch(`/api/history/${sessionId}`);
    if (!res.ok) {
      // Session no longer exists on the server — start fresh
      sessionStorage.removeItem('zenplace_session_id');
      sessionId = null;
      return;
    }

    const data = await res.json();
    if (data.messages && data.messages.length > 0) {
      data.messages.forEach(msg => appendMessage(msg.content, msg.role));
    }
  } catch {
    // Network error — silently start fresh
    sessionId = null;
  }
}

// ── UI Functions ──────────────────────────────────────────────────

/** Creates and appends a message bubble to the chat window */
function appendMessage(content, role) {
  document.getElementById('emptyState')?.remove();

  const message = document.createElement('div');
  message.className = `message message--${role === 'user' ? 'user' : 'ai'}`;

  const avatar = document.createElement('div');
  avatar.className = 'message__avatar';
  avatar.textContent = role === 'user' ? '🙂' : '🌿';

  const bubble = document.createElement('div');
  bubble.className = 'message__bubble';
  bubble.textContent = content;

  message.appendChild(avatar);
  message.appendChild(bubble);
  chatWindow.appendChild(message);
  scrollToBottom();
}

/** Shows the animated "typing..." indicator */
function showTypingIndicator() {
  const wrapper = document.createElement('div');
  wrapper.className = 'message message--ai';
  wrapper.id = 'typingIndicator';

  const avatar = document.createElement('div');
  avatar.className = 'message__avatar';
  avatar.textContent = '🌿';

  const indicator = document.createElement('div');
  indicator.className = 'typing-indicator';
  indicator.innerHTML = '<span></span><span></span><span></span>';

  wrapper.appendChild(avatar);
  wrapper.appendChild(indicator);
  chatWindow.appendChild(wrapper);
  scrollToBottom();
}

/** Removes the "typing..." indicator */
function removeTypingIndicator() {
  document.getElementById('typingIndicator')?.remove();
}

/** Scrolls the chat window to the latest message */
function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

/** Locks/unlocks the input while the backend is responding */
function setLoading(state) {
  isLoading = state;
  sendBtn.disabled = state;
  inputQuestion.disabled = state;
  if (!state) inputQuestion.focus();
}

// ── Send logic ────────────────────────────────────────────────────

async function sendMessage() {
  const text = inputQuestion.value.trim();
  if (!text || isLoading) return;

  appendMessage(text, 'user');

  inputQuestion.value = '';
  inputQuestion.style.height = 'auto';
  setLoading(true);
  showTypingIndicator();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message:    text,
        session_id: sessionId,   // null on first message → backend creates a new session
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err?.error || `Server error ${response.status}`);
    }

    const data = await response.json();

    // Save the session_id the backend assigned (only needed once)
    if (data.session_id && data.session_id !== sessionId) {
      sessionId = data.session_id;
      sessionStorage.setItem('zenplace_session_id', sessionId);
    }

    removeTypingIndicator();
    appendMessage(data.reply, 'assistant');

  } catch (error) {
    console.error('Chat error:', error);
    removeTypingIndicator();
    appendMessage(
      "Something went wrong while trying to respond. Check your connection or try again in a moment. 🌿",
      'assistant'
    );
  } finally {
    setLoading(false);
  }
}

// ── Event Listeners ───────────────────────────────────────────────

// Send on Enter (Shift+Enter inserts a newline)
inputQuestion.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener('click', sendMessage);

// Auto-resize textarea as the user types
inputQuestion.addEventListener('input', () => {
  inputQuestion.style.height = 'auto';
  inputQuestion.style.height = Math.min(inputQuestion.scrollHeight, 140) + 'px';
});

// ── Init ──────────────────────────────────────────────────────────
restoreSession();
