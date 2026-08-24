// StudyMate AI — Chat assistant interface

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const thread = document.getElementById("chat-thread");
  if (!form) return;

  thread.scrollTop = thread.scrollHeight;

  function bubble(role, content) {
    const wrap = document.createElement("div");
    wrap.className = `chat-bubble ${role}`;
    wrap.innerHTML = `<div class="bubble-inner">${content}</div>`;
    thread.appendChild(wrap);
    thread.scrollTop = thread.scrollHeight;
    return wrap;
  }

  function typingBubble() {
    const wrap = document.createElement("div");
    wrap.className = "chat-bubble assistant";
    wrap.innerHTML = `<div class="bubble-inner typing"><span></span><span></span><span></span></div>`;
    thread.appendChild(wrap);
    thread.scrollTop = thread.scrollHeight;
    return wrap;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    input.disabled = true;

    bubble("user", escapeHtml(message));
    const typing = typingBubble();

    try {
      const res = await fetch("/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      typing.remove();
      if (!res.ok) throw new Error(data.error || "Something went wrong");
      bubble("assistant", renderMarkdownish(data.reply));
    } catch (err) {
      typing.remove();
      bubble("assistant", `⚠️ ${escapeHtml(err.message)}`);
    } finally {
      input.disabled = false;
      input.focus();
    }
  });

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function renderMarkdownish(text) {
    let safe = escapeHtml(text);
    safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    safe = safe.replace(/\n\s*[-*]\s+(.*)/g, "<br>• $1");
    safe = safe.replace(/\n/g, "<br>");
    return safe;
  }
});
