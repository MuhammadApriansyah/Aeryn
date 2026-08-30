#!/usr/bin/env python3
"""Dashboard HTML templates."""
from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

router = APIRouter()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aeryn Dashboard — V40.55</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #09090b;
  --bg-card: #18181b;
  --bg-hover: #27272a;
  --border: #27272a;
  --text: #fafafa;
  --text-muted: #a1a1aa;
  --accent: #22d3ee;
  --green: #4ade80;
  --yellow: #facc15;
  --red: #f87171;
  --purple: #c084fc;
  --orange: #fb923c;
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  padding: 24px;
  line-height: 1.5;
}

/* ── Header ──────────────────────────────── */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.header .brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand .logo {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.brand h1 {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.brand .version {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-card);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
}

.header .clock {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  color: var(--text-muted);
}

/* ── Grid ────────────────────────────────── */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  transition: border-color 0.2s, transform 0.2s;
}

.card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.card .label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-bottom: 8px;
  font-weight: 600;
}

.card .value {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  font-family: 'JetBrains Mono', monospace;
}

.card .unit {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 400;
  margin-left: 4px;
}

.card .detail {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* ── Progress Bar ────────────────────────── */
.progress-track {
  height: 4px;
  background: var(--bg);
  border-radius: 2px;
  margin-top: 12px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--green), var(--accent));
  border-radius: 2px;
  transition: width 0.5s ease;
}

.progress-fill.warn { background: linear-gradient(90deg, var(--yellow), var(--orange)); }
.progress-fill.danger { background: linear-gradient(90deg, var(--orange), var(--red)); }

/* ── Section ─────────────────────────────── */
.section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.section h2 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Service Status ──────────────────────── */
.service-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.service-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg);
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.online { background: var(--green); box-shadow: 0 0 6px var(--green); }
.dot.offline { background: var(--red); }

/* ── Table ───────────────────────────────── */
table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}

th {
  color: var(--text-muted);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

td { font-family: 'JetBrains Mono', monospace; }
td:last-child { text-align: right; }

tr:last-child td { border-bottom: none; }

/* ── Endpoints ───────────────────────────── */
.endpoint-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.endpoint-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg);
  border-radius: 6px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  border: 1px solid transparent;
}

.endpoint-chip:hover {
  border-color: var(--accent);
}

.method {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}

.method.get { background: rgba(74, 222, 128, 0.15); color: var(--green); }
.method.post { background: rgba(34, 211, 238, 0.15); color: var(--accent); }
.method.delete { background: rgba(248, 113, 113, 0.15); color: var(--red); }

/* ── Live indicator ──────────────────────── */
.live {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.live .pulse {
  width: 6px;
  height: 6px;
  background: var(--green);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Sparkline ──────────────────────────────── */
.sparkline-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.sparkline-card {
  background: var(--bg);
  border-radius: 8px;
  padding: 16px;
}

.sparkline-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sparkline {
  width: 100%;
  height: 40px;
}

.sparkline-lg {
  width: 100%;
  height: 60px;
}

/* ── Quick Actions ──────────────────────────── */
.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text);
  font-family: inherit;
}

.action-btn:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  background: var(--bg-hover);
}

.action-btn:active {
  transform: translateY(0);
}

.action-icon {
  font-size: 24px;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
}

/* ── Activity Feed ──────────────────────────── */
.activity-feed {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-empty {
  color: var(--text-muted);
  text-align: center;
  padding: 20px;
  font-size: 13px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg);
  border-radius: 8px;
  font-size: 13px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.activity-dot.info { background: var(--accent); }
.activity-dot.success { background: var(--green); }
.activity-dot.warning { background: var(--yellow); }
.activity-dot.error { background: var(--red); }

.activity-text {
  flex: 1;
}

.activity-time {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

/* ── Notifications ──────────────────────────── */
.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
  border-left: 3px solid var(--yellow);
  font-size: 13px;
}

.notification-item.critical {
  border-left-color: var(--red);
}

.notification-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
}

