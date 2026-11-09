"""The real PClaimAssist forms page (PClaimAssist/index.html), offline, in
headless Microsoft Edge (Playwright).

Why a browser: the claim's last steps run in the page's own JavaScript -
claim-loader.js loadClaimFromUrl -> app.js applyFormData and its
automations (member = patient, mother's names, derived fields) ->
validation-rules.js runValidationRules -> pdf-overlay.js buildFilledPdf
with pdf-lib. Running the page itself means those files are used exactly
as the clinic uses them, unedited.

Offline: every request is answered here, nothing goes to the network.
  - the page's own files are read from PClaimAssist/;
  - pdf-lib is research_tests/vendor/pdf-lib.min.js (pdf-lib 1.17.1, the
    version index.html names, downloaded once);
  - Bootstrap's and AOS's scripts are tiny stand-ins (no visible page is
    needed); stylesheets, fonts and anything else external get an empty
    answer;
  - /api/auth/me answers a research user; /api/claims/<id>/form-data
    answers with the claim built by the real Python auto-population
    (philhealth.form_prefill.build_form_data); any other /api call gets
    {"success": false}. No server, no database.
"""
import base64
import itertools
import json
import time

from research_tests import FORMS_DIR, VENDOR

HOST = "http://pclaimassist.research/"
_STUBS = {
    "bootstrap.bundle.min.js": ("window.bootstrap = new Proxy({}, {get: () => ({"
                                "getOrCreateInstance: () => ({show(){}, hide(){}}),"
                                "getInstance: () => ({show(){}, hide(){}})})});"),
    "aos.js": "window.AOS = {init(){}, refresh(){}};",
    "pdf.min.js": "",          # PDF.js only draws the on-screen preview
}
RESEARCH_USER = {"id": 1, "email": "research@test.local", "full_name": "Research tests", "role": "admin"}


