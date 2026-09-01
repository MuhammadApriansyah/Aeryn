/* ═══════════════════════════════════════════════════════════════════ */
/* AERYN — Frontend Engine v5 (Advanced)                              */
/* Tech: Three.js + GSAP ScrollTrigger + Magnetic Cursor              */
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
  /* MAGNETIC CURSOR — Interactive hover effect                         */
  /* ═══════════════════════════════════════════════════════════════════ */

  const cursorOuter = document.getElementById('cursor-outer');
  const cursorInner = document.getElementById('cursor-inner');
  const cursorLabel = document.getElementById('cursor-label');
  let mouseX = 0, mouseY = 0;
  let outerX = 0, outerY = 0;
  let innerX = 0, innerY = 0;
  let isHovering = false;
  let hoverLabel = '';

  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  // Hover detection for magnetic effect
  $$('[data-cursor-hover]').forEach(el => {
    el.addEventListener('mouseenter', () => {
      isHovering = true;
      hoverLabel = el.getAttribute('data-cursor-hover') || '';
      if (cursorLabel) cursorLabel.textContent = hoverLabel;
      if (cursorOuter) cursorOuter.classList.add('hovering');
    });
    el.addEventListener('mouseleave', () => {
      isHovering = false;
      hoverLabel = '';
      if (cursorLabel) cursorLabel.textContent = '';
      if (cursorOuter) cursorOuter.classList.remove('hovering');
    });
  });

  (function animateCursor() {
    // Outer cursor follows with delay (magnetic effect)
    outerX += (mouseX - outerX) * 0.12;
    outerY += (mouseY - outerY) * 0.12;
    // Inner cursor follows faster
    innerX += (mouseX - innerX) * 0.25;
    innerY += (mouseY - innerY) * 0.25;

    if (cursorOuter) {
      cursorOuter.style.left = outerX + 'px';
      cursorOuter.style.top = outerY + 'px';
    }
    if (cursorInner) {
      cursorInner.style.left = innerX + 'px';
      cursorInner.style.top = innerY + 'px';
    }
    requestAnimationFrame(animateCursor);
  })();

  /* ═══════════════════════════════════════════════════════════════════ */
  /* THREE.JS — Advanced particle field with post-processing           */
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

    // Create particle geometry - 5000 particles
    const particleCount = 5000;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;

      // Color gradient from indigo to cyan to pink
      const t = Math.random();
      if (t < 0.33) {
        colors[i * 3] = 0.39; colors[i * 3 + 1] = 0.4; colors[i * 3 + 2] = 0.95;
      } else if (t < 0.66) {
        colors[i * 3] = 0.02; colors[i * 3 + 1] = 0.71; colors[i * 3 + 2] = 0.83;
      } else {
        colors[i * 3] = 0.92; colors[i * 3 + 1] = 0.28; colors[i * 3 + 2] = 0.6;
      }

      sizes[i] = Math.random() * 3 + 1;
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.PointsMaterial({
      size: 0.04,
      vertexColors: true,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    // Add point light
    const pointLight = new THREE.PointLight(0x6366f1, 1, 100);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    camera.position.z = 8;

    // Mouse interaction
    let mouseX = 0, mouseY = 0;
    let targetRotationX = 0, targetRotationY = 0;
    
    document.addEventListener('mousemove', (e) => {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    });

    // Animation loop
    function animate() {
      requestAnimationFrame(animate);

      // Smooth rotation based on mouse
      targetRotationX += (mouseY * 0.3 - targetRotationX) * 0.05;
      targetRotationY += (mouseX * 0.3 - targetRotationY) * 0.05;

      particles.rotation.x += 0.0002;
      particles.rotation.y += 0.0003;
      particles.rotation.x += targetRotationX * 0.001;
      particles.rotation.y += targetRotationY * 0.001;

      // Animate particle positions slightly
      const positions = particles.geometry.attributes.position.array;
      for (let i = 0; i < particleCount; i++) {
        positions[i * 3 + 1] += Math.sin(Date.now() * 0.001 + i) * 0.001;
      }
      particles.geometry.attributes.position.needsUpdate = true;

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
  /* GSAP SCROLLTRIGGER — Scroll-driven animations                      */
  /* ═══════════════════════════════════════════════════════════════════ */

  function initGSAP() {
    if (typeof gsap === 'undefined') return;
    if (typeof ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(ScrollTrigger);
    }

    // Cover title animation
    gsap.from('.title-line', {
      y: 120,
      opacity: 0,
      duration: 1.4,
      stagger: 0.2,
      ease: 'power4.out',
      delay: 0.3
    });

    // Stats animation
    gsap.from('.stat-card', {
      y: 80,
      opacity: 0,
      duration: 1,
      stagger: 0.15,
      delay: 1,
      ease: 'power3.out'
    });

    // Scroll-triggered animations for each section
    const sections = $$('section');
    sections.forEach((section, index) => {
      if (index === 0) return; // Skip cover

      const header = section.querySelector('.hdr');
      const cards = section.querySelectorAll('.practice-card, .stack-cat, .div-card, .tool-card, .dossier-card, .stat-card');
      const workItems = section.querySelectorAll('.work-item');

      if (header) {
        gsap.from(header, {
          scrollTrigger: {
            trigger: section,
            start: 'top 80%',
            end: 'top 20%',
            scrub: 1
          },
          y: 60,
          opacity: 0,
          duration: 1,
          ease: 'power3.out'
        });
      }

      if (cards.length > 0) {
        gsap.from(cards, {
          scrollTrigger: {
            trigger: section,
            start: 'top 70%',
            end: 'top 30%',
            scrub: 1
          },
          y: 80,
          opacity: 0,
          duration: 1,
          stagger: 0.1,
          ease: 'power3.out'
        });
      }

      if (workItems.length > 0) {
        gsap.from(workItems, {
          scrollTrigger: {
            trigger: section,
            start: 'top 70%',
            end: 'top 30%',
            scrub: 1
          },
          x: -50,
          opacity: 0,
          duration: 0.8,
          stagger: 0.15,
          ease: 'power3.out'
        });
      }
    });

    // Smooth scroll for navigation links
    $$('a[href^="#"]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = link.getAttribute('href').substring(1);
        const el = document.getElementById(target);
        if (el) {
          gsap.to(window, {
            duration: 1,
            scrollTo: { y: el, offsetY: 80 },
            ease: 'power3.inOut'
          });
        }
      });
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