.notification-dismiss:hover {
  color: var(--text);
}

/* ── Toast ──────────────────────────────────── */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast {
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  animation: toastIn 0.3s ease;
  max-width: 300px;
}

.toast.success { border-left: 3px solid var(--green); }
.toast.error { border-left: 3px solid var(--red); }
.toast.warning { border-left: 3px solid var(--yellow); }
.toast.info { border-left: 3px solid var(--accent); }

@keyframes toastIn {
  from { opacity: 0; transform: translateX(100%); }
  to { opacity: 1; transform: translateX(0); }
}
/* ── Light Theme ───────────────────────────── */
body.light {
  --bg: #fafafa;
  --bg-card: #ffffff;
  --bg-hover: #f4f4f5;
  --border: #e4e4e7;
  --text: #18181b;
  --text-muted: #71717a;
}

/* ── Task Queue ─────────────────────────────── */
.task-count {
  background: var(--accent);
  color: var(--bg);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  margin-left: 8px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-empty {
  color: var(--text-muted);
  text-align: center;
  padding: 16px;
  font-size: 13px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 13px;
  font-weight: 500;
}

.task-status {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
}

.task-progress {
  width: 60px;
  height: 4px;
  background: var(--bg-hover);
  border-radius: 2px;
  overflow: hidden;
}

.task-progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s;
}

/* ── Memory Browser ────────────────────────── */
.search-box {
  position: relative;
  margin-bottom: 16px;
}

.search-box input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
  outline: none;
}

.search-box input:focus {
  border-color: var(--accent);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  display: none;
}

.search-results.active {
  display: block;
}

.search-result-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}

.search-result-item:hover {
  background: var(--bg-hover);
}

.memory-table-wrap {
  max-height: 300px;
  overflow-y: auto;
}

.memory-table {
  width: 100%;
}

.memory-table th {
  position: sticky;
  top: 0;
  background: var(--bg-card);
}

.memory-table td {
  font-size: 12px;
}

.memory-table .view-btn {
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}

.memory-table .view-btn:hover {
  border-color: var(--accent);
}

.pagination {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.pagination button {
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.pagination button:hover:not(:disabled) {
  border-color: var(--accent);
}

.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination .page-info {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--text-muted);
}

/* ── Modal ──────────────────────────────────── */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 24px;
  cursor: pointer;
  padding: 4px;
}

