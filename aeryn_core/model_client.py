"""ModelClient — Klien LLM OpenAI-compatible untuk agentic loop aeryn.

Membaca kredensial dari env (OPENROUTER_API_KEY / NOUS_API_KEY) atau
~/.hermes/.env jika ada. Tidak menyimpan kredensial di kode.
"""
import json
import os
import time
import urllib.request


class ModelClient:
    def __init__(self, provider: str = None, model: str = None, api_key: str = None):
        self.provider = provider or os.getenv("AERYN_LLM_PROVIDER", "openrouter")
        if self.provider == "gemini":
            self.base_url = os.getenv("GEMINI_BASE_URL",
                                      "https://generativelanguage.googleapis.com/v1beta/openai/")
            self.model = model or os.getenv("AERYN_GEMINI_MODEL", "gemini-2.5-pro")
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
        """Fallback: baca API key dari ~/.hermes/.env (secrets-only file)."""
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
        # PRIMARY: NOUS stealth/ox-alpha (paling reliable, instruction-following)
        if key("NOUS_API_KEY"):
            cands.append((os.getenv("NOUS_BASE_URL",
                                     "https://inference-api.nousresearch.com/v1"),
                           os.getenv("NOUS_MODEL", "stealth/ox-alpha"),
                           key("NOUS_API_KEY")))
        # FALLBACK: Gemini (untuk complex tasks)
        if key("GEMINI_API_KEY"):
            cands.append((os.getenv("GEMINI_BASE_URL",
                                     "https://generativelanguage.googleapis.com/v1beta/openai/"),
                           os.getenv("AERYN_GEMINI_MODEL", "gemini-2.5-pro"),
                           key("GEMINI_API_KEY")))
        # FALLBACK: OpenRouter + Groq chain
        if self.provider == "openrouter":
            if key("GROQ_API_KEY"):
                for gm in (os.getenv("AERYN_GROQ_MODEL") or
                           ["openai/gpt-oss-20b",
                            "qwen/qwen3.6-27b"]):
                    cands.append(("https://api.groq.com/openai/v1", gm,
                                  key("GROQ_API_KEY")))
            cands.append(("https://openrouter.ai/api/v1", self.model,
                          key("OPENROUTER_API_KEY", "NOUS_API_KEY")))
            for m in self.fallback_models:
                cands.append(("https://openrouter.ai/api/v1", m,
                              key("OPENROUTER_API_KEY", "NOUS_API_KEY")))
            # Fallback lintas-provider: NVIDIA NIM (key terpisah).
            if key("NVIDIA_API_KEY"):
                nv_first = os.getenv("AERYN_NVIDIA_MODEL")
                nvs = ([nv_first] if nv_first else
                       ["meta/llama-3.1-8b-instruct",
                        "nvidia/llama-3.3-nemotron-super-49b-v1.5"])
                for nm in nvs:
                    cands.append(("https://integrate.api.nvidia.com/v1", nm,
                                  key("NVIDIA_API_KEY")))
        else:  # nous
            cands.append((self.base_url, self.model, key("NOUS_API_KEY")))
            if key("NVIDIA_API_KEY"):
                cands.append(("https://integrate.api.nvidia.com/v1",
                              os.getenv("AERYN_NVIDIA_MODEL",
                                        "meta/llama-3.1-8b-instruct"),
                              key("NVIDIA_API_KEY")))
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
            payload["model"] = model_name
            req = urllib.request.Request(
                f"{base_url}/chat/completions",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    # Cloudflare Groq memblok UA Python-urllib (error 1010)
                    "User-Agent": "aeryn-core/27 (+https://github.com/sen/aeryn-core)",
                },
            )
            for attempt in range(3):  # retry dgn backoff utk 429/5xx
                try:
                    with urllib.request.urlopen(req, timeout=75) as resp:
                        out = json.loads(resp.read())
                    if model_name != self.model:
                        out.setdefault("model_used", model_name)  # jejak fallback
                    return out
                except urllib.error.HTTPError as e:
                    last_err = e
                    if e.code in (400, 401, 402, 403, 404):
                        break   # slug/endpoint invalid → kandidat berikutnya
                    if e.code == 429:
                        # V28: rate limit → rotasi kandidat SEGERA tanpa
                        # sleep (sleep 8s di sini bikin run menggantung;
                        # kandidat berikutnya sudah cukup sebagai jeda).
                        break
                    if e.code in (500, 502, 503):
                        break   # provider ini bermasalah → kandidat berikutnya
                    raise
                except (TimeoutError, OSError) as e:
                    # Timeout baca/koneksi: provider lambat/hang → rotasi model
                    # berikutnya SEGERA (dulu ini bikin seluruh run menggantung).
                    last_err = e
                    break
        raise last_err
