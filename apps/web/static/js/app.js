/**
 * app.js — App shell controller: floating navbar routing + modal manager +
 * command palette. Vanilla (ES5, no modules), a11y-aware.
 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // === State ===
  var s = {
    activeView: 'chat',
    modalOpen: false,
    focusReturn: null,
  };

  // === DOM ===
  var navLinks = document.querySelectorAll('.nav-link');
  var settingsBtn = document.getElementById('settingsBtn');
  var commandBtn = document.getElementById('commandBtn');
  var modalRoot = document.getElementById('modalRoot');
  var modal = document.getElementById('modal');
  var modalTitle = document.getElementById('modalTitle');
  var modalBody = document.getElementById('modalBody');
  var modalClose = document.getElementById('modalClose');
  var modalBackdrop = document.getElementById('modalBackdrop');
  var toastRoot = document.getElementById('toastRoot');
  var paletteRoot = document.getElementById('paletteRoot');
  var paletteInput = document.getElementById('paletteInput');
  var paletteResults = document.getElementById('paletteResults');

  // === Module registry (untuk modal + command palette) ===
  var MODULES = [
    { id: 'chat',       label: 'Chat',           icon: '💬', size: 'full',   view: true },
    { id: 'memory',     label: 'Memory',         icon: '🧠', size: 'large' },
    { id: 'tools',      label: 'Tools',          icon: '🔧', size: 'large' },
    { id: 'agents',     label: 'Agents',         icon: '🤖', size: 'large' },
    { id: 'safety',     label: 'Safety',         icon: '🛡', size: 'medium' },
    { id: 'trace',      label: 'Trace',          icon: '📈', size: 'medium' },
    { id: 'eval',       label: 'Evaluation',     icon: '🏆', size: 'medium' },
    { id: 'plugins',    label: 'Plugins',        icon: '🧩', size: 'medium' },
    { id: 'settings',   label: 'Settings',       icon: '⚙', size: 'small' },
  ];

  function moduleById(id) {
    for (var i = 0; i < MODULES.length; i++) if (MODULES[i].id === id) return MODULES[i];
    return null;
  }

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
    }, 2800);
  }
  window.AerynToast = showToast;

  // === Modal manager ===
  function openModal(id) {
    var m = moduleById(id);
    if (!m || m.view) return; // view modules bukan modal (chat)

    s.focusReturn = document.activeElement;
    modalTitle.textContent = m.label;
    modal.className = 'modal size-' + (m.size || 'medium');
    modalBody.innerHTML = '<div class="modal-loading" id="modalLoading">Memuat ' + m.label + '…</div>';
    modal.setAttribute('aria-hidden', 'false');
    modalRoot.classList.add('open');

    // body scroll lock
    document.body.style.overflow = 'hidden';
    s.modalOpen = true;

    // Muat konten modul (hook untuk section loader, diisi nanti).
    if (window.AerynSection && window.AerynSection.load) {
      window.AerynSection.load(id, modalBody);
    } else {
      var lb = document.getElementById('modalLoading');
      if (lb) lb.textContent = m.label + ' (belum diimplementasi)';
    }
  }

  function closeModal() {
    if (!s.modalOpen) return;
    modalRoot.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    s.modalOpen = false;
    if (s.focusReturn) { s.focusReturn.focus(); s.focusReturn = null; }
  }

  function focusTrap(e) {
    if (!s.modalOpen || e.key !== 'Tab') return;
    var focusables = modal.querySelectorAll('button, select, textarea, input, [tabindex]:not([tabindex="-1"])');
    if (focusables.length === 0) return;
    var first = focusables[0];
    var last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  // === Navbar routing ===
  function activate(id) {
    var m = moduleById(id);
    if (!m) return;
    s.activeView = id;

    // Update nav active state
    for (var i = 0; i < navLinks.length; i++) {
      navLinks[i].classList.toggle('active', navLinks[i].getAttribute('data-target') === id);
    }

    if (m.view) {
      // view module (chat) — tutup modal, pastikan view aktif
      closeModal();
      var panels = document.querySelectorAll('.view-panel');
      for (var j = 0; j < panels.length; j++) {
        panels[j].classList.toggle('active', panels[j].getAttribute('data-view') === id);
      }
    } else {
      openModal(id);
    }
  }

  // Wire nav links
  function wireNav() {
    for (var i = 0; i < navLinks.length; i++) {
      navLinks[i].addEventListener('click', function () {
        activate(this.getAttribute('data-target'));
      });
    }
    if (settingsBtn) settingsBtn.addEventListener('click', function () { activate('settings'); });
  }

  // === Command palette ===
  function openPalette() {
    paletteRoot.classList.add('open');
    paletteInput.value = '';
    paletteInput.focus();
    renderPalette('');
  }
  function closePalette() {
    paletteRoot.classList.remove('open');
  }
  function renderPalette(q) {
    q = (q || '').toLowerCase();
    paletteResults.innerHTML = '';
    var matches = MODULES.filter(function (m) {
      return !q || m.label.toLowerCase().indexOf(q) !== -1;
    });
    matches.forEach(function (m) {
      var item = document.createElement('div');
      item.className = 'palette-item';
      item.innerHTML = '<span class="palette-icon">' + m.icon + '</span>' + m.label;
      item.addEventListener('click', function () {
        closePalette();
        activate(m.id);
      });
      paletteResults.appendChild(item);
    });
  }

  // Wire command palette
  if (commandBtn) commandBtn.addEventListener('click', openPalette);

  // === Global keyboard ===
  document.addEventListener('keydown', function (e) {
    // Cmd/Ctrl+K → command palette
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (paletteRoot.classList.contains('open')) closePalette();
      else openPalette();
      return;
    }
    // ESC → tutup modal / palette
    if (e.key === 'Escape') {
      if (s.modalOpen) { closeModal(); return; }
      if (paletteRoot.classList.contains('open')) { closePalette(); return; }
    }
    focusTrap(e);
  });

  if (paletteInput) {
    paletteInput.addEventListener('input', function () { renderPalette(paletteInput.value); });
    paletteInput.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closePalette();
    });
  }

  // Modal close events
  if (modalClose) modalClose.addEventListener('click', closeModal);
  if (modalBackdrop) modalBackdrop.addEventListener('click', closeModal);

  // === Init ===
  function init() {
    wireNav();
    activate('chat');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose
  window.AerynApp = {
    showToast: showToast,
    openModal: openModal,
    closeModal: closeModal,
    activate: activate,
  };
})();