.modal-close:hover {
  color: var(--text);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  max-height: 60vh;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* ── Collapsible ────────────────────────────── */
.section.collapsible .section-header {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section.collapsible .section-header::after {
  content: '▾';
  font-size: 14px;
  transition: transform 0.2s;
}

.section.collapsed .section-header::after {
  transform: rotate(-90deg);
}

.section.collapsed .section-content {
  display: none;
}

/* ── Phase 4: UX Polish ────────────────────── */

/* Skeleton Loading */
.skeleton {
  background: linear-gradient(90deg, var(--bg) 25%, var(--bg-hover) 50%, var(--bg) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-text {
  height: 14px;
  margin-bottom: 8px;
}

.skeleton-card {
  height: 80px;
}

/* Card Expand */
.card.expandable {
  cursor: pointer;
  transition: all 0.2s;
}

.card.expandable:hover {
  transform: translateY(-2px);
  border-color: var(--accent);
}

/* Live Logs */
.log-viewer {
  max-height: 150px;
  overflow-y: auto;
  background: var(--bg);
  border-radius: 8px;
  padding: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  line-height: 1.6;
}

.log-entry {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--border);
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  color: var(--text-muted);
  flex-shrink: 0;
}

.log-level {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 10px;
  text-transform: uppercase;
}

.log-level.info { background: rgba(34, 211, 238, 0.15); color: var(--accent); }
.log-level.warn { background: rgba(250, 204, 21, 0.15); color: var(--yellow); }
.log-level.error { background: rgba(248, 113, 113, 0.15); color: var(--red); }

.log-message {
  flex: 1;
  word-break: break-all;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  body { padding: 16px; }
  
  .header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header .live {
    width: 100%;
    justify-content: space-between;
  }
  
  .grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .sparkline-grid {
    grid-template-columns: 1fr;
  }
  
  .action-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .service-list {
    flex-direction: column;
  }
  
  .service-chip {
    width: 100%;
  }
  
  .endpoint-grid {
    grid-template-columns: 1fr;
  }
  
  .card .value {
    font-size: 22px;
  }
  
  .modal {
    width: 95%;
    max-width: none;
  }
  
  .memory-table-wrap {
    max-height: 200px;
  }
}

/* Touch-friendly */
@media (hover: none) {
  .action-btn:hover {
    transform: none;
  }
  
  .card:hover {
    transform: none;
  }
  
  .action-btn:active {
    background: var(--bg-hover);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Offline indicator */
.offline-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: var(--red);
  color: white;
  text-align: center;
  padding: 8px;
  font-size: 12px;
  z-index: 9999;
  display: none;
}

body.offline .offline-banner {
  display: block;
}

body.offline .header {
  margin-top: 36px;
}

.footer {
  text-align: center;
  padding: 24px 0;
  color: var(--text-muted);
  font-size: 12px;
}
</style>
</head>
<body>

<div class="header">
  <div class="brand">
    <div class="logo">✦</div>
    <div>
      <h1>Aeryn</h1>
      <span class="version" id="version">v40.54</span>
    </div>
  </div>
  <div class="live">
    <div class="pulse" id="sse-dot"></div>
    <span id="conn-status">LIVE</span>
    <span class="clock" id="clock">--:--:--</span>
  </div>
</div>

<!-- ── System Cards ────────────────────────── -->
<div class="grid">
  <div class="card">
    <div class="label">🧠 Memory</div>
    <div class="value" id="mem">--<span class="unit">MB</span></div>
    <div class="detail" id="mem-detail">--% used</div>
    <div class="progress-track"><div class="progress-fill" id="mem-bar" style="width:0%"></div></div>
  </div>

  <div class="card">
    <div class="label">💾 Disk</div>
    <div class="value" id="disk">--<span class="unit">GB</span></div>
    <div class="detail" id="disk-detail">-- used</div>
    <div class="progress-track"><div class="progress-fill" id="disk-bar" style="width:0%"></div></div>
  </div>

  <div class="card">
    <div class="label">⚡ Process</div>
    <div class="value" id="proc-mem">--<span class="unit">MB</span></div>
    <div class="detail" id="uptime">-- uptime</div>
  </div>

  <div class="card">
    <div class="label">📊 Requests</div>
    <div class="value" id="req-total">--</div>
    <div class="detail" id="err-detail">-- errors</div>
    <canvas id="sparkline-reqs" class="sparkline" width="200" height="40"></canvas>
  </div>
</div>

<!-- ── Sparkline Charts ──────────────────────── -->
<div class="section">
  <h2>📈 Trends (60s)</h2>
  <div class="sparkline-grid">
    <div class="sparkline-card">
      <div class="sparkline-label">Memory</div>
      <canvas id="sparkline-mem" class="sparkline-lg" width="300" height="60"></canvas>
    </div>
    <div class="sparkline-card">
      <div class="sparkline-label">Disk</div>
      <canvas id="sparkline-disk" class="sparkline-lg" width="300" height="60"></canvas>
    </div>
  </div>
</div>

<!-- ── Quick Actions ─────────────────────────── -->
<div class="section">
  <h2>⚡ Quick Actions</h2>
  <div class="action-grid">
    <button class="action-btn" onclick="runAction('backup')">
      <span class="action-icon">💾</span>
      <span class="action-label">Backup</span>
    </button>
    <button class="action-btn" onclick="runAction('dream')">
      <span class="action-icon">💭</span>
      <span class="action-label">Dream</span>
    </button>
    <button class="action-btn" onclick="runAction('cache-clear')">
      <span class="action-icon">🗑️</span>
      <span class="action-label">Clear Cache</span>
    </button>
    <button class="action-btn" onclick="runAction('restart')">
      <span class="action-icon">🔄</span>
      <span class="action-label">Restart</span>
    </button>
  </div>
</div>

<!-- ── Activity Feed ─────────────────────────── -->
<div class="section">
  <h2>🔔 Activity Feed</h2>
  <div class="activity-feed" id="activity-feed">
    <div class="activity-empty">Waiting for events...</div>
  </div>
</div>

<!-- ── Notifications Panel ───────────────────── -->
<div class="section" id="notifications-section" style="display:none">
  <h2>🚨 Alerts</h2>
  <div class="notifications-list" id="notifications-list"></div>
</div>

<!-- ── Task Queue Monitor ─────────────────────── -->
<div class="section" id="task-monitor-section">
  <h2>📋 Task Queue <span class="task-count" id="task-count">0</span></h2>
  <div class="task-list" id="task-list">
    <div class="task-empty">No pending tasks</div>
  </div>
</div>

<!-- ── Memory Browser ────────────────────────── -->
<div class="section" id="memory-browser-section">
  <h2>🧠 Memory Browser</h2>
  <div class="search-box">
    <input type="text" id="memory-search" placeholder="Search memories..." autocomplete="off">
    <div class="search-results" id="search-results"></div>
  </div>
  <div class="memory-table-wrap">
    <table class="memory-table">
      <thead><tr><th>Title</th><th>Layer</th><th>Tags</th><th></th></tr></thead>
      <tbody id="memory-table-body"></tbody>
    </table>
  </div>
  <div class="pagination" id="memory-pagination"></div>
</div>

<!-- ── Memory Detail Modal ───────────────────── -->
<div class="modal-overlay" id="memory-modal" style="display:none">
  <div class="modal">
    <div class="modal-header">
      <h3 id="modal-title">Memory Detail</h3>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>
<div class="section">
  <h2>🖥️ Services</h2>
  <div class="service-list" id="services">
    <div class="service-chip"><div class="dot online"></div><span>aeryn-api</span></div>
    <div class="service-chip"><div class="dot online"></div><span>n8n</span></div>
    <div class="service-chip"><div class="dot online"></div><span>webnovel-api</span></div>
    <div class="service-chip"><div class="dot online"></div><span>webnovel-web</span></div>
    <div class="service-chip"><div class="dot offline"></div><span>hermes-gw</span></div>
  </div>
</div>

<!-- ── Aeryn Stats ─────────────────────────── -->
<div class="section">
  <h2>📈 Aeryn Metrics</h2>
  <table>
    <thead><tr><th>Metric</th><th style="text-align:right">Value</th></tr></thead>
    <tbody>
      <tr><td>Vault Entries</td><td id="vault-total">--</td></tr>
      <tr><td>Search Documents</td><td id="search-docs">--</td></tr>
      <tr><td>Social People</td><td id="social-ppl">--</td></tr>
      <tr><td>Safety Engine</td><td style="color:var(--green)">● OK</td></tr>
    </tbody>
  </table>
</div>

<!-- ── Vault Layers ────────────────────────── -->
<div class="section">
  <h2>📁 Vault Layers</h2>
  <table>
    <thead><tr><th>Layer</th><th style="text-align:right">Entries</th></tr></thead>
    <tbody id="vault-table"><tr><td colspan="2" style="text-align:center;color:var(--text-muted)">...</td></tr></tbody>
  </table>
</div>

<!-- ── Endpoints ───────────────────────────── -->
<div class="section">
  <h2>🔌 Quick Endpoints</h2>
  <div class="endpoint-grid">
    <div class="endpoint-chip"><span class="method get">GET</span>/health</div>
    <div class="endpoint-chip"><span class="method get">GET</span>/search</div>
    <div class="endpoint-chip"><span class="method post">POST</span>/run</div>
    <div class="endpoint-chip"><span class="method post">POST</span>/compile</div>
    <div class="endpoint-chip"><span class="method post">POST</span>/digest</div>
    <div class="endpoint-chip"><span class="method get">GET</span>/agents</div>
    <div class="endpoint-chip"><span class="method post">POST</span>/dream/synthesize</div>
    <div class="endpoint-chip"><span class="method get">GET</span>/dashboard/stats</div>
  </div>
</div>

<!-- ── Live Logs Viewer ───────────────────────── -->
<div class="section" id="logs-section">
  <h2>📜 Live Logs</h2>
  <div class="log-viewer" id="log-viewer">
    <div class="log-entry"><span class="log-message">Connecting...</span></div>
  </div>
</div>

<div class="offline-banner" id="offline-banner">
  ⚠️ Connection lost. Reconnecting...
</div>

<div class="toast-container" id="toast-container"></div>

<div class="footer">
  Aeryn V40.54 — Built with ❤️ by Hermes + Aeryn
</div>

<script>
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('id-ID', { hour12: false });
}

// ── Sparkline Charts ────────────────────────
const sparklineData = {
  mem: [],
  disk: [],
  reqs: [],
  maxPoints: 60
};

function drawSparkline(canvasId, data, color) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  
  ctx.clearRect(0, 0, w, h);
  
  if (data.length < 2) return;
  
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  
  for (let i = 0; i < data.length; i++) {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((data[i] - min) / range) * (h - 4) - 2;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  
  // Fill under curve
  ctx.lineTo(w, h);
  ctx.lineTo(0, h);
  ctx.closePath();
  ctx.fillStyle = color.replace(')', ', 0.1)').replace('rgb', 'rgba');
  ctx.fill();
}

// ── Activity Feed ────────────────────────────
const activityFeed = [];

function addActivity(type, text) {
  const feed = document.getElementById('activity-feed');
  if (!feed) return;
  
  const empty = feed.querySelector('.activity-empty');
  if (empty) empty.remove();
  
  const item = document.createElement('div');
  item.className = 'activity-item';
  item.innerHTML = `
    <div class="activity-dot ${type}"></div>
    <span class="activity-text">${text}</span>
    <span class="activity-time">${new Date().toLocaleTimeString('id-ID', {hour12:false})}</span>
  `;
  
  feed.insertBefore(item, feed.firstChild);
  
  // Keep max 20 items
  while (feed.children.length > 20) {
    feed.removeChild(feed.lastChild);
  }
}

// ── Notifications ────────────────────────────
const notifications = [];

function addNotification(type, message) {
  const section = document.getElementById('notifications-section');
  const list = document.getElementById('notifications-list');
  if (!section || !list) return;
  
  section.style.display = 'block';
  
  const item = document.createElement('div');
  item.className = 'notification-item' + (type === 'critical' ? ' critical' : '');
  item.innerHTML = `
    <span>${type === 'critical' ? '🚨' : '⚠️'}</span>
    <span>${message}</span>
    <button class="notification-dismiss" onclick="this.parentElement.remove()">×</button>
  `;
  
  list.insertBefore(item, list.firstChild);
  
  // Show toast
  showToast(type, message);
}

function showToast(type, message) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = 'toast ' + type;
  toast.textContent = message;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}

// ── Quick Actions ────────────────────────────
function runAction(action) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast('error', 'WebSocket not connected');
    return;
  }
  
  ws.send(JSON.stringify({type: 'action', data: {action: action}}));
  addActivity('info', `Action: ${action}`);
  showToast('info', `Running: ${action}`);
}

