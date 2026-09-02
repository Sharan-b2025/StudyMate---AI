// StudyMate AI — AI Coach: topic-scoped tutor chat with voice input/output

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("coach-form");
  const input = document.getElementById("coach-input");
  const thread = document.getElementById("coach-thread");
  const micBtn = document.getElementById("mic-btn");
  const voiceReplyToggle = document.getElementById("voice-reply-toggle");
  const autoListenToggle = document.getElementById("auto-listen-toggle");
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

  function errorBubbleWithRetry(message, retryFn) {
    const wrap = document.createElement("div");
    wrap.className = "chat-bubble assistant";
    wrap.innerHTML = `<div class="bubble-inner">⚠️ ${escapeHtml(message)}<br>
      <button type="button" class="btn btn-ghost btn-sm mt-1" style="font-size:12px;">Retry</button></div>`;
    wrap.querySelector("button").addEventListener("click", () => {
      wrap.remove();
      retryFn();
    });
    thread.appendChild(wrap);
    thread.scrollTop = thread.scrollHeight;
    return wrap;
  }

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

  function speak(text, onDone) {
    if (!voiceReplyToggle || !voiceReplyToggle.checked) {
      if (onDone) onDone();
      return;
    }
    if (!("speechSynthesis" in window)) {
      if (onDone) onDone();
      return;
    }
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text.replace(/\*\*/g, ""));
    utter.rate = 1.0;
    micBtn.classList.add("speaking");
    utter.onend = () => {
      micBtn.classList.remove("speaking");
      if (onDone) onDone();
    };
    window.speechSynthesis.speak(utter);
  }

  async function sendMessage(message) {
    if (!message) return;
    bubble("user", escapeHtml(message));
    const typing = typingBubble();

    try {
      const res = await fetch(`/coach/${COACH_TOPIC_ID}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      typing.remove();
      if (!res.ok) throw new Error(data.error || "Something went wrong");
      bubble("assistant", renderMarkdownish(data.reply));
      speak(data.reply, () => {
        // Auto-listen: once the reply finishes (or voice reply is off),
        // automatically reopen the mic for a hands-free conversation loop.
        if (autoListenToggle && autoListenToggle.checked) {
          startListening();
        }
      });
    } catch (err) {
      typing.remove();
      errorBubbleWithRetry(err.message, () => sendMessage(message));
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    input.disabled = true;
    await sendMessage(message);
    input.disabled = false;
    input.focus();
  });

  // ---- Voice input (Web Speech API) ----
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let listening = false;

  function startListening() {
    if (!recognition || listening) return;
    try {
      recognition.start();
    } catch (e) {
      // recognition already starting/running — ignore
    }
  }

  if (SpeechRecognition && micBtn) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    micBtn.addEventListener("click", () => {
      if (listening) {
        recognition.stop();
        return;
      }
      startListening();
    });

    recognition.onstart = () => {
      listening = true;
      micBtn.classList.add("active");
    };
    recognition.onend = () => {
      listening = false;
      micBtn.classList.remove("active");
    };
    recognition.onerror = () => {
      listening = false;
      micBtn.classList.remove("active");
      // Auto-listen shouldn't retry forever on repeated errors (e.g. mic
      // permission denied) — user can always tap the mic manually again.
      if (autoListenToggle) autoListenToggle.checked = false;
    };
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      sendMessage(transcript);
    };
  } else if (micBtn) {
    micBtn.disabled = true;
    micBtn.title = "Voice input isn't supported in this browser";
    micBtn.style.opacity = "0.4";
    if (autoListenToggle) {
      autoListenToggle.disabled = true;
      autoListenToggle.title = "Voice input isn't supported in this browser";
    }
  }
});
