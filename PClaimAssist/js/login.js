/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Login Page Logic
   Sign-in is checked by the Flask backend (see js/auth-client.js).
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
  setTimeout(() => div.remove(), 10000);
}

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
  this.querySelector('span').textContent = showing ? 'Show' : 'Hide';
  this.title = showing ? 'Show password' : 'Hide password';
});

// Submit: credentials are checked by the Flask backend against the bcrypt
// hash in the users table. The browser never decides whether the password
// was right — it only shows the answer.
document.getElementById('loginForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const signInBtn = document.getElementById('signInBtn');
  if (signInBtn.disabled) return;

  const email    = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  const remember = document.getElementById('rememberMe').checked;

  if (!email || !password) {
    showToast('Missing details', 'Enter both your email and password.', 'warning');
    return;
  }

  function setBusy(busy) {
    signInBtn.disabled = busy;
    signInBtn.querySelector('.btn-label').classList.toggle('d-none', busy);
    signInBtn.querySelector('.btn-spinner').classList.toggle('d-none', !busy);
  }
  setBusy(true);

  // "Remember me" stores only the email so it can be pre-filled next time.
  // The password is never written to the browser.
  if (remember) localStorage.setItem('pca_remembered_email', email);
  else          localStorage.removeItem('pca_remembered_email');

  const result = await PCAAuth.login(email, password);

  if (!result.ok) {
    setBusy(false);
    document.getElementById('loginPassword').value = '';
    showToast('Sign-in failed', result.error, 'danger');
    return;
  }

  showToast('Welcome back', `Signed in as ${result.user.full_name}.`, 'success');
  setTimeout(() => { window.location.href = 'index.html'; }, 600);
});

// Forgot password modal
document.getElementById('forgotPasswordLink').addEventListener('click', function (e) {
  e.preventDefault();
  new bootstrap.Modal(document.getElementById('forgotPasswordModal')).show();
});

// Accounts are created and reset by a clinic administrator (research design
// §3.8), so there is no self-service reset to perform here. Say so plainly
// rather than implying an email was sent.
document.getElementById('sendResetBtn').addEventListener('click', function () {
  const modalEl = document.getElementById('forgotPasswordModal');
  bootstrap.Modal.getInstance(modalEl).hide();
  showToast('Ask your administrator',
            'Passwords are reset by your clinic administrator. Please contact them to regain access.',
            'info');
});
