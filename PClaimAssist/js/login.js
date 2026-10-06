/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Login Page Logic
   Prototype auth: no credential verification, no storage/server.
═══════════════════════════════════════════════════════════ */

function showToast(title, message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const c = {
    success:{ bg:'#F0FDF4', border:'#86EFAC', title:'#166534', icon:'bi-check-circle-fill text-success' },
    info:   { bg:'#EFF6FF', border:'#BFDBFE', title:'#1E40AF', icon:'bi-info-circle-fill text-primary' },
    danger: { bg:'#FEF2F2', border:'#FECACA', title:'#991B1B', icon:'bi-x-circle-fill text-danger' },
    warning:{ bg:'#FFFBEB', border:'#FDE68A', title:'#78350F', icon:'bi-exclamation-triangle-fill text-warning' },
  }[type] || {};
  const div = document.createElement('div');
  div.className = 'toast pca-toast show'; div.setAttribute('role','alert');
  div.style.cssText = `background:${c.bg};border:1px solid ${c.border};`;
  div.innerHTML = `<div class="toast-header" style="background:${c.bg};color:${c.title};">
    <i class="bi ${c.icon} me-2"></i><strong class="me-auto">${title}</strong>
    <button type="button" class="btn-close btn-close-sm ms-2" onclick="this.closest('.toast').remove()"></button>
  </div><div class="toast-body" style="color:${c.title};">${message}</div>`;
  container.appendChild(div);
  setTimeout(() => div.remove(), 4000);
}

// Typewriter effect on the heading — loops: type, pause, delete, repeat
(function typewriter() {
  const el = document.getElementById('typewriterText');
  const text = 'Welcome back!';
  const typeSpeed = 70;
  const deleteSpeed = 40;
  const holdMs = 1600;
  const restartDelay = 400;
  let i = 0;

  function type() {
    if (i <= text.length) {
      el.textContent = text.slice(0, i);
      i++;
      setTimeout(type, typeSpeed);
    } else {
      setTimeout(erase, holdMs);
    }
  }

  function erase() {
    if (i > 0) {
      i--;
      el.textContent = text.slice(0, i);
      setTimeout(erase, deleteSpeed);
    } else {
      setTimeout(type, restartDelay);
    }
  }

  type();
})();

// Pre-fill remembered email, if any
(function restoreRememberedEmail() {
  const savedEmail = localStorage.getItem('pca_remembered_email');
  if (savedEmail) {
    document.getElementById('loginEmail').value = savedEmail;
    document.getElementById('rememberMe').checked = true;
  }
})();

// Show/hide password
document.getElementById('togglePassword').addEventListener('click', function () {
  const input = document.getElementById('loginPassword');
  const icon = this.querySelector('i');
  const showing = input.type === 'text';
  input.type = showing ? 'password' : 'text';
  icon.classList.toggle('bi-eye', showing);
  icon.classList.toggle('bi-eye-slash', !showing);
  this.title = showing ? 'Show password' : 'Hide password';
});

// Submit: no credential check in this prototype — just proceed
document.getElementById('loginForm').addEventListener('submit', function (e) {
  e.preventDefault();

  const signInBtn = document.getElementById('signInBtn');
  if (signInBtn.disabled) return;

  signInBtn.disabled = true;
  signInBtn.querySelector('.btn-label').classList.add('d-none');
  signInBtn.querySelector('.btn-spinner').classList.remove('d-none');

  const email = document.getElementById('loginEmail').value.trim();
  const remember = document.getElementById('rememberMe').checked;

  if (remember && email) {
    localStorage.setItem('pca_remembered_email', email);
  } else {
    localStorage.removeItem('pca_remembered_email');
  }

  sessionStorage.setItem('pca_logged_in', '1');
  sessionStorage.setItem('pca_user_email', email || 'staff@clinic.ph');

  setTimeout(() => { window.location.href = 'index.html'; }, 2000);
});

// Forgot password modal
document.getElementById('forgotPasswordLink').addEventListener('click', function (e) {
  e.preventDefault();
  new bootstrap.Modal(document.getElementById('forgotPasswordModal')).show();
});

document.getElementById('sendResetBtn').addEventListener('click', function () {
  const modalEl = document.getElementById('forgotPasswordModal');
  bootstrap.Modal.getInstance(modalEl).hide();
  showToast('Request Sent', 'If an account exists, a reset link has been sent.', 'success');
});
