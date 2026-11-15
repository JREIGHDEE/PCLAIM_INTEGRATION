"""Every missing box, through "Go to Field" / a click on its red box.

    venv\\Scripts\\python.exe check_go_to_field.py

"Go to Field" and the red boxes kept going nowhere for one box after
another - fixed one at a time (dates signed, civil status, then CF2's
co-pay) with nothing checking the rest. This goes through every box the
checker lists for a new patient, on every form of the claim, and checks
that the jump (app.js focusField) opens the right page, shows the box on
screen and makes it glow. Run it after changing the forms or the jump.

A separate copy of the app on port 5055 with a temporary administrator,
deleted at the end; nothing is saved (the claim API is blocked). Needs
MariaDB running and Microsoft Edge (Playwright, as research_tests). Exits
1 when a box does not land.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = 5055
BASE = f"http://127.0.0.1:{PORT}"
EMAIL, PASSWORD = "zz.goto-check.temp@example.com", "GoTo-Check-2026!"

LANDED = """async key => {
  focusField(key);
  await new Promise(r => setTimeout(r, 1800));   // a long panel scrolls smoothly
  const el = editableFieldFor(key);
  if (!el) return {key, problem: 'no box found to go to'};
  const r = el.getBoundingClientRect();
  const shown = !!(el.offsetParent || el.getClientRects().length) && r.width > 0 && r.height > 0;
  const section = (el.closest('.content-section') || {}).id;
  const active = document.querySelector('.content-section.active').id;
  const problems = [];
  if (section !== active) problems.push(`page not opened (${active}, not ${section})`);
  if (!shown) problems.push('box hidden');
  else if (r.bottom <= 0 || r.top >= innerHeight) problems.push('box off screen');
  if (!el.classList.contains('field-flash')) problems.push('no glow');
  return problems.length ? {key, problem: problems.join(', '), box: `${el.tagName}.${el.className.split(' ')[0]}`} : null;
}"""


def main():
    sys.path.insert(0, str(HERE))
    os.chdir(HERE)
    import user_store
    from db import get_db_cursor
    from playwright.sync_api import sync_playwright

    server = subprocess.Popen([sys.executable, "app.py"], cwd=HERE,
                              env=dict(os.environ, OCR_PORT=str(PORT), OCR_DEBUG="0"),
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    made, failures, errors, total = False, [], [], 0
    try:
        for _ in range(120):
            try:
                urllib.request.urlopen(BASE + "/login.html", timeout=2)
                break
            except Exception:
                time.sleep(1)
        user_store.create_user(EMAIL, PASSWORD, "Go to Field check (temporary)", role="admin")
        made = True
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="msedge")
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("dialog", lambda d: d.accept())
            page.route("**/api/claims/**",
                       lambda r: r.abort() if r.request.method in ("POST", "PUT", "DELETE") else r.continue_())
            page.goto(BASE + "/login.html")
            page.fill("input[type=email]", EMAIL)
            page.fill("input[type=password]", PASSWORD)
            page.click("button[type=submit]")
            page.wait_for_url("**/index.html**", timeout=20000)
            page.wait_for_timeout(2000)
            # A first professional named, so CF2's co-pay is asked for.
            page.evaluate("() => applyFormData({cf2Prof1Name: 'TEST'})")
            # Every form of the claim, then - "View All Forms" - the PMRF too,
            # which a new patient's claim does not need.
            first = page.evaluate("() => claimForms()")
            page.evaluate("() => { showAllForms = true; clearFormCheckCache(); updateValidation(); updateFormPreviews(); }")
            page.wait_for_timeout(1000)
            forms = first + [f for f in page.evaluate("() => claimForms()") if f not in first]
            for form in forms:
                page.click('.sidebar-item[data-section="validation"]')
                page.wait_for_timeout(800)
                keys = page.evaluate(f"""() => [...new Set([
                    ...formStillRedKeys('{form}').map(x => x.key),
                    ...[...document.querySelectorAll('.val-item[data-form="{form}"]:not(.complete):not(.skipped)')]
                        .map(x => x.dataset.field)])]""")
                for key in keys:
                    total += 1
                    # From Patient details: a form not open yet redraws itself
                    # after the jump (how CF2's co-pay went missing).
                    page.click('.sidebar-item[data-section="patient"]')
                    page.wait_for_timeout(300)
                    result = page.evaluate(LANDED, key)
                    if result:
                        failures.append({"form": form, **result})
            browser.close()
    finally:
        if made:
            with get_db_cursor(commit=True) as cur:
                cur.execute("DELETE FROM users WHERE email = %s", (EMAIL,))
        server.terminate()
    print(f"{total} boxes checked; {len(failures)} did not land")
    for failure in failures:
        print("  ", json.dumps(failure))
    if errors:
        print("page errors:", errors)
    return 1 if failures or errors else 0


if __name__ == "__main__":
    sys.exit(main())
