/**
 * Aeryn Dashboard — Full SPA with Accessibility
 * Features: Nav, Toast, Keyboard, Theme, Offline, Loading, Reduced Motion
 */
(function() {
  'use strict';

  const navItems = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard' },
    { id: 'projects', icon: '📁', label: 'Projects' },
    { id: 'workspaces', icon: '🏢', label: 'Workspaces' },
    { id: 'chat', icon: '💬', label: 'Chat' },
    { id: 'plugins', icon: '🧩', label: 'Plugins' },
    { id: 'audit', icon: '📋', label: 'Audit Trail' },
    { id: 'settings', icon: '⚙️', label: 'Settings' }
  ];

  let currentPage = 'dashboard';
  let healthData = null;
  let startTime = Date.now();

  // === THEME ===
  function getTheme() {
    return localStorage.getItem('aeryn-theme') || 'dark';
  }

  function setTheme(theme) {
    localStorage.setItem('aeryn-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) metaTheme.content = theme === 'dark' ? '#1a1a2e' : '#f5f7fa';
  }

  function toggleTheme() {
    const newTheme = getTheme() === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    announceToScreenReader('Theme changed to ' + newTheme);
  }

  // === TOAST ===
  function showToast(msg, type, duration) {
    type = type || 'info';
    duration = duration || 3000;
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = '<span class="toast-message">' + msg + '</span>' +
      '<button class="toast-close" aria-label="Close notification">&times;</button>';
    container.appendChild(toast);
    toast.querySelector('.toast-close').onclick = function() {
      toast.remove();
    };
    setTimeout(function() {
      if (toast.parentNode) toast.remove();
    }, duration);
    announceToScreenReader(type + ' notification: ' + msg);
  }

  // === SCREAD READER ANNOUNCEMENT ===
  function announceToScreenReader(msg) {
    let announcer = document.getElementById('sr-announcer');
    if (!announcer) {
      announcer = document.createElement('div');
      announcer.id = 'sr-announcer';
      announcer.setAttribute('role', 'status');
      announcer.setAttribute('aria-live', 'polite');
      announcer.setAttribute('aria-atomic', 'true');
      announcer.style.position = 'absolute';
      announcer.style.left = '-9999px';
      announcer.style.width = '1px';
      announcer.style.height = '1px';
      announcer.style.overflow = 'hidden';
      document.body.appendChild(announcer);
    }
    announcer.textContent = '';
    setTimeout(function() { announcer.textContent = msg; }, 50);
  }

  // === NAVIGATION ===
  function renderNav() {
    const list = document.getElementById('nav-list');
    if (!list) return;
    list.innerHTML = navItems.map(function(item) {
      const active = currentPage === item.id ? ' active' : '';
      const ariaCurrent = currentPage === item.id ? 'page' : undefined;
      return '<li><button class="nav-item' + active + '" ' +
        'onclick="window.AerynApp.navigate(\'' + item.id + '\')" ' +
        'aria-current="' + (ariaCurrent || '') + '">' +
        '<span class="nav-icon" aria-hidden="true">' + item.icon + '</span> ' +
        '<span class="nav-label">' + item.label + '</span></button></li>';
    }).join('');
  }

  function navigate(page) {
    currentPage = page;
    window.history.pushState({}, '', '/' + page);
    renderNav();
    renderBreadcrumb();
    renderPage();
    showToast('Navigated to ' + page, 'info', 1000);
  }

  // === BREADCRUMB ===
  function renderBreadcrumb() {
    const current = navItems.find(function(n) { return n.id === currentPage; });
    const label = current ? current.label : currentPage;
    const bc = document.getElementById('breadcrumb-current');
    if (bc) bc.textContent = label;
    const title = document.getElementById('page-title');
    if (title) title.textContent = label;
  }

  // === PAGE CONTENT ===
  function renderPage() {
    const container = document.getElementById('page-content');
    if (!container) return;

    switch(currentPage) {
      case 'dashboard':
        if (healthData) {
          const s = healthData.status || 'offline';
          const sc = s === 'healthy' ? 'online' : 'offline';
          const m = (healthData.memory_mb || 0).toFixed(1);
          const v = healthData.version || '--';
          container.innerHTML =
            '<div class="stats-grid">' +
              '<div class="stat"><div class="label">Backend Status</div><div class="value ' + sc + '">' + s + '</div></div>' +
              '<div class="stat"><div class="label">Memory</div><div class="value accent">' + m + ' MB</div></div>' +
              '<div class="stat"><div class="label">Version</div><div class="value purple">' + v + '</div></div>' +
              '<div class="stat"><div class="label">Uptime</div><div class="value orange" id="uptime">00:00:00</div></div>' +
            '</div>' +
            '<div class="card"><h2>Quick Actions</h2>' +
            '<div class="actions-grid">' +
              '<button class="action-btn" onclick="window.location.reload()"><span class="action-icon">🔄</span><span>Refresh</span></button>' +
              '<button class="action-btn" onclick="document.getElementById(\'search-input\').focus()"><span class="action-icon">🔍</span><span>Search</span></button>' +
            '</div></div>';
          startUptimeCounter();
        } else {
          container.innerHTML =
            '<div class="stats-grid">' +
              '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>' +
              '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>' +
              '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>' +
              '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>' +
            '</div>';
        }
        break;

      case 'projects':
        container.innerHTML = '<div class="card"><h2>Projects</h2><p style="color:var(--muted)">Create and manage your AI projects.</p>' +
          '<div class="actions-grid"><button class="action-btn"><span class="action-icon">➕</span><span>New Project</span></button>' +
          '<button class="action-btn"><span class="action-icon">📂</span><span>Browse</span></button></div></div>';
        break;

      case 'workspaces':
        container.innerHTML = '<div class="card"><h2>Workspaces</h2><p style="color:var(--muted)">Multi-tenant workspace management.</p>' +
          '<div class="actions-grid"><button class="action-btn"><span class="action-icon">🏢</span><span>Create Workspace</span></button>' +
          '<button class="action-btn"><span class="action-icon">👥</span><span>Invite Members</span></button></div></div>';
        break;

      case 'chat':
        container.innerHTML = '<div class="card"><h2>Chat with Aeryn</h2><p style="color:var(--muted)">Conversational AI interface.</p>' +
          '<div class="actions-grid"><button class="action-btn"><span class="action-icon">💬</span><span>New Chat</span></button>' +
          '<button class="action-btn"><span class="action-icon">📜</span><span>History</span></button></div></div>';
        break;

      case 'plugins':
        container.innerHTML = '<div class="card"><h2>Plugins</h2><p style="color:var(--muted)">Extend Aeryn with plugins.</p>' +
          '<div class="actions-grid"><button class="action-btn"><span class="action-icon">🧩</span><span>Browse Plugins</span></button>' +
          '<button class="action-btn"><span class="action-icon">⚡</span><span>Create Plugin</span></button></div></div>';
        break;

      case 'audit':
        container.innerHTML = '<div class="card"><h2>Audit Trail</h2><p style="color:var(--muted)">Track all actions and changes.</p></div>';
        break;

      case 'settings':
        const t = getTheme();
        container.innerHTML =
          '<div class="card"><h2>Appearance</h2>' +
          '<div style="display:flex;align-items:center;gap:16px;margin-top:12px">' +
          '<span>Theme: <strong>' + t + '</strong></span>' +
          '<button class="action-btn" style="padding:8px 16px" onclick="window.AerynApp.toggleTheme()">' +
          '<span class="action-icon">🌓</span><span>Toggle</span></button></div></div>' +
          '<div class="card"><h2>Keyboard Shortcuts</h2>' +
          '<div style="display:grid;gap:8px;margin-top:12px">' +
          '<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)"><span>Search</span><span class="kbd">Ctrl</span> + <span class="kbd">K</span></div>' +
          '<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)"><span>Toggle Theme</span><span class="kbd">Ctrl</span> + <span class="kbd">T</span></div>' +
          '<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)"><span>Help</span><span class="kbd">Ctrl</span> + <span class="kbd">/</span></div>' +
          '<div style="display:flex;justify-content:space-between;padding:8px 0"><span>Skip to content</span><span class="kbd">Tab</span></div></div></div>';
        break;

      default:
        container.innerHTML = '<div class="card"><h2>Dashboard</h2><p>Welcome to Aeryn.</p></div>';
    }
  }

  // === HEALTH CHECK ===
  function fetchHealth() {
    fetch('/api/py/health', { method: 'GET' })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        healthData = data;
        const banner = document.getElementById('offline-banner');
        if (banner) banner.style.display = 'none';
        if (currentPage === 'dashboard') renderPage();
      })
      .catch(function() {
        healthData = null;
        const banner = document.getElementById('offline-banner');
        if (banner) banner.style.display = 'flex';
        if (currentPage === 'dashboard') renderPage();
      });
  }

  // === UPTIME ===
  let uptimeStarted = false;
  function startUptimeCounter() {
    if (uptimeStarted) return;
    uptimeStarted = true;
    setInterval(function() {
      const el = document.getElementById('uptime');
      if (el) {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const h = Math.floor(elapsed / 3600).toString().padStart(2, '0');
        const m = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0');
        const s = (elapsed % 60).toString().padStart(2, '0');
        el.textContent = h + ':' + m + ':' + s;
      }
    }, 1000);
  }

  // === KEYBOARD SHORTCUTS ===
  function setupKeyboard() {
    document.addEventListener('keydown', function(e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const input = document.getElementById('search-input');
        if (input) input.focus();
        showToast('Search focused', 'info', 1500);
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 't') {
        e.preventDefault();
        toggleTheme();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        showToast('Shortcuts: Ctrl+K search, Ctrl+T theme, Ctrl+/ help', 'info', 3000);
      }
      if (e.key === 'Escape') {
        const input = document.getElementById('search-input');
        if (input && document.activeElement === input) {
          input.blur();
        }
      }
    });
  }

  // === SEARCH ===
  function setupSearch() {
    const input = document.getElementById('search-input');
    if (!input) return;
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        const q = input.value.toLowerCase();
        const found = navItems.find(function(n) { return n.label.toLowerCase().includes(q); });
        if (found) {
          navigate(found.id);
          input.value = '';
        } else {
          showToast('No results for: ' + q, 'warning');
        }
      }
    });
  }

  // === HISTORY ===
  function setupHistory() {
    window.addEventListener('popstate', function() {
      const path = window.location.pathname.replace(/^\//, '') || 'dashboard';
      if (path !== currentPage) {
        currentPage = path;
        renderNav();
        renderBreadcrumb();
        renderPage();
      }
    });
  }

  // === INIT ===
  function init() {
    // Check reduced motion
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.documentElement.setAttribute('data-reduced-motion', 'true');
    }

    setTheme(getTheme());
    renderNav();
    renderBreadcrumb();
    fetchHealth();
    setupKeyboard();
    setupSearch();
    setupHistory();
    setInterval(fetchHealth, 5000);

    // Expose API
    window.AerynApp = {
      navigate: navigate,
      toggleTheme: toggleTheme,
      showToast: showToast,
      fetchHealth: fetchHealth
    };
  }

  // Run when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
