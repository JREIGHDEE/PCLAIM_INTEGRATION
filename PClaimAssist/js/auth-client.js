/* ═══════════════════════════════════════════════════════════
   PClaimAssist – Authentication client

   Every auth decision is made by the Flask backend; this file only
   asks and reports. The browser never decides whether someone is
   signed in, because anything held here can be edited by whoever
   is sitting at the machine (research design §3.4.2.9: the backend
   owns the logic, the frontend only captures input and displays).

   `credentials: 'include'` is what sends the session cookie to the
   API on a different port (:5500 page -> :5000 API). Without it the
   browser silently omits the cookie and every call looks signed out.
═══════════════════════════════════════════════════════════ */

/* js/claim-loader.js also declares a top-level PCA_API_BASE. Both files
   load on index.html, and two `const` declarations of the same name in
   classic scripts is a syntax error that stops everything after it, so
   this one keeps its base URL private and only publishes the shared
   window value when nothing has set it yet. */
const PCA_AUTH_API_BASE = 'http://127.0.0.1:5000';

const PCAAuth = (function () {

  async function call(path, options) {
    const res = await fetch(PCA_AUTH_API_BASE + path, Object.assign({
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    }, options || {}));

    let body = null;
    try { body = await res.json(); } catch (_) { /* non-JSON error page */ }
    return { ok: res.ok, status: res.status, body };
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