class FormsPage:
    """with FormsPage() as page: page.open_claim(body); page.validate(); ..."""

    def __init__(self, headless=True):
        self.headless = headless
        self.bodies = {}
        self.api = {}          # "api/claims/<id>/<name>" -> answer, for one claim (open_claim api=)
        self.errors = []
        self.external = set()
        self._ids = itertools.count(900001)

    # ── lifecycle ──────────────────────────────────────────────────────
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        if not (VENDOR / "pdf-lib.min.js").is_file():
            raise RuntimeError("research_tests/vendor/pdf-lib.min.js is missing (see README.md)")
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(channel="msedge", headless=self.headless)
        self.context = self.browser.new_context()
        self.context.route("**/*", self._answer)
        self.page = self.context.new_page()
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        return self

    def __exit__(self, *exc):
        try:
            self.browser.close()
        finally:
            self._pw.stop()

    @property
    def browser_version(self):
        return f"Microsoft Edge {self.browser.version}"

    def _answer(self, route):
        url = route.request.url
        if url.startswith(HOST):
            path = url[len(HOST):].split("?")[0].split("#")[0]
            if path.startswith("api/"):
                if path == "api/auth/me":
                    return route.fulfill(json={"success": True, "user": RESEARCH_USER})
                if path in self.api:
                    return route.fulfill(json=self.api[path])
                if path.startswith("api/claims/") and path.endswith("/form-data"):
                    body = self.bodies.get(path.split("/")[2])
                    if body is not None:
                        return route.fulfill(json=body)
                return route.fulfill(json={"success": False, "error": "offline research run"})
            file = (FORMS_DIR / path).resolve()
            if file.is_file() and FORMS_DIR.resolve() in file.parents:
                return route.fulfill(path=str(file))
            return route.fulfill(status=404, body="")
        name = url.split("?")[0].rsplit("/", 1)[-1]
        if name == "pdf-lib.min.js":
            return route.fulfill(path=str(VENDOR / "pdf-lib.min.js"), content_type="application/javascript")
        if name in _STUBS:
            return route.fulfill(body=_STUBS[name], content_type="application/javascript")
        self.external.add(url.split("?")[0])
        return route.fulfill(status=204, body="")

    # ── a claim ────────────────────────────────────────────────────────
    def open_claim(self, body, timeout=30000, api=None):
        """Load a claim the way the page does (?claim=<id>, claim-loader.js).
        body: {"data", "fields", "saved_values", ...} as GET
        /api/claims/<id>/form-data answers. api: other answers for this
        claim, {"family": {...}, "from-mother": {...}} as GET
        /api/claims/<id>/<name> answers. Returns state.data."""
        claim_id = str(next(self._ids))
        body = json.loads(json.dumps({"success": True, "fields": {}, "saved_values": {},
                                      "ocr_reference": {}, **body}, default=str))
        self.bodies[claim_id] = body
        for name, answer in (api or {}).items():
            self.api[f"api/claims/{claim_id}/{name}"] = json.loads(json.dumps(answer, default=str))
        self.page.goto(f"{HOST}index.html?claim={claim_id}")
        expect = {k: body["data"][k] for k in ("patientLastName", "dateAdmitted") if body["data"].get(k)}
        self.page.wait_for_function(
            """expect => window.state && state.data && document.readyState === 'complete' &&
                 Object.entries(expect).every(([k, v]) => String(state.data[k] || '').toUpperCase()
                                                           === String(v).toUpperCase())""",
            arg=expect, timeout=timeout)
        self.page.wait_for_timeout(300)          # automations after loading
        self.page.evaluate("() => { try { localStorage.clear(); } catch (e) {} }")
        return self.data()

    def data(self):
        return self.page.evaluate("() => JSON.parse(JSON.stringify(state.data))")

    def set_values(self, values):
        """Change state.data as if typed (seeded errors), then let the page
        redraw its previews."""
        self.page.evaluate("""values => { Object.assign(state.data, values);
            if (typeof updateFormPreviews === 'function') updateFormPreviews(); }""", values)

    def claim_forms(self):
        return self.page.evaluate("() => typeof pcaClaimForms === 'function' ? pcaClaimForms() : claimFormKeys(state.data)")

    def computed(self, keys):
        return self.page.evaluate("keys => Object.fromEntries(keys.map(k => [k, getComputedValue(k)]))", keys)

    # ── validation-rules.js ────────────────────────────────────────────
    def validate(self, ocr_state=None, signature_state=None, attachments=0):
        """runValidationRules(getComputedValue, state.data) as the page runs
        it, with the OCR and signature states the rules read.
        -> {"fired": [ids], "violations": [...], "features": {...}, "ms": float}"""
        return self.page.evaluate("""([ocr, sig, att]) => {
            window.PCA_OCR_STATE = ocr || undefined;
            window.PCA_SIGNATURE_STATE = sig || undefined;
            window.PCA_ATTACHMENT_COUNT = att || 0;
            const t = performance.now();
            const r = runValidationRules(getComputedValue, state.data);
            const ms = performance.now() - t;
            window.PCA_OCR_STATE = undefined; window.PCA_SIGNATURE_STATE = undefined;
            return {fired: r.violations.map(v => v.id), ms,
                    violations: r.violations.map(v => ({id: v.id, category: v.category, action: v.action,
                                                         message: v.message, field: v.field, form: v.form})),
                    features: r.features, canGeneratePDF: r.canGeneratePDF};
        }""", [ocr_state, signature_state, attachments])

    def rules(self):
        return self.page.evaluate("""() => VALIDATION_RULES.map(r => ({id: r.id, category: r.category,
            action: r.action, form: r.form || null, message: r.message}))""")

    # ── pdf-overlay.js ─────────────────────────────────────────────────
    def overlay_spots(self, form):
        """Every box of the form's overlay map with the value the page puts
        in it (resolveOverlayFieldValue, the on-screen and printed value)."""
        return self.page.evaluate("""form => (OVERLAY_MAP[form] || []).map(f => ({
            id: f.id, key: f.key || '', page: f.page, top: f.top, left: f.left, w: f.w, fs: f.fs || 7,
            wrap: !!f.wrap, lines: f.lines || f.maxLines || 1, lh: f.lh || 0,
            computed: f.computed || '', digitKey: f.digitKey || '', digit: f.digit ?? null,
            digitOrder: f.digitOrder || '', dateComponent: f.dateComponent || '',
            timeComponent: f.timeComponent || '', amPmCheck: f.amPmCheck || '', unless: f.unless || '',
            checkbox: !!f.checkbox, checkValue: f.checkValue === undefined ? null : f.checkValue,
            value: String(resolveOverlayFieldValue(f) ?? '')}))""", form)

    def build_pdf(self, form):
        """buildFilledPdf(form) + save, as "Save as PDF" does -> (bytes, ms)."""
        b64, ms = self.page.evaluate("""async form => {
            const t = performance.now();
            const doc = await buildFilledPdf(form);
            const bytes = await doc.save();
            const ms = performance.now() - t;
            let s = ''; const chunk = 0x8000;
            for (let i = 0; i < bytes.length; i += chunk) s += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
            return [btoa(s), ms];
        }""", form)
        return base64.b64decode(b64), ms


def timed(fn, *args, **kwargs):
    """(result, milliseconds) of fn(*args, **kwargs)."""
    started = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, (time.perf_counter() - started) * 1000.0
