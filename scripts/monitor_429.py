"""429 monitor + downtime tracker — laporan frekuensi & durasi tiap-provider.

Probe M61: audit provider health. Laporan tiap 5 menit (atau manual)
berapa sering tiap provider 429, berapa lama downtime total.

Usage:
    python3 scripts/monitor_429.py  # jalan 1 siklus saja (cepat & selesai)
    python3 scripts/monitor_429.py --watch       # loop tiap 5 menit
    python3 scripts/monitor_429.py --report      # tampilkan ringkasan sejauh ini
"""
import argparse, json, os, sys, time, urllib.request, urllib.error, logging
from dataclasses import dataclass
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs(os.path.expanduser("~/hermes"), exist_ok=True)

# V39.11 — baca endpoint dari ModelClient biar konsisten dengan runtime.
from aeryn_core.model_client import ModelClient

REPORT_FILE = os.path.expanduser("~/hermes/429_monitor_report.json")
LOG_FILE = os.path.expanduser("~/hermes/429_monitor.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@dataclass
class PStat:
    total: int = 0
    ok: int = 0
    failed: int = 0
    rate_429: int = 0
    rate_4xx: int = 0
    rate_5xx: int = 0
    timeout: int = 0
    downtime_s: float = 0.0

    def to_dict(self):
        return {
            "total": self.total, "ok": self.ok, "failed": self.failed,
            "rate_429": self.rate_429, "rate_4xx": self.rate_4xx,
            "rate_5xx": self.rate_5xx,
            "timeout": self.timeout, "downtime_s": round(self.downtime_s, 1),
        }


def _collect_candidates():
    """Bangun daftar (name, url, key) valid dari environment Hermes."""
    client = ModelClient()
    seen = set()
    cands = []
    for url, model, key in client._endpoint_candidates():
        ident = (url, key)
        if ident in seen:
            continue
        seen.add(ident)
        label = model if "nousresearch" in url or "groq" in url else model
        urlpart = url.split("//")[1].split(".")[0] if "//" in url else url[:12]
        cands.append((f"{label[:22]}@{urlpart}", url, key, model))
    return cands


def _ping(url: str, key: str, model: str = "gpt-2b") -> tuple:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }
    req = urllib.request.Request(
        f"{url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "Mozilla/5.0 (X11; Linux aarch64) "
                          "AppleWebKit/537.36 Chrome/120.0 "
                          "Safari/537.36",
            "X-Client": "aeryn-monitor/39",
        },
    )
    start = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        dur = time.time() - start
        body = resp.read()[:200]
        return (resp.status, dur, body, False)
    except urllib.error.HTTPError as e:
        dur = time.time() - start
        try:
            body = e.read()[:200]
        except Exception:
            body = b"<no body>"
        return (e.code, dur, body, True)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        dur = time.time() - start
        return (-1, dur, str(type(e).__name__).encode(), True)


def run_once(stats: Dict[str, PStat]) -> Dict[str, PStat]:
    candidates = _collect_candidates()
    logging.info("monitor ping -> %d providers", len(candidates))
    for label, url, key, model in candidates:
        code, dur, body, failed = _ping(url, key, model)
        stat = stats.setdefault(label, PStat())
        stat.total += 1
        if not failed:
            stat.ok += 1
        else:
            stat.failed += 1
            if code == 429:
                stat.rate_429 += 1
                logging.warning("429: %s (%s)", label, body[:80])
            elif 400 <= code < 500:
                stat.rate_4xx += 1
            elif 500 <= code < 600:
                stat.rate_5xx += 1
            elif code == -1:
                stat.timeout += 1
            stat.downtime_s += dur
    return stats


def print_report(stats: Dict[str, PStat], out=sys.stdout):
    out.write("\n=== 429 + Provider Health Report ===\n")
    out.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    out.write(f"{'Provider':<26} {'Total':>5} {'OK':>4} {'FAIL':>5} "
              f"{'429':>4} {'4xx':>4} {'5xx':>4} {'TO':>3} {'Down(s)':>8}\n")
    out.write("-" * 73 + "\n")
    for name, s in sorted(stats.items()):
        out.write(f"{name:<26} {s.total:>5} {s.ok:>4} {s.failed:>5} "
                  f"{s.rate_429:>4} {s.rate_4xx:>4} {s.rate_5xx:>4} "
                  f"{s.timeout:>3} {s.downtime_s:>8.1f}\n")
    out.write("-" * 73 + "\n")
    total_all = sum(s.total for s in stats.values())
    rate429 = sum(s.rate_429 for s in stats.values())
    ok_all = sum(s.ok for s in stats.values())
    success = ok_all / total_all * 100 if total_all else 0
    out.write(f"TOTAL:                        {total_all:>5} "
              f"{ok_all:>4} {total_all - ok_all:>5} {rate429:>4} "
              f"success={success:.1f}%\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true",
                    help="Loop tiap 5 menit hingga di-Ctrl-C")
    ap.add_argument("--report", action="store_true",
                    help="Tampilkan ringkasan terakhir")
    ap.add_argument("--interval", type=int, default=300,
                    help="Interval loop (detik), default 300 (5m)")
    args = ap.parse_args()

    if args.report:
        if not os.path.exists(REPORT_FILE):
            print_report({})
            return 0
        raw = json.load(open(REPORT_FILE))
        stats = {k: PStat(**v) for k, v in raw.items()}
        print_report(stats)
        return 0

    stats: Dict[str, PStat] = {}
    if os.path.exists(REPORT_FILE):
        raw = json.load(open(REPORT_FILE))
        stats = {k: PStat(**v) for k, v in raw.items()}

    if not args.watch:
        run_once(stats)
        print_report(stats)
        out = {k: s.to_dict() for k, s in stats.items()}
        json.dump(out, open(REPORT_FILE, "w"), indent=2)
        return 0

    print(f"Monitoring started - interval {args.interval}s. Ctrl-C to stop.")
    try:
        while True:
            run_once(stats)
            print_report(stats)
            out = {k: s.to_dict() for k, s in stats.items()}
            json.dump(out, open(REPORT_FILE, "w"), indent=2)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped. Final report:")
        print_report(stats)
        json.dump({k: s.to_dict() for k, s in stats.items()},
                  open(REPORT_FILE, "w"), indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
