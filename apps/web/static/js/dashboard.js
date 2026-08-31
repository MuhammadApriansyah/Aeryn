/**
 * Aeryn Dashboard v61.1 — Full Functional SPA
 * Features: Overview, Chat, Tools, Divisions, Workflows, Observability, Settings
 * API Integration: All D7-D11 endpoints
 */
(function() {
  'use strict';

  // ============================================================================
  // STATE
  // ============================================================================
  
  const state = {
    currentTab: 'overview',
    healthData: null,
    traces: [],
    workflows: [],
    tools: [],
    divisions: {},
    sessionId: 'web_' + Date.now(),
    ws: null,
    wsReconnectDelay: 1000,
    refreshInterval: null,
  };

  const API = {
    health: '/health',
    gatewayEnv: '/gateway/env',
    traces: '/observability/traces',
    trace: (id) => `/observability/traces/${id}`,
    traceStats: '/observability/stats',
    selfImprovementStats: '/self-improvement/stats',
    selfImprovementPatterns: '/self-improvement/patterns',
    selfImprovementAdapt: '/self-improvement/adapt',
    plugins: '/plugins',
    discoverTools: (q) => `/plugins/discover?q=${encodeURIComponent(q)}`,
    divisions: '/divisions',
    executeDivision: (name) => `/divisions/${name}/execute`,
    connectors: '/connectors',
    syncConnector: (name) => `/connectors/${name}/sync`,
    syncAllConnectors: '/connectors/sync-all',
    workflows: '/workflows',
    workflow: (id) => `/workflows/${id}`,
    workflowStep: (id) => `/workflows/${id}/step`,
    workflowApprove: (id) => `/workflows/${id}/approve`,
    chat: '/chat',
    run: '/run',
    search: (q) => `/search?q=${encodeURIComponent(q)}`,
  };

  // ============================================================================
  // UTILITIES
  // ============================================================================

  async function api(url, options = {}) {
    try {
      const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      return await response.json();
    } catch (err) {
      console.error(`API Error [${url}]:`, err);
      return { error: err.message };
    }
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'alert');
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  function announce(message) {
    const announcer = document.createElement('div');
    announcer.setAttribute('role', 'status');
    announcer.setAttribute('aria-live', 'polite');
    announcer.className = 'sr-only';
    announcer.textContent = message;
    document.body.appendChild(announcer);
    setTimeout(() => announcer.remove(), 1000);
  }

  function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ============================================================================
  // NAVIGATION
  // ============================================================================

  function switchTab(tabName) {
    state.currentTab = tabName;
    
    document.querySelectorAll('.nav-tab').forEach(tab => {
      const isActive = tab.dataset.tab === tabName;
      tab.classList.toggle('active', isActive);
      tab.setAttribute('aria-selected', isActive);
    });
    
    document.querySelectorAll('.tab-panel').forEach(panel => {
      panel.classList.toggle('active', panel.id === `tab-${tabName}`);
    });
    
    announce(`Switched to ${tabName}`);
    
    const tabLoaders = {
      overview: loadOverview,
      chat: () => {},
      tools: loadTools,
      divisions: loadDivisions,
      workflows: loadWorkflows,
      observability: loadTraces,
      settings: loadSettings,
    };
    
    if (tabLoaders[tabName]) tabLoaders[tabName]?.();
  }

  // ============================================================================
  // OVERVIEW
  // ============================================================================

  async function loadOverview() {
    const health = await api(API.health);
    state.healthData = health;
    
    const statsEl = document.getElementById('health-stats');
    statsEl.innerHTML = `
      <div class="stat-card">
        <span class="stat-value">${escapeHtml(health.status || 'unknown')}</span>
        <span class="stat-label">Status</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">${health.memory_mb || 0}MB</span>
        <span class="stat-label">Memory</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">${escapeHtml(health.version || '61.1')}</span>
        <span class="stat-label">Version</span>
      </div>
      <div class="stat-card">
        <span class="stat-value">${state.traces.length}</span>
        <span class="stat-label">Traces</span>
      </div>
    `;
    
    updateStatusIndicator(health.status === 'healthy');
    loadTraces();
    loadSelfImprovement();
  }

  function updateStatusIndicator(healthy) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    if (dot) dot.className = `status-dot ${healthy ? 'online' : 'offline'}`;
    if (text) text.textContent = healthy ? 'Online' : 'Offline';
  }

  async function loadSelfImprovement() {
    const stats = await api(API.selfImprovementStats);
    const el = document.getElementById('self-improvement-status');
    if (!el) return;
    el.querySelector('.card-content').innerHTML = `
      <div class="metric"><span class="metric-value">${stats.total_learnings || 0}</span><span class="metric-label">Learnings</span></div>
      <div class="metric"><span class="metric-value">${stats.total_improvements || 0}</span><span class="metric-label">Improvements</span></div>
      <button class="btn-sm" onclick="AerynApp.triggerAdapt()">Trigger Adapt</button>
    `;
  }

  // ============================================================================
  // CHAT
  // ============================================================================

  async function sendChat() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    addMessage('user', message);
    input.value = '';
    
    const result = await api(API.chat, {
      method: 'POST',
      body: JSON.stringify({ goal: message, session_id: state.sessionId }),
    });
    
    if (result.response) {
      addMessage('assistant', result.response);
      if (result.tool_used) {
        addMessage('system', `Tool used: ${result.tool_used} | Division: ${result.division || 'none'}`);
      }
    } else if (result.error) {
      addMessage('system', `Error: ${result.error}`);
    }
    
    announce('Response received');
  }

  function addMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  // ============================================================================
  // TOOLS
  // ============================================================================

  async function loadTools() {
    const result = await api(API.plugins);
    state.tools = result.tools || [];
    renderTools(state.tools);
  }

  function renderTools(tools) {
    const el = document.getElementById('tools-grid');
    if (!tools.length) {
      el.innerHTML = '<p class="muted">No tools registered</p>';
      return;
    }
    el.innerHTML = tools.map(t => `
      <div class="tool-card">
        <div class="tool-header">
          <span class="tool-name">${escapeHtml(t.name)}</span>
          <span class="tool-version">v${escapeHtml(t.version || '1.0')}</span>
        </div>
        <p class="tool-desc">${escapeHtml(t.description)}</p>
        <div class="tool-tags">${(t.tags || []).map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}</div>
      </div>
    `).join('');
  }

  async function discoverTools(query) {
    if (!query) { renderTools(state.tools); return; }
    const result = await api(API.discoverTools(query));
    renderTools(result.tools || []);
  }

  // ============================================================================
  // DIVISIONS
  // ============================================================================

  async function loadDivisions() {
    const result = await api(API.divisions);
    state.divisions = result;
    const el = document.getElementById('divisions-grid');
    
    const divisions = result.divisions || [];
    const status = result.divisions || {};
    
    el.innerHTML = divisions.map(name => {
      const info = status[name] || {};
      return `
        <div class="division-card">
          <h3>${name.charAt(0).toUpperCase() + name.slice(1)}</h3>
          <p>Agents: ${info.agents || 0}</p>
          <p>Pending: ${info.pending_tasks || 0}</p>
          <button class="btn-sm" onclick="AerynApp.executeDivision('${name}')">Execute</button>
        </div>
      `;
    }).join('');
  }

  async function executeDivision(name) {
    const tasks = [{ name: 'quick_task', description: `Quick task for ${name}` }];
    const result = await api(API.executeDivision(name), {
      method: 'POST',
      body: JSON.stringify({ tasks }),
    });
    showToast(`Division ${name}: ${result.completed}/${result.tasks} completed`);
  }

  // ============================================================================
  // WORKFLOWS
  // ============================================================================

  async function loadWorkflows() {
    const result = await api(API.workflows);
    state.workflows = result.workflows || [];
    const el = document.getElementById('workflows-list');
    
    if (!state.workflows.length) {
      el.innerHTML = '<p class="muted">No workflows yet. Create one to get started.</p>';
      return;
    }
    
    el.innerHTML = state.workflows.map(w => `
      <div class="workflow-card">
        <div class="workflow-header">
          <span class="workflow-name">${escapeHtml(w.name)}</span>
          <span class="workflow-status status-${w.status}">${escapeHtml(w.status)}</span>
        </div>
        <div class="workflow-actions">
          <button class="btn-sm" onclick="AerynApp.stepWorkflow('${w.id}')">Next Step</button>
          <button class="btn-sm" onclick="AerynApp.viewWorkflow('${w.id}')">View</button>
        </div>
      </div>
    `).join('');
  }

  async function createWorkflow() {
    const idea = prompt('Enter your SaaS idea:');
    if (!idea) return;
    
    const result = await api(API.workflows, {
      method: 'POST',
      body: JSON.stringify({ name: 'saas', idea }),
    });
    
    showToast(`Workflow created: ${result.id}`);
    loadWorkflows();
  }

  async function stepWorkflow(id) {
    const result = await api(API.workflowStep(id), { method: 'POST' });
    showToast(`Step: ${result.status}`);
    loadWorkflows();
  }

  async function viewWorkflow(id) {
    const result = await api(API.workflow(id));
    showModal('Workflow Details', `<pre>${JSON.stringify(result, null, 2)}</pre>`);
  }

  // ============================================================================
  // OBSERVABILITY
  // ============================================================================

  async function loadTraces() {
    const result = await api(API.traces + '?limit=10');
    state.traces = result.traces || [];
    const el = document.getElementById('traces-list');
    
    const statsEl = document.getElementById('trace-stats');
    if (statsEl) statsEl.textContent = `${state.traces.length} traces`;
    
    if (!state.traces.length) {
      el.innerHTML = '<p class="muted">No traces yet</p>';
      return;
    }
    
    el.innerHTML = state.traces.map(t => `
      <div class="trace-card">
        <div class="trace-header">
          <span class="trace-id">${escapeHtml(t.id)}</span>
          <span class="trace-sessions">${escapeHtml(t.session_id || 'default')}</span>
        </div>
        <div class="trace-meta">
          <span>${t.spans || 0} spans</span>
        </div>
      </div>
    `).join('');
  }

  // ============================================================================
  // SETTINGS
  // ============================================================================

  async function loadSettings() {
    const env = await api(API.gatewayEnv);
    const envEl = document.getElementById('env-info');
    if (envEl) {
      envEl.innerHTML = `
        <p>Environment: <strong>${escapeHtml(env.environment?.type || 'unknown')}</strong></p>
        <p>DB: <strong>${escapeHtml(env.environment?.db || 'sqlite')}</strong></p>
        <p>Auth: <strong>${env.auth_enabled ? '✅' : '❌'}</strong></p>
        <p>Rate Limiter: <strong>${env.rate_limiter_enabled ? '✅' : '❌'}</strong></p>
      `;
    }
    
    const gwEl = document.getElementById('gateway-info');
    if (gwEl) {
      const cb = env.circuit_breakers || {};
      gwEl.innerHTML = `
        <p>Chat CB: <strong>${escapeHtml(cb.chat?.state || 'unknown')}</strong></p>
        <p>LLM CB: <strong>${escapeHtml(cb.llm?.state || 'unknown')}</strong></p>
      `;
    }
  }

  // ============================================================================
  // MODAL
  // ============================================================================

  function showModal(title, content) {
    const overlay = document.getElementById('modal-overlay');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    overlay.hidden = false;
  }

  function closeModal() {
    document.getElementById('modal-overlay').hidden = true;
  }

  // ============================================================================
  // ADAPTATION
  // ============================================================================

  async function triggerAdapt() {
    const result = await api(API.selfImprovementAdapt, { method: 'POST' });
    showToast(`Adaptation: ${result.changes?.length || 0} changes`);
    loadSelfImprovement();
  }

  async function loadPatterns() {
    const result = await api(API.selfImprovementPatterns + '?pattern_type=tool_selection');
    showModal('Tool Patterns', `<pre>${JSON.stringify(result.patterns, null, 2)}</pre>`);
  }

  // ============================================================================
  // THEME
  // ============================================================================

  function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    document.getElementById('theme-toggle').textContent = next === 'dark' ? '🌙' : '☀️';
  }

  // ============================================================================
  // QUICK RUN
  // ============================================================================

  function quickRun() {
    const goal = prompt('Enter goal:');
    if (!goal) return;
    
    api(API.run, {
      method: 'POST',
      body: JSON.stringify({ goal }),
    }).then(result => {
      if (result.response) {
        addMessage('assistant', result.response);
        switchTab('chat');
      }
    });
  }

  // ============================================================================
  // REFRESH
  // ============================================================================

  function refreshAll() {
    loadOverview();
    showToast('Refreshed');
  }

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  function init() {
    // Tab switching
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Theme toggle
    document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
    
    // Refresh
    document.getElementById('refresh-btn')?.addEventListener('click', refreshAll);
    
    // Chat input
    document.getElementById('chat-input')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChat();
      }
    });
    
    // Tools search
    document.getElementById('tools-search')?.addEventListener('input', (e) => {
      discoverTools(e.target.value);
    });
    
    // Global search
    document.getElementById('global-search')?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        api(API.search(e.target.value)).then(result => {
          showModal('Search Results', `<pre>${JSON.stringify(result, null, 2)}</pre>`);
        });
      }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        document.getElementById('global-search')?.focus();
      }
      if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        toggleTheme();
      }
      if (e.key === 'Escape') {
        closeModal();
      }
    });
    
    // Initial load
    loadOverview();
    state.refreshInterval = setInterval(loadOverview, 10000);
  }

  // ============================================================================
  // PUBLIC API
  // ============================================================================

  window.AerynApp = {
    switchTab,
    sendChat,
    loadOverview,
    loadTraces,
    loadTools,
    loadDivisions,
    loadWorkflows,
    loadSettings,
    createWorkflow,
    stepWorkflow,
    viewWorkflow,
    executeDivision,
    triggerAdapt,
    loadPatterns,
    toggleTheme,
    quickRun,
    refreshAll,
    closeModal,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
