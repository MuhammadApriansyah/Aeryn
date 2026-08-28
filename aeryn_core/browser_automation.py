#!/usr/bin/env python3
"""V1.0 — BrowserSession: Playwright-style browser control with security hardening.

Provides navigate, click, fill, screenshot, extract_text methods.
Falls back to selenium if playwright unavailable.
All operations gated by SecurityKernel-style checks (no credential sites,
no local/sensitive URLs, anti-injection on selectors/inputs).
"""

from __future__ import annotations

import os
import re
import time
import logging
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ── Security Configuration ───────────────────────────────────────

# URL patterns that are NEVER allowed (local networks, metadata, secrets)
BLOCKED_HOST_PATTERNS = [
    re.compile(r"^localhost$", re.I),
    re.compile(r"^127\.", re.I),
    re.compile(r"^10\.", re.I),
    re.compile(r"^172\.(1[6-9]|2\d|3[01])\.", re.I),
    re.compile(r"^192\.168\.", re.I),
    re.compile(r"^169\.254\.", re.I),  # link-local
    re.compile(r"^0\.0\.0\.0$", re.I),
    re.compile(r"^::1$", re.I),
    re.compile(r"^fc00:", re.I),  # IPv6 private
    re.compile(r"^fe80:", re.I),  # IPv6 link-local
    re.compile(r"\.internal$", re.I),
    re.compile(r"\.local$", re.I),
]

BLOCKED_SCHEMES = {"file", "ftp", "data", "javascript"}

# Credential-heavy sites that should not be automated
SENSITIVE_DOMAINS = {
    "accounts.google.com", "login.microsoftonline.com",
    "github.com", "gitlab.com",
    "facebook.com", "twitter.com", "x.com",
    "bank", "paypal.com",
}

# Anti-injection: selectors must be simple CSS or XPath
SAFE_SELECTOR_RE = re.compile(r'^[a-zA-Z0-9\s\.\#\[\]\=\-\_\:\>\+\~\,\"\'\^\$\*\|]+$')
SAFE_XPATH_RE = re.compile(r'^\.?//[a-zA-Z0-9\s\@\[\]\=\-\_\:\.\/\*\(\)\,\']+$')

# Max content extraction size (anti-DoS)
MAX_EXTRACT_CHARS = 50_000
MAX_SCREENSHOT_BYTES = 10 * 1024 * 1024  # 10 MB


class BrowserSecurityError(Exception):
    """Raised when a browser operation violates security policy."""
    pass


