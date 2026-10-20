/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Authentication client

   Every auth decision is made by the Flask backend; this file only
   asks and reports. The browser never decides whether someone is
   signed in, because anything held here can be edited by whoever
   is sitting at the machine (research design §3.4.2.9: the backend
   owns the logic, the frontend only captures input and displays).

   The backend serves these pages as well as the API, so every call
   below is same-origin and the session cookie rides along with
   `credentials: 'include'` regardless of which port the server uses.
═══════════════════════════════════════════════════════════ */

/* js/claim-loader.js also declares a top-level PCA_API_BASE. Both files
   load on index.html, and two `const` declarations of the same name in
   classic scripts is a syntax error that stops everything after it, so
   this one keeps its base URL private and only publishes the shared
   window value when nothing has set it yet.

   Empty string = same origin. Hard-coding a port here is what made the
   app break when the page was opened from anywhere else. */
const PCA_AUTH_API_BASE = '';

/* Opened through VS Code Live Server (.vscode/settings.json, port 5501)
   or straight from the disk, the page has no backend behind it: every
   sign-in or sign-up request would go to a static file server that cannot
   answer it. Move to the same page on the Flask server instead, but only
   once it answers: redirecting to a server that is not running leaves the
   browser on a "site can't be reached" page. */
const PCA_BACKEND_URL = 'http://127.0.0.1:5000';
(function openFromBackend() {
  const staticServer = location.protocol === 'file:' || ['5500', '5501'].includes(location.port);
  if (!staticServer) return;
  const page = location.pathname.split('/').pop() || 'login.html';
  fetch(`${PCA_BACKEND_URL}/db_health`, { mode: 'no-cors', cache: 'no-store' })
    .then(() => location.replace(`${PCA_BACKEND_URL}/${page}${location.search}${location.hash}`))
    .catch(() => console.warn(
      `PClaimAssist backend is not running at ${PCA_BACKEND_URL}. ` +
      'Start it with PClaimAssist.bat, then reload this page.'));
})();

