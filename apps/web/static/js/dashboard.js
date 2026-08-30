/**
 * Aeryn Dashboard — Single Page Application
 * All sections (Projects, Workspaces, Plugins, Audit, Settings) in one scrollable page
 */
(function() {
  'use strict';

  // ============================================================================
  // STATE
  // ============================================================================

  var healthData = null;
  var startTime = Date.now();
  var notifications = [];
  var commandPaletteOpen = false;
  var confirmDialogCallback = null;
  var uptimeInterval = null;

  // ============================================================================
  // ERROR BOUNDARY
  // ============================================================================

  function showErrorBoundary(errorMsg, stackTrace) {
    var container = document.getElementById('dashboard-content');
    if (!container) return;
    container.innerHTML = 
      '<div class="error-boundary" role="alert">' +
        '<div class="error-boundary-icon">⚠️</div>' +
        '<h2>Something went wrong</h2>' +
        '<p class="error-message">' + (errorMsg || 'An unexpected error occurred') + '</p>' +
        '<details class="error-details"><summary>Technical details</summary>' +
          '<pre>' + (stackTrace || 'No stack trace available') + '</pre></details>' +
        '<div class="error-actions">' +
          '<button class="action-btn" onclick="window.location.reload()">🔄 Reload</button>' +
          '<button class="action-btn" onclick="window.AerynApp.renderAll()">🏠 Home</button>' +
        '</div>' +
      '</div>';
    announce('Error: ' + errorMsg);
  }

  function safeExecute(fn, context) {
    try { return fn(); }
    catch (e) {
      console.error('Error in ' + (context || 'unknown') + ':', e);
      showErrorBoundary(e.message, e.stack);
      return null;
    }
  }

  // ============================================================================
  // THEME
  // ============================================================================

  function getTheme() { return localStorage.getItem('aeryn-theme') || 'dark'; }

  function setTheme(theme) {
    localStorage.setItem('aeryn-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    announce('Theme: ' + theme);
  }

  function toggleTheme() { setTheme(getTheme() === 'dark' ? 'light' : 'dark'); }

  // ============================================================================
  // TOAST
  // ============================================================================

  function showToast(msg, type, duration) {
    type = type || 'info';
    duration = duration || 3000;
    var container = document.getElementById('toast-container');
    if (!container) return;
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = '<span class="toast-message">' + msg + '</span>' +
      '<button class="toast-close" aria-label="Close">&times;</button>';
    container.appendChild(toast);
    toast.querySelector('.toast-close').onclick = function() { toast.remove(); };
    setTimeout(function() { if (toast.parentNode) toast.remove(); }, duration);
    announce(type + ': ' + msg);
  }

  // ============================================================================
  // NOTIFICATIONS
  // ============================================================================

  function addNotification(title, message, type) {
    type = type || 'info';
    notifications.unshift({ id: Date.now(), title: title, message: message, type: type, read: false, timestamp: new Date().toISOString() });
    updateNotifBadge();
    showToast(title + ': ' + message, type, 4000);
  }

  function markNotifRead(id) {
    notifications.forEach(function(n) { if (n.id === id) n.read = true; });
    updateNotifBadge();
    renderNotifications();
  }

  function markAllRead() {
    notifications.forEach(function(n) { n.read = true; });
    updateNotifBadge();
    renderNotifications();
  }

  function updateNotifBadge() {
    var badge = document.getElementById('notification-badge');
    if (!badge) return;
    var unread = notifications.filter(function(n) { return !n.read; }).length;
    badge.textContent = unread;
    badge.style.display = unread > 0 ? 'block' : 'none';
  }

  // ============================================================================
  // SCREEN READER
  // ============================================================================

  function announce(msg) {
    var el = document.getElementById('sr-announcer');
    if (!el) {
      el = document.createElement('div');
      el.id = 'sr-announcer';
      el.setAttribute('role', 'status');
      el.setAttribute('aria-live', 'polite');
      el.style.cssText = 'position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden';
      document.body.appendChild(el);
    }
    el.textContent = '';
    setTimeout(function() { el.textContent = msg; }, 50);
  }

  // ============================================================================
  // HELPERS
  // ============================================================================

  function formatTime(isoString) {
    var d = new Date(isoString);
    var now = new Date();
    var diff = Math.floor((now - d) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    return Math.floor(diff / 86400) + 'd ago';
  }

  // ============================================================================
  // CONFIRM DIALOG
  // ============================================================================

  function showConfirm(title, msg, onConfirm, onCancel) {
    var overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'confirm-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.innerHTML =
      '<div class="modal confirm-dialog">' +
        '<h3>' + title + '</h3><p>' + msg + '</p>' +
        '<div class="modal-actions">' +
          '<button class="action-btn" id="confirm-cancel">Cancel</button>' +
          '<button class="action-btn danger" id="confirm-ok">Confirm</button>' +
        '</div></div>';
    document.body.appendChild(overlay);
    document.getElementById('confirm-cancel').onclick = function() { overlay.remove(); if (onCancel) onCancel(); };
    document.getElementById('confirm-ok').onclick = function() { overlay.remove(); if (onConfirm) onConfirm(); };
    document.getElementById('confirm-cancel').focus();
    overlay.addEventListener('click', function(e) { if (e.target === overlay) { overlay.remove(); if (onCancel) onCancel(); } });
  }

  // ============================================================================
  // COMMAND PALETTE
  // ============================================================================

  function toggleCommandPalette() {
    commandPaletteOpen = !commandPaletteOpen;
    var palette = document.getElementById('command-palette');
    if (commandPaletteOpen) {
      if (!palette) {
        palette = document.createElement('div');
        palette.id = 'command-palette';
        palette.className = 'modal-overlay';
        document.body.appendChild(palette);
      }
      var commands = [
        { id: 'home', label: 'Go to Dashboard', icon: '🏠', action: function() { window.scrollTo(0,0); } },
        { id: 'theme', label: 'Toggle Theme', icon: '🌓', action: toggleTheme },
        { id: 'notif', label: 'View Notifications', icon: '🔔', action: function() { document.getElementById('section-notifications').scrollIntoView(); } },
        { id: 'projects', label: 'Go to Projects', icon: '📁', action: function() { document.getElementById('section-projects').scrollIntoView(); } },
        { id: 'workspaces', label: 'Go to Workspaces', icon: '🏢', action: function() { document.getElementById('section-workspaces').scrollIntoView(); } },
        { id: 'plugins', label: 'Go to Plugins', icon: '🧩', action: function() { document.getElementById('section-plugins').scrollIntoView(); } },
        { id: 'audit', label: 'Go to Audit', icon: '📋', action: function() { document.getElementById('section-audit').scrollIntoView(); } },
        { id: 'settings', label: 'Go to Settings', icon: '⚙️', action: function() { document.getElementById('section-settings').scrollIntoView(); } }
      ];
      palette.innerHTML =
        '<div class="command-palette-panel">' +
          '<input type="text" class="command-input" placeholder="Type a command..." aria-label="Command search">' +
          '<div class="command-results">' +
            commands.map(function(c) {
              return '<button class="command-item" data-id="' + c.id + '">' +
                '<span class="command-icon">' + c.icon + '</span>' +
                '<span class="command-label">' + c.label + '</span></button>';
            }).join('') +
          '</div></div>';
      palette.style.display = 'flex';
      var input = palette.querySelector('.command-input');
      input.focus();
      input.addEventListener('input', function() {
        var q = input.value.toLowerCase();
        palette.querySelectorAll('.command-item').forEach(function(item) {
          var label = item.querySelector('.command-label').textContent.toLowerCase();
          item.style.display = label.includes(q) ? 'flex' : 'none';
        });
      });
      input.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') toggleCommandPalette();
        if (e.key === 'Enter') {
          var visible = Array.from(palette.querySelectorAll('.command-item')).filter(function(r) { return r.style.display !== 'none'; });
          if (visible.length > 0) visible[0].click();
        }
      });
      palette.querySelectorAll('.command-item').forEach(function(item) {
        item.addEventListener('click', function() {
          var cmd = commands.find(function(c) { return c.id === item.dataset.id; });
          if (cmd) cmd.action();
          toggleCommandPalette();
        });
      });
    } else if (palette) {
      palette.style.display = 'none';
    }
  }

  // ============================================================================
  // UPTIME COUNTER
  // ============================================================================

  function startUptimeCounter() {
    if (uptimeInterval) clearInterval(uptimeInterval);
    uptimeInterval = setInterval(function() {
      var el = document.getElementById('uptime');
      if (!el) return;
      var diff = Math.floor((Date.now() - startTime) / 1000);
      var h = String(Math.floor(diff / 3600)).padStart(2, '0');
      var m = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
      var s = String(diff % 60).padStart(2, '0');
      el.textContent = h + ':' + m + ':' + s;
    }, 1000);
  }

  // ============================================================================
  // SECTION RENDERERS
  // ============================================================================

  function renderHealthStats(container) {
    if (!healthData) {
      container.innerHTML = '<div class="stats-grid">' +
        '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>'.repeat(4) +
        '</div>';
      return;
    }
    var s = healthData.status || 'offline';
    var sc = s === 'healthy' ? 'online' : 'offline';
    var m = (healthData.memory_mb || 0).toFixed(1);
    var v = healthData.version || '--';
    container.innerHTML = '<div class="stats-grid">' +
      '<div class="stat"><div class="label">Backend</div><div class="value ' + sc + '">' + s + '</div></div>' +
      '<div class="stat"><div class="label">Memory</div><div class="value accent">' + m + ' MB</div></div>' +
      '<div class="stat"><div class="label">Version</div><div class="value purple">' + v + '</div></div>' +
      '<div class="stat"><div class="label">Uptime</div><div class="value orange" id="uptime">00:00:00</div></div>' +
      '</div>';
    startUptimeCounter();
  }

  function renderQuickActions(container) {
    container.innerHTML = '<div class="card"><h2>Quick Actions</h2>' +
      '<div class="actions-grid">' +
        '<button class="action-btn" onclick="window.location.reload()"><span class="action-icon">🔄</span><span>Refresh</span></button>' +
        '<button class="action-btn" onclick="document.getElementById(\'search-input\').focus()"><span class="action-icon">🔍</span><span>Search</span></button>' +
        '<button class="action-btn" onclick="window.AerynApp.toggleCommandPalette()"><span class="action-icon">⌘</span><span>Command</span></button>' +
        '<button class="action-btn" onclick="window.scrollTo({top:document.body.scrollHeight,behavior:\'smooth\'})"><span class="action-icon">🔔</span><span>Notifications</span></button>' +
      '</div></div>';
  }

  function renderProjects() {
    var container = document.getElementById('section-projects');
    if (!container) return;
    var projects = JSON.parse(localStorage.getItem('aeryn-projects') || '[]');
    if (projects.length === 0) {
      container.innerHTML = '<div class="empty-state">' +
        '<div class="empty-state-icon">📁</div><h3>No Projects Yet</h3>' +
        '<p>Create your first AI project to get started.</p>' +
        '<button class="action-btn" onclick="window.AerynApp.createProject()"><span class="action-icon">➕</span><span>Create Project</span></button>' +
        '</div>';
      return;
    }
    var html = '<div class="page-header"><h2>Projects</h2>' +
      '<button class="action-btn" onclick="window.AerynApp.createProject()"><span class="action-icon">➕</span><span>New</span></button></div>' +
      '<div class="card-grid">';
    projects.forEach(function(p) {
      html += '<div class="project-card">' +
        '<div class="project-icon">📁</div><h3>' + p.name + '</h3>' +
        '<p>' + (p.description || 'No description') + '</p>' +
        '<div class="project-meta">Created: ' + formatTime(p.created) + '</div>' +
        '<div class="project-actions">' +
          '<button class="action-btn" onclick="window.AerynApp.openProject(' + p.id + ')">Open</button>' +
          '<button class="action-btn danger" onclick="window.AerynApp.deleteProject(' + p.id + ')">Delete</button>' +
        '</div></div>';
    });
    container.innerHTML = html + '</div>';
  }

  function renderWorkspaces() {
    var container = document.getElementById('section-workspaces');
    if (!container) return;
    var workspaces = JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]');
    if (workspaces.length === 0) {
      container.innerHTML = '<div class="empty-state">' +
        '<div class="empty-state-icon">🏢</div><h3>No Workspaces</h3>' +
        '<p>Create a workspace to organize your AI agents.</p>' +
        '<button class="action-btn" onclick="window.AerynApp.createWorkspace()"><span class="action-icon">➕</span><span>Create Workspace</span></button>' +
        '</div>';
      return;
    }
    var html = '<div class="page-header"><h2>Workspaces</h2>' +
      '<button class="action-btn" onclick="window.AerynApp.createWorkspace()"><span class="action-icon">➕</span><span>New</span></button></div>' +
      '<div class="card-grid">';
    workspaces.forEach(function(w) {
      html += '<div class="project-card">' +
        '<div class="project-icon">🏢</div><h3>' + w.name + '</h3>' +
        '<p>' + (w.description || 'No description') + '</p>' +
        '<div class="project-meta">Members: ' + (w.members || 1) + '</div>' +
        '<div class="project-actions">' +
          '<button class="action-btn" onclick="window.AerynApp.openWorkspace(' + w.id + ')">Open</button>' +
          '<button class="action-btn danger" onclick="window.AerynApp.deleteWorkspace(' + w.id + ')">Delete</button>' +
        '</div></div>';
    });
    container.innerHTML = html + '</div>';
  }

  function renderPlugins() {
    var container = document.getElementById('section-plugins');
    if (!container) return;
    var plugins = [
      { name: 'Code Review', icon: '🔍', desc: 'Review code for security and quality', enabled: true },
      { name: 'Research', icon: '📚', desc: 'Deep research and investigation', enabled: true },
      { name: 'Database', icon: '🗄️', desc: 'Manage SQLite/PostgreSQL databases', enabled: false },
      { name: 'Deploy', icon: '🚀', desc: 'Deploy applications to production', enabled: false },
      { name: 'Analytics', icon: '📊', desc: 'Track metrics and generate reports', enabled: true },
      { name: 'Security', icon: '🛡️', desc: 'Scan for vulnerabilities', enabled: false }
    ];
    var html = '<div class="page-header"><h2>Plugins</h2></div><div class="card-grid">';
    plugins.forEach(function(p) {
      html += '<div class="project-card">' +
        '<div class="project-icon">' + p.icon + '</div>' +
        '<h3>' + p.name + '</h3>' +
        '<p>' + p.desc + '</p>' +
        '<div class="project-meta">Status: ' + (p.enabled ? '✅ Active' : '⏸️ Inactive') + '</div>' +
        '<div class="project-actions">' +
          '<button class="action-btn ' + (p.enabled ? 'danger' : '') + '" onclick="window.AerynApp.togglePlugin(\'' + p.name + '\')">' +
          (p.enabled ? 'Disable' : 'Enable') + '</button>' +
        '</div></div>';
    });
    container.innerHTML = html + '</div>';
  }

  function renderAudit() {
    var container = document.getElementById('section-audit');
    if (!container) return;
    var logs = JSON.parse(localStorage.getItem('aeryn-audit') || '[]');
    if (logs.length === 0) {
      // Seed with default entries
      logs = [
        { action: 'System initialized', timestamp: new Date().toISOString(), user: 'system' },
        { action: 'Dashboard loaded', timestamp: new Date(Date.now() - 60000).toISOString(), user: 'system' },
        { action: 'Health check passed', timestamp: new Date(Date.now() - 30000).toISOString(), user: 'system' }
      ];
      localStorage.setItem('aeryn-audit', JSON.stringify(logs));
    }
    var html = '<div class="page-header"><h2>Audit Trail</h2>' +
      '<button class="action-btn" onclick="window.AerynApp.clearAudit()">Clear All</button></div>' +
      '<div class="card"><table><thead><tr><th>Time</th><th>Action</th><th>User</th></tr></thead><tbody>';
    logs.forEach(function(l) {
      html += '<tr><td>' + formatTime(l.timestamp) + '</td><td>' + l.action + '</td><td>' + l.user + '</td></tr>';
    });
    container.innerHTML = html + '</tbody></table></div>';
  }

  function renderNotifications() {
    var container = document.getElementById('section-notifications');
    if (!container) return;
    var html = '<div class="page-header"><h2>Notifications</h2>';
    if (notifications.length > 0) {
      html += '<button class="action-btn" style="padding:6px 12px" onclick="window.AerynApp.markAllRead()">Mark all read</button>';
    }
    html += '</div>';
    if (notifications.length === 0) {
      html += '<div class="empty-state"><div class="empty-state-icon">🔔</div>' +
        '<p>No notifications yet</p>' +
        '<p style="font-size:12px;color:var(--muted)">Notifications will appear here when events occur</p></div>';
    } else {
      html += '<div class="notification-list">';
      notifications.forEach(function(n) {
        var cls = n.read ? 'notification-item read' : 'notification-item';
        html += '<div class="' + cls + '" onclick="window.AerynApp.markNotifRead(' + n.id + ')">' +
          '<div class="notification-icon toast-' + n.type + '">' + getNotifIcon(n.type) + '</div>' +
          '<div class="notification-content">' +
            '<div class="notification-title">' + n.title + '</div>' +
            '<div class="notification-message">' + n.message + '</div>' +
            '<div class="notification-time">' + formatTime(n.timestamp) + '</div>' +
          '</div></div>';
      });
      html += '</div>';
    }
    container.innerHTML = html;
  }

  function renderSettings() {
    var container = document.getElementById('section-settings');
    if (!container) return;
    var theme = getTheme();
    container.innerHTML = '<div class="page-header"><h2>Settings</h2></div>' +
      '<div class="card">' +
        '<h3>Appearance</h3>' +
        '<div class="settings-row"><span>Theme</span>' +
          '<button class="action-btn" onclick="window.AerynApp.toggleTheme()">' +
            (theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode') + '</button></div>' +
      '</div>' +
      '<div class="card">' +
        '<h3>Keyboard Shortcuts</h3>' +
        '<div class="settings-row"><span>Search</span><kbd>Ctrl + K</kbd></div>' +
        '<div class="settings-row"><span>Theme</span><kbd>Ctrl + T</kbd></div>' +
        '<div class="settings-row"><span>Command Palette</span><kbd>Ctrl + Shift + P</kbd></div>' +
        '<div class="settings-row"><span>Help</span><kbd>Ctrl + /</kbd></div>' +
      '</div>' +
      '<div class="card">' +
        '<h3>Data</h3>' +
        '<div class="actions-grid">' +
          '<button class="action-btn" onclick="window.AerynApp.exportData()"><span class="action-icon">📤</span><span>Export</span></button>' +
          '<button class="action-btn danger" onclick="window.AerynApp.clearData()"><span class="action-icon">🗑️</span><span>Clear All</span></button>' +
        '</div>' +
      '</div>';
  }

  function getNotifIcon(type) {
    var icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    return icons[type] || 'ℹ️';
  }

  // ============================================================================
  // CRUD OPERATIONS
  // ============================================================================

  function createProject() {
    var name = prompt('Project name:');
    if (!name) return;
    var desc = prompt('Description (optional):') || '';
    var projects = JSON.parse(localStorage.getItem('aeryn-projects') || '[]');
    projects.push({ id: Date.now(), name: name, description: desc, created: new Date().toISOString() });
    localStorage.setItem('aeryn-projects', JSON.stringify(projects));
    renderProjects();
    addNotification('Project Created', name, 'success');
  }

  function deleteProject(id) {
    showConfirm('Delete Project', 'Are you sure?', function() {
      var projects = JSON.parse(localStorage.getItem('aeryn-projects') || '[]');
      projects = projects.filter(function(p) { return p.id !== id; });
      localStorage.setItem('aeryn-projects', JSON.stringify(projects));
      renderProjects();
      addNotification('Project Deleted', '', 'warning');
    });
  }

  function openProject(id) {
    addNotification('Project Opened', 'Opening project...', 'info');
  }

  function createWorkspace() {
    var name = prompt('Workspace name:');
    if (!name) return;
    var desc = prompt('Description (optional):') || '';
    var workspaces = JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]');
    workspaces.push({ id: Date.now(), name: name, description: desc, members: 1, created: new Date().toISOString() });
    localStorage.setItem('aeryn-workspaces', JSON.stringify(workspaces));
    renderWorkspaces();
    addNotification('Workspace Created', name, 'success');
  }

  function deleteWorkspace(id) {
    showConfirm('Delete Workspace', 'Are you sure?', function() {
      var workspaces = JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]');
      workspaces = workspaces.filter(function(w) { return w.id !== id; });
      localStorage.setItem('aeryn-workspaces', JSON.stringify(workspaces));
      renderWorkspaces();
      addNotification('Workspace Deleted', '', 'warning');
    });
  }

  function openWorkspace(id) {
    addNotification('Workspace Opened', 'Opening workspace...', 'info');
  }

  function togglePlugin(name) {
    addNotification('Plugin Toggled', name + ' status changed', 'info');
  }

  function clearAudit() {
    showConfirm('Clear Audit', 'Delete all audit logs?', function() {
      localStorage.setItem('aeryn-audit', '[]');
      renderAudit();
      addNotification('Audit Cleared', '', 'warning');
    });
  }

  function exportData() {
    var data = {
      projects: JSON.parse(localStorage.getItem('aeryn-projects') || '[]'),
      workspaces: JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]'),
      notifications: notifications,
      audit: JSON.parse(localStorage.getItem('aeryn-audit') || '[]')
    };
    var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'aeryn-dashboard-data.json';
    a.click();
    URL.revokeObjectURL(url);
    addNotification('Data Exported', 'Downloaded as JSON', 'success');
  }

  function clearData() {
    showConfirm('Clear All Data', 'Delete everything? This cannot be undone.', function() {
      localStorage.removeItem('aeryn-projects');
      localStorage.removeItem('aeryn-workspaces');
      localStorage.removeItem('aeryn-audit');
      notifications = [];
      updateNotifBadge();
      renderAll();
      addNotification('Data Cleared', 'All dashboard data removed', 'warning');
    });
  }

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  function renderAll() {
    safeExecute(function() {
      renderHealthStats(document.getElementById('health-stats'));
      renderQuickActions(document.getElementById('quick-actions'));
      renderProjects();
      renderWorkspaces();
      renderPlugins();
      renderAudit();
      renderNotifications();
      renderSettings();
    }, 'renderAll');
  }

  // ============================================================================
  // HEALTH POLLING
  // ============================================================================

  function fetchHealth() {
    fetch('/api/adaptive/health')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.overall_status) {
          healthData = { status: data.overall_status, memory_mb: data.metrics ? data.metrics.memory.used_mb / 1024 : 0, version: 'V59' };
        } else {
          healthData = data;
        }
        renderHealthStats(document.getElementById('health-stats'));
      })
      .catch(function() {
        healthData = { status: 'offline', memory_mb: 0, version: 'V59' };
        renderHealthStats(document.getElementById('health-stats'));
      });
  }

  // ============================================================================
  // KEYBOARD SHORTCUTS
  // ============================================================================

  function initKeyboard() {
    document.addEventListener('keydown', function(e) {
      if (e.ctrlKey && e.key === 'k') { e.preventDefault(); document.getElementById('search-input').focus(); }
      if (e.ctrlKey && e.key === 't') { e.preventDefault(); toggleTheme(); }
      if (e.ctrlKey && e.shiftKey && e.key === 'P') { e.preventDefault(); toggleCommandPalette(); }
      if (e.ctrlKey && e.key === '/') { e.preventDefault(); showToast('Shortcuts: Ctrl+K=Search, Ctrl+T=Theme, Ctrl+Shift+P=Commands', 'info'); }
    });
  }

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  function init() {
    setTheme(getTheme());
    renderAll();
    fetchHealth();
    setInterval(fetchHealth, 5000);
    initKeyboard();
    updateNotifBadge();
  }

  // ============================================================================
  // PUBLIC API
  // ============================================================================

  window.AerynApp = {
    init: init,
    renderAll: renderAll,
    createProject: createProject,
    deleteProject: deleteProject,
    openProject: openProject,
    createWorkspace: createWorkspace,
    deleteWorkspace: deleteWorkspace,
    openWorkspace: openWorkspace,
    togglePlugin: togglePlugin,
    clearAudit: clearAudit,
    markNotifRead: markNotifRead,
    markAllRead: markAllRead,
    toggleTheme: toggleTheme,
    toggleCommandPalette: toggleCommandPalette,
    exportData: exportData,
    clearData: clearData
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
