import subprocess, re
from collections import Counter

out = subprocess.run(
    ["bash", "-lc", r'''grep -rn -B1 "^\s*pass\s*$" --include="*.py" aeryn_core/ scripts/ apps/ | grep -v "venv"'''],
    cwd="/home/sen/aeryn-core-agent",
    capture_output=True, text=True
).stdout

lines = out.split("\n")
cats = Counter()
stub_methods = []
except_handlers = []
control_no_ops = []
class_bodies = []
other = []

prev_context = None
i = 0
while i < len(lines):
    ln = lines[i]
    if ln.startswith("-- "):
        i += 1
        continue
    # context line from -B1: "file:line-content" (dash separator)
    cm = re.match(r'^(?P<file>[^:]+):(?P<line>\d+)-(?P<content>.+)$', ln)
    if cm and prev_context is None:
        prev_context = cm.group("content").strip()
        i += 1
        continue
    # match line: "file:line:content" (colon separator)
    m = re.match(r'^(?P<file>[^:]+):(?P<line>\d+):(?P<content>.+)$', ln)
    if m:
        ctx = (prev_context or "").strip()
        fileline = f"{m.group('file')}:{m.group('line')}"
        stripped = m.group("content").strip()
        if ctx.startswith("except") or ctx.startswith("try:") or ctx.startswith("else:") or ctx.startswith("finally:"):
            except_handlers.append((fileline, ctx))
            cats["except/try/else/finally"] += 1
        elif ctx.startswith("if ") or ctx.startswith("elif ") or ctx.startswith("with ") or ctx.startswith("for ") or ctx.startswith("while "):
            control_no_ops.append((fileline, ctx))
            cats["if/elif/with/for/while"] += 1
        elif ctx.startswith("class "):
            class_bodies.append((fileline, ctx))
            cats["class-body"] += 1
        elif ctx.startswith("def "):
            stub_methods.append((fileline, ctx))
            cats["def-stub"] += 1
        else:
            other.append((fileline, ctx))
            cats["other"] += 1
        prev_context = None
        i += 1
        continue
    # unexpected line
    i += 1

print("=== CATEGORY COUNTS ===")
for k, v in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"{k}: {v}")
print("TOTAL:", sum(cats.values()))

print("\n=== DEF STUBS ===")
for f, c in stub_methods:
    print(f"  {f}  ctx={c!r}")
print("\n=== CLASS BODIES ===")
for f, c in class_bodies:
    print(f"  {f}  ctx={c!r}")
print("\n=== CONTROL NO-OPS ===")
for f, c in control_no_ops:
    print(f"  {f}  ctx={c!r}")
print("\n=== OTHER ===")
for f, c in other:
    print(f"  {f}  ctx={c!r}")
