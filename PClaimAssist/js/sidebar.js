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

const PCA_SIDEBAR = [
  { label: 'Overview', items: [
    { key: 'dashboard', icon: 'bi-grid-1x2', text: 'Dashboard' },
  ]},
  { label: 'Data Entry', items: [
    { key: 'patient', icon: 'bi-person-vcard', text: 'Patient Information', badge: 'Step 1' },
  ]},
  { label: 'OCR', items: [
    { key: 'ocr', icon: 'bi-camera', text: 'Read Logbook Scan', href: 'ocr.html' },
  ]},
  { label: 'Form Previews', items: [
    { key: 'csf',  icon: 'bi-file-earmark-text', text: 'Claim Signature Form', badge: 'CSF' },
    { key: 'cf2',  icon: 'bi-file-earmark-text', text: 'Confinement Form 2',   badge: 'CF2' },
    { key: 'cf3',  icon: 'bi-file-earmark-text', text: 'Confinement Form 3',   badge: 'CF3' },
    { key: 'cf4',  icon: 'bi-file-earmark-text', text: 'Confinement Form 4',   badge: 'CF4' },
    { key: 'pmrf', icon: 'bi-file-earmark-text', text: 'Member Reg. Form',     badge: 'PMRF' },
  ]},
  { label: 'Tools', items: [
    { key: 'validation', icon: 'bi-clipboard-check', text: 'Validation Checker' },
    { key: 'settings',   icon: 'bi-hospital',        text: 'Clinic Details', role: 'admin' },
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
        const href = it.href || (page === 'app' ? '#' : 'index.html');
        const section = (isLink && it.href) || page !== 'app'
          ? '' : ` data-section="${it.key}"`;
        const gate = it.role ? ` data-requires-role="${it.role}" hidden` : '';
        const badge = it.badge ? `<span class="sidebar-badge">${it.badge}</span>` : '';
        const on = it.key === active ? ' active' : '';
        return `<a href="${href}" class="sidebar-item${on}"${section}${gate}>` +
               `<i class="bi ${it.icon}"></i><span>${it.text}</span>${badge}</a>`;
      }).join('');
      return label + items;
    }).join('');
  },
};
