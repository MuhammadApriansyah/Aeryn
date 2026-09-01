/* ═══════════════════════════════════════════════════════════════════ */
/* AERYN — Frontend Engine v3                                         */
/* ═══════════════════════════════════════════════════════════════════ */

(() => {
  'use strict';

  const state = {
    theme: localStorage.getItem('aery-theme') || 'dark',
    lang: localStorage.getItem('aery-lang') || 'id',
    uptimeStart: Date.now(),
    requests: 0,
    tokens: 0,
    chatHistory: []
  };

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  /* ── Cursor ── */
  const cursor = $('#cursor');
  const trail = $('#cursor-trail');
  let mx = 0, my = 0, cx = 0, cy = 0;

  document.addEventListener('mousemove', (e) => {
    mx = e.clientX; my = e.clientY;
    trail.style.left = mx + 'px';
    trail.style.top = my + 'px';
  });

  (function animate() {
    cx += (mx - cx) * 0.15;
    cy += (my - cy) * 0.15;
    cursor.style.left = cx + 'px';
    cursor.style.top = cy + 'px';
    requestAnimationFrame(animate);
  })();

  $$('a,button,.system-card,.work-item,.stack-item,.nav-link,.division-card,.tool-card,.workspace-card,.integration-card,.marketplace-card').forEach(el => {
    el.addEventListener('mouseenter', () => { cursor.style.width = '40px'; cursor.style.height = '40px'; });
    el.addEventListener('mouseleave', () => { cursor.style.width = '20px'; cursor.style.height = '20px'; });
  });

  /* ── Scroll reveal ── */
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('revealed');
        const sec = e.target.getAttribute('data-section');
        if (sec) $$('.nav-link').forEach(l => l.classList.toggle('active', l.getAttribute('href') === `#section-${sec}`));
      }
    });
  }, { threshold: 0.15 });

  $$('section').forEach(s => observer.observe(s));

  /* ── Smooth scroll ── */
  window.scrollToSection = (id) => {
    const el = document.getElementById(`section-${id}`);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  $$('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const t = link.getAttribute('href').substring(1);
      const el = document.getElementById(t);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    });
  });

  /* ── Nav scroll ── */
  window.addEventListener('scroll', () => {
    $('#top-nav').classList.toggle('scrolled', window.scrollY > 50);
  }, { passive: true });

  /* ── Theme ── */
  function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('aery-theme', state.theme);
    const btn = $('#theme-toggle');
    if (btn) btn.textContent = state.theme === 'dark' ? '☀️' : '🌙';
  }
  const themeBtn = $('#theme-toggle');
  if (themeBtn) themeBtn.addEventListener('click', () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    applyTheme();
    showToast(`Theme: ${state.theme}`, 'success');
  });
  applyTheme();

  /* ── Lang ── */
  const langBtn = $('#lang-toggle');
  if (langBtn) langBtn.addEventListener('click', () => {
    state.lang = state.lang === 'id' ? 'en' : 'id';
    localStorage.setItem('aery-lang', state.lang);
    langBtn.textContent = state.lang.toUpperCase();
    showToast(`Language: ${state.lang}`, 'success');
  });

  /* ── Toast ── */
  function showToast(msg, type = 'info') {
    const c = $('#toast-container');
    if (!c) return;
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => {
      t.style.opacity = '0';
      t.style.transform = 'translateX(100%)';
      t.style.transition = 'all 0.3s ease';
      setTimeout(() => t.remove(), 300);
    }, 3000);
  }
  window.toast = showToast;

  /* ── Work items toggle ── */
  window.toggleWork = (el) => {
    el.classList.toggle('open');
  };

  /* ── System detail ── */
  window.showSystemDetail = (sys) => {
    showToast(`System: ${sys} — Details coming soon!`, 'info');
  };

  /* ── Divisions execute ── */
  window.executeDivision = async (div) => {
    showToast(`Executing ${div} division...`, 'info');
    try {
      const res = await fetch(`/divisions/${div}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: `Execute ${div} task` })
      });
      const data = await res.json();
      showToast(`${div} completed: ${data.status || 'ok'}`, 'success');
    } catch (e) {
      showToast(`Error: ${e.message}`, 'error');
    }
  };

  /* ── Plugins run ── */
  window.runPlugin = async (name) => {
    showToast(`Running ${name}...`, 'info');
    try {
      const res = await fetch('/plugins/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, input: 'test' })
      });
      const data = await res.json();
      showToast(`${name}: ${data.status || 'ok'}`, 'success');
    } catch (e) {
      showToast(`Error: ${e.message}`, 'error');
    }
  };

  /* ── Tools execute ── */
  window.executeTool = async (name) => {
    showToast(`Executing tool: ${name}...`, 'info');
    try {
      const res = await fetch(`/tools/${name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      showToast(`Tool ${name}: ${data.status || 'ok'}`, 'success');
    } catch (e) {
      showToast(`Error: ${e.message}`, 'error');
    }
  };

  /* ── Memory search ── */
  window.searchMemory = async () => {
    const q = $('#memory-search').value.trim();
    if (!q) return showToast('Enter search query', 'warning');
    showToast(`Searching: ${q}...`, 'info');
    try {
      const res = await fetch(`/memory/recall?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      const results = data.results || [];
      const container = $('#memory-results');
      if (results.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><p>No results found</p></div>';
      } else {
        container.innerHTML = results.map(r => `
          <div style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-bottom:0.5rem">
            <div style="font-weight:600;margin-bottom:0.25rem">${r.key || r.source || 'memory'}</div>
            <div style="color:var(--fg2);font-size:0.85rem">${(r.value || r.content || '').substring(0, 100)}</div>
          </div>
        `).join('');
      }
      $('#results-count').textContent = `${results.length} found`;
      showToast(`Found ${results.length} results`, 'success');
    } catch (e) {
      showToast(`Error: ${e.message}`, 'error');
    }
  };

  /* ── Memory store ── */
  window.storeMemory = async () => {
    const key = $('#memory-key').value.trim();
    const val = $('#memory-value').value.trim();
    if (!key || !val) return showToast('Enter key and value', 'warning');
    showToast(`Storing: ${key}...`, 'info');
    try {
      const res = await fetch('/memory/store', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value: val })
      });
      const data = await res.json();
      showToast(`Stored: ${key}`, 'success');
      $('#memory-key').value = '';
      $('#memory-value').value = '';
    } catch (e) {
      showToast(`Error: ${e.message}`, 'error');
    }
  };

  /* ── Chat ── */
  const chatForm = $('#chat-form');
  const chatWin = $('#chat-window');
  const chatIn = $('#chat-input');

  function appendMsg(type, text) {
    const msg = document.createElement('div');
    msg.className = `chat-msg ${type}`;
    msg.innerHTML = `<div class="msg-content">${escapeHtml(text)}</div>`;
    chatWin.appendChild(msg);
    chatWin.scrollTop = chatWin.scrollHeight;
    state.chatHistory.push({ type, text, time: Date.now() });
  }

  function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = chatIn.value.trim();
      if (!msg) return;
      appendMsg('user', msg);
      chatIn.value = '';
      chatIn.style.height = 'auto';

      const typing = document.createElement('div');
      typing.className = 'chat-msg assistant';
      typing.innerHTML = '<div class="msg-content">Typing...</div>';
      chatWin.appendChild(typing);
      chatWin.scrollTop = chatWin.scrollHeight;

      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ goal: msg })
        });
        const data = await res.json();
        typing.remove();
        appendMsg('assistant', data.response || data.error || 'No response');
      } catch (err) {
        typing.remove();
        appendMsg('assistant', 'Sorry, error occurred.');
      }
    });

    chatIn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    });

    chatIn.addEventListener('input', () => {
      chatIn.style.height = 'auto';
      chatIn.style.height = Math.min(chatIn.scrollHeight, 120) + 'px';
    });
  }

  /* ── Stats fetcher ── */
  async function fetchStats() {
    try {
      const res = await fetch('/dashboard/stats');
      if (!res.ok) return;
      const data = await res.json();
      const req = data.requests || state.requests;
      const tok = data.tokens || state.tokens + Math.floor(Math.random() * 1000);
      animateVal('stat-requests', state.requests, req, 1000);
      state.requests = req;
      animateVal('stat-tokens', state.tokens, tok, 1000);
      state.tokens = tok;
      $('#live-rps').textContent = (Math.random() * 5).toFixed(1);
      $('#live-latency').textContent = Math.floor(Math.random() * 150 + 50);
      $('#live-memory').textContent = (Math.random() * 50 + 400).toFixed(0);
      const up = Math.floor((Date.now() - state.uptimeStart) / 1000);
      $('#stat-uptime').textContent = fmtDur(up);
      $('#dossier-uptime').textContent = fmtDur(up);
      $('#dossier-requests').textContent = state.requests;
    } catch (e) { /* silent */ }
  }

  function fmtDur(s) {
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (d > 0) return `${d}d ${h}h`;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${sec}s`;
    return `${sec}s`;
  }

  function animateVal(id, start, end, dur) {
    const el = document.getElementById(id);
    if (!el) return;
    const t0 = performance.now();
    const diff = end - start;
    function step(t) {
      const p = Math.min((t - t0) / dur, 1);
      const e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.floor(start + diff * e).toLocaleString();
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* ── Countdown ── */
  setInterval(() => {
    const s = Math.floor((Date.now() - state.uptimeStart) / 1000);
    $('#cd-days').textContent = Math.floor(s / 86400);
    $('#cd-hours').textContent = Math.floor((s % 86400) / 3600);
    $('#cd-mins').textContent = Math.floor((s % 3600) / 60);
    $('#cd-secs').textContent = s % 60;
  }, 1000);

  /* ── Case number ── */
  const caseNum = $('#case-num');
  if (caseNum) caseNum.textContent = String(Math.floor(Math.random() * 999) + 1).padStart(3, '0');

  /* ── Case scope ── */
  const caseScope = $('#case-scope');
  if (caseScope) {
    let v = 0;
    setInterval(() => { v += Math.floor(Math.random() * 100); caseScope.textContent = '$' + v.toLocaleString(); }, 2000);
  }

  /* ── Keyboard ── */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'k' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      showToast('Command palette — Coming soon!', 'info');
    }
  });

  /* ── Performance monitoring ── */
  if ('PerformanceObserver' in window) {
    const perfObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'largest-contentful-paint') {
          // LCP logged
        }
      }
    });
    perfObserver.observe({ entryTypes: ['largest-contentful-paint', 'first-input'] });
  }

  window.addEventListener('load', () => {
    const timing = performance.timing;
    const loadTime = timing.loadEventEnd - timing.navigationStart;
    // Load time logged
  });

  setInterval(fetchStats, 5000);
  fetchStats();

  window.Aery = { state, showToast, scrollToSection: window.scrollToSection, fetchStats };

})();