// ── SSE: Real-time stats ──────────────────────
function connectSSE() {
  const evtSource = new EventSource('/dashboard/stream');
  
  evtSource.onopen = function() {
    document.getElementById('sse-dot').style.background = 'var(--green)';
    document.getElementById('conn-status').textContent = 'LIVE';
  };
  
  evtSource.addEventListener('stats', function(e) {
    const d = JSON.parse(e.data);
    const s = d.data;
    
    // Update sparkline data
    sparklineData.mem.push(s.memory_percent);
    if (sparklineData.mem.length > sparklineData.maxPoints) sparklineData.mem.shift();
    
    sparklineData.disk.push(s.disk_percent);
    if (sparklineData.disk.length > sparklineData.maxPoints) sparklineData.disk.shift();
    
    sparklineData.reqs.push(s.requests_total);
    if (sparklineData.reqs.length > sparklineData.maxPoints) sparklineData.reqs.shift();
    
    // Draw sparklines
    drawSparkline('sparkline-mem', sparklineData.mem, 'rgb(74, 222, 128)');
    drawSparkline('sparkline-disk', sparklineData.disk, 'rgb(34, 211, 238)');
    drawSparkline('sparkline-reqs', sparklineData.reqs, 'rgb(192, 132, 252)');
    
    // Memory
    document.getElementById('mem').innerHTML = s.memory_used_mb + '<span class="unit">MB</span>';
    document.getElementById('mem-detail').textContent = s.memory_percent + '% of ' + s.memory_total_mb + ' MB';
    const memBar = document.getElementById('mem-bar');
    memBar.style.width = s.memory_percent + '%';
    memBar.className = 'progress-fill' + (s.memory_percent > 85 ? ' warn' : '') + (s.memory_percent > 95 ? ' danger' : '');

    // Disk
    document.getElementById('disk').innerHTML = s.disk_free_gb + '<span class="unit">GB</span>';
    document.getElementById('disk-detail').textContent = s.disk_percent + '% used';
    const diskBar = document.getElementById('disk-bar');
    diskBar.style.width = s.disk_percent + '%';
    diskBar.className = 'progress-fill' + (s.disk_percent > 85 ? ' warn' : '') + (s.disk_percent > 95 ? ' danger' : '');

    // Process
    document.getElementById('proc-mem').innerHTML = s.process_mem_mb + '<span class="unit">MB</span>';
    const hrs = Math.floor(s.uptime_s / 3600);
    const mins = Math.floor((s.uptime_s % 3600) / 60);
    document.getElementById('uptime').textContent = hrs + 'h ' + mins + 'm uptime';

    // Requests
    document.getElementById('req-total').textContent = s.requests_total;
    document.getElementById('err-detail').textContent = s.errors_total + ' errors';
    
    // Threshold alerts
    if (s.memory_percent > 90) {
      addNotification('critical', `Memory usage critical: ${s.memory_percent}%`);
    } else if (s.memory_percent > 80) {
      addNotification('warning', `Memory usage high: ${s.memory_percent}%`);
    }
    
    if (s.disk_percent > 90) {
      addNotification('critical', `Disk usage critical: ${s.disk_percent}%`);
    }
  });
  
  evtSource.onerror = function() {
    document.getElementById('sse-dot').style.background = 'var(--red)';
    document.getElementById('conn-status').textContent = 'RECONNECTING';
    evtSource.close();
    setTimeout(connectSSE, 3000);
  };
}

