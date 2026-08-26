// StudyMate AI — AI Coach: topic-scoped tutor chat with voice input/output

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("coach-form");
  const input = document.getElementById("coach-input");
  const thread = document.getElementById("coach-thread");
  const micBtn = document.getElementById("mic-btn");
  const voiceReplyToggle = document.getElementById("voice-reply-toggle");
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

  function speak(text) {
    if (!voiceReplyToggle || !voiceReplyToggle.checked) return;
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text.replace(/\*\*/g, ""));
    utter.rate = 1.0;
    micBtn.classList.add("speaking");
    utter.onend = () => micBtn.classList.remove("speaking");
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
      speak(data.reply);
    } catch (err) {
      typing.remove();
      bubble("assistant", `⚠️ ${escapeHtml(err.message)}`);
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
  if (SpeechRecognition && micBtn) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    let listening = false;

    micBtn.addEventListener("click", () => {
      if (listening) {
        recognition.stop();
        return;
      }
      recognition.start();
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
    };
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      input.value = transcript;
      sendMessage(transcript);
      input.value = "";
    };
  } else if (micBtn) {
    micBtn.disabled = true;
    micBtn.title = "Voice input isn't supported in this browser";
    micBtn.style.opacity = "0.4";
  }
});
