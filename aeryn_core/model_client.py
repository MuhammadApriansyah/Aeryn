"""ModelClient — Klien LLM Openai-compatible untuk agentic loop aeryn.

Membaca kredensial dari env (OPENROUTER_API_KEY / NOUS_API_KEY) atau
~/.hermes/.env jika ada. Tidak menyimpan kredensial di kode.
"""
import json
import os
import time
import urllib.request


class CircuitBreaker:
    """Anti-429 adaptive backoff per provider.

    V39.11 — tiap provider dapatnya CircuitBreaker; 429 berulang →
    cooldown eksponen, beri jeda ke provider lain. Fresh per proses
    (in-memory); state tidak persist — jadi per-restart selalu
    'semangat baru'.

    State: closed (normal) → open (cooldown) → half-open (test sekali)
    """
    def __init__(self, max_failures: int = 3, base_wait: float = 2.0,
                 max_wait: int = 60):
        self._max_failures = max_failures
        self._base_wait = base_wait
        self._max_wait = max_wait
        self._fail_count = 0
        self._fail_time = 0.0
        self._last_wait = base_wait

    def record_failure(self):
        self._fail_count += 1
        self._fail_time = time.time()
        # exponential backoff
        self._last_wait = min(self._base_wait * (2 ** (self._fail_count - 1)),
                              self._max_wait)

    def reset(self):
        self._fail_count = 0
        self._fail_time = 0.0
        self._last_wait = self._base_wait

    def is_opened(self) -> bool:
        return self._fail_count >= self._max_failures

    def retry_after(self) -> float:
        return self._last_wait

    def should_skip(self, now: float | None = None) -> bool:
        """True bila dalam cooldown (bukan waktu half-open test)."""
        if not self.is_opened():
            return False
        now = now or time.time()
        if now - self._fail_time >= self._last_wait:
            # masuk half-open: boleh coba sekali
            return False
        return True


# V39.11 — global circuit breaker per provider key; persist lifetime
# process saja (bukan tiap chain). Supaya 429 berulang = cooldown.
_PROVIDER_CBS: dict[str, CircuitBreaker] = {}
_CB_MAX_FAILURE = 3  # 429 berulang 3× = cooldown


def _get_cb(base_url: str) -> CircuitBreaker:
    if base_url not in _PROVIDER_CBS:
        _PROVIDER_CBS[base_url] = CircuitBreaker(max_failures=_CB_MAX_FAILURE)
    return _PROVIDER_CBS[base_url]


