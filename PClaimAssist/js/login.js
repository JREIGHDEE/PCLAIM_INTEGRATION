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
function bindPasswordToggle(buttonId, inputIds) {
  document.getElementById(buttonId).addEventListener('click', function () {
    const inputs = inputIds.map(id => document.getElementById(id));
    const icon = this.querySelector('i');
    const showing = inputs[0].type === 'text';
    inputs.forEach(input => { input.type = showing ? 'password' : 'text'; });
    icon.classList.toggle('bi-eye', showing);
    icon.classList.toggle('bi-eye-slash', !showing);
    this.querySelector('span').textContent = showing ? 'Show' : 'Hide';
    this.title = showing ? 'Show password' : 'Hide password';
  });
}
bindPasswordToggle('togglePassword', ['loginPassword']);
bindPasswordToggle('toggleRegPassword', ['regPassword', 'regConfirm']);

function setButtonBusy(btn, busy) {
  btn.disabled = busy;
  btn.querySelector('.btn-label').classList.toggle('d-none', busy);
  btn.querySelector('.btn-spinner').classList.toggle('d-none', !busy);
}

/* ── Sign in ⇄ Create account ─────────────────────────────── */
async function showRegister(updateHash = true) {
  document.getElementById('signInCard').hidden = true;
  document.getElementById('registerCard').hidden = false;
  if (updateHash) history.replaceState(null, '', '#register');
  document.getElementById('regFullName').focus();

  // A fresh install: say plainly that this account runs the clinic.
  const status = await PCAAuth.status();
  const first = !!status && !status.hasAccounts;
  document.getElementById('firstAccountNote').classList.toggle('d-none', !first);
  document.getElementById('registerIntro').textContent = first
    ? 'Set up the first account for this clinic.'
    : 'Fill in your details. Your clinic administrator will approve the account before you can sign in.';
}

function showSignIn() {
  document.getElementById('registerCard').hidden = true;
  document.getElementById('signInCard').hidden = false;
  history.replaceState(null, '', location.pathname);
  const email = document.getElementById('loginEmail');
  (email.value ? document.getElementById('loginPassword') : email).focus();
}

document.getElementById('showRegisterLink').addEventListener('click', e => { e.preventDefault(); showRegister(); });
document.getElementById('showSignInLink').addEventListener('click', e => { e.preventDefault(); showSignIn(); });
if (location.hash === '#register') showRegister(false);

/* ── Password rules, shown live while typing ──────────────── */
// The server enforces the 8-character minimum (user_store.MIN_PASSWORD_LENGTH);
// the letter and number rules are checked here before sending.
const PW_RULES = {
  length: pw => pw.length >= 8,
  letter: pw => /[A-Za-z]/.test(pw),
  number: pw => /\d/.test(pw),
};

function checkPasswordRules() {
  const pw = document.getElementById('regPassword').value;
  let passed = 0;
  Object.entries(PW_RULES).forEach(([rule, test]) => {
    const ok = test(pw);
    if (ok) passed++;
    const li = document.querySelector(`#pwRules [data-rule="${rule}"]`);
    li.classList.toggle('text-success', ok);
    li.classList.toggle('text-muted', !ok);
    li.querySelector('i').className = `bi ${ok ? 'bi-check-circle-fill' : 'bi-circle'} me-1`;
  });
  const bar = document.getElementById('pwStrengthBar');
  const strong = passed === 3 && pw.length >= 12;
  bar.style.width = pw ? `${strong ? 100 : (passed / 3) * 85}%` : '0%';
  bar.className = 'progress-bar ' + (passed < 2 ? 'bg-danger' : passed < 3 ? 'bg-warning' : 'bg-success');
  return passed === 3;
}

function checkPasswordMatch() {
  const pw = document.getElementById('regPassword').value;
  const confirm = document.getElementById('regConfirm').value;
  const note = document.getElementById('pwMatchNote');
  if (!confirm) { note.textContent = ''; return false; }
  const same = pw === confirm;
  note.textContent = same ? '✓ The passwords match.' : '✗ The passwords do not match yet.';
  note.className = 'small mt-1 ' + (same ? 'text-success' : 'text-danger');
  return same;
}

document.getElementById('regPassword').addEventListener('input', () => { checkPasswordRules(); checkPasswordMatch(); });
document.getElementById('regConfirm').addEventListener('input', checkPasswordMatch);
checkPasswordRules();

document.getElementById('registerForm').addEventListener('submit', async function (e) {
  e.preventDefault();
  const btn = document.getElementById('registerBtn');
  if (btn.disabled) return;

  const fullName = document.getElementById('regFullName').value.trim();
  const email    = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPassword').value;
  const confirm  = document.getElementById('regConfirm').value;

  if (!fullName || !email || !password || !confirm) {
    showToast('Missing details', 'Fill in your name, email and both password boxes.', 'warning');
    return;
  }
  if (!checkPasswordRules()) {
    showToast('Password too weak', 'Use at least 8 characters with a letter and a number.', 'warning');
    return;
  }
  if (!checkPasswordMatch()) {
    showToast('Passwords do not match', 'Type the same password in both boxes.', 'warning');
    return;
  }

  setButtonBusy(btn, true);
  const result = await PCAAuth.register(fullName, email, password, confirm);
  setButtonBusy(btn, false);

  if (!result.ok) {
    showToast('Could not create the account', result.error, 'danger');
    return;
  }

  this.reset();
  checkPasswordRules();
  checkPasswordMatch();

  if (result.signedIn) {
    showToast('Administrator account created',
              `Welcome, ${result.user.full_name}. You are signed in.`, 'success');
    setTimeout(() => { window.location.href = 'index.html'; }, 800);
    return;
  }

  document.getElementById('loginEmail').value = result.user.email;
  showSignIn();
  showToast('Account created',
            'Your clinic administrator needs to approve it. You can sign in once they have.',
            'success');
});

