/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Sidebar

   One definition of the navigation, shared by index.html and
   ocr.html. These two pages used to each carry their own copy of
   the markup, which is why the menu changed when you opened the
   OCR page: the copies had drifted apart.

   index.html switches sections in place, so its items carry
   data-section and app.js intercepts the click. ocr.html is a
   separate document, so the same items become plain links back to
   index.html. Order and labels come from this file either way.

   Must load BEFORE app.js — app.js binds its click handlers to
   .sidebar-item at parse time, so the items have to exist first.
═══════════════════════════════════════════════════════════ */

// Written for older clinic staff: plain words, the everyday job as
// numbered steps, and no codes. `step` shows a big number instead of an icon.
const PCA_SIDEBAR = [
  { label: 'Start here', items: [
    { key: 'dashboard', icon: 'bi-house-door-fill', text: 'Home' },
  ]},
  { label: 'Step by step', items: [
    { key: 'ocr',        step: 1, text: 'Read a logbook page', href: 'ocr.html' },
    { key: 'patient',    step: 2, text: 'Patient details' },
    { key: 'validation', step: 3, text: 'Check for missing information' },
  ]},
  { label: 'The forms (open, check, print)', items: [
    { key: 'csf',  icon: 'bi-file-earmark-text', text: 'CSF',   badge: 'CSF' },
    { key: 'cf1',  icon: 'bi-file-earmark-text', text: 'CF1', badge: 'CF1' },
    { key: 'cf2',  icon: 'bi-file-earmark-text', text: 'CF2', badge: 'CF2' },
    { key: 'cf4',  icon: 'bi-file-earmark-text', text: 'CF4', badge: 'CF4' },
    { key: 'pmrf', icon: 'bi-file-earmark-text', text: 'PMRF',  badge: 'PMRF' },
  ]},
  { label: 'Clinic', items: [
    { key: 'settings',   icon: 'bi-hospital',        text: 'Clinic Details', role: 'admin' },
    // No "Set up a logbook" item: every scan's columns are checked as
    // step 2 of "Read a logbook page" (Ocr_module/templates/review.html).
  ]},
];

const PCASidebar = {
  /** page: 'app' (index.html) or 'ocr' (ocr.html). active: item key. */
  render(opts) {
    const nav = document.getElementById('sidebarNav');
    if (!nav) return;
    const page = (opts && opts.page) || 'app';
    const active = (opts && opts.active) || '';

    nav.innerHTML = PCA_SIDEBAR.map((group, gi) => {
      const label = `<div class="sidebar-section-label${gi ? ' mt-3' : ''}">${group.label}</div>`;
      const items = group.items.map(it => {
        // On the OCR page every item except the OCR one is a link home;
        // on index.html they are section switches handled by app.js.
        const isLink = it.href || page !== 'app';
        // From the OCR page, link straight to the section (index.html#patient)
        // so "Patient details" opens Patient details, not Home.
        const href = it.href || (page === 'app' ? '#' : `index.html#${it.key}`);
        const section = (isLink && it.href) || page !== 'app'
          ? '' : ` data-section="${it.key}"`;
        const gate = it.role ? ` data-requires-role="${it.role}" hidden` : '';
        const badge = it.badge ? `<span class="sidebar-badge">${it.badge}</span>` : '';
        const on = it.key === active ? ' active' : '';
        const mark = it.step
          ? `<span class="sidebar-step" aria-hidden="true">${it.step}</span>`
          : `<i class="bi ${it.icon}"></i>`;
        return `<a href="${href}" class="sidebar-item${on}"${section}${gate}>` +
               `${mark}<span>${it.text}</span>${badge}</a>`;
      }).join('');
      return label + items;
    }).join('');
    this.fold();
  },

  /** On wide screens the menu folds itself shut once a page is picked, and
      stays shut on the next page. The mouse coming over it opens it again
      (.peek, style.css), and it stays open until a click outside it - not
      merely the mouse leaving. Only classes change here: app.js and ocr.js
      still handle the clicks and the toggle button. */
  fold() {
    const sb = document.getElementById('sidebar');
    if (!sb || sb.dataset.fold) return;
    sb.dataset.fold = '1';
    const KEY = 'pca_sidebar_collapsed';
    const wide = () => window.innerWidth >= 768;
    let saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* private window */ }
    if (saved === '1' && wide()) sb.classList.add('collapsed');

    // Just after a page is picked the mouse is still over the menu; it only
    // opens on hover again once the mouse has been off it.
    let armed = false;
    sb.addEventListener('mouseleave', () => { armed = true; });
    sb.addEventListener('mouseenter', () => {
      if (armed && wide() && sb.classList.contains('collapsed')) sb.classList.add('peek');
    });
    sb.addEventListener('click', e => {
      if (!wide() || !e.target.closest('.sidebar-item')) return;
      sb.classList.add('collapsed');
      sb.classList.remove('peek');
      armed = false;
    });
    document.addEventListener('click', e => {
      if (!sb.contains(e.target)) sb.classList.remove('peek');
    });
    new MutationObserver(() => {
      if (!wide()) return;
      try { localStorage.setItem(KEY, sb.classList.contains('collapsed') ? '1' : '0'); } catch (e) { /* not kept */ }
    }).observe(sb, { attributes: true, attributeFilter: ['class'] });
  },
};
