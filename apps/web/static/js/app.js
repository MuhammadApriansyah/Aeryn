/**
 * app.js — App shell controller: bottom dock, modal manager, chat modal.
 * Vanilla (ES5), a11y-aware (focus trap + ESC).
 */
(function () {
  'use strict';

  // === DOM ===
  var dockItems = document.querySelectorAll('.dock-item');
  var openChatBtns = document.querySelectorAll('[data-open-chat]');
  var scrollToBtns = document.querySelectorAll('[data-scroll-to]');

  var modalRoot = document.getElementById('modalRoot');
  var modal = document.getElementById('modal');
  var modalTitle = document.getElementById('modalTitle');
  var modalBody = document.getElementById('modalBody');
  var modalClose = document.getElementById('modalClose');
  var modalBackdrop = document.getElementById('modalBackdrop');

  var chatModalRoot = document.getElementById('chatModalRoot');
  var chatModalClose = document.getElementById('chatModalClose');
  var chatModalBackdrop = document.getElementById('chatModalBackdrop');

  var drawer = document.getElementById('drawer');
  var drawerBackdrop = document.getElementById('drawerBackdrop');
  var drawerHamburger = document.getElementById('dockHamburger');

  var toastRoot = document.getElementById('toastRoot');

  var s = { focusReturn: null };

  // === Module registry (untuk modal) ===
  var MODULES = {
    health:  { label: 'Health',  size: 'medium' },
    memory:  { label: 'Memory',  size: 'large' },
    tools:   { label: 'Tools',   size: 'large' },
    agents:  { label: 'Agents',  size: 'large' },
    auth:    { label: 'Auth',    size: 'medium' },
    sessions:{ label: 'Sessions', size: 'medium' },
    skills:  { label: 'Skills',  size: 'medium' },
    logs:    { label: 'Console', size: 'medium' },
    tasks:   { label: 'Tasks',   size: 'medium' },
    safety:  { label: 'Safety',  size: 'medium' },
    trace:   { label: 'Trace',   size: 'medium' },
    eval:    { label: 'Evaluation', size: 'medium' },
    plugins: { label: 'Plugins', size: 'medium' },
    settings:{ label: 'Settings', size: 'small' },
  };

  // === Toast ===
  function showToast(msg, type) {
    type = type || 'info';
    if (!toastRoot) return;
    var t = document.createElement('div');
    t.className = 'toast ' + type;
    t.textContent = msg;
    toastRoot.appendChild(t);
    setTimeout(function () {
      t.classList.add('hide');
      setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 260);
    }, 2600);
  }
  window.AerynToast = showToast;

  // === Modal (module) ===
  function openModal(id) {
    var m = MODULES[id];
    if (!m) return;
    s.focusReturn = document.activeElement;
    modalTitle.textContent = m.label;
    modal.className = 'modal size-' + m.size;
    modalBody.innerHTML = '<div class="modal-loading" id="modalLoading">Memuat ' + m.label + '…</div>';
    modal.setAttribute('aria-hidden', 'false');
    modalRoot.classList.add('open');
    document.body.style.overflow = 'hidden';
    setPanelFocus(modal);
    // P0: persist modul terakhir dibuka.
    try { localStorage.setItem('aeryn.lastModule', id); } catch (e) {}

    if (window.AerynSection && window.AerynSection.load) {
      window.AerynSection.load(id, modalBody);
    }
  }

  function closeModal() {
    modalRoot.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    releaseFocus();
    if (s.focusReturn) { s.focusReturn.focus(); s.focusReturn = null; }
  }

  // === Chat modal ===
  function openChat() {
    s.focusReturn = document.activeElement;
    chatModalRoot.classList.add('open');
    chatModalRoot.querySelector('.chatmodal').setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    setPanelFocus(chatModalRoot.querySelector('.chatmodal'));
  }
  function closeChat() {
    chatModalRoot.classList.remove('open');
    chatModalRoot.querySelector('.chatmodal').setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    releaseFocus();
    if (s.focusReturn) { s.focusReturn.focus(); s.focusReturn = null; }
  }
  // Buka chat modal + resume sesi tertentu (set iframe src, reload).
  function openSession(sessionId) {
    if (!sessionId) { openChat(); return; }
    var frame = chatModalRoot.querySelector('.chatmodal-iframe');
    if (frame) frame.src = '/chat?session=' + encodeURIComponent(sessionId);
    openChat();
  }

  // === Scroll-to (hero buttons) ===
  function scrollTo(target) {
    var el = document.querySelector(target);
    if (el) {
      if (window.lenis) window.lenis.scrollTo(el);
      else el.scrollIntoView({ behavior: 'smooth' });
    }
  }

  // === Drawer (hamburger menu) ===
  function openDrawer() {
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    drawerHamburger.classList.add('open');
    drawerHamburger.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    setPanelFocus(drawer.querySelector('.drawer-panel'));
  }
  function closeDrawer() {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    drawerHamburger.classList.remove('open');
    drawerHamburger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    releaseFocus();
  }
  function toggleDrawer() {
    if (drawer.classList.contains('open')) closeDrawer();
    else openDrawer();
  }

  // === Focus management (ringkas: pakai `inert`) ===
  // Saat panel (modal/drawer/chat) terbuka, kita buat area lain inert sehingga
  // fokus keyboard & screen-reader otomatis terkurung di dalam panel — tanpa
  // kalkulasi first/last manual yang rumit.
  var HOME = document.querySelector('.homepage');
  function setPanelFocus(panel) {
    if (!HOME) return;
    // Semua panel non-aktif di-jadikan inert. Panel aktif bebas fokus.
    HOME.inert = true;
    document.querySelectorAll('.dock, .drawer').forEach(function (el) {
      el.inert = !(el === panel);
    });
  }
  function releaseFocus() {
    if (!HOME) return;
    HOME.inert = false;
    document.querySelectorAll('.dock, .drawer').forEach(function (el) { el.inert = false; });
  }

  // === Wire events ===
  function wire() {
    // Dock items → module modal
    dockItems.forEach(function (item) {
      item.addEventListener('click', function () {
        var mid = item.getAttribute('data-open-modal');
        if (mid) openModal(mid);
      });
    });

    // Open chat buttons (hero + dock)
    openChatBtns.forEach(function (btn) {
      btn.addEventListener('click', openChat);
    });

    // Drawer items → module modal (tutup drawer dulu)
    document.querySelectorAll('.drawer-item').forEach(function (item) {
      item.addEventListener('click', function () {
        var mid = item.getAttribute('data-open-modal');
        closeDrawer();
        if (mid) openModal(mid);
      });
    });

    // Quick actions → aksi cepat
    document.querySelectorAll('.quick-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var q = btn.getAttribute('data-quick');
        closeDrawer();
        if (q === 'chat') { openChat(); }
        else if (q === 'tasks') { openModal('tasks'); }
        else { openModal(q); }
      });
    });

    // Filter drawer grid (cari modul cepat)
    var drawerInput = document.getElementById('drawerInput');
    if (drawerInput) {
      drawerInput.addEventListener('input', function () {
        var q = drawerInput.value.trim().toLowerCase();
        document.querySelectorAll('.drawer-item').forEach(function (item) {
          var label = item.querySelector('.drawer-label');
          var desc = item.querySelector('.drawer-desc');
          var text = (label ? label.textContent : '') + ' ' + (desc ? desc.textContent : '');
          item.classList.toggle('hidden', q && text.toLowerCase().indexOf(q) === -1);
        });
      });
    }

    // Hamburger toggle
    if (drawerHamburger) drawerHamburger.addEventListener('click', toggleDrawer);
    if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeDrawer);

    // Scroll-to buttons
    scrollToBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        scrollTo(btn.getAttribute('data-scroll-to'));
      });
    });

    // Modal close
    if (modalClose) modalClose.addEventListener('click', closeModal);
    if (modalBackdrop) modalBackdrop.addEventListener('click', closeModal);
    if (chatModalClose) chatModalClose.addEventListener('click', closeChat);
    if (chatModalBackdrop) chatModalBackdrop.addEventListener('click', closeChat);

    // ESC + focus trap
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (chatModalRoot.classList.contains('open')) { closeChat(); return; }
        if (modalRoot.classList.contains('open')) { closeModal(); return; }
        if (drawer.classList.contains('open')) { closeDrawer(); return; }
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }

  window.AerynApp = {
    showToast: showToast,
    openModal: openModal,
    closeModal: closeModal,
    openChat: openChat,
    closeChat: closeChat,
    openSession: openSession,
    openDrawer: openDrawer,
    closeDrawer: closeDrawer,
  };
})();