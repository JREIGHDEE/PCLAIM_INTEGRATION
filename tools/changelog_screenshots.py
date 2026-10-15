"""
Pre-commit helper: when a commit changes the user interface, screenshot the
affected pages and add an entry to the top of CHANGELOG.md.

Run by .githooks/pre-commit - you don't run it yourself. It:
  1. looks at the staged files and picks the pages whose files changed;
  2. signs in to the running app (http://127.0.0.1:5000) and screenshots
     those pages into docs/screenshots/;
  3. writes a CHANGELOG.md entry: the changed UI files plus the screenshots
     (add a sentence describing the change yourself if you like);
  4. stages the screenshots and CHANGELOG.md so they go into the same commit.

It never blocks a commit: if the app isn't running or something fails, it
prints why and lets the commit through without screenshots.

Settings (in Ocr_module/.env, which is never committed):
  SCREENSHOT_EMAIL / SCREENSHOT_PASSWORD   an account to sign in with
  SCREENSHOT_BASE_URL                      default http://127.0.0.1:5000
Skip it for one commit:  set SKIP_SCREENSHOTS=1 (or git commit --no-verify).

One-time setup per computer (see SETUP.md):
  git config core.hooksPath .githooks
  Ocr_module/venv/Scripts/python -m pip install playwright
  Ocr_module/venv/Scripts/python -m playwright install chromium
"""
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
SHOTS_DIR = ROOT / "docs" / "screenshots"
VIEWPORT = {"width": 1366, "height": 768}

# page key -> (title, path on the server, files that change how it looks)
PAGES = {
    "login": ("Login page", "/login.html",
              [r"^PClaimAssist/login\.html$", r"^PClaimAssist/js/(login|auth-client)\.js$"]),
    "app": ("Main app (dashboard)", "/index.html",
            [r"^PClaimAssist/index\.html$", r"^PClaimAssist/css/style\.css$",
             r"^PClaimAssist/js/(app|sidebar|box-input|pin-input|claim-loader|ocr-review|validation-rules)\.js$"]),
    "ocr": ("Read Logbook Scan page", "/ocr.html",
            [r"^PClaimAssist/ocr\.html$", r"^PClaimAssist/css/ocr\.css$", r"^PClaimAssist/js/ocr\.js$",
             r"^PClaimAssist/js/sidebar\.js$"]),
    "review": ("Logbook Review page", "/review", [r"^Ocr_module/templates/review\.html$"]),
    "workspace": ("OCR workspace", "/ocr-workspace", [r"^Ocr_module/templates/index\.html$"]),
}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=True).stdout


def load_env():
    env_file = ROOT / "Ocr_module" / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def staged_files():
    return [f for f in git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines() if f]


def pages_for(files):
    return [key for key, (_, _, patterns) in PAGES.items()
            if any(re.search(p, f) for p in patterns for f in files)]


def take_screenshots(page_keys, stamp):
    from playwright.sync_api import sync_playwright

    base = os.environ.get("SCREENSHOT_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    email, password = os.environ.get("SCREENSHOT_EMAIL"), os.environ.get("SCREENSHOT_PASSWORD")
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport=VIEWPORT)
        if any(k != "login" for k in page_keys):
            if not (email and password):
                raise RuntimeError("SCREENSHOT_EMAIL / SCREENSHOT_PASSWORD are not set in Ocr_module/.env")
            response = context.request.post(f"{base}/api/auth/login",
                                            data={"email": email, "password": password})
            if not response.ok:
                raise RuntimeError(f"could not sign in as {email} (HTTP {response.status})")
        page = context.new_page()
        for key in page_keys:
            title, path, _ = PAGES[key]
            if key == "login":
                # A signed-in browser is sent past the login page.
                login_context = browser.new_context(viewport=VIEWPORT)
                shot_page = login_context.new_page()
            else:
                shot_page = page
            shot_page.goto(base + path, wait_until="networkidle", timeout=30000)
            shot_page.wait_for_timeout(800)  # let animations settle
            out = SHOTS_DIR / f"{stamp}_{key}.jpg"
            shot_page.screenshot(path=str(out), type="jpeg", quality=70)
            saved.append((title, out))
        browser.close()
    return saved


def summarize(files):
    """The bullet for the entry: which UI files changed. Edit CHANGELOG.md
    afterwards to describe the change in your own words."""
    return [f"Changed: {', '.join(Path(f).name for f in files)}"]


def write_entry(bullets, shots, when):
    author = git("config", "user.name").strip() or "unknown"
    lines = [f"## {when:%Y-%m-%d %H:%M}: UI update ({author})", ""]
    lines += [f"- {b}" for b in bullets]
    for title, path in shots:
        rel = path.relative_to(ROOT).as_posix()
        lines += ["", f"**{title}**", "", f"![{title}]({rel})"]
    entry = "\n".join(lines) + "\n\n"

    text = CHANGELOG.read_text(encoding="utf-8")
    # New entries go right after the intro (the first '---' line).
    marker = "\n---\n"
    at = text.find(marker)
    at = len(text) if at < 0 else at + len(marker)
    CHANGELOG.write_text(text[:at] + "\n" + entry + text[at:].lstrip("\n"), encoding="utf-8")


def main():
    if os.environ.get("SKIP_SCREENSHOTS") == "1":
        return
    files = staged_files()
    page_keys = pages_for(files)
    if not page_keys:
        return
    load_env()
    ui_files = [f for f in files if any(re.search(p, f) for k in page_keys for p in PAGES[k][2])]
    when = datetime.now()
    try:
        shots = take_screenshots(page_keys, when.strftime("%Y-%m-%d_%H%M%S"))
    except Exception as exc:
        print(f"[changelog] No screenshots ({exc}). Is the app running at "
              f"{os.environ.get('SCREENSHOT_BASE_URL', 'http://127.0.0.1:5000')}? Committing without them.")
        return
    write_entry(summarize(ui_files), shots, when)
    git("add", str(CHANGELOG), *[str(path) for _, path in shots])
    print(f"[changelog] Added {len(shots)} screenshot(s) and an entry to CHANGELOG.md")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[changelog] Skipped: {exc}")
    sys.exit(0)
