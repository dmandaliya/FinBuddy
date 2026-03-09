// chat.js — powers the AI chat page
// Sends messages to Claude via the backend, maintains conversation history

requireAuth();
loadSidebarUser();

// Keep conversation history in memory so Claude has context across messages
let history = [];

function fillPrompt(text) {
  document.getElementById("chat-input").value = text;
  document.getElementById("chat-input").focus();
}

async function sendMessage() {
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  // Clear input and disable send while waiting
  input.value = "";
  const sendBtn = document.getElementById("send-btn");
  sendBtn.disabled = true;

  // Show the user's message in the chat window
  appendBubble(message, "user");

  // Show typing indicator
  const typingId = appendTyping();

  try {
    const data = await apiPost("/api/ai/chat", { message, history });

    // Remove typing indicator
    removeTyping(typingId);

    // Show Claude's response
    appendBubble(data.reply, "bot");

    // Add both sides to history for multi-turn context
    history.push({ role: "user", content: message });
    history.push({ role: "assistant", content: data.reply });

    // Cap history at last 10 exchanges to avoid huge payloads
    if (history.length > 20) history = history.slice(-20);

  } catch (err) {
    removeTyping(typingId);
    appendBubble("Sorry, something went wrong. Is the backend running?", "bot");
  }

  sendBtn.disabled = false;
  input.focus();
  scrollToBottom();
}

function appendBubble(text, role) {
  const messages = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = `chat-bubble bubble-${role === "user" ? "user" : "bot"}`;
  // Basic markdown-ish: make **bold** text bold
  div.innerHTML = text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
  messages.appendChild(div);
  scrollToBottom();
  return div;
}

function appendTyping() {
  const messages = document.getElementById("chat-messages");
  const id = "typing-" + Date.now();
  const div = document.createElement("div");
  div.id = id;
  div.className = "bubble-typing";
  div.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
  `;
  messages.appendChild(div);
  scrollToBottom();
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollToBottom() {
  const messages = document.getElementById("chat-messages");
  messages.scrollTop = messages.scrollHeight;
}