class BrowserSession:
    """Playwright-style browser control with security checks.

    Usage:
        session = BrowserSession(headless=True)
        session.start()
        session.navigate("https://example.com")
        session.fill("#search", "aeryn")
        session.click("button[type=submit]")
        text = session.extract_text()
        session.screenshot("page.png")
        session.close()
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None,
        timeout: int = 30_000,
        allow_sensitive: bool = False,
        proxy: Optional[str] = None,
    ):
        self.headless = headless
        self.browser_type = browser_type
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.user_agent = user_agent
        self.timeout = timeout
        self.allow_sensitive = allow_sensitive
        self.proxy = proxy

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._backend: str = "none"  # "playwright" or "selenium"

    # ── Lifecycle ──────────────────────────────────────────────────

    def start(self) -> "BrowserSession":
        """Initialize browser backend (playwright preferred, selenium fallback)."""
        try:
            self._start_playwright()
            self._backend = "playwright"
            logger.info("BrowserSession: using playwright backend")
        except ImportError:
            try:
                self._start_selenium()
                self._backend = "selenium"
                logger.info("BrowserSession: using selenium backend")
            except ImportError:
                raise BrowserSecurityError(
                    "No browser automation library available. "
                    "Install playwright: pip install playwright && playwright install chromium"
                )
        return self

    def _start_playwright(self):
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        browser_cls = getattr(self._playwright, self.browser_type, None)
        if browser_cls is None:
            raise ImportError(f"Unknown browser type: {self.browser_type}")

        launch_opts = {"headless": self.headless}
        if self.proxy:
            launch_opts["proxy"] = {"server": self.proxy}

        self._browser = browser_cls.launch(**launch_opts)

        ctx_opts = {"viewport": self.viewport}
        if self.user_agent:
            ctx_opts["user_agent"] = self.user_agent

        self._context = self._browser.new_context(**ctx_opts)
        self._context.set_default_timeout(self.timeout)
        self._page = self._context.new_page()

    def _start_selenium(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument(f"--window-size={self.viewport['width']},{self.viewport['height']}")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        if self.user_agent:
            opts.add_argument(f"--user-agent={self.user_agent}")
        if self.proxy:
            opts.add_argument(f"--proxy-server={self.proxy}")

        self._browser = webdriver.Chrome(options=opts)
        self._browser.set_page_load_timeout(self.timeout // 1000)
        self._page = self._browser  # selenium driver IS the page target

    def close(self):
        """Shutdown browser and release resources."""
        try:
            if self._backend == "playwright":
                if self._context:
                    self._context.close()
                if self._browser:
                    self._browser.close()
                if self._playwright:
                    self._playwright.stop()
            elif self._backend == "selenium":
                if self._browser:
                    self._browser.quit()
        except Exception as e:
            logger.warning("BrowserSession.close error: %s", e)
        finally:
            self._playwright = None
            self._browser = None
            self._context = None
            self._page = None
            self._backend = "none"

    def __enter__(self) -> "BrowserSession":
        return self.start()

    def __exit__(self, *args):
        self.close()

    # ── Security Checks ────────────────────────────────────────────

    @staticmethod
    def _validate_url(url: str) -> None:
        """Enforce URL security policy. Raises BrowserSecurityError on violation."""
        if not url or not isinstance(url, str):
            raise BrowserSecurityError("URL kosong atau tidak valid")

        url = url.strip()

        # Block dangerous schemes
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme in BLOCKED_SCHEMES:
            raise BrowserSecurityError(
                f"URL scheme '{scheme}' diblokir untuk keamanan"
            )
        if not scheme:
            raise BrowserSecurityError("URL harus memiliki scheme (https://)")
        if scheme not in ("http", "https"):
            raise BrowserSecurityError(
                f"URL scheme '{scheme}' tidak diizinkan (hanya http/https)"
            )

        # Block local/internal hosts
        hostname = parsed.hostname or ""
        for pattern in BLOCKED_HOST_PATTERNS:
            if pattern.match(hostname):
                raise BrowserSecurityError(
                    f"URL host '{hostname}' diblokir (alamat lokal/internal)"
                )

    def _check_sensitive_domain(self, url: str) -> None:
        """Warn/block sensitive credential domains unless explicitly allowed."""
        if self.allow_sensitive:
            return
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        for domain in SENSITIVE_DOMAINS:
            if hostname == domain or hostname.endswith("." + domain):
                raise BrowserSecurityError(
                    f"Domain sensitif '{hostname}' diblokir tanpa allow_sensitive=True"
                )

    @staticmethod
    def _validate_selector(selector: str) -> None:
        """Prevent selector-based injection attacks."""
        if not selector or not isinstance(selector, str):
            raise BrowserSecurityError("Selector kosong")
        selector = selector.strip()
        if selector.startswith("/"):
            if not SAFE_XPATH_RE.match(selector):
                raise BrowserSecurityError(
                    f"XPath selector mengandung karakter berbahaya: {selector[:50]}"
                )
        else:
            if not SAFE_SELECTOR_RE.match(selector):
                raise BrowserSecurityError(
                    f"CSS selector mengandung karakter berbahaya: {selector[:50]}"
                )

    @staticmethod
    def _sanitize_input(text: str) -> str:
        """Sanitize text input to prevent injection via form fields."""
        if not isinstance(text, str):
            text = str(text)
        # Block null bytes and control chars (except newline/tab)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return text

    # ── Core Operations ────────────────────────────────────────────

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> Dict[str, Any]:
        """Navigate to URL. Returns status info dict.

        Args:
            url: Target URL (must be http/https, non-local)
            wait_until: Playwright wait strategy | selenium: ignored
        """
        self._validate_url(url)
        self._check_sensitive_domain(url)

        result = {"url": url, "status": None, "title": "", "backend": self._backend}

        if self._backend == "playwright":
            response = self._page.goto(url, wait_until=wait_until)
            result["status"] = response.status if response else None
            result["title"] = self._page.title()
        elif self._backend == "selenium":
            self._page.get(url)
            result["status"] = 200  # selenium doesn't expose status easily
            result["title"] = self._page.title
        else:
            raise BrowserSecurityError("Browser belum di-start")

        logger.info("navigate → %s (status=%s)", result["url"], result["status"])
        return result

    def click(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Click element matching selector. Returns True on success."""
        self._validate_selector(selector)

        if self._backend == "playwright":
            self._page.click(selector, timeout=timeout or self.timeout)
        elif self._backend == "selenium":
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            by = By.XPATH if selector.startswith("/") else By.CSS_SELECTOR
            wait = WebDriverWait(self._page, (timeout or self.timeout) // 1000)
            el = wait.until(EC.element_to_be_clickable((by, selector)))
            el.click()
        else:
            raise BrowserSecurityError("Browser belum di-start")

        logger.info("click → %s", selector)
        return True

    def fill(self, selector: str, text: str, timeout: Optional[int] = None) -> bool:
        """Fill input/textarea matching selector with text."""
        self._validate_selector(selector)
        text = self._sanitize_input(text)

        if self._backend == "playwright":
            self._page.fill(selector, text, timeout=timeout or self.timeout)
        elif self._backend == "selenium":
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            by = By.XPATH if selector.startswith("/") else By.CSS_SELECTOR
            wait = WebDriverWait(self._page, (timeout or self.timeout) // 1000)
            el = wait.until(EC.element_to_be_clickable((by, selector)))
            el.clear()
            el.send_keys(text)
        else:
            raise BrowserSecurityError("Browser belum di-start")

        logger.info("fill → %s (%d chars)", selector, len(text))
        return True

    def screenshot(
        self,
        path: str = "screenshot.png",
        full_page: bool = False,
    ) -> str:
        """Save screenshot to path. Returns absolute file path."""
        if not path or not isinstance(path, str):
            raise BrowserSecurityError("Path screenshot tidak valid")

        # Ensure output dir exists and is writable
        abs_path = os.path.realpath(os.path.expanduser(path))
        os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)

        if self._backend == "playwright":
            self._page.screenshot(path=abs_path, full_page=full_page)
        elif self._backend == "selenium":
            self._page.save_screenshot(abs_path)
        else:
            raise BrowserSecurityError("Browser belum di-start")

        size = os.path.getsize(abs_path)
        if size > MAX_SCREENSHOT_BYTES:
            logger.warning("Screenshot besar: %d bytes (max %d)", size, MAX_SCREENSHOT_BYTES)

        logger.info("screenshot → %s (%d bytes)", abs_path, size)
        return abs_path

    def extract_text(self, selector: Optional[str] = None) -> str:
        """Extract text content. If selector given, extract from that element only."""
        if selector:
            self._validate_selector(selector)

        if self._backend == "playwright":
            if selector:
                el = self._page.query_selector(selector)
                text = el.inner_text() if el else ""
            else:
                text = self._page.inner_text("body")
        elif self._backend == "selenium":
            from selenium.webdriver.common.by import By

            if selector:
                by = By.XPATH if selector.startswith("/") else By.CSS_SELECTOR
                els = self._page.find_elements(by, selector)
                text = els[0].text if els else ""
            else:
                text = self._page.find_element(By.TAG_NAME, "body").text
        else:
            raise BrowserSecurityError("Browser belum di-start")

        if len(text) > MAX_EXTRACT_CHARS:
            logger.warning(
                "extract_text truncated: %d → %d chars", len(text), MAX_EXTRACT_CHARS
            )
            text = text[:MAX_EXTRACT_CHARS] + "\n... [TRUNCATED]"

        return text

    def extract_html(self, selector: Optional[str] = None) -> str:
        """Extract inner HTML. If selector given, extract from that element only."""
        if selector:
            self._validate_selector(selector)

        if self._backend == "playwright":
            if selector:
                el = self._page.query_selector(selector)
                html = el.inner_html() if el else ""
            else:
                html = self._page.content()
        elif self._backend == "selenium":
            from selenium.webdriver.common.by import By

            if selector:
                by = By.XPATH if selector.startswith("/") else By.CSS_SELECTOR
                els = self._page.find_elements(by, selector)
                html = els[0].get_attribute("innerHTML") if els else ""
            else:
                html = self._page.page_source
        else:
            raise BrowserSecurityError("Browser belum di-start")

        if len(html) > MAX_EXTRACT_CHARS:
            html = html[:MAX_EXTRACT_CHARS] + "\n... [TRUNCATED]"

        return html

    def get_url(self) -> str:
        """Return current page URL."""
        if self._backend == "playwright":
            return self._page.url
        elif self._backend == "selenium":
            return self._page.current_url
        return ""

    def wait(self, seconds: float = 1.0) -> None:
        """Explicit wait (seconds). Prefer selectors over this."""
        time.sleep(max(0, min(seconds, 30)))  # cap at 30s

    def evaluate(self, expression: str) -> Any:
        """Evaluate JS expression in page context. Returns result.

        Security: expression is checked for obviously dangerous patterns.
        """
        if not expression or not isinstance(expression, str):
            raise BrowserSecurityError("Expression kosong")

        # Block dangerous JS patterns
        dangerous = re.compile(
            r"(fetch|XMLHttpRequest|WebSocket|import\s*\(|require\s*\(|"
            r"document\.cookie|localStorage|sessionStorage|indexedDB|"
            r"window\.location\s*=|document\.location\s*=|eval\s*\()",
            re.I,
        )
        if dangerous.search(expression):
            raise BrowserSecurityError(
                f"JS expression mengandung operasi berbahaya: {expression[:80]}"
            )

        if self._backend == "playwright":
            return self._page.evaluate(expression)
        elif self._backend == "selenium":
            return self._page.execute_script(expression)
        else:
            raise BrowserSecurityError("Browser belum di-start")

    @property
    def backend(self) -> str:
        """Current backend: 'playwright' or 'selenium'."""
        return self._backend

    @property
    def is_active(self) -> bool:
        """True if browser session is open."""
        return self._backend != "none" and self._page is not None


# ── Convenience Functions ──────────────────────────────────────────

def quick_scrape(url: str, selector: Optional[str] = None) -> str:
    """One-shot: navigate + extract_text. Returns text content."""
    with BrowserSession() as session:
        session.navigate(url)
        return session.extract_text(selector)


def quick_screenshot(url: str, path: str = "screenshot.png") -> str:
    """One-shot: navigate + screenshot. Returns file path."""
    with BrowserSession() as session:
        session.navigate(url)
        return session.screenshot(path)