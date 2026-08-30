"""V61.0 — Shared DB endpoints router for Aeryn API."""
from fastapi import APIRouter
import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import aeryn_core.utils.patch_sqlite  # noqa

from aeryn_core.database.shared_db import get_shared_db
from aeryn_core.memory.vault import AerynVault
from aeryn_core.utils.logger import info, warn, error, log_exception

router = APIRouter()
_start_time = time.time()
_request_count = 0
_error_count = 0

  // Keep max 50 lines
  while (logViewer.children.length > 50) {
    logViewer.removeChild(logViewer.firstChild);
  }
  
  // Auto-scroll
  logViewer.scrollTop = logViewer.scrollHeight;
}

// SSE for logs
function connectLogStream() {
  const evtSource = new EventSource('/dashboard/stream');
  
  evtSource.addEventListener('log', function(e) {
    const data = JSON.parse(e.data);
    addLogLine(data.level || 'info', data.message);
  });
  
  return evtSource;
}

// ── Error Handling + Fallback ─────────────────
let sseRetries = 0;
const maxSseRetries = 3;
let fallbackToPolling = false;

function startFallbackPolling() {
  if (fallbackToPolling) return;
  fallbackToPolling = true;
  showToast('warning', 'Using fallback polling mode');
  
  setInterval(async () => {
    try {
      const r = await fetch('/dashboard/stats');
      const d = await r.json();
      if (!d.error && d.system) {
        const s = d.system;
        document.getElementById('mem').innerHTML = s.memory_used_mb + '<span class="unit">MB</span>';
        document.getElementById('mem-detail').textContent = s.memory_percent + '% of ' + s.memory_total_mb + ' MB';
        const memBar = document.getElementById('mem-bar');
        memBar.style.width = s.memory_percent + '%';
        memBar.className = 'progress-fill' + (s.memory_percent > 85 ? ' warn' : '') + (s.memory_percent > 95 ? ' danger' : '');
        
        document.getElementById('disk').innerHTML = s.disk_free_gb + '<span class="unit">GB</span>';
        document.getElementById('disk-detail').textContent = s.disk_percent + '% used';
        const diskBar = document.getElementById('disk-bar');
        diskBar.style.width = s.disk_percent + '%';
        diskBar.className = 'progress-fill' + (s.disk_percent > 85 ? ' warn' : '') + (s.disk_percent > 95 ? ' danger' : '');
        
        document.getElementById('proc-mem').innerHTML = s.process_mem_mb + '<span class="unit">MB</span>';
        const hrs = Math.floor(s.uptime_s / 3600);
        const mins = Math.floor((s.uptime_s % 3600) / 60);
        document.getElementById('uptime').textContent = hrs + 'h ' + mins + 'm uptime';
        
        document.getElementById('req-total').textContent = s.requests_total;
        document.getElementById('err-detail').textContent = s.errors_total + ' errors';
      }
    } catch(e) {
      console.error('Fallback poll failed:', e);
    }
  }, 5000);
}

// ── Offline Detection ─────────────────────────
window.addEventListener('offline', () => {
  document.body.classList.add('offline');
  document.getElementById('offline-banner').style.display = 'block';
});

window.addEventListener('online', () => {
  document.body.classList.remove('offline');
  document.getElementById('offline-banner').style.display = 'none';
  showToast('success', 'Connection restored');
});

// ── Card Expand ───────────────────────────────
function setupCardExpand() {
  document.querySelectorAll('.card').forEach(card => {
    card.classList.add('expandable');
    card.addEventListener('click', () => {
      const label = card.querySelector('.label')?.textContent || 'Detail';
      const value = card.querySelector('.value')?.textContent || '';
      const detail = card.querySelector('.detail')?.textContent || '';
      
      const modal = document.getElementById('memory-modal');
      const title = document.getElementById('modal-title');
      const body = document.getElementById('modal-body');
      
      if (modal && title && body) {
        title.textContent = label;
        body.innerHTML = `<strong>${value}</strong><br><br>${detail}`;
        modal.style.display = 'flex';
      }
    });
  });
}

// ── Performance: Throttle sparkline redraw ────
let sparklineThrottle = null;

function throttledSparklineUpdate() {
  if (sparklineThrottle) return;
  sparklineThrottle = setTimeout(() => {
    sparklineThrottle = null;
  }, 1000); // Max 1 update per second
}

