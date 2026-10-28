/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Colour-blind friendly colours (css/colorblind.css)

   A setting for whoever uses this computer, not for the claim: it is kept
   in this browser, so each PC can have it on or off. Loaded in <head> so
   the page never flashes the usual colours first, and it follows the
   setting when it changes in another tab or in the page around it (the
   Logbook Reader and logbook setup are shown inside PClaimAssist).

   Clinic Details has the tick: <input type="checkbox" data-colorblind-toggle>.
═══════════════════════════════════════════════════════════ */
(function () {
  const KEY = 'pclaimassist.colorBlind';

  function isOn() {
    try { return localStorage.getItem(KEY) === '1'; } catch (_) { return false; }
  }

  function apply(on) {
    document.documentElement.classList.toggle('cb-mode', !!on);
    document.querySelectorAll('[data-colorblind-toggle]').forEach(box => { box.checked = !!on; });
  }

  function set(on) {
    try {
      if (on) localStorage.setItem(KEY, '1'); else localStorage.removeItem(KEY);
    } catch (_) { /* storage off: on for this page only */ }
    apply(on);
    // Pages shown inside this one (same browser storage) follow at once.
    document.querySelectorAll('iframe').forEach(frame => {
      try { frame.contentDocument.documentElement.classList.toggle('cb-mode', !!on); } catch (_) {}
    });
  }

  apply(isOn());
  window.addEventListener('storage', e => { if (e.key === KEY) apply(isOn()); });
  document.addEventListener('DOMContentLoaded', () => apply(isOn()));
  document.addEventListener('change', e => {
    if (e.target.matches && e.target.matches('[data-colorblind-toggle]')) set(e.target.checked);
  });

  window.PCAColorBlind = { isOn, set };
})();
