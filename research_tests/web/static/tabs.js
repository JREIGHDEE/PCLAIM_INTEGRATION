/* The tab bar above the OCR comparison frame (PClaimAssist/ocr-compare.html,
   in its "RESEARCH TESTS (removable)" block). The first tab is the OCR
   comparison itself, unchanged; the others are the research tests, each
   shown in the same frame. Without the research blueprint (the flag off)
   this file is not served at all and the bar stays hidden. */
(async function () {
  const nav = document.getElementById('researchTabs');
  const frame = document.getElementById('ocrIframe');
  if (!nav || !frame) return;
  let tabs;
  try {
    const res = await fetch('/ocr-testing/research/api/tabs', { credentials: 'same-origin' });
    if (!res.ok) return;
    tabs = (await res.json()).tabs || [];
  } catch (err) { return; }
  const all = [{ key: 'ocr-compare', tab: 'OCR comparison', url: frame.dataset.src || '/ocr-compare' }].concat(tabs);
  const STORE = 'pclaimassist.researchTab';
  const buttons = all.map(t => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = t.tab;
    b.dataset.key = t.key;
    b.addEventListener('click', () => show(t));
    return b;
  });
  function show(t) {
    buttons.forEach(b => b.classList.toggle('active', b.dataset.key === t.key));
    if (frame.getAttribute('src') !== t.url) frame.setAttribute('src', t.url);
    try { sessionStorage.setItem(STORE, t.key); } catch (err) { /* storage off */ }
  }
  const style = document.createElement('style');
  style.textContent = `
    #researchTabs{ display:flex; flex-wrap:wrap; gap:6px; margin:0 0 10px; }
    #researchTabs button{ font:inherit; font-size:.85rem; font-weight:600; border:1.5px solid #CBD5E1; background:#fff;
      color:#1E293B; border-radius:999px; padding:5px 12px; cursor:pointer; }
    #researchTabs button:hover{ border-color:#2563EB; }
    #researchTabs button.active{ background:#2563EB; border-color:#2563EB; color:#fff; }`;
  document.head.appendChild(style);
  nav.replaceChildren(...buttons);
  nav.hidden = false;
  let last = null;
  try { last = sessionStorage.getItem(STORE); } catch (err) { /* storage off */ }
  show(all.find(t => t.key === last) || all[0]);
})();