const PCAAuth = (function () {

  async function call(path, options) {
    const res = await fetch(PCA_AUTH_API_BASE + path, Object.assign({
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    }, options || {}));

    let body = null;
    try { body = await res.json(); } catch (_) { /* non-JSON error page */ }
    if (!body) {
      // The backend always answers in JSON, so this came from something else.
      body = {
        success: false,
        error: `The server did not understand the request (HTTP ${res.status}). ` +
               `Make sure PClaimAssist is running and open it at ${PCA_BACKEND_URL}/`,
      };
    }
    return { ok: res.ok && body.success !== false, status: res.status, body };
  }

  return {
    /** Sign in. Resolves {ok, user} or {ok:false, error}. */
    async login(email, password) {
      try {
        const r = await call('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
        if (r.ok && r.body && r.body.success) return { ok: true, user: r.body.user };
        return { ok: false, error: (r.body && r.body.error) || 'Sign-in failed.' };
      } catch (err) {
        return { ok: false, error: 'Cannot reach the server. Is the OCR backend running?' };
      }
    },

    /**
     * Create your own account. Resolves {ok, user, signedIn} or
     * {ok:false, error}. Only the first account on a fresh install is
     * signed in at once (as administrator); later ones wait for approval.
     */
    async register(fullName, email, password, confirmPassword) {
      try {
        const r = await call('/api/auth/register', {
          method: 'POST',
          body: JSON.stringify({
            full_name: fullName,
            email,
            password,
            confirm_password: confirmPassword,
          }),
        });
        if (r.ok && r.body && r.body.success) {
          return { ok: true, user: r.body.user, signedIn: !!r.body.signed_in };
        }
        return { ok: false, error: (r.body && r.body.error) || 'Could not create the account.' };
      } catch (err) {
        return { ok: false, error: 'Cannot reach the server. Is the OCR backend running?' };
      }
    },

    /** {hasAccounts} so the sign-in page can explain a fresh install, or null. */
    async status() {
      try {
        const r = await call('/api/auth/status');
        return (r.ok && r.body) ? { hasAccounts: !!r.body.has_accounts } : null;
      } catch (err) {
        return null;
      }
    },

    /** Admin: every account. Resolves {ok, users} or {ok:false, error}. */
    async listUsers() {
      try {
        const r = await call('/api/auth/users');
        if (r.ok && r.body && r.body.success) return { ok: true, users: r.body.users };
        return { ok: false, error: (r.body && r.body.error) || 'Could not load accounts.' };
      } catch (err) {
        return { ok: false, error: 'Cannot reach the server.' };
      }
    },

    /** Admin: approve (true) or switch off (false) an account. */
    async setUserActive(userId, isActive) {
      try {
        const r = await call(`/api/auth/users/${encodeURIComponent(userId)}`, {
          method: 'PATCH',
          body: JSON.stringify({ is_active: isActive }),
        });
        if (r.ok && r.body && r.body.success) return { ok: true, user: r.body.user };
        return { ok: false, error: (r.body && r.body.error) || 'Could not update the account.' };
      } catch (err) {
        return { ok: false, error: 'Cannot reach the server.' };
      }
    },

    /** Admin: set a new password for a staff member who forgot theirs. */
    async resetUserPassword(userId, newPassword) {
      try {
        const r = await call(`/api/auth/users/${encodeURIComponent(userId)}/password`, {
          method: 'POST',
          body: JSON.stringify({ new_password: newPassword }),
        });
        if (r.ok && r.body && r.body.success) return { ok: true };
        return { ok: false, error: (r.body && r.body.error) || 'Could not set the password.' };
      } catch (err) {
        return { ok: false, error: 'Cannot reach the server.' };
      }
    },

    async logout() {
      try { await call('/api/auth/logout', { method: 'POST' }); }
      catch (_) { /* signing out locally matters more than the round trip */ }
    },

    /** The signed-in user, or null. The single source of truth. */
    async me() {
      try {
        const r = await call('/api/auth/me');
        return (r.ok && r.body && r.body.user) ? r.body.user : null;
      } catch (err) {
        return null;
      }
    },

    /**
     * Guard a page: resolve with the user, or send to login.html.
     * Returns null when redirecting so callers can stop work.
     */
    async requireLogin() {
      const user = await this.me();
      if (!user) {
        window.location.replace('login.html');
        return null;
      }
      return user;
    },

    /** Change your own password. Resolves {ok} or {ok:false, error}. */
    async changePassword(currentPassword, newPassword) {
      try {
        const r = await call('/api/auth/password', {
          method: 'POST',
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
          }),
        });
        if (r.ok && r.body && r.body.success) return { ok: true };
        return { ok: false, error: (r.body && r.body.error) || 'Could not change the password.' };
      } catch (err) {
        return { ok: false, error: 'Cannot reach the server.' };
      }
    },

    /** The clinic's name, PAN and address (Table 3.1 "entered once"). */
    async getClinicSettings() {
      try {
        const r = await call('/api/settings/clinic');
        return (r.ok && r.body) ? r.body.settings : null;
      } catch (err) {
        return null;
      }
    },

    /** Save clinic settings. Admin only; others get {ok:false}. */
    async saveClinicSettings(settings) {
      try {
        const r = await call('/api/settings/clinic', {
          method: 'POST',
          body: JSON.stringify({ settings }),
        });
        if (r.ok && r.body && r.body.success) return { ok: true, settings: r.body.settings };
        return { ok: false, error: (r.body && r.body.error) || 'Could not save.' };
      } catch (err) {
        return { ok: false, error: 'Cannot reach the server.' };
      }
    },

    /** Human-readable role label for the navbar. */
    roleLabel(role) {
      return role === 'admin' ? 'Clinic Administrator' : 'Claims Encoder';
    },
  };
})();

window.PCAAuth = PCAAuth;
if (typeof window.PCA_API_BASE === 'undefined') {
  window.PCA_API_BASE = PCA_AUTH_API_BASE;
}