// Submit: credentials are checked by the Flask backend against the bcrypt
// hash in the users table. The browser never decides whether the password
// was right — it only shows the answer.
/* ═══════════════════════════════════════════════════════════
   WRONG PASSWORDS, SHOWN ABOVE THE BOXES

   The backend counts them (Ocr_module/sign_in_guard.py) and says how
   many tries are left, or how many seconds the account is closed for.
   This draws that: a dot per try, and a ring that empties while the
   wait runs down. The Sign In button is held while it does, so nobody
   wastes a try on a closed account.
═══════════════════════════════════════════════════════════ */
const PCAAttempts = (function () {
  const card   = document.getElementById('loginAttempts');
  if (!card) return { show() {}, clear() {} };
  const ring   = document.getElementById('loginAttemptsRing');
  const run    = document.getElementById('loginRingRun');
  const count  = document.getElementById('loginCountdown');
  const title  = document.getElementById('loginAttemptsTitle');
  const sub    = document.getElementById('loginAttemptsSub');
  const dots   = document.getElementById('loginAttemptsDots');
  const btn    = document.getElementById('signInBtn');
  const CIRCUMFERENCE = 119.38;        // 2 * pi * 19, as in style.css
  let ticker = null;

  function drawDots(left, total) {
    dots.innerHTML = '';
    for (let i = 0; i < total; i++) {
      const dot = document.createElement('i');
      if (i >= left) dot.classList.add('spent');
      dots.appendChild(dot);
    }
    dots.hidden = false;
  }

  function stop() {
    clearInterval(ticker);
    ticker = null;
  }

  function clear() {
    stop();
    card.hidden = true;
    card.classList.remove('is-locked', 'is-last', 'is-shake');
    if (btn) btn.disabled = false;
  }

  /* Count the wait down, emptying the ring as it goes. */
  function lock(seconds) {
    stop();
    const total = Math.max(1, seconds);
    let left = total;
    card.hidden = false;
    card.classList.add('is-locked');
    card.classList.remove('is-last');
    ring.hidden = false;
    dots.hidden = true;
    title.textContent = 'Too many wrong passwords';
    if (btn) btn.disabled = true;

    const paint = () => {
      count.textContent = left > 60
        ? Math.ceil(left / 60) + 'm'
        : left;
      run.style.strokeDashoffset = CIRCUMFERENCE * (1 - left / total);
      // Said the way a person would say it: minutes while there are
      // minutes to wait, seconds once it is nearly over.
      if (left > 90) {
        const mins = Math.ceil(left / 60);
        sub.textContent = `Try again in about ${mins} minutes`;
      } else if (left > 60) {
        sub.textContent = 'Try again in about a minute';
      } else {
        sub.textContent = left === 1
          ? 'Try again in 1 second'
          : `Try again in ${left} seconds`;
      }
    };
    paint();

    ticker = setInterval(() => {
      left -= 1;
      if (left <= 0) {
        stop();
        clear();
        title.textContent = '';
        return;
      }
      paint();
    }, 1000);
  }

  /* A wrong password, with tries still left. */
  function warn(left, total) {
    stop();
    card.hidden = false;
    ring.hidden = true;
    card.classList.remove('is-locked');
    card.classList.toggle('is-last', left === 1);
    if (btn) btn.disabled = false;

    const used = total - left;
    title.textContent = used === 1
      ? '1 wrong password'
      : `${used} wrong passwords`;
    sub.textContent = left === 1
      ? 'One more try before this account is closed for a minute'
      : `${left} tries left`;
    drawDots(left, total);

    // One shake, restarted each time.
    card.classList.remove('is-shake');
    void card.offsetWidth;
    card.classList.add('is-shake');
  }

  return {
    show(result) {
      const locked = Number(result.lockedSeconds) || 0;
      if (locked > 0) { lock(locked); return; }
      const left = Number(result.attemptsLeft);
      // An older backend says nothing about tries; then there is
      // nothing to count, and the message at the foot stands alone.
      if (!Number.isFinite(left)) { clear(); return; }
      warn(left, 5);
    },
    clear,
  };
})();

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

  setButtonBusy(signInBtn, true);

  // "Remember me" stores only the email so it can be pre-filled next time.
  // The password is never written to the browser.
  if (remember) localStorage.setItem('pca_remembered_email', email);
  else          localStorage.removeItem('pca_remembered_email');

  const result = await PCAAuth.login(email, password);

  if (!result.ok) {
    setButtonBusy(signInBtn, false);
    document.getElementById('loginPassword').value = '';
    document.getElementById('loginPassword').focus();
    PCAAttempts.show(result);
    return;
  }

  PCAAttempts.clear();
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
