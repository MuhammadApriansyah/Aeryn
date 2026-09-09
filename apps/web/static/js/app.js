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
    memory:  { label: 'Memory',  size: 'large' },
    tools:   { label: 'Tools',   size: 'large' },
    agents:  { label: 'Agents',  size: 'large' },
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

    if (window.AerynSection && window.AerynSection.load) {
      window.AerynSection.load(id, modalBody);
    }
  }

  function closeModal() {
    modalRoot.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (s.focusReturn) { s.focusReturn.focus(); s.focusReturn = null; }
  }

  // === Chat modal ===
  function openChat() {
    s.focusReturn = document.activeElement;
    chatModalRoot.classList.add('open');
    chatModalRoot.querySelector('.chatmodal').setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }
  function closeChat() {
    chatModalRoot.classList.remove('open');
    chatModalRoot.querySelector('.chatmodal').setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (s.focusReturn) { s.focusReturn.focus(); s.focusReturn = null; }
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
  }
  function closeDrawer() {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    drawerHamburger.classList.remove('open');
    drawerHamburger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }
  function toggleDrawer() {
    if (drawer.classList.contains('open')) closeDrawer();
    else openDrawer();
  }

  // === Focus trap ===
  function focusTrap(e) {
    if (e.key !== 'Tab') return;
    var container = document.querySelector('.modal-root.open .modal, .chatmodal-root.open .chatmodal');
    if (!container) return;
    var focusables = container.querySelectorAll('button, select, textarea, input, [tabindex]:not([tabindex="-1"])');
    if (focusables.length === 0) return;
    var first = focusables[0];
    var last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
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
      focusTrap(e);
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
  };
})();