#!/usr/bin/env python3
"""LEDGER2: tool keuangan harian — wire AccountingLedgerEngine (Rust) ke
tool_runtime + trust layer intent.

Modul: aeryn_core/platform/ledger_tools.py
- tool_spending_log(text) — parse 'pengeluaran/penghasilan N deskripsi'
  → ledger entry (persist di PG facts + in-memory Rust engine).
- tool_balance() — saldo + total bulan ini + per kategori.
- tool_monthly_report(month) — laporan bulanan (untuk briefing).
Real API only — no test doubles."""

import json
import re
from datetime import datetime


def _ledger_persist(entity: str, predicate: str, fact: dict) -> str:
    """Persist transaksi ke PG facts (bitemporal — audit trail)."""
    from aeryn_core.memory.fact_store import get_fact_store
    get_fact_store().record(entity=entity, predicate=predicate,
                            fact=json.dumps(fact), source="ledger",
                            confidence=1.0)
    return "ok"


def tool_spending_log(text: str, user_id: str = "sen") -> dict:
    """Parse natural language keuangan → ledger entry.

    Format dikenali (kasual Indonesia):
    - 'pengeluaran 15000 makan siang' → expense 15000 [makan siang]
    - 'pengeluaran 15k makan' → expense 15000
    - 'penghasilan 3000000 gaji' → income 3000000
    - 'gajian 3jt' → income 3000000
    """
    if not text:
        return {"ok": False, "error": "text kosong"}
    msg = text.strip().lower()

    # Deteksi kind
    is_income = any(k in msg for k in ("penghasilan", "gajian", "gaji", "income", "masuk", "terima"))
    kind = "income" if is_income else "expense"

    # Parse angka: 15000, 15k, 15.000, 3jt, 1.5jt
    amount = None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(jt|juta|k|ribu|rb)?", msg)
    if m:
        num = float(m.group(1).replace(",", "").replace(".", "")) if m.group(1) and "." in m.group(1) and len(m.group(1).split(".")[-1]) == 3 else None
        if num is None:
            num = float(m.group(1).replace(",", ""))
        suffix = m.group(2)
        if suffix in ("jt", "juta"):
            amount = num * 1_000_000
        elif suffix in ("k", "ribu", "rb"):
            amount = num * 1_000
        else:
            amount = num
    if amount is None or amount <= 0:
        return {"ok": False, "error": "jumlah tidak dikenali — sebutkan angka (mis. 'pengeluaran 15k makan')"}

    # Parse deskripsi: setelah angka ATAU sebelum angka (B3)
    desc_m = re.search(r"\d+(?:[.,]\d+)?\s*(?:jt|juta|k|ribu)?\s+(.+)", msg)
    if desc_m:
        desc = desc_m.group(1).strip()[:80]
    else:
        # B3: angka di akhir → deskripsi = teks SEBELUM angka,
        # buang kata intent/kerja + angka + suffix
        before = re.split(r"\d+(?:[.,]\d+)?\s*(?:jt|juta|k|ribu)?", msg)[0]
        before = re.sub(r"^(pengeluaran|penghasilan|beli|bayar|jajan|belanja|catat|log|top\s?up|topup)\s+", "", before).strip()
        desc = before[:80] if before else "transaksi"

    # Kategori sederhana (keyword)
    cat = "lainnya"
    cat_map = {
        "makan": "makan", "minum": "minuman", "kopi": "minuman",
        "bakso": "makan", "mie": "makan", "nasi": "makan", "ayam": "makan",
        "warung": "makan", "resto": "makan", "sate": "makan",
        "transport": "transportasi", "ojek": "transportasi", "bensin": "transportasi",
        "belanja": "belanja", "pulsa": "pulsa", "listrik": "tagihan",
        "sewa": "tempat tinggal", "gaji": "penghasilan", "bonus": "penghasilan",
    }
    for kw, c in cat_map.items():
        if kw in desc or kw in msg:
            cat = c
            break
    if kind == "income" and cat == "lainnya":
        cat = "penghasilan"

    today = datetime.now().strftime("%Y-%m-%d")
    fact = {"date": today, "description": desc, "amount": amount,
            "kind": kind, "category": cat, "user_id": user_id}

    try:
        # LEDGER2: entity unik per transaksi (finance:<uuid>) — bitemporal
        # menutup versi state per (entity, predicate); transaksi = EVENT
        # nyata yang harus tetap terbuka (tidak ditimpa transaksi berikut).
        import uuid as _uuid
        _ledger_persist(f"finance:{_uuid.uuid4().hex[:12]}", "transaction", fact)
    except Exception as e:
        return {"ok": False, "error": f"persist gagal: {str(e)[:150]}"}

    return {"ok": True, "fact": fact,
            "message": f"{'Pengeluaran' if kind == 'expense' else 'Penghasilan'} {desc} {amount:.0f} dicatat [kategori: {cat}]"}


def tool_balance() -> dict:
    """Saldo + total bulan ini + per kategori (Rust ledger engine)."""
    try:
        import aeryn_engine
        e = aeryn_engine.AccountingLedgerEngine()
        # Muat ulang entries dari PG facts (Rust engine in-memory kosong per process)
        from aeryn_core.database.neon_db import get_neon
        db = get_neon()
        rows = db.fetchall(
            "SELECT fact FROM facts WHERE predicate = 'transaction' "
            "AND tx_to IS NULL ORDER BY valid_from", None)
        month = datetime.now().strftime("%Y-%m")
        for r in rows or []:
            try:
                d = json.loads(r["fact"])
                e.add_entry(d.get("date", ""), d.get("description", ""),
                            float(d.get("amount", 0)), d.get("kind", "expense"),
                            d.get("category", "lainnya"))
            except Exception:
                continue
        return {"ok": True, "balance": e.balance(),
                "month": month,
                "total_expense": e.total_expense(month),
                "total_income": e.total_income(month),
                "by_category": e.by_category(month),
                "entry_count": e.entry_count()}
    except Exception as ex:
        return {"ok": False, "error": str(ex)[:200]}


def tool_monthly_report(month: str = "") -> dict:
    """Laporan bulanan (untuk briefing + endpoint)."""
    if not month:
        month = datetime.now().strftime("%Y-%m")
    b = tool_balance()
    if not b.get("ok"):
        return b
    return {"ok": True, "month": month,
            "income": b.get("total_income", 0),
            "expense": b.get("total_expense", 0),
            "balance": b.get("balance", 0),
            "by_category": b.get("by_category", {}),
            "transactions": b.get("entry_count", 0)}
