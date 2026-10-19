/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Easy-to-use helpers (goes with css/easy.css)

   For older clinic staff who are not computer experts:
     • a yellow "What to do on this page" box on each form page and on
       the Check page, in plain numbered steps;
     • "Back" / "Next part" buttons under each part of Patient details,
       so nobody has to find the small tabs at the top.
   Only adds things to the page - it never changes the form fields or
   how they are saved.
═══════════════════════════════════════════════════════════ */

(function () {
  const FORM_STEPS = [
    'Type the details in the boxes on the <strong>left</strong>.',
    'The form on the <strong>right</strong> fills itself in as you type. Use the arrows above it to see the other pages.',
    'When you are done, press the green <strong>Save as PDF to print</strong> button at the top.',
  ];
  const HOW_TO = {
    csf: FORM_STEPS, cf2: FORM_STEPS, cf4: FORM_STEPS, pmrf: FORM_STEPS,
    validation: [
      'Each form below shows the boxes that are <strong>not filled in yet</strong>, in red.',
      'Open the form from the menu on the left and fill those boxes in.',
      'When a form says <strong>Ready to print</strong>, open it and press <strong>Save as PDF to print</strong>.',
    ],
  };

  function howToBox(steps) {
    const box = document.createElement('div');
    box.className = 'how-to';
    box.innerHTML = '<i class="bi bi-lightbulb-fill" aria-hidden="true"></i><div>' +
      '<strong>What to do on this page:</strong><ol>' +
      steps.map(s => `<li>${s}</li>`).join('') + '</ol></div>';
    return box;
  }

  function addHowToBoxes() {
    Object.entries(HOW_TO).forEach(([key, steps]) => {
      const header = document.querySelector(`#section-${key} .section-header`);
      if (header && !header.nextElementSibling?.classList.contains('how-to')) {
        header.insertAdjacentElement('afterend', howToBox(steps));
      }
    });
  }

  function addTabSteps() {
    const tabs = [...document.querySelectorAll('#patientTabs .nav-link')];
    tabs.forEach((tab, i) => {
      const pane = document.querySelector(tab.dataset.bsTarget);
      if (!pane || pane.querySelector('.tab-step-nav')) return;
      const nav = document.createElement('div');
      nav.className = 'tab-step-nav';
      const back = i > 0
        ? `<button type="button" class="btn btn-outline-secondary" data-go="${i - 1}">
             <i class="bi bi-arrow-left me-2"></i>Back</button>`
        : '<span></span>';
      const next = i < tabs.length - 1
        ? `<button type="button" class="btn btn-primary" data-go="${i + 1}">
             Next part: ${tabs[i + 1].textContent.trim().replace(/^\d+\.\s*/, '')}
             <i class="bi bi-arrow-right ms-2"></i></button>`
        : `<button type="button" class="btn btn-success" data-section-go="validation">
             Done &mdash; check for missing information <i class="bi bi-arrow-right ms-2"></i></button>`;
      nav.innerHTML = back + next;
      pane.appendChild(nav);
    });

    document.addEventListener('click', e => {
      const go = e.target.closest('[data-go]');
      if (go) {
        const tab = tabs[Number(go.dataset.go)];
        if (tab && window.bootstrap) {
          bootstrap.Tab.getOrCreateInstance(tab).show();
          tab.scrollIntoView({ block: 'start' });
          window.scrollBy(0, -100);
        }
      }
      const section = e.target.closest('[data-section-go]');
      if (section && typeof navigateTo === 'function') navigateTo(section.dataset.sectionGo);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    addHowToBoxes();
    addTabSteps();
  });
})();
