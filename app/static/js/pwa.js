// StudyMate AI — PWA registration

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Registration can fail in some dev/proxy setups — non-fatal.
    });
  });
}

// Optional "Install app" prompt — captured here so a future UI element
// (e.g. a button in settings) could trigger it with deferredInstallPrompt.prompt().
let deferredInstallPrompt = null;
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
});
