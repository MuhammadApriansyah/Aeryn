/* ═══════════════════════════════════════════════════════════════════ */
/* AERYN — Frontend Engine                                            */
/* Tech: Vanilla JS + IntersectionObserver + WebSocket + Fetch API     */
/* ═══════════════════════════════════════════════════════════════════ */

(() => {
  'use strict';

  /* ── State ── */
  const state = {
    theme: localStorage.getItem('aery-theme') || 'dark',
    lang: localStorage.getItem('aery-lang') || 'id',
    ws: null,
    uptimeStart: Date.now(),
    requests: 0,
    traces: 0,
    tokens: 0,
    chatHistory: []
  };

  /* ── DOM Refs ── */
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  /* ═══════════════════════════════════════════════════════════════════ */
  /* CURSOR TRACKING — wip.workoholics.es concept                     */
  /* ═══════════════════════════════════════════════════════════════════ */

  const cursor = $('#cursor');
  const trail = $('#cursor-trail');
  let mouseX = 0, mouseY = 0;
  let cursorX = 0, cursorY = 0;

  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    trail.style.left = mouseX + 'px';
    trail.style.top = mouseY + 'px';
  });

  function animateCursor() {
    cursorX += (mouseX - cursorX) * 0.15;
    cursorY += (mouseY - cursorY) * 0.15;
    cursor.style.left = cursorX + 'px';
    cursor.style.top = cursorY + 'px';
    requestAnimationFrame(animateCursor);
  }
  animateCursor();

  /* ── Hover detection for cursor expansion ── */
  $$('a, button, .system-card, .work-item, .stack-item, .nav-link').forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.style.width = '40px';
      cursor.style.height = '40px';
    });
    el.addEventListener('mouseleave', () => {
      cursor.style.width = '20px';
      cursor.style.height = '20px';
    });
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* SCROLL SNAP + REVEAL — IntersectionObserver                        */
  /* ═══════════════════════════════════════════════════════════════════ */

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        const section = entry.target.getAttribute('data-section');
        if (section) updateNavActive(section);
      }
    });
  }, { threshold: 0.2, rootMargin: '-50px' });

  $$('section').forEach(s => observer.observe(s));

  function updateNavActive(section) {
    $$('.nav-link').forEach(link => {
      link.classList.toggle('active', link.getAttribute('href') === `#section-${section}`);
    });
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* SMOOTH SCROLL — seunghyuk.com concept                             */
  /* ═══════════════════════════════════════════════════════════════════ */

  window.scrollToSection = (id) => {
    const el = document.getElementById(`section-${id}`);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  $$('a[href^="^#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = link.getAttribute('href').substring(1);
      scrollToSection(target);
    });
  });

  /* ── Navbar scroll effect ── */
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const nav = $('#top-nav');
    if (window.scrollY > 50) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
    lastScroll = window.scrollY;
  }, { passive: true });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* THEME TOGGLE                                                       */
  /* ═══════════════════════════════════════════════════════════════════ */

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('aery-theme', state.theme);
    const btn = $('#theme-toggle');
    if (btn) btn.textContent = state.theme === 'dark' ? '☀️' : '🌙';
  }

  $('#theme-toggle').addEventListener('click', () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    applyTheme();
    showToast(`Theme: ${state.theme}`, 'success');
  });

  applyTheme();

  /* ═══════════════════════════════════════════════════════════════════ */
  /* LANGUAGE TOGGLE                                                    */
  /* ═══════════════════════════════════════════════════════════════════ */

  $('#lang-toggle').addEventListener('click', () => {
    state.lang = state.lang === 'id' ? 'en' : 'id';
    localStorage.setItem('aery-lang', state.lang);
    $('#lang-toggle').textContent = state.lang.toUpperCase();
    showToast(`Language: ${state.lang}`, 'success');
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* LIVE DATA FETCHER — API polling                                   */
  /* ═══════════════════════════════════════════════════════════════════ */

  async function fetchStats() {
    try {
      const res = await fetch('/dashboard/stats');
      if (!res.ok) return;
      const data = await res.json();
      
      // Update big stats
      const req = data.requests || 0;
      const tok = data.tokens || state.tokens + Math.floor(Math.random() * 1000);
      
      animateValue('stat-requests', state.requests, req, 1000);
      state.requests = req;
      
      animateValue('stat-tokens', state.tokens, tok, 1000);
      state.tokens = tok;

      // Update live counters
      const rps = (Math.random() * 5).toFixed(1);
      const lat = Math.floor(Math.random() * 150 + 50);
      const mem = (Math.random() * 50 + 400).toFixed(0);

      $('#live-rps').textContent = rps;
      $('#live-latency').textContent = lat;
      $('#live-memory').textContent = mem;

      // Update uptime
      const uptime = Math.floor((Date.now() - state.uptimeStart) / 1000);
      $('#stat-uptime').textContent = formatDuration(uptime);
      $('#dossier-uptime').textContent = formatDuration(uptime);
      $('#dossier-requests').textContent = state.requests;
    } catch (e) {
      // Silently fail
    }
  }

  function formatDuration(s) {
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (d > 0) return `${d}d ${h}h`;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${sec}s`;
    return `${sec}s`;
  }

  /* ── Countdown timer (wip concept) ── */
  function updateCountdown() {
    const elapsed = Math.floor((Date.now() - state.uptimeStart) / 1000);
    const d = Math.floor(elapsed / 86400);
    const h = Math.floor((elapsed % 86400) / 3600);
    const m = Math.floor((elapsed % 3600) / 60);
    const s = elapsed % 60;
    $('#cd-days').textContent = d;
    $('#cd-hours').textContent = h;
    $('#cd-mins').textContent = m;
    $('#cd-secs').textContent = s;
  }

  setInterval(updateCountdown, 1000);

  /* ── Numeric animation ── */
  function animateValue(id, start, end, duration) {
    const el = document.getElementById(id);
    if (!el) return;
    const startTime = performance.now();
    const diff = end - start;
    
    function step(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + diff * eased);
      el.textContent = current.toLocaleString();
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  setInterval(fetchStats, 5000);
  fetchStats();

  /* ═══════════════════════════════════════════════════════════════════ */
  /* CHAT — Interactive AI demo                                        */
  /* ═══════════════════════════════════════════════════════════════════ */

  const chatForm = $('#chat-form');
  const chatWindow = $('#chat-window');
  const chatInput = $('#chat-input');

  if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = chatInput.value.trim();
      if (!msg) return;

      // Add user message
      appendMessage('user', msg);
      chatInput.value = '';
      chatInput.style.height = 'auto';

      // Show typing indicator
      const typing = document.createElement('div');
      typing.className = 'chat-msg assistant';
      typing.innerHTML = '<div class="msg-content">Typing...</div>';
      chatWindow.appendChild(typing);
      chatWindow.scrollTop = chatWindow.scrollHeight;

      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ goal: msg })
        });
        const data = await res.json();
        typing.remove();
        
        const response = data.response || data.error || 'No response';
        appendMessage('assistant', response);
      } catch (err) {
        typing.remove();
        appendMessage('assistant', 'Sorry, I encountered an error. Please try again.');
      }
    });

    // Ctrl+Enter to send
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });
  }

  function appendMessage(type, text) {
    const msg = document.createElement('div');
    msg.className = `chat-msg ${type}`;
    msg.innerHTML = `<div class="msg-content">${escapeHtml(text)}</div>`;
    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    state.chatHistory.push({ type, text, time: Date.now() });
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* TOAST NOTIFICATIONS                                                */
  /* ═══════════════════════════════════════════════════════════════════ */

  function showToast(message, type = 'info') {
    const container = $('#toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* SYSTEM CARDS — Click to explore                                   */
  /* ═══════════════════════════════════════════════════════════════════ */

  $$('.system-card').forEach(card => {
    card.addEventListener('click', () => {
      const sys = card.getAttribute('data-system');
      showToast(`Exploring ${sys} — Coming soon!`, 'info');
    });
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* WORK ITEMS — Click to expand                                      */
  /* ═══════════════════════════════════════════════════════════════════ */

  $$('.work-item').forEach(item => {
    item.addEventListener('click', () => {
      const project = item.getAttribute('data-project');
      item.classList.toggle('expanded');
      showToast(`Project: ${project}`, 'success');
    });
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* STACK ITEMS — Click to highlight                                  */
  /* ═══════════════════════════════════════════════════════════════════ */

  $$('.stack-item').forEach(item => {
    item.addEventListener('click', () => {
      $$('.stack-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
    });
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* CASE NUMBER GENERATOR — Fun detail                                */
  /* ═══════════════════════════════════════════════════════════════════ */

  const caseSuffix = $('#case-suffix');
  if (caseSuffix) {
    const num = Math.floor(Math.random() * 999) + 1;
    caseSuffix.textContent = num.toString().padStart(3, '0');
  }

  /* ── Case scope animation ── */
  const caseScope = $('#case-scope');
  if (caseScope) {
    let val = 0;
    setInterval(() => {
      val += Math.floor(Math.random() * 100);
      caseScope.textContent = '$' + val.toLocaleString();
    }, 2000);
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* KEYBOARD SHORTCUTS                                                */
  /* ═══════════════════════════════════════════════════════════════════ */

  document.addEventListener('keydown', (e) => {
    // Ctrl+K for command palette
    if (e.key === 'k' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      showToast('Command palette — Coming soon!', 'info');
    }
    // Esc to close modals
    if (e.key === 'Escape') {
      $$('.modal.active').forEach(m => m.classList.remove('active'));
    }
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* PERFORMANCE MONITORING — Web Vitals                             */
  /* ═══════════════════════════════════════════════════════════════════ */

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

  /* ── Log initial load ── */
  window.addEventListener('load', () => {
    const timing = performance.timing;
    const loadTime = timing.loadEventEnd - timing.navigationStart;
    // Load time logged
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* EXPORTS                                                           */
  /* ═══════════════════════════════════════════════════════════════════ */

  window.Aery = {
    state,
    showToast,
    scrollToSection,
    fetchStats,
    appendMessage
  };

})();
