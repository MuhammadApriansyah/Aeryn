/**
 * Aeryn Dashboard — Full SPA with Accessibility + Sprint 0 Features
 * Features: Error Boundary, Empty States, Confirmation Dialog, Loading States,
 * Real Pages (Projects/Chat/Workspaces/Plugins/Audit), Advanced Search,
 * Command Palette, Notification Center
 */
(function() {
  'use strict';

  // ============================================================================
  // CONFIGURATION
  // ============================================================================

  var navItems = [
    { id: 'dashboard', icon: '📊', label: 'Dashboard', category: 'main' },
    { id: 'projects', icon: '📁', label: 'Projects', category: 'work' },
    { id: 'workspaces', icon: '🏢', label: 'Workspaces', category: 'work' },
    { id: 'chat', icon: '💬', label: 'Chat', category: 'work' },
    { id: 'plugins', icon: '🧩', label: 'Plugins', category: 'extend' },
    { id: 'audit', icon: '📋', label: 'Audit Trail', category: 'admin' },
    { id: 'settings', icon: '⚙️', label: 'Settings', category: 'admin' }
  ];

  var currentPage = 'dashboard';
  var healthData = null;
  var startTime = Date.now();
  var notifications = [];
  var commandPaletteOpen = false;
  var confirmDialogCallback = null;

  // ============================================================================
  // ERROR BOUNDARY
  // ============================================================================

  function showErrorBoundary(errorMsg, stackTrace) {
    var container = document.getElementById('page-content');
    if (!container) return;
    
    var errorHtml = 
      '<div class="error-boundary" role="alert">' +
        '<div class="error-boundary-icon">⚠️</div>' +
        '<h2>Something went wrong</h2>' +
        '<p class="error-message">' + (errorMessage || 'An unexpected error occurred') + '</p>' +
        '<details class="error-details">' +
          '<summary>Technical details</summary>' +
          '<pre>' + (stackTrace || 'No stack trace available') + '</pre>' +
        '</details>' +
        '<div class="error-actions">' +
          '<button class="action-btn" onclick="window.location.reload()">' +
            '<span class="action-icon">🔄</span><span>Reload Page</span></button>' +
          '<button class="action-btn" onclick="window.AerynApp.goHome()">' +
            '<span class="action-icon">🏠</span><span>Go Home</span></button>' +
        '</div>' +
      '</div>';
    
    container.innerHTML = errorHtml;
    announceToScreenReader('Error: ' + errorMessage);
  }

  function safeExecute(fn, context) {
    try {
      return fn();
    } catch (e) {
      console.error('Error in ' + (context || 'unknown') + ':', e);
      showErrorBoundary(e.message, e.stack);
      return null;
    }
  }

  // ============================================================================
  // THEME
  // ============================================================================

  function getTheme() {
    return localStorage.getItem('aeryn-theme') || 'dark';
  }

  function setTheme(theme) {
    localStorage.setItem('aeryn-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    var metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) metaTheme.content = theme === 'dark' ? '#1a1a2e' : '#f5f7fa';
    announceToScreenReader('Theme changed to ' + theme);
  }

  function toggleTheme() {
    var newTheme = getTheme() === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  }

  // ============================================================================
  // TOAST NOTIFICATIONS
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

  // ============================================================================
  // NOTIFICATION CENTER
  // ============================================================================

  function addNotification(title, message, type) {
    type = type || 'info';
    var notif = {
      id: Date.now(),
      title: title,
      message: message,
      type: type,
      read: false,
      timestamp: new Date().toISOString()
    };
    notifications.unshift(notif);
    updateNotificationBadge();
    showToast(title + ': ' + message, type, 4000);
    return notif;
  }

  function markNotificationRead(id) {
    notifications.forEach(function(n) {
      if (n.id === id) n.read = true;
    });
    updateNotificationBadge();
  }

  function markAllNotificationsRead() {
    notifications.forEach(function(n) { n.read = true; });
    updateNotificationBadge();
  }

  function updateNotificationBadge() {
    var badge = document.getElementById('notification-badge');
    if (!badge) return;
    var unread = notifications.filter(function(n) { return !n.read; }).length;
    badge.textContent = unread;
    badge.style.display = unread > 0 ? 'block' : 'none';
  }

  function renderNotificationCenter() {
    var container = document.getElementById('page-content');
    if (!container) return;
    
    var html = '<div class="notification-center">';
    html += '<div class="notification-header">';
    html += '<h2>Notifications</h2>';
    if (notifications.length > 0) {
      html += '<button class="action-btn" style="padding:6px 12px" onclick="window.AerynApp.markAllRead()">Mark all read</button>';
    }
    html += '</div>';
    
    if (notifications.length === 0) {
      html += '<div class="empty-state">' +
        '<div class="empty-state-icon">🔔</div>' +
        '<p>No notifications yet</p>' +
        '<p style="font-size:12px;color:var(--muted)">Notifications will appear here when events occur</p>' +
      '</div>';
    } else {
      html += '<div class="notification-list">';
      notifications.forEach(function(n) {
        var cls = n.read ? 'notification-item read' : 'notification-item';
        html += '<div class="' + cls + '" onclick="window.AerynApp.markRead(' + n.id + ')">';
        html += '<div class="notification-icon toast-' + n.type + '">' + getNotifIcon(n.type) + '</div>';
        html += '<div class="notification-content">';
        html += '<div class="notification-title">' + n.title + '</div>';
        html += '<div class="notification-message">' + n.message + '</div>';
        html += '<div class="notification-time">' + formatTime(n.timestamp) + '</div>';
        html += '</div></div>';
      });
      html += '</div>';
    }
    
    html += '</div>';
    container.innerHTML = html;
  }

  function getNotifIcon(type) {
    var icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    return icons[type] || 'ℹ️';
  }

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
  // SCREEN READER ANNOUNCEMENT
  // ============================================================================

  function announceToScreenReader(msg) {
    var announcer = document.getElementById('sr-announcer');
    if (!announcer) {
      announcer = document.createElement('div');
      announcer.id = 'sr-announcer';
      announcer.setAttribute('role', 'status');
      announcer.setAttribute('aria-live', 'polite');
      announcer.setAttribute('aria-atomic', 'true');
      announcer.style.cssText = 'position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden';
      document.body.appendChild(announcer);
    }
    announcer.textContent = '';
    setTimeout(function() { announcer.textContent = msg; }, 50);
  }

  // ============================================================================
  // NAVIGATION
  // ============================================================================

  function renderNav() {
    var list = document.getElementById('nav-list');
    if (!list) return;
    
    list.innerHTML = navItems.map(function(item) {
      var active = currentPage === item.id ? ' active' : '';
      var ariaCurrent = currentPage === item.id ? 'page' : undefined;
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
    announceToScreenReader('Navigated to ' + page);
  }

  // ============================================================================
  // BREADCRUMB
  // ============================================================================

  function renderBreadcrumb() {
    var current = navItems.find(function(n) { return n.id === currentPage; });
    var label = current ? current.label : currentPage;
    var bc = document.getElementById('breadcrumb-current');
    if (bc) bc.textContent = label;
    var title = document.getElementById('page-title');
    if (title) title.textContent = label;
  }

  // ============================================================================
  // CONFIRMATION DIALOG
  // ============================================================================

  function showConfirmDialog(title, message, onConfirm, onCancel) {
    var overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'confirm-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', 'confirm-title');
    
    overlay.innerHTML = 
      '<div class="modal confirm-dialog">' +
        '<h3 id="confirm-title">' + title + '</h3>' +
        '<p>' + message + '</p>' +
        '<div class="modal-actions">' +
          '<button class="action-btn" id="confirm-cancel">Cancel</button>' +
          '<button class="action-btn danger" id="confirm-ok">Confirm</button>' +
        '</div>' +
      '</div>';
    
    document.body.appendChild(overlay);
    
    document.getElementById('confirm-cancel').onclick = function() {
      overlay.remove();
      if (onCancel) onCancel();
    };
    
    document.getElementById('confirm-ok').onclick = function() {
      overlay.remove();
      if (onConfirm) onConfirm();
    };
    
    // Focus trap
    document.getElementById('confirm-cancel').focus();
    
    // Close on overlay click
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) {
        overlay.remove();
        if (onCancel) onCancel();
      }
    });
  }

  // ============================================================================
  // LOADING STATE
  // ============================================================================

  function showLoading(container, message) {
    if (!container) return;
    container.innerHTML = 
      '<div class="loading-state">' +
        '<div class="loading-spinner"></div>' +
        '<p>' + (message || 'Loading...') + '</p>' +
      '</div>';
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
        palette.setAttribute('role', 'dialog');
        palette.setAttribute('aria-modal', 'true');
        document.body.appendChild(palette);
      }
      
      renderCommandPalette(palette);
      palette.style.display = 'flex';
      var input = palette.querySelector('.command-input');
      if (input) input.focus();
    } else if (palette) {
      palette.style.display = 'none';
    }
  }

  function renderCommandPalette(container) {
    var commands = [
      { id: 'goto-dashboard', label: 'Go to Dashboard', icon: '📊', action: function() { navigate('dashboard'); } },
      { id: 'goto-projects', label: 'Go to Projects', icon: '📁', action: function() { navigate('projects'); } },
      { id: 'goto-workspaces', label: 'Go to Workspaces', icon: '🏢', action: function() { navigate('workspaces'); } },
      { id: 'goto-chat', label: 'Go to Chat', icon: '💬', action: function() { navigate('chat'); } },
      { id: 'goto-plugins', label: 'Go to Plugins', icon: '🧩', action: function() { navigate('plugins'); } },
      { id: 'goto-audit', label: 'Go to Audit Trail', icon: '📋', action: function() { navigate('audit'); } },
      { id: 'goto-settings', label: 'Go to Settings', icon: '⚙️', action: function() { navigate('settings'); } },
      { id: 'toggle-theme', label: 'Toggle Theme', icon: '🌓', action: toggleTheme },
      { id: 'notifications', label: 'View Notifications', icon: '🔔', action: function() { navigate('notifications'); } }
    ];
    
    container.innerHTML = 
      '<div class="command-palette-panel">' +
        '<input type="text" class="command-input" placeholder="Type a command..." aria-label="Command palette search">' +
        '<div class="command-results">' +
          commands.map(function(cmd) {
            return '<button class="command-item" data-id="' + cmd.id + '">' +
              '<span class="command-icon">' + cmd.icon + '</span>' +
              '<span class="command-label">' + cmd.label + '</span>' +
            '</button>';
          }).join('') +
        '</div>' +
      '</div>';
    
    var input = container.querySelector('.command-input');
    var results = container.querySelectorAll('.command-item');
    
    input.addEventListener('input', function() {
      var q = input.value.toLowerCase();
      results.forEach(function(item) {
        var label = item.querySelector('.command-label').textContent.toLowerCase();
        item.style.display = label.includes(q) ? 'flex' : 'none';
      });
    });
    
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') toggleCommandPalette();
      if (e.key === 'Enter') {
        var visible = Array.from(results).filter(function(r) { return r.style.display !== 'none'; });
        if (visible.length > 0) visible[0].click();
      }
    });
    
    results.forEach(function(item) {
      item.addEventListener('click', function() {
        var cmd = commands.find(function(c) { return c.id === item.dataset.id; });
        if (cmd) cmd.action();
        toggleCommandPalette();
      });
    });
  }

  // ============================================================================
  // PAGE CONTENT RENDERERS
  // ============================================================================

  function renderPage() {
    safeExecute(function() {
      var container = document.getElementById('page-content');
      if (!container) return;
      
      switch(currentPage) {
        case 'dashboard': renderDashboard(container); break;
        case 'projects': renderProjects(container); break;
        case 'workspaces': renderWorkspaces(container); break;
        case 'chat': renderChat(container); break;
        case 'plugins': renderPlugins(container); break;
        case 'audit': renderAudit(container); break;
        case 'settings': renderSettings(container); break;
        case 'notifications': renderNotificationCenter(); break;
        default:
          container.innerHTML = '<div class="card"><h2>Dashboard</h2><p>Welcome to Aeryn.</p></div>';
      }
    }, 'renderPage');
  }

  function renderDashboard(container) {
    if (!healthData) {
      container.innerHTML = 
        '<div class="stats-grid">' +
          '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>' +
          '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>' +
          '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>' +
          '<div class="stat skeleton-stat"><div class="skeleton-label"></div><div class="skeleton-value"></div></div>' +
        '</div>';
      return;
    }
    
    var s = healthData.status || 'offline';
    var sc = s === 'healthy' ? 'online' : 'offline';
    var m = (healthData.memory_mb || 0).toFixed(1);
    var v = healthData.version || '--';
    
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
          '<button class="action-btn" onclick="window.AerynApp.toggleCommandPalette()"><span class="action-icon">⌘</span><span>Command</span></button>' +
          '<button class="action-btn" onclick="window.AerynApp.navigate(\'notifications\')"><span class="action-icon">🔔</span><span>Notifications</span></button>' +
        '</div></div>';
    
    startUptimeCounter();
  }

  function renderProjects(container) {
    var projects = JSON.parse(localStorage.getItem('aeryn-projects') || '[]');
    
    if (projects.length === 0) {
      container.innerHTML = 
        '<div class="empty-state">' +
          '<div class="empty-state-icon">📁</div>' +
          '<h3>No Projects Yet</h3>' +
          '<p>Create your first AI project to get started.</p>' +
          '<button class="action-btn" onclick="window.AerynApp.createProject()">' +
            '<span class="action-icon">➕</span><span>Create Project</span></button>' +
        '</div>';
      return;
    }
    
    var html = '<div class="page-header"><h2>Projects</h2>' +
      '<button class="action-btn" onclick="window.AerynApp.createProject()">' +
        '<span class="action-icon">➕</span><span>New Project</span></button></div>';
    
    html += '<div class="card-grid">';
    projects.forEach(function(p) {
      html += '<div class="project-card">' +
        '<div class="project-icon">📁</div>' +
        '<h3>' + p.name + '</h3>' +
        '<p>' + (p.description || 'No description') + '</p>' +
        '<div class="project-meta">Created: ' + formatTime(p.created) + '</div>' +
        '<div class="project-actions">' +
          '<button class="action-btn" onclick="window.AerynApp.openProject(' + p.id + ')">Open</button>' +
          '<button class="action-btn danger" onclick="window.AerynApp.deleteProject(' + p.id + ')">Delete</button>' +
        '</div>' +
      '</div>';
    });
    html += '</div>';
    container.innerHTML = html;
  }

  function renderWorkspaces(container) {
    var workspaces = JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]');
    
    if (workspaces.length === 0) {
      container.innerHTML = 
        '<div class="empty-state">' +
          '<div class="empty-state-icon">🏢</div>' +
          '<h3>No Workspaces</h3>' +
          '<p>Create a workspace to collaborate with your team.</p>' +
          '<button class="action-btn" onclick="window.AerynApp.createWorkspace()">' +
            '<span class="action-icon">➕</span><span>Create Workspace</span></button>' +
        '</div>';
      return;
    }
    
    var html = '<div class="page-header"><h2>Workspaces</h2>' +
      '<button class="action-btn" onclick="window.AerynApp.createWorkspace()">' +
        '<span class="action-icon">➕</span><span>New Workspace</span></button></div>';
    
    html += '<div class="card-grid">';
    workspaces.forEach(function(w) {
      html += '<div class="project-card">' +
        '<div class="project-icon">🏢</div>' +
        '<h3>' + w.name + '</h3>' +
        '<p>' + (w.description || 'No description') + '</p>' +
        '<div class="project-meta">Members: ' + (w.members || 1) + '</div>' +
        '<div class="project-actions">' +
          '<button class="action-btn" onclick="window.AerynApp.openWorkspace(' + w.id + ')">Open</button>' +
          '<button class="action-btn danger" onclick="window.AerynApp.deleteWorkspace(' + w.id + ')">Delete</button>' +
        '</div>' +
      '</div>';
    });
    html += '</div>';
    container.innerHTML = html;
  }

  function renderChat(container) {
    var sessions = JSON.parse(localStorage.getItem('aeryn-chat-sessions') || '[]');
    
    if (sessions.length === 0) {
      container.innerHTML = 
        '<div class="empty-state">' +
          '<div class="empty-state-icon">💬</div>' +
          '<h3>No Chat Sessions</h3>' +
          '<p>Start a conversation with Aeryn.</p>' +
          '<button class="action-btn" onclick="window.AerynApp.newChat()">' +
            '<span class="action-icon">➕</span><span>New Chat</span></button>' +
        '</div>';
      return;
    }
    
    var html = '<div class="page-header"><h2>Chat</h2>' +
      '<button class="action-btn" onclick="window.AerynApp.newChat()">' +
        '<span class="action-icon">➕</span><span>New Chat</span></button></div>';
    
    html += '<div class="chat-session-list">';
    sessions.forEach(function(s) {
      html += '<div class="chat-session-item" onclick="window.AerynApp.openChat(' + s.id + ')">' +
        '<div class="chat-icon">💬</div>' +
        '<div class="chat-info">' +
          '<div class="chat-title">' + (s.title || 'Untitled') + '</div>' +
          '<div class="chat-preview">' + (s.lastMessage || 'No messages') + '</div>' +
        '</div>' +
        '<div class="chat-time">' + formatTime(s.updated) + '</div>' +
      '</div>';
    });
    html += '</div>';
    container.innerHTML = html;
  }

  function renderPlugins(container) {
    var plugins = [
      { id: 'code-review', name: 'Code Review', description: 'Review code for security, quality, and best practices', installed: true },
      { id: 'research', name: 'Research Assistant', description: 'Deep research and investigation capabilities', installed: true },
      { id: 'database', name: 'Database Manager', description: 'Manage SQLite and PostgreSQL databases', installed: false },
      { id: 'deploy', name: 'Deploy Assistant', description: 'Deploy applications to various platforms', installed: false },
      { id: 'analytics', name: 'Analytics Dashboard', description: 'Track metrics and generate reports', installed: false },
      { id: 'security', name: 'Security Scanner', description: 'Scan for vulnerabilities and security issues', installed: false }
    ];
    
    var html = '<div class="page-header"><h2>Plugins</h2></div>';
    html += '<div class="card-grid">';
    
    plugins.forEach(function(p) {
      html += '<div class="project-card">' +
        '<div class="project-icon">🧩</div>' +
        '<h3>' + p.name + '</h3>' +
        '<p>' + p.description + '</p>' +
        '<div class="project-actions">' +
          (p.installed ? 
            '<button class="action-btn" disabled>Installed</button>' +
            '<button class="action-btn danger" onclick="window.AerynApp.uninstallPlugin(\'' + p.id + '\')">Uninstall</button>' :
            '<button class="action-btn" onclick="window.AerynApp.installPlugin(\'' + p.id + '\')">Install</button>'
          ) +
        '</div>' +
      '</div>';
    });
    
    html += '</div>';
    container.innerHTML = html;
  }

  function renderAudit(container) {
    var logs = JSON.parse(localStorage.getItem('aeryn-audit-log') || '[]');
    
    if (logs.length === 0) {
      container.innerHTML = 
        '<div class="empty-state">' +
          '<div class="empty-state-icon">📋</div>' +
          '<h3>No Audit Logs</h3>' +
          '<p>Activity will be recorded here as you use Aeryn.</p>' +
        '</div>';
      return;
    }
    
    var html = '<div class="page-header"><h2>Audit Trail</h2>' +
      '<button class="action-btn" onclick="window.AerynApp.clearAudit()">Clear All</button></div>';
    
    html += '<div class="audit-table"><table><thead><tr>' +
      '<th>Time</th><th>Action</th><th>Details</th>' +
      '</tr></thead><tbody>';
    
    logs.forEach(function(log) {
      html += '<tr>' +
        '<td>' + formatTime(log.timestamp) + '</td>' +
        '<td>' + log.action + '</td>' +
        '<td>' + (log.details || '-') + '</td>' +
      '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
  }

  function renderSettings(container) {
    var t = getTheme();
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
          '<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)"><span>Command Palette</span><span class="kbd">Ctrl</span> + <span class="kbd">Shift+P</span></div>' +
          '<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border)"><span>Help</span><span class="kbd">Ctrl</span> + <span class="kbd">/</span></div>' +
          '<div style="display:flex;justify-content:space-between;padding:8px 0"><span>Skip to content</span><span class="kbd">Tab</span></div></div></div>' +
      '<div class="card"><h2>Data Management</h2>' +
        '<div class="actions-grid">' +
          '<button class="action-btn" onclick="window.AerynApp.exportData()"><span class="action-icon">📤</span><span>Export Data</span></button>' +
          '<button class="action-btn danger" onclick="window.AerynApp.clearAllData()"><span class="action-icon">🗑️</span><span>Clear All Data</span></button></div></div>';
  }

  // ============================================================================
  // PROJECT ACTIONS
  // ============================================================================

  function createProject() {
    var name = prompt('Project name:');
    if (!name) return;
    var description = prompt('Description (optional):') || '';
    
    var projects = JSON.parse(localStorage.getItem('aeryn-projects') || '[]');
    var project = { id: Date.now(), name: name, description: description, created: new Date().toISOString() };
    projects.push(project);
    localStorage.setItem('aeryn-projects', JSON.stringify(projects));
    addNotification('Project Created', name + ' has been created', 'success');
    renderProjects(document.getElementById('page-content'));
  }

  function openProject(id) {
    var projects = JSON.parse(localStorage.getItem('aeryn-projects') || '[]');
    var project = projects.find(function(p) { return p.id === id; });
    if (project) {
      showToast('Opening project: ' + project.name, 'info');
    }
  }

  function deleteProject(id) {
    showConfirmDialog('Delete Project', 'Are you sure you want to delete this project?', function() {
      var projects = JSON.parse(localStorage.getItem('aeryn-projects') || '[]');
      projects = projects.filter(function(p) { return p.id !== id; });
      localStorage.setItem('aeryn-projects', JSON.stringify(projects));
      addNotification('Project Deleted', 'Project has been deleted', 'warning');
      renderProjects(document.getElementById('page-content'));
    });
  }

  function createWorkspace() {
    var name = prompt('Workspace name:');
    if (!name) return;
    var description = prompt('Description (optional):') || '';
    
    var workspaces = JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]');
    var workspace = { id: Date.now(), name: name, description: description, members: 1, created: new Date().toISOString() };
    workspaces.push(workspace);
    localStorage.setItem('aeryn-workspaces', JSON.stringify(workspaces));
    addNotification('Workspace Created', name + ' has been created', 'success');
    renderWorkspaces(document.getElementById('page-content'));
  }

  function openWorkspace(id) {
    var workspaces = JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]');
    var ws = workspaces.find(function(w) { return w.id === id; });
    if (ws) showToast('Opening workspace: ' + ws.name, 'info');
  }

  function deleteWorkspace(id) {
    showConfirmDialog('Delete Workspace', 'Are you sure? This will remove all workspace data.', function() {
      var workspaces = JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]');
      workspaces = workspaces.filter(function(w) { return w.id !== id; });
      localStorage.setItem('aeryn-workspaces', JSON.stringify(workspaces));
      addNotification('Workspace Deleted', 'Workspace has been deleted', 'warning');
      renderWorkspaces(document.getElementById('page-content'));
    });
  }

  function newChat() {
    var title = prompt('Chat title:');
    if (!title) title = 'New Chat';
    
    var sessions = JSON.parse(localStorage.getItem('aeryn-chat-sessions') || '[]');
    var session = { id: Date.now(), title: title, messages: [], lastMessage: '', updated: new Date().toISOString() };
    sessions.push(session);
    localStorage.setItem('aeryn-chat-sessions', JSON.stringify(sessions));
    addNotification('New Chat', title + ' has been created', 'success');
    renderChat(document.getElementById('page-content'));
  }

  function openChat(id) {
    var sessions = JSON.parse(localStorage.getItem('aeryn-chat-sessions') || '[]');
    var session = sessions.find(function(s) { return s.id === id; });
    if (session) showToast('Opening chat: ' + session.title, 'info');
  }

  function installPlugin(id) {
    addNotification('Plugin Installed', id + ' has been installed', 'success');
    showToast('Plugin installed: ' + id, 'success');
  }

  function uninstallPlugin(id) {
    addNotification('Plugin Uninstalled', id + ' has been removed', 'warning');
    showToast('Plugin uninstalled: ' + id, 'info');
  }

  function clearAudit() {
    showConfirmDialog('Clear Audit Logs', 'Are you sure? This cannot be undone.', function() {
      localStorage.setItem('aeryn-audit-log', '[]');
      addNotification('Audit Cleared', 'All audit logs have been cleared', 'warning');
      renderAudit(document.getElementById('page-content'));
    });
  }

  function exportData() {
    var data = {
      projects: JSON.parse(localStorage.getItem('aeryn-projects') || '[]'),
      workspaces: JSON.parse(localStorage.getItem('aeryn-workspaces') || '[]'),
      chatSessions: JSON.parse(localStorage.getItem('aeryn-chat-sessions') || '[]'),
      notifications: notifications,
      exportDate: new Date().toISOString()
    };
    
    var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'aeryn-export-' + Date.now() + '.json';
    a.click();
    URL.revokeObjectURL(url);
    addNotification('Data Exported', 'Your data has been exported', 'success');
  }

  function clearAllData() {
    showConfirmDialog('Clear All Data', 'This will delete ALL projects, workspaces, chats, and notifications. Continue?', function() {
      localStorage.removeItem('aeryn-projects');
      localStorage.removeItem('aeryn-workspaces');
      localStorage.removeItem('aeryn-chat-sessions');
      localStorage.removeItem('aeryn-audit-log');
      notifications = [];
      addNotification('Data Cleared', 'All data has been cleared', 'warning');
      navigate('dashboard');
    });
  }

  function goHome() {
    navigate('dashboard');
  }

  // ============================================================================
  // HEALTH CHECK
  // ============================================================================

  function fetchHealth() {
    fetch('/api/py/health', { method: 'GET' })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        healthData = data;
        var banner = document.getElementById('offline-banner');
        if (banner) banner.style.display = 'none';
        if (currentPage === 'dashboard') renderPage();
      })
      .catch(function() {
        healthData = null;
        var banner = document.getElementById('offline-banner');
        if (banner) banner.style.display = 'flex';
        if (currentPage === 'dashboard') renderPage();
      });
  }

  // ============================================================================
  // UPTIME COUNTER
  // ============================================================================

  var uptimeStarted = false;
  function startUptimeCounter() {
    if (uptimeStarted) return;
    uptimeStarted = true;
    setInterval(function() {
      var el = document.getElementById('uptime');
      if (el) {
        var elapsed = Math.floor((Date.now() - startTime) / 1000);
        var h = Math.floor(elapsed / 3600).toString().padStart(2, '0');
        var m = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0');
        var s = (elapsed % 60).toString().padStart(2, '0');
        el.textContent = h + ':' + m + ':' + s;
      }
    }, 1000);
  }

  // ============================================================================
  // KEYBOARD SHORTCUTS
  // ============================================================================

  function setupKeyboard() {
    document.addEventListener('keydown', function(e) {
      // Ctrl+K: Focus search
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        var input = document.getElementById('search-input');
        if (input) input.focus();
        showToast('Search focused', 'info', 1500);
      }
      // Ctrl+T: Toggle theme
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 't') {
        e.preventDefault();
        toggleTheme();
      }
      // Ctrl+Shift+P: Command palette
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'p') {
        e.preventDefault();
        toggleCommandPalette();
      }
      // Ctrl+/: Help
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        showToast('Shortcuts: Ctrl+K search, Ctrl+T theme, Ctrl+Shift+P command palette', 'info', 3000);
      }
      // Escape: Close modals
      if (e.key === 'Escape') {
        if (commandPaletteOpen) toggleCommandPalette();
        var input = document.getElementById('search-input');
        if (input && document.activeElement === input) input.blur();
      }
    });
  }

  // ============================================================================
  // SEARCH
  // ============================================================================

  function setupSearch() {
    var input = document.getElementById('search-input');
    if (!input) return;
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        var q = input.value.toLowerCase();
        var found = navItems.find(function(n) { return n.label.toLowerCase().includes(q); });
        if (found) {
          navigate(found.id);
          input.value = '';
        } else {
          showToast('No results for: ' + q, 'warning');
        }
      }
    });
  }

  // ============================================================================
  // HISTORY
  // ============================================================================

  function setupHistory() {
    window.addEventListener('popstate', function() {
      var path = window.location.pathname.replace(/^\//, '') || 'dashboard';
      if (path !== currentPage) {
        currentPage = path;
        renderNav();
        renderBreadcrumb();
        renderPage();
      }
    });
  }

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

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
      fetchHealth: fetchHealth,
      toggleCommandPalette: toggleCommandPalette,
      createProject: createProject,
      openProject: openProject,
      deleteProject: deleteProject,
      createWorkspace: createWorkspace,
      openWorkspace: openWorkspace,
      deleteWorkspace: deleteWorkspace,
      newChat: newChat,
      openChat: openChat,
      installPlugin: installPlugin,
      uninstallPlugin: uninstallPlugin,
      clearAudit: clearAudit,
      exportData: exportData,
      clearAllData: clearAllData,
      goHome: goHome,
      markRead: markNotificationRead,
      markAllRead: markAllNotificationsRead
    };
  }

  // Run when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
