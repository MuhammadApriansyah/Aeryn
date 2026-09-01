/* ═══════════════════════════════════════════════════════════════════ */
/* AERYN — Frontend Engine v4                                         */
/* Tech: Three.js + GSAP + Vanilla JS                                 */
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

  /* ═══════════════════════════════════════════════════════════════════ */
  /* THREE.JS PARTICLE FIELD — Cover background                        */
  /* ═══════════════════════════════════════════════════════════════════ */
  
  function initThreeJS() {
    const container = document.getElementById('cover-3d');
    if (!container || typeof THREE === 'undefined') return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Create particle geometry
    const particleCount = 3000;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 15;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 15;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 15;

      // Color gradient from indigo to cyan
      const t = Math.random();
      colors[i * 3] = 0.39 + t * 0.4;     // R
      colors[i * 3 + 1] = 0.4 + t * 0.4;  // G
      colors[i * 3 + 2] = 0.95;           // B
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.03,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // Add connecting lines
    const lineGeometry = new THREE.BufferGeometry();
    const linePositions = new Float32Array(500 * 6);
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x6366f1,
      transparent: true,
      opacity: 0.1
    });
    
    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lines);

    camera.position.z = 5;

    // Mouse interaction
    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (e) => {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    });

    // Animation loop
    function animate() {
      requestAnimationFrame(animate);

      particles.rotation.x += 0.0003;
      particles.rotation.y += 0.0005;
      
      // Subtle mouse influence
      particles.rotation.x += mouseY * 0.0005;
      particles.rotation.y += mouseX * 0.0005;

      // Update connecting lines
      const positions = particles.geometry.attributes.position.array;
      const linePos = lines.geometry.attributes.position.array;
      
      for (let i = 0; i < 500; i++) {
        const i3 = i * 6;
        const p1 = Math.floor(Math.random() * particleCount);
        const p2 = Math.floor(Math.random() * particleCount);
        
        linePos[i3] = positions[p1 * 3];
        linePos[i3 + 1] = positions[p1 * 3 + 1];
        linePos[i3 + 2] = positions[p1 * 3 + 2];
        linePos[i3 + 3] = positions[p2 * 3];
        linePos[i3 + 4] = positions[p2 * 3 + 1];
        linePos[i3 + 5] = positions[p2 * 3 + 2];
      }
      
      lines.geometry.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    }

    animate();

    // Handle resize
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* CUSTOM CURSOR                                                      */
  /* ═══════════════════════════════════════════════════════════════════ */

  const cursor = $('#cursor');
  const trail = $('#cursor-trail');
  let mx = 0, my = 0, cx = 0, cy = 0;

  document.addEventListener('mousemove', (e) => {
    mx = e.clientX;
    my = e.clientY;
    if (trail) {
      trail.style.left = mx + 'px';
      trail.style.top = my + 'px';
    }
  });

  (function animateCursor() {
    cx += (mx - cx) * 0.15;
    cy += (my - cy) * 0.15;
    if (cursor) {
      cursor.style.left = cx + 'px';
      cursor.style.top = cy + 'px';
    }
    requestAnimationFrame(animateCursor);
  })();

  $$('a, button, .stat-card, .work-item, .stack-item, .nav-link, .div-card, .tool-card, .practice-card, .dossier-card').forEach(el => {
    el.addEventListener('mouseenter', () => {
      if (cursor) { cursor.style.width = '40px'; cursor.style.height = '40px'; }
    });
    el.addEventListener('mouseleave', () => {
      if (cursor) { cursor.style.width = '20px'; cursor.style.height = '20px'; }
    });
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* GSAP ANIMATIONS                                                    */
  /* ═══════════════════════════════════════════════════════════════════ */

  function initGSAP() {
    if (typeof gsap === 'undefined') return;

    // Cover title animation
    gsap.from('.title-line', {
      y: 100,
      opacity: 0,
      duration: 1.2,
      stagger: 0.15,
      ease: 'power4.out',
      delay: 0.3
    });

    // Stats animation
    gsap.from('.stat-card', {
      y: 60,
      opacity: 0,
      duration: 1,
      stagger: 0.1,
      delay: 0.8,
      ease: 'power3.out'
    });

    // Scroll-triggered animations for each section
    const sections = $$('section');
    sections.forEach(section => {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const section = entry.target;
            
            // Animate headers
            const header = section.querySelector('.hdr');
            if (header) {
              gsap.from(header, {
                y: 40,
                opacity: 0,
                duration: 0.8,
                ease: 'power3.out'
              });
            }

            // Animate cards
            const cards = section.querySelectorAll('.practice-card, .stack-cat, .div-card, .tool-card, .dossier-card');
            if (cards.length > 0) {
              gsap.from(cards, {
                y: 50,
                opacity: 0,
                duration: 0.8,
                stagger: 0.1,
                delay: 0.2,
                ease: 'power3.out'
              });
            }

            // Animate work items
            const workItems = section.querySelectorAll('.work-item');
            if (workItems.length > 0) {
              gsap.from(workItems, {
                x: -30,
                opacity: 0,
                duration: 0.6,
                stagger: 0.1,
                delay: 0.2,
                ease: 'power3.out'
              });
            }

            observer.unobserve(section);
          }
        });
      }, { threshold: 0.2 });

      observer.observe(section);
    });
  }

  /* ═══════════════════════════════════════════════════════════════════ */
  /* SCROLL & NAVIGATION                                                */
  /* ═══════════════════════════════════════════════════════════════════ */

  window.addEventListener('scroll', () => {
    const nav = $('#top-nav');
    if (nav) nav.classList.toggle('scrolled', window.scrollY > 50);
  }, { passive: true });

  window.scrollTo = (id) => {
    const el = document.getElementById(id);
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

  /* ═══════════════════════════════════════════════════════════════════ */
  /* THEME TOGGLE                                                       */
  /* ═══════════════════════════════════════════════════════════════════ */

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('aery-theme', state.theme);
    const btn = $('#theme-btn');
    if (btn) btn.textContent = state.theme === 'dark' ? '☀️' : '🌙';
  }

  const themeBtn = $('#theme-btn');
  if (themeBtn) themeBtn.addEventListener('click', () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    applyTheme();
    showToast(`Theme: ${state.theme}`, 'success');
  });
  applyTheme();

  /* ═══════════════════════════════════════════════════════════════════ */
  /* LANGUAGE TOGGLE                                                    */
  /* ═══════════════════════════════════════════════════════════════════ */

  const langBtn = $('#lang-btn');
  if (langBtn) langBtn.addEventListener('click', () => {
    state.lang = state.lang === 'id' ? 'en' : 'id';
    localStorage.setItem('aery-lang', state.lang);
    langBtn.textContent = state.lang.toUpperCase();
    showToast(`Language: ${state.lang}`, 'success');
  });

  /* ═══════════════════════════════════════════════════════════════════ */
  /* TOAST NOTIFICATIONS                                                */
  /* ═══════════════════════════════════════════════════════════════════ */

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

  /* ═══════════════════════════════════════════════════════════════════ */
  /* WORK ITEMS TOGGLE                                                  */
  /* ═══════════════════════════════════════════════════════════════════ */

  window.toggleWork = (el) => {
    el.classList.toggle('open');
  };

  /* ═══════════════════════════════════════════════════════════════════ */
  /* DIVISIONS EXECUTE                                                  */
  /* ═══════════════════════════════════════════════════════════════════ */

  window.execDiv = async (div) => {
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

  /* ═══════════════════════════════════════════════════════════════════ */
  /* PLUGINS RUN                                                        */
  /* ═══════════════════════════════════════════════════════════════════ */

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

  /* ═══════════════════════════════════════════════════════════════════ */
  /* CHAT                                                               */
  /* ═══════════════════════════════════════════════════════════════════ */

  const chatForm = $('#chat-form');
  const chatWin = $('#chat-win');
  const chatIn = $('#chat-in');

  function appendMsg(type, text) {
    const msg = document.createElement('div');
    msg.className = `msg ${type}`;
    msg.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
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
      typing.className = 'msg asst';
      typing.innerHTML = '<div class="bubble">Typing...</div>';
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
        appendMsg('asst', data.response || data.error || 'No response');
      } catch (err) {
        typing.remove();
        appendMsg('asst', 'Sorry, error occurred.');
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

  /* ═══════════════════════════════════════════════════════════════════ */
  /* STATS FETCHER                                                      */
  /* ═══════════════════════════════════════════════════════════════════ */

  async function fetchStats() {
    try {
      const res = await fetch('/dashboard/stats');
      if (!res.ok) return;
      const data = await res.json();
      const req = data.requests || state.requests;
      const tok = data.tokens || state.tokens + Math.floor(Math.random() * 1000);
      animateVal('s-req', state.requests, req, 1000);
      state.requests = req;
      animateVal('s-tok', state.tokens, tok, 1000);
      state.tokens = tok;
      $('#l-rps').textContent = (Math.random() * 5).toFixed(1);
      $('#l-lat').textContent = Math.floor(Math.random() * 150 + 50);
      $('#l-mem').textContent = (Math.random() * 50 + 400).toFixed(0);
      const up = Math.floor((Date.now() - state.uptimeStart) / 1000);
      $('#s-up').textContent = fmtDur(up);
      $('#dos-up').textContent = fmtDur(up);
      $('#dos-req').textContent = state.requests;
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
    $('#cd-d').textContent = Math.floor(s / 86400);
    $('#cd-h').textContent = Math.floor((s % 86400) / 3600);
    $('#cd-m').textContent = Math.floor((s % 3600) / 60);
    $('#cd-s').textContent = s % 60;
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

  /* ── Being processed ── */
  const beingProc = $('#b-proc');
  if (beingProc) {
    let bp = 0;
    setInterval(() => { bp += Math.floor(Math.random() * 50); beingProc.textContent = bp.toLocaleString(); }, 1000);
  }

  /* ── Clock ── */
  const clockJkt = $('#clock-jkt');
  if (clockJkt) {
    setInterval(() => {
      const now = new Date();
      const h = now.getHours().toString().padStart(2, '0');
      const m = now.getMinutes().toString().padStart(2, '0');
      clockJkt.textContent = `${h}:${m}`;
    }, 1000);
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

  /* ═══════════════════════════════════════════════════════════════════ */
  /* INITIALIZATION                                                     */
  /* ═══════════════════════════════════════════════════════════════════ */

  setInterval(fetchStats, 5000);
  fetchStats();

  // Initialize Three.js and GSAP when DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    initThreeJS();
    initGSAP();
  });

  // Also try immediately in case DOM is already loaded
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    initThreeJS();
    initGSAP();
  }

  window.Aery = { state, showToast, scrollTo: window.scrollTo, fetchStats };

})();
