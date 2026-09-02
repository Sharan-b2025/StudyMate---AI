// Shared front-end utilities for StudyMate AI

function autoDismissFlashes() {
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s, transform .4s";
      el.style.opacity = "0";
      el.style.transform = "translateX(20px)";
      setTimeout(() => el.remove(), 400);
    }, 4200);
  });
}

async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data || {}),
  });
  let payload = {};
  try { payload = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) throw new Error(payload.error || `Request failed (${res.status})`);
  return payload;
}

// ---- Skeleton loaders & retry banners, shared across pages that make
// AI calls (materials, quiz, planner). Keeps "waiting on AI" states
// consistent instead of a blank screen or a stuck button label. ----
function showSkeleton(el, lines = 4) {
  if (!el) return;
  el.innerHTML = Array.from({ length: lines }, () => '<div class="skeleton-line"></div>').join("");
}

function showRetryBanner(el, message, retryFn) {
  if (!el) return;
  el.innerHTML = `<div class="retry-banner">
    <span>⚠️ ${message}</span>
    <button type="button" class="btn btn-ghost btn-sm" data-retry-btn>Retry</button>
  </div>`;
  el.querySelector("[data-retry-btn]").addEventListener("click", retryFn);
}

document.addEventListener("DOMContentLoaded", () => {
  autoDismissFlashes();

  // File upload drag & drop enhancement
  const dropzone = document.querySelector("[data-dropzone]");
  if (dropzone) {
    const input = dropzone.querySelector("input[type=file]");
    const label = dropzone.querySelector("[data-filename]");

    ["dragenter", "dragover"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      })
    );
    dropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer.files.length && input) {
        input.files = e.dataTransfer.files;
        if (label) label.textContent = e.dataTransfer.files[0].name;
      }
    });
    if (input) {
      input.addEventListener("change", () => {
        if (label && input.files.length) label.textContent = input.files[0].name;
      });
    }
  }

  // Topic status quick-toggle buttons
  document.querySelectorAll("[data-topic-status]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const topicId = btn.dataset.topicId;
      const status = btn.dataset.topicStatus;
      try {
        await postJSON(`/planner/topic/${topicId}/status`, { status });
        window.location.reload();
      } catch (err) {
        alert(err.message);
      }
    });
  });

  // Plan item checkbox toggle
  document.querySelectorAll("[data-plan-item-toggle]").forEach((cb) => {
    cb.addEventListener("change", async () => {
      const itemId = cb.dataset.planItemToggle;
      try {
        await postJSON(`/planner/plan-item/${itemId}/toggle`, {});
        const row = cb.closest(".plan-item-row");
        if (row) row.classList.toggle("done", cb.checked);
      } catch (err) {
        alert(err.message);
        cb.checked = !cb.checked;
      }
    });
  });
});