// ── WebSocket: Commands ───────────────────────
let ws = null;

function connectWS() {
  ws = new WebSocket('ws://' + window.location.host + '/ws/dashboard');
  
  ws.onopen = function() {
    console.log('WS connected');
  };
  
  ws.onmessage = function(e) {
    const msg = JSON.parse(e.data);
    if (msg.type === 'connected') {
      console.log('WS ready');
    } else if (msg.type === 'action_result') {
      addActivity('success', `Action ${msg.data.action}: ${msg.data.status}`);
      showToast('success', `${msg.data.action} → ${msg.data.status}`);
    }
  };
  
  ws.onclose = function() {
    console.log('WS disconnected, reconnecting...');
    setTimeout(connectWS, 3000);
  };
}

// ── Theme Toggle ─────────────────────────────
function toggleTheme() {
  document.body.classList.toggle('light');
  localStorage.setItem('aeryn-theme', document.body.classList.contains('light') ? 'light' : 'dark');
}

function loadTheme() {
  if (localStorage.getItem('aeryn-theme') === 'light') {
    document.body.classList.add('light');
  }
}

// ── Task Queue Monitor ────────────────────────
async function loadTasks() {
  try {
    const r = await fetch('/shared/tasks/all');
    const d = await r.json();
    const list = document.getElementById('task-list');
    const count = document.getElementById('task-count');
    
    if (!list || !count) return;
    
    count.textContent = d.count;
    
    if (d.count === 0) {
      list.innerHTML = '<div class="task-empty">No pending tasks</div>';
      return;
    }
    
    list.innerHTML = '';
    d.tasks.forEach(task => {
      const item = document.createElement('div');
      item.className = 'task-item';
      const progress = task.progress || 0;
      const statusClass = task.status === 'completed' ? 'success' : 
                          task.status === 'failed' ? 'error' : 'info';
      
      item.innerHTML = `
        <div class="task-dot ${statusClass}"></div>
        <div class="task-info">
          <div class="task-title">${task.title || 'Untitled'}</div>
          <div class="task-status">${task.status} • Priority ${task.priority || 5}</div>
        </div>
        <div class="task-progress">
          <div class="task-progress-fill" style="width: ${progress * 100}%"></div>
        </div>
      `;
      list.appendChild(item);
    });
  } catch(e) {
    console.error('Task load failed:', e);
  }
}