class ModelClient:
    def __init__(self, provider: str = None, model: str = None, api_key: str = None):
        self.provider = provider or os.getenv("AERYN_LLM_PROVIDER", "openrouter")
        if self.provider == "gemini":
            self.base_url = os.getenv("GEMINI_BASE_URL",
                                      "https://generativelanguage.googleapis.com/v1beta/openai/")
            # V39.12a — gemini-2.5-pro DEPRECATED; pakai 2.0-flash (stable)
            self.model = model or os.getenv("AERYN_GEMINI_MODEL", "gemini-2.0-flash")
            self.fallback_models = []
        elif self.provider == "openrouter":
            self.base_url = "https://openrouter.ai/api/v1"
            self.model = model or os.getenv("AERYN_LLM_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free")
            # Rantai fallback :free — dipakai berurutan saat model utama kena 429
            self.fallback_models = [
                m.strip() for m in os.getenv(
                    "AERYN_LLM_FALLBACKS",
                    "nvidia/nemotron-3-super-120b-a12b:free,poolside/laguna-s-2.1:free").split(",")
                if m.strip() and m.strip() != self.model
            ]
        else:  # nous
            self.base_url = "https://inference-api.nousresearch.com/v1"
            self.model = model or os.getenv("AERYN_LLM_MODEL", "Hermes-4-405B")
            self.fallback_models = []
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("NOUS_API_KEY") or ""

    @staticmethod
    def _load_hermes_env():
        """Fallback: baca API key dari ~/.hermes/.env + auth.json Hermes.

        V34: NOUS pakai OAuth short-lived — agent_key di ~/.hermes/auth.json
        di-refresh otomatis oleh Hermes, jadi dibaca FRESH setiap chain
        dibangun (bukan di-cache ke env permanen).
        """
        wanted = ("OPENROUTER_API_KEY", "NOUS_API_KEY", "NVIDIA_API_KEY",
                  "GROQ_API_KEY", "GEMINI_API_KEY")
        for cand in (os.path.expanduser("~/.hermes/.env"),):
            try:
                for line in open(cand):
                    line = line.strip()
                    if "=" not in line:
                        continue
                    name, _, val = line.partition("=")
                    val = val.strip().strip('"').strip("'")
                    if name in wanted and not os.getenv(name):
                        os.environ[name] = val
                    # Map OPENROUTER_API_KEY sebagai NOUS jika NOUS belum set
                    if name == "OPENROUTER_API_KEY" and not os.getenv("NOUS_API_KEY"):
                        os.environ["NOUS_API_KEY"] = val
            except OSError:
                pass
        # V34 — NOUS OAuth: ambil agent_key terkini dari auth.json Hermes.
        # Selalu overwrite env supaya token rotasi ikut (key statis = mati
        # besok pagi). Ini sumber paling valid: dipakai Hermes sendiri.
        try:
            import json as _json
            auth_path = os.path.expanduser("~/.hermes/auth.json")
            with open(auth_path) as f:
                nous = _json.load(f)["providers"]["nous"]
            ak = nous.get("agent_key") or ""
            if ak:
                os.environ["NOUS_API_KEY"] = ak
                bu = nous.get("inference_base_url") or ""
                if bu:
                    os.environ.setdefault("NOUS_BASE_URL",
                                          bu.rstrip("/") + "/v1"
                                          if not bu.endswith("/v1") else bu)
        except Exception:
            pass  # auth.json tidak ada/rusak → jatuh ke key statis biasa

    def _endpoint_candidates(self):
        """Rantai (base_url, model, api_key_env) yang dicoba berurutan."""
        self._load_hermes_env()

        def key(*names):
            for n in names:
                v = os.getenv(n)
                if v:
                    return v
            return ""

        cands = []
        # PRIMARY: NOUS longcat (free, reliable via Hermes OAuth)
        if key("NOUS_API_KEY"):
            cands.append((os.getenv("NOUS_BASE_URL",
                                     "https://inference-api.nousresearch.com/v1"),
                           os.getenv("NOUS_MODEL", "meituan/longcat-2.0:free"),
                           key("NOUS_API_KEY")))
        # SECONDARY: Gemini 3.5 flash lite (fast, cheap)
        if key("GEMINI_API_KEY"):
            cands.append((os.getenv("GEMINI_BASE_URL",
                                     "https://generativelanguage.googleapis.com/v1beta/openai/"),
                           os.getenv("AERYN_GEMINI_MODEL", "gemini-3.5-flash-lite"),
                           key("GEMINI_API_KEY")))
        # TERTIARY: OpenRouter (many models)
        if key("OPENROUTER_API_KEY"):
            cands.append(("https://openrouter.ai/api/v1",
                           os.getenv("AERYN_OPENROUTER_MODEL", "openai/gpt-4o-mini"),
                           key("OPENROUTER_API_KEY")))
            for m in self.fallback_models:
                cands.append(("https://openrouter.ai/api/v1", m,
                              key("OPENROUTER_API_KEY")))
        # FALLBACK: Groq (fast, free tier)
        if key("GROQ_API_KEY"):
            for gm in (os.getenv("AERYN_GROQ_MODEL") or
                       ["openai/gpt-oss-20b",
                        "openai/gpt-oss-120b"]):
                cands.append(("https://api.groq.com/openai/v1", gm,
                              key("GROQ_API_KEY")))
        return [(u, m, k) for u, m, k in cands if k]

    def chat(self, messages, tools=None, temperature=0.4, max_tokens=2048):
        payload = {"messages": messages, "temperature": temperature,
                   "max_tokens": max_tokens}
        # V32 — tools=None: jangan kirim key "tools" sama sekali
        # (Gemini/Groq tetap akan panggil tool jika schema tersedia)
        if tools is not None:
            payload["tools"] = tools
        # gpt-oss (Groq): reasoning default "medium" makan token & bikin
        # content kosong di max_tokens kecil — turunkan ke "low".
        candidates = self._endpoint_candidates()
        for base_url, model_name, _k in candidates:
            # reasoning_effort hanya untuk Groq gpt-oss
            if "gpt-oss" in model_name:
                payload.setdefault("reasoning_effort", "low")
            # Gemini tidak support reasoning_effort — hapus jika ada
            elif "gemini" in model_name and "reasoning_effort" in payload:
                del payload["reasoning_effort"]
            break
        if not candidates:
            raise RuntimeError(
                "No API key: set OPENROUTER_API_KEY/NOUS_API_KEY/NVIDIA_API_KEY "
                "di env atau ~/.hermes/.env")
        last_err = None
        for base_url, model_name, api_key in candidates:
            # V39.11 — check circuit breaker per provider
            cb = _get_cb(base_url)
            if cb.should_skip():
                continue

            payload["model"] = model_name
            req = urllib.request.Request(
                f"{base_url}/chat/completions",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    # V34 — Cloudflare Groq blok UA Python-urllib (1010).
                    # V39.10b — Nous inference-api juga kini blok custom
                    # UA (403 code 1010 → semua provider 404 di chain).
                    # Pakai UA browser; identitas tetap di header X-Client.
                    "User-Agent": "Mozilla/5.0 (X11; Linux aarch64) "
                                  "AppleWebKit/537.36 Chrome/120.0 "
                                  "Safari/537.36",
                    "X-Client": "aeryn-core/39",
                },
            )
            # V39.11 — attempt dikurangi jadi 1: 429 = rotasi provider segera.
            for attempt in range(1):
                try:
                    with urllib.request.urlopen(req, timeout=75) as resp:
                        out = json.loads(resp.read())
                    if model_name != self.model:
                        out.setdefault("model_used", model_name)  # jejak fallback
                    cb.reset()  # success = sehat kembali
                    return out
                except urllib.error.HTTPError as e:
                    last_err = e
                    if e.code in (400, 401, 402, 403, 404):
                        break   # slug/endpoint invalid → kandidat berikutnya
                    if e.code == 429:
                        # V39.11 — record failure di circuit breaker
                        cb.record_failure()
                        break
                    if e.code in (500, 502, 503):
                        # provider bermasalah → hitung kegagalan juga
                        cb.record_failure()
                        break
                    raise
                except (TimeoutError, OSError) as e:
                    # Timeout baca/koneksi: provider lambat/hang
                    cb.record_failure()
                    last_err = e
                    break
        raise last_err or RuntimeError("No candidates left (all skipped by drift/rate-limit)")