// ── Init ──────────────────────────────────────
loadTheme();
updateClock();
setInterval(updateClock, 1000);
connectSSE();
connectWS();
connectLogStream();
loadVaultData();
loadTasks();
loadMemory();
setupSearch();
setupKeyboard();
setupCollapsible();
setupCardExpand();
setInterval(loadTasks, 30000);
setInterval(loadMemory, 60000); // Refresh vault data every 60s
</script>
</body>
</html>"""

@router.get("/dashboard/stats")
async def dashboard_stats():
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem_total = mem_available = 0
        for line in lines:
            if line.startswith("MemTotal:"): mem_total = int(line.split()[1])
            elif line.startswith("MemAvailable:"): mem_available = int(line.split()[1])
        mem_used_mb = (mem_total - mem_available) / 1024 if mem_total else 0
        mem_total_mb = mem_total / 1024 if mem_total else 0
        mem_pct = round(mem_used_mb / mem_total_mb * 100, 1) if mem_total_mb else 0
        import shutil
        disk = shutil.disk_usage("/")
        process_mem = 0
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"): process_mem = int(line.split()[1]) / 1024; break
        except Exception: pass
        vault = AerynVault()
        vault_counts = vault.count_entries()
        total_vault = sum(vault_counts.values())
        hse = get_search_engine()
        doc_count = hse._doc_count if hasattr(hse, '_doc_count') else 0
        sm = SocialMemory()
        person_count = len(sm._data.get("people", {})) if hasattr(sm, '_data') else 0
        return {"timestamp": time.time(), "system": {"memory_total_mb": round(mem_total_mb, 1), "memory_used_mb": round(mem_used_mb, 1), "memory_percent": mem_pct, "disk_free_gb": round(disk.free / (1024**3), 2), "disk_percent": round((disk.total - disk.free) / disk.total * 100, 1), "process_mem_mb": round(process_mem, 1), "uptime_s": round(time.time() - _start_time, 0)}, "aeryn": {"vault_total_entries": total_vault, "vault_layers": vault_counts, "search_docs": doc_count, "social_people": person_count, "requests_total": _request_count, "errors_total": _error_count, "safety_engine": True}}
    except Exception as e:
        return {"error": str(e)}

@router.get("/shared/reminders/due")
async def get_due_reminders():
    db = get_shared_db()
    reminders = db.get_due_reminders()
    return {"reminders": reminders, "count": len(reminders)}

@router.get("/shared/reminders")
async def get_all_reminders():
    db = get_shared_db()
    reminders = db.get_all_reminders()
    return {"reminders": reminders, "count": len(reminders)}

@router.post("/shared/reminders/add")
async def add_reminder(text: str, when: str, source: str = "n8n", target: str = "all"):
    db = get_shared_db()
    rid = db.add_reminder(text, when, source, target)
    return {"id": rid, "status": "ok"}

@router.post("/shared/reminders/mark-sent")
async def mark_reminder_sent(reminder_id: str):
    db = get_shared_db()
    db.mark_reminder_sent(reminder_id)
    return {"status": "ok"}

@router.get("/shared/tasks")
async def get_pending_tasks():
    db = get_shared_db()
    tasks = db.get_pending_tasks()
    return {"tasks": tasks, "count": len(tasks)}

@router.get("/shared/tasks/all")
async def get_all_tasks():
    db = get_shared_db()
    tasks = db.get_all_tasks()
    return {"tasks": tasks, "count": len(tasks)}

@router.get("/vault/entries")
async def get_vault_entries(layer: str = None, page: int = 1, per_page: int = 10):
    """Get vault entries with pagination."""
    vault = AerynVault()
    entries = vault.list_entries(layer=layer, limit=per_page, offset=(page - 1) * per_page)
    counts = vault.count_entries()
    total = counts.get(layer, sum(counts.values())) if layer else sum(counts.values())
    return {
        "entries": entries,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }

@router.get("/vault/entry/{entry_id}")
async def get_vault_entry(entry_id: str):
    """Get single vault entry."""
    vault = AerynVault()
    entry = vault.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.get("/vault/search")
async def search_vault(q: str, limit: int = 10):
    """Search vault entries."""
    vault = AerynVault()
    results = vault.search(q, limit=limit)
    return {"results": results, "count": len(results)}

@router.post("/shared/tasks/add")
async def add_task(title: str, description: str = "", priority: int = 5):
    db = get_shared_db()
    tid = db.add_task(title, description, priority)
    return {"id": tid, "status": "ok"}

@router.post("/shared/tasks/update")
async def update_task(task_id: str, status: str = None, progress: float = None, result: str = None, error: str = None):
    db = get_shared_db()
    db.update_task(task_id, status, progress, result, error)
    return {"status": "ok"}

