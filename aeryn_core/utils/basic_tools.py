"""V39.2 — Dua tool baru dari analisa episode nyata + fallback map lengkap.

1. `datetime_now` — pertanyaan waktu/tanggal muncul berulang; tanpa tool,
   model menebak (halusinasi tanggal).
2. `math_calc` — kalkulasi aman via AST whitelist (tanpa eval bebas).

Plus: FALLBACK_MAP dilengkapi untuk SEMUA tool (sebelumnya 7/12).
"""
import ast
import datetime
import json
import operator
import zoneinfo

JAKARTA = zoneinfo.ZoneInfo("Asia/Jakarta")

MATH_OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
            ast.Mult: operator.mul, ast.Div: operator.truediv,
            ast.Pow: operator.pow, ast.Mod: operator.mod,
            ast.USub: operator.neg, ast.UAdd: operator.pos,
            ast.FloorDiv: operator.floordiv}


def _safe_eval(node, _depth=0):
    # V39.4-SEC — depth + operand guard: cegah DoS via ekspresi raksasa
    # ("9**9**9" menggantung thread daemon >30s menghitung bigint raksasa)
    if _depth > 20:
        raise ValueError("ekspresi terlalu dalam (maks 20 level)")
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        v = node.value
        if abs(v) > 10**12:
            raise ValueError(f"angka terlalu besar: {v}")
        return v
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in MATH_OPS:
            raise ValueError("operator tidak diizinkan")
        # pow dengan eksponen/radiks besar → tolak sebelum komputasi
        if isinstance(node.op, ast.Pow):
            left = _safe_eval(node.left, _depth + 1)
            right = _safe_eval(node.right, _depth + 1)
            if abs(right) > 1000 or abs(left) > 10**6:
                raise ValueError("eksponen/radiks terlalu besar (maks b<1000)")
            result = MATH_OPS[ast.Pow](left, right)
            if abs(result) > 10**18:
                raise ValueError("hasil terlalu besar (>10^18)")
            return result
        return MATH_OPS[op_type](_safe_eval(node.left, _depth + 1),
                                 _safe_eval(node.right, _depth + 1))
    if isinstance(node, ast.UnaryOp) and type(node.op) in MATH_OPS:
        return MATH_OPS[type(node.op)](_safe_eval(node.operand, _depth + 1))
    raise ValueError(f"ekspresi tidak diizinkan: {ast.dump(node)[:60]}")


def math_calc(expression: str):
    """Kalkulator aritmetika aman (AST-whitelist, TANPA eval bebas)."""
    expr = str(expression or "").strip().rstrip("=")
    try:
        tree = ast.parse(expr, mode="eval")
        result = _safe_eval(tree.body)
        result = round(result, 6)
        return {"ok": True, "expression": expr[:200], "result": result}
    except (ValueError, SyntaxError, ZeroDivisionError, TypeError) as e:
        return {"ok": False, "error": f"ekspresi tidak valid: {e}"}


def datetime_now(tz: str = "Asia/Jakarta"):
    """Waktu sekarang — sumber kebenaran tunggal, anti halusinasi tanggal."""
    try:
        tz_obj = zoneinfo.ZoneInfo(tz)
    except Exception:
        return {"ok": False, "error": f"timezone tidak dikenal: {tz}"}
    now = datetime.datetime.now(tz_obj)
    days_id = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu",
               "Minggu"]
    return {"ok": True,
            "iso": now.isoformat(timespec="seconds"),
            "tanggal": now.strftime("%Y-%m-%d"),
            "hari": days_id[now.weekday()],
            "jam": now.strftime("%H:%M:%S"),
            "tz": tz}


DATETIME_SCHEMA = {
    "type": "function", "function": {"name": "datetime_now",
    "description": ("Dapatkan tanggal/jam/waktu SEKARANG yang akurat "
                    "(jangan menebak). Default WIB."),
    "parameters": {"type": "object", "properties": {
        "tz": {"type": "string", "description": "IANA timezone, default "
              "Asia/Jakarta"}}}},
}

MATH_SCHEMA = {
    "type": "function", "function": {"name": "math_calc",
    "description": ("Hitung ekspresi aritmetika aman (+ - * / % // **). "
                    "Contoh: '25*4+10' atau '2**10'."),
    "parameters": {"type": "object", "properties": {
        "expression": {"type": "string"}}, "required": ["expression"]}},
}