// ── Memory Browser ────────────────────────────
let memoryPage = 1;
const memoryPerPage = 10;
let searchTimeout = null;

async function loadMemory(page = 1) {
  try {
    const r = await fetch(`/vault/entries?page=${page}&per_page=${memoryPerPage}`);
    const d = await r.json();
    const tbody = document.getElementById('memory-table-body');
    const pagination = document.getElementById('memory-pagination');
    
    if (!tbody || !pagination) return;
    
    if (d.entries.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No entries found</td></tr>';
      pagination.innerHTML = '';
      return;
    }
    
    tbody.innerHTML = '';
    d.entries.forEach(entry => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${entry.title?.substring(0, 40) || 'Untitled'}</td>
        <td>${entry.layer || 'wiki'}</td>
        <td>${(entry.tags || []).join(', ')}</td>
        <td><button class="view-btn" onclick="viewEntry('${entry.id}')">View</button></td>
      `;
      tbody.appendChild(tr);
    });
    
    // Pagination
    pagination.innerHTML = '';
    if (d.total_pages > 1) {
      const prevBtn = document.createElement('button');
      prevBtn.textContent = '← Prev';
      prevBtn.disabled = page <= 1;
      prevBtn.onclick = () => loadMemory(page - 1);
      
      const pageInfo = document.createElement('span');
      pageInfo.className = 'page-info';
      pageInfo.textContent = `Page ${page} of ${d.total_pages}`;
      
      const nextBtn = document.createElement('button');
      nextBtn.textContent = 'Next →';
      nextBtn.disabled = page >= d.total_pages;
      nextBtn.onclick = () => loadMemory(page + 1);
      
      pagination.appendChild(prevBtn);
      pagination.appendChild(pageInfo);
      pagination.appendChild(nextBtn);
    }
  } catch(e) {
    console.error('Memory load failed:', e);
  }
}

async function viewEntry(id) {
  try {
    const r = await fetch(`/vault/entry/${id}`);
    const entry = await r.json();
    
    const modal = document.getElementById('memory-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    
    if (!modal || !title || !body) return;
    
    title.textContent = entry.title || 'Untitled';
    body.textContent = entry.body || 'No content';
    
    modal.style.display = 'flex';
  } catch(e) {
    console.error('Entry load failed:', e);
  }
}

function closeModal() {
  const modal = document.getElementById('memory-memory');
  if (modal) modal.style.display = 'none';
}

// ── Search Box ────────────────────────────────
function setupSearch() {
  const input = document.getElementById('memory-search');
  const results = document.getElementById('search-results');
  
  if (!input || !results) return;
  
  input.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    const q = input.value.trim();
    
    if (q.length < 2) {
      results.classList.remove('active');
      return;
    }
    
    searchTimeout = setTimeout(async () => {
      try {
        const r = await fetch(`/vault/search?q=${encodeURIComponent(q)}&limit=10`);
        const d = await r.json();
        
        results.innerHTML = '';
        
        if (d.results.length === 0) {
          results.innerHTML = '<div class="search-result-item">No results</div>';
        } else {
          d.results.forEach(item => {
            const div = document.createElement('div');
            div.className = 'search-result-item';
            div.textContent = item.title;
            div.onclick = () => {
              results.classList.remove('active');
              viewEntry(item.id);
            };
            results.appendChild(div);
          });
        }
        
        results.classList.add('active');
      } catch(e) {
        console.error('Search failed:', e);
      }
    }, 300);
  });
  
  input.addEventListener('blur', () => {
    setTimeout(() => results.classList.remove('active'), 200);
  });
  
  input.addEventListener('focus', () => {
    if (input.value.trim().length >= 2) {
      results.classList.add('active');
    }
  });
}

// ── Keyboard Shortcuts ────────────────────────
function setupKeyboard() {
  document.addEventListener('keydown', (e) => {
    // R - Refresh
    if (e.key === 'r' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      if (document.activeElement.tagName !== 'INPUT') {
        loadTasks();
        loadMemory();
        loadVaultData();
        showToast('info', 'Refreshed');
      }
    }
    
    // T - Toggle theme
    if (e.key === 't' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      if (document.activeElement.tagName !== 'INPUT') {
        toggleTheme();
      }
    }
    
    // / - Focus search
    if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      const input = document.getElementById('memory-search');
      if (input) input.focus();
    }
    
    // Esc - Close modal / blur
    if (e.key === 'Escape') {
      closeModal();
      const input = document.getElementById('memory-search');
      if (input && document.activeElement === input) {
        input.blur();
      }
    }
  });
}

// ── Collapsible Sections ──────────────────────
function setupCollapsible() {
  document.querySelectorAll('.section h2').forEach(header => {
    header.style.cursor = 'pointer';
    header.addEventListener('click', () => {
      const section = header.closest('.section');
      if (section.id === 'task-monitor-section' || section.id === 'memory-browser-section') {
        section.classList.toggle('collapsed');
        localStorage.setItem(`aeryn-collapse-${section.id}`, section.classList.contains('collapsed'));
      }
    });
  });
  
  // Restore collapse state
  ['task-monitor-section', 'memory-browser-section'].forEach(id => {
    const section = document.getElementById(id);
    if (section && localStorage.getItem(`aeryn-collapse-${id}`) === 'true') {
      section.classList.add('collapsed');
    }
  });
}

// ── Fetch vault data (one-time) ────────────────
async function loadVaultData() {
  try {
    const r = await fetch('/dashboard/stats');
    const d = await r.json();
    if (d.error) return;
    
    const a = d.aeryn;
    document.getElementById('vault-total').textContent = a.vault_total_entries;
    document.getElementById('search-docs').textContent = a.search_docs;
    document.getElementById('social-ppl').textContent = a.social_people;

    const tbody = document.getElementById('vault-table');
    tbody.innerHTML = '';
    for (const [layer, count] of Object.entries(a.vault_layers)) {
      tbody.innerHTML += '<tr><td>' + layer + '</td><td>' + count + '</td></tr>';
    }
  } catch(e) {
    console.error('Vault load failed:', e);
  }
}

// ── Live Logs Viewer ──────────────────────────
const logViewer = document.getElementById('log-viewer');
let logLines = [];

function addLogLine(level, message) {
  if (!logViewer) return;
  
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `
    <span class="log-time">${new Date().toLocaleTimeString('id-ID', {hour12:false})}</span>
    <span class="log-level ${level}">${level}</span>
    <span class="log-message">${message}</span>
  `;
  
  logViewer.appendChild(entry);
  
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

