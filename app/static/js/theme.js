// StudyMate AI — Dark/Light theme toggle

document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("theme-toggle-btn");
  const iconDark = document.getElementById("theme-icon-dark");
  const iconLight = document.getElementById("theme-icon-light");
  const label = document.getElementById("theme-label");
  if (!toggleBtn) return;

  function applyThemeUI(theme) {
    const isLight = theme === "light";
    if (iconDark) iconDark.style.display = isLight ? "none" : "block";
    if (iconLight) iconLight.style.display = isLight ? "block" : "none";
    if (label) label.textContent = isLight ? "Light mode" : "Dark mode";
  }

  const current = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  applyThemeUI(current);

  toggleBtn.addEventListener("click", () => {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    const next = isLight ? "dark" : "light";
    if (next === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    localStorage.setItem("studymate_theme", next);
    applyThemeUI(next);
  });
});
