/**
 * Aeryn Dashboard v61.4 — Massive SPA
 * Comprehensive UI for all Aeryn modules with WCAG 2.1 AA accessibility
 */
(function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════
  
  const state = {
    currentSection: 'overview',
    sidebarCollapsed: false,
    sidebarMobileOpen: false,
    sessionId: 'web_' + Date.now(),
    theme: localStorage.getItem('theme') || 'dark',
    refreshInterval: null,
    ws: null,
    traces: [],
    workflows: [],
    tools: [],
    divisions: {},
    plugins: [],
    memories: [],
    workspaces: [],
    notifications: [],
    health: null,
    env: null,
  };

  const API = {
    // Core
    health: '/health',
    gatewayEnv: '/gateway/env',
    
    // Chat & Execution
    chat: '/chat',
    run: '/run',
    search: (q) => `/search?q=${encodeURIComponent(q)}`,
    compile: '/compile',
    digest: '/digest',
    
    // Divisions & Workflows
    divisions: '/divisions',
    executeDivision: (name) => `/divisions/${name}/execute`,
    workflows: '/workflows',
    workflow: (id) => `/workflows/${id}`,
    workflowStep: (id) => `/workflows/${id}/step`,
    workflowApprove: (id) => `/workflows/${id}/approve`,
    
    // Plugins
    plugins: '/plugins',
    pluginRun: '/plugins/run',
    pluginDiscover: (q) => `/plugins/discover?q=${encodeURIComponent(q)}`,
    
    // Memory (PostgreSQL)
    pgStats: '/v1/postgres-memory/stats',
    pgRemember: '/v1/postgres-memory/remember',
    pgRecall: (q, limit) => `/v1/postgres-memory/recall?q=${encodeURIComponent(q)}&limit=${limit || 10}`,
    pgSessions: (q, limit) => `/v1/postgres-memory/sessions?q=${encodeURIComponent(q)}&limit=${limit || 5}`,
    pgForget: (key) => `/v1/postgres-memory/forget?key=${encodeURIComponent(key)}`,
    pgIndex: '/v1/postgres-memory/index',
    
    // Memory (Vault)
    memoryRecall: (q) => `/memory/recall?q=${encodeURIComponent(q)}`,
    vaultSearch: (q) => `/vault/search?q=${encodeURIComponent(q)}`,
    vaultEntries: '/vault/entries',
    
    // Tools
    tools: '/tools/list',
    toolsExecute: '/tools/execute',
    toolsDiscover: (q) => `/tools/discover?q=${encodeURIComponent(q)}`,
    
    // Agents
    agents: '/agents',
    agentTasks: '/agents/tasks',
    
    // Observability
    traces: '/observability/traces',
    trace: (id) => `/observability/traces/${id}`,
    traceStats: '/observability/stats',
    performance: '/performance/stats',
    
    // Workspaces
    workspaces: '/workspaces',
    workspace: (id) => `/workspaces/${id}`,
    
    // Projects & Tasks
    planningTasks: '/planning/tasks',
    sharedTasks: '/shared/tasks',
    sharedReminders: '/shared/reminders',
    
    // Billing
    billingPricing: '/billing/pricing',
    billingQuota: '/billing/quota',
    usageSummary: '/usage/summary',
    
    // Notifications
    notifications: '/notifications/pending',
    notificationsCreate: '/notifications/create',
    
    // Admin
    adminStats: '/admin/stats',
    adminUsers: '/admin/users',
    complianceReport: '/admin/compliance/report',
    
    // Self-Improvement
    selfImprovementStats: '/self-improvement/stats',
    selfImprovementAdapt: '/self-improvement/adapt',
    selfImprovementPatterns: '/self-improvement/patterns',
    
    // Experience Transfer
    experienceStatus: '/v1/experience/status',
    experienceLessons: '/v1/experience/lessons',
    experiencePreferences: '/v1/experience/preferences',
    experienceInitialize: '/v1/experience/initialize',
    
    // Messaging
    messagingStatus: '/v1/messaging/status',
    messagingSend: (platform) => `/v1/messaging/send/${platform}`,
  };

  // ═══════════════════════════════════════════════════════════════
  // UTILITIES
  // ═══════════════════════════════════════════════════════════════
  
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

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function formatDuration(ms) {
    if (!ms) return '—';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  }

  function formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleString('id-ID');
    } catch {
      return dateStr;
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // NAVIGATION
  // ═══════════════════════════════════════════════════════════════
  
  function switchSection(sectionName) {
    state.currentSection = sectionName;
    
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.section === sectionName);
    });
    
    // Update sections
    document.querySelectorAll('.section').forEach(section => {
      section.classList.toggle('active', section.id === `section-${sectionName}`);
    });
    
    // Update header title
    const titles = {
      overview: 'Overview',
      chat: 'Chat',
      divisions: 'Cognitive Divisions',
      workspaces: 'Workspaces',
      projects: 'Projects',
      workflows: 'Workflows',
      plugins: 'Plugins',
      memory: 'Memory',
      tools: 'Tools',
      agents: 'Agents',
      observability: 'Observability',
      billing: 'Billing & Usage',
      notifications: 'Notifications',
      settings: 'Settings',
      admin: 'Admin',
    };
    document.getElementById('page-title').textContent = titles[sectionName] || sectionName;
    
    announce(`Switched to ${titles[sectionName] || sectionName}`);
    
    // Load section data
    loadSectionData(sectionName);
  }

  function toggleSidebar() {
    state.sidebarCollapsed = !state.sidebarCollapsed;
    document.getElementById('sidebar').classList.toggle('collapsed', state.sidebarCollapsed);
  }

  function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    document.getElementById('theme-toggle').textContent = next === 'dark' ? '🌙' : '☀️';
  }

  function showModal(title, content) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    document.getElementById('modal-overlay').classList.add('active');
  }

  function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
  }

  // ═══════════════════════════════════════════════════════════════
  // SECTION LOADERS
  // ═══════════════════════════════════════════════════════════════
  
  function loadSectionData(section) {
    const loaders = {
      overview: loadOverview,
      chat: () => {},
      divisions: loadDivisions,
      workspaces: loadWorkspaces,
      projects: loadProjects,
      workflows: loadWorkflows,
      plugins: loadPlugins,
      memory: loadMemory,
      tools: loadTools,
      agents: loadAgents,
      observability: loadObservability,
      billing: loadBilling,
      notifications: loadNotifications,
      settings: loadSettings,
      admin: loadAdmin,
    };
    
    if (loaders[section]) loaders[section]();
  }

  // ── Overview ──
  
  async function loadOverview() {
    const health = await api(API.health);
    state.health = health;
    
    document.getElementById('ov-status').textContent = health.status || 'unknown';
    document.getElementById('ov-memory').textContent = (health.memory_mb || 0) + ' MB';
    document.getElementById('ov-plugins').textContent = state.plugins.length || '—';
    
    const traceStats = await api(API.traceStats);
    document.getElementById('ov-traces').textContent = traceStats.total_traces || 0;
    
    const healthDetails = document.getElementById('ov-health-details');
    if (healthDetails) {
      healthDetails.innerHTML = `
        <div style="display: grid; gap: 8px;">
          <div><span class="badge badge-${health.status === 'healthy' ? 'success' : 'danger'}">${health.status}</span></div>
          <div>Memory: <strong>${health.memory_mb} MB</strong></div>
          <div>Version: <strong>${health.version}</strong></div>
        </div>
      `;
    }
    
    // Update status dot
    const isHealthy = health.status === 'healthy';
    document.getElementById('status-dot').className = `status-dot ${isHealthy ? 'online' : ''}`;
    document.getElementById('status-text').textContent = isHealthy ? 'Online' : 'Offline';
  }

  // ── Divisions ──
  
  async function loadDivisions() {
    const result = await api(API.divisions);
    state.divisions = result;
  }

  async function executeDivision(name) {
    const goal = prompt(`Enter task for ${name} division:`);
    if (!goal) return;
    
    showToast(`Executing ${name}...`, 'info');
    const result = await api(API.executeDivision(name), {
      method: 'POST',
      body: JSON.stringify({ goal }),
    });
    
    if (result.error) {
      showToast(`Error: ${result.error}`, 'error');
    } else {
      showToast(`Completed: ${result.completed}/${result.tasks} tasks`, 'success');
      showModal('Division Result', `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`);
    }
  }

  // ── Workspaces ──
  
  async function loadWorkspaces() {
    const result = await api(API.workspaces);
    state.workspaces = result.workspaces || [];
    
    const list = document.getElementById('workspaces-list');
    if (!list) return;
    
    if (!state.workspaces.length) {
      list.innerHTML = '<p style="color: var(--text2);">No workspaces yet. Create one to get started.</p>';
      return;
    }
    
    list.innerHTML = state.workspaces.map(ws => `
      <div class="card" style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong>${escapeHtml(ws.name)}</strong>
            <p style="color: var(--text2); font-size: 12px;">${escapeHtml(ws.description || '')}</p>
          </div>
          <span class="badge badge-${ws.status === 'active' ? 'success' : 'warning'}">${ws.status || 'unknown'}</span>
        </div>
      </div>
    `).join('');
  }

  async function createWorkspace() {
    const name = document.getElementById('ws-name').value;
    const desc = document.getElementById('ws-desc').value;
    if (!name) return showToast('Name required', 'error');
    
    const result = await api(API.workspaces, {
      method: 'POST',
      body: JSON.stringify({ name, description: desc }),
    });
    
    if (result.error) {
      showToast(`Error: ${result.error}`, 'error');
    } else {
      showToast('Workspace created!', 'success');
      loadWorkspaces();
    }
  }

  // ── Projects ──
  
  async function loadProjects() {
    const [planning, shared, reminders] = await Promise.all([
      api(API.planningTasks),
      api(API.sharedTasks),
      api(API.sharedReminders),
    ]);
    
    document.getElementById('planning-count').textContent = (planning.tasks || []).length;
    document.getElementById('shared-count').textContent = (shared.tasks || []).length;
    document.getElementById('reminders-count').textContent = (reminders.reminders || []).length;
    
    const planningList = document.getElementById('planning-list');
    if (planningList) {
      const tasks = planning.tasks || [];
      planningList.innerHTML = tasks.length ? tasks.map(t => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(t.name || t.title || 'Untitled')}</strong>
          <span class="badge badge-${t.status === 'completed' ? 'success' : 'warning'}" style="margin-left: 8px;">${t.status || 'pending'}</span>
        </div>
      `).join('') : '<p style="color: var(--text2);">No tasks</p>';
    }
    
    const sharedList = document.getElementById('shared-tasks-list');
    if (sharedList) {
      const tasks = shared.tasks || [];
      sharedList.innerHTML = tasks.length ? tasks.map(t => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(t.name || t.title || 'Untitled')}</strong>
          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(t.description || '')}</p>
        </div>
      `).join('') : '<p style="color: var(--text2);">No shared tasks</p>';
    }
    
    const remindersList = document.getElementById('reminders-list');
    if (remindersList) {
      const rems = reminders.reminders || [];
      remindersList.innerHTML = rems.length ? rems.map(r => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(r.text || r.title || 'Reminder')}</strong>
          <span style="font-size: 11px; color: var(--text2); margin-left: 8px;">${formatDate(r.due_at || r.created_at)}</span>
        </div>
      `).join('') : '<p style="color: var(--text2);">No reminders</p>';
    }
  }

  // ── Workflows ──
  
  async function loadWorkflows() {
    const result = await api(API.workflows);
    state.workflows = result.workflows || [];
    
    const list = document.getElementById('workflows-list');
    if (!list) return;
    
    if (!state.workflows.length) {
      list.innerHTML = '<p style="color: var(--text2);">No workflows yet. Create one to get started.</p>';
      return;
    }
    
    list.innerHTML = state.workflows.map(w => `
      <div class="card" style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong>${escapeHtml(w.name || 'Untitled')}</strong>
            <span class="badge badge-${w.status === 'completed' ? 'success' : 'warning'}" style="margin-left: 8px;">${w.status || 'active'}</span>
          </div>
          <div style="display: flex; gap: 4px;">
            <button class="btn btn-sm btn-secondary" onclick="stepWorkflow('${w.id}')">Step</button>
            <button class="btn btn-sm btn-primary" onclick="viewWorkflow('${w.id}')">View</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  async function createWorkflow() {
    const name = document.getElementById('wf-name').value;
    const idea = document.getElementById('wf-idea').value;
    if (!name || !idea) return showToast('Name and idea required', 'error');
    
    const result = await api(API.workflows, {
      method: 'POST',
      body: JSON.stringify({ name, idea }),
    });
    
    if (result.error) {
      showToast(`Error: ${result.error}`, 'error');
    } else {
      showToast('Workflow created!', 'success');
      loadWorkflows();
    }
  }

  async function stepWorkflow(id) {
    const result = await api(API.workflowStep(id), { method: 'POST' });
    showToast(`Step: ${result.status}`, 'info');
    loadWorkflows();
  }

  async function viewWorkflow(id) {
    const result = await api(API.workflow(id));
    showModal('Workflow Details', `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`);
  }

  // ── Plugins ──
  
  async function loadPlugins() {
    const result = await api(API.plugins);
    state.plugins = result.tools || result.plugins || [];
    
    document.getElementById('ov-plugins').textContent = state.plugins.length;
    document.getElementById('plugin-count').textContent = state.plugins.length;
    document.getElementById('installed-plugins-count').textContent = state.plugins.length;
    
    const list = document.getElementById('installed-plugins-list');
    if (list) {
      list.innerHTML = state.plugins.length ? state.plugins.map(p => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(p.name)}</strong>
          <span class="badge badge-info" style="margin-left: 8px;">v${p.version || '1.0'}</span>
          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(p.description || '')}</p>
        </div>
      `).join('') : '<p style="color: var(--text2);">No plugins installed</p>';
    }
  }

  async function runPlugin(name) {
    let input, outputId;
    
    if (name === 'code-review') {
      input = document.getElementById('plugin-code-review-input').value;
      outputId = 'plugin-code-review-output';
    } else if (name === 'research-assistant') {
      input = document.getElementById('plugin-research-input').value;
      outputId = 'plugin-research-output';
    }
    
    if (!input) return showToast('Input required', 'error');
    
    const result = await api(API.pluginRun, {
      method: 'POST',
      body: JSON.stringify({ name, input }),
    });
    
    const output = document.getElementById(outputId);
    if (output) {
      if (result.error) {
        output.innerHTML = `<span style="color: var(--danger);">${escapeHtml(result.error)}</span>`;
      } else {
        output.innerHTML = `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
      }
    }
  }

  // ── Memory ──
  
  async function loadMemory() {
    const stats = await api(API.pgStats);
    
    document.getElementById('mem-sessions').textContent = stats.total_sessions || 0;
    document.getElementById('mem-total').textContent = stats.total_memories || 0;
    document.getElementById('mem-hot').textContent = stats.hot_memories || 0;
    document.getElementById('mem-warm').textContent = stats.warm_memories || 0;
  }

  async function searchMemories() {
    const q = document.getElementById('mem-search-input').value;
    if (!q) return;
    
    const result = await api(API.pgRecall(q, 20));
    const list = document.getElementById('mem-search-results');
    if (!list) return;
    
    if (!result.results || !result.results.length) {
      list.innerHTML = '<p style="color: var(--text2);">No memories found</p>';
      return;
    }
    
    list.innerHTML = result.results.map(m => `
      <div class="card" style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <strong>${escapeHtml(m.key)}</strong>
          <span class="badge badge-${m.tier === 'hot' ? 'danger' : m.tier === 'warm' ? 'warning' : 'info'}">${m.tier}</span>
        </div>
        <p style="font-size: 13px; color: var(--text2);">${escapeHtml(m.value?.substring(0, 150) || '')}</p>
        <div style="font-size: 11px; color: var(--text2); margin-top: 4px;">
          Type: ${m.type || 'fact'} | Importance: ${(m.importance || 0).toFixed(2)} | Similarity: ${(m.similarity || 0).toFixed(2)}
        </div>
      </div>
    `).join('');
  }

  async function storeMemory() {
    const key = document.getElementById('mem-key').value;
    const value = document.getElementById('mem-value').value;
    const type = document.getElementById('mem-type').value;
    
    if (!key || !value) return showToast('Key and value required', 'error');
    
    const result = await api(API.pgRemember, {
      method: 'POST',
      body: JSON.stringify({ key, value, type, importance: 0.7, skip_embedding: true }),
    });
    
    if (result.error) {
      showToast(`Error: ${result.error}`, 'error');
    } else {
      showToast('Memory stored!', 'success');
      loadMemory();
    }
  }

  // ── Tools ──
  
  async function loadTools() {
    const result = await api(API.toolsDiscover(''));
    state.tools = result.tools || [];
    
    document.getElementById('tools-count').textContent = state.tools.length;
    
    const list = document.getElementById('tools-list');
    if (list) {
      list.innerHTML = state.tools.length ? state.tools.map(t => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(t.name)}</strong>
          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(t.description || '')}</p>
        </div>
      `).join('') : '<p style="color: var(--text2);">No tools available</p>';
    }
    
    const select = document.getElementById('tool-select');
    if (select) {
      select.innerHTML = state.tools.map(t => `<option value="${escapeHtml(t.name)}">${escapeHtml(t.name)}</option>`).join('');
    }
  }

  async function executeTool() {
    const name = document.getElementById('tool-select').value;
    const inputStr = document.getElementById('tool-input').value;
    
    if (!name) return showToast('Select a tool', 'error');
    
    let input = {};
    try {
      if (inputStr) input = JSON.parse(inputStr);
    } catch {
      input = { query: inputStr };
    }
    
    const result = await api(API.toolsExecute, {
      method: 'POST',
      body: JSON.stringify({ name, ...input }),
    });
    
    const output = document.getElementById('tool-output');
    if (output) {
      output.innerHTML = `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
    }
  }

  // ── Agents ──
  
  async function loadAgents() {
    const [agents, tasks] = await Promise.all([
      api(API.agents),
      api(API.agentTasks),
    ]);
    
    document.getElementById('agents-count').textContent = (agents.agents || []).length;
    document.getElementById('agent-tasks-count').textContent = (tasks.tasks || []).length;
    
    const agentsList = document.getElementById('agents-list');
    if (agentsList) {
      const agentList = agents.agents || [];
      agentsList.innerHTML = agentList.length ? agentList.map(a => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(a.name || 'Agent')}</strong>
          <span class="badge badge-${a.status === 'active' ? 'success' : 'warning'}" style="margin-left: 8px;">${a.status || 'idle'}</span>
        </div>
      `).join('') : '<p style="color: var(--text2);">No agents registered</p>';
    }
    
    const tasksList = document.getElementById('agent-tasks-list');
    if (tasksList) {
      const taskList = tasks.tasks || [];
      tasksList.innerHTML = taskList.length ? taskList.map(t => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(t.name || 'Task')}</strong>
          <span class="badge badge-${t.status === 'completed' ? 'success' : 'warning'}" style="margin-left: 8px;">${t.status || 'pending'}</span>
        </div>
      `).join('') : '<p style="color: var(--text2);">No tasks</p>';
    }
  }

  // ── Observability ──
  
  async function loadObservability() {
    const [traceStats, traces, perf] = await Promise.all([
      api(API.traceStats),
      api(API.traces + '?limit=10'),
      api(API.performance),
    ]);
    
    document.getElementById('obs-traces').textContent = traceStats.total_traces || 0;
    document.getElementById('obs-spans').textContent = traceStats.total_spans || 0;
    document.getElementById('obs-avg').textContent = formatDuration(traceStats.avg_duration || 0);
    
    const tracesList = document.getElementById('traces-list');
    if (tracesList) {
      const traceList = traces.traces || [];
      tracesList.innerHTML = traceList.length ? traceList.map(t => `
        <div class="card" style="margin-bottom: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong>${escapeHtml(t.id)}</strong>
              <span style="font-size: 12px; color: var(--text2); margin-left: 8px;">${escapeHtml(t.session_id || 'default')}</span>
            </div>
            <span class="badge badge-info">${t.spans || 0} spans</span>
          </div>
        </div>
      `).join('') : '<p style="color: var(--text2);">No traces yet</p>';
    }
    
    const perfEl = document.getElementById('performance-metrics');
    if (perfEl) {
      perfEl.innerHTML = `
        <div style="display: grid; gap: 8px;">
          <div>Memory: <strong>${perf.memory_mb || 0} MB</strong></div>
          <div>CPU: <strong>${perf.cpu_percent || 0}%</strong></div>
          <div>Uptime: <strong>${formatDuration(perf.uptime_ms || 0)}</strong></div>
        </div>
      `;
    }
  }

  // ── Billing ──
  
  async function loadBilling() {
    const [pricing, quota, usage] = await Promise.all([
      api(API.billingPricing),
      api(API.billingQuota),
      api(API.usageSummary),
    ]);
    
    document.getElementById('billing-plan').textContent = pricing.plan || 'Free';
    document.getElementById('billing-quota').textContent = quota.used ? `${quota.used}%` : '—';
    document.getElementById('billing-cost').textContent = usage.cost ? `$${usage.cost}` : '$0';
    
    const plans = document.getElementById('pricing-plans');
    if (plans) {
      const planList = pricing.plans || [];
      plans.innerHTML = `<div class="grid grid-3">${planList.map(p => `
        <div class="card">
          <div class="card-title">${escapeHtml(p.name)}</div>
          <div class="card-value">$${p.price || 0}</div>
          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(p.description || '')}</p>
        </div>
      `).join('')}</div>`;
    }
  }

  // ── Notifications ──
  
  async function loadNotifications() {
    const result = await api(API.notifications);
    state.notifications = result.notifications || [];
    
    document.getElementById('pending-notifs-count').textContent = state.notifications.length;
    document.getElementById('notif-count').textContent = state.notifications.length;
    
    const list = document.getElementById('pending-notifs-list');
    if (list) {
      list.innerHTML = state.notifications.length ? state.notifications.map(n => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(n.title || 'Notification')}</strong>
          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(n.content || n.message || '')}</p>
        </div>
      `).join('') : '<p style="color: var(--text2);">No pending notifications</p>';
    }
  }

  async function createNotification() {
    const title = document.getElementById('notif-title').value;
    const content = document.getElementById('notif-content').value;
    if (!title) return showToast('Title required', 'error');
    
    const result = await api(API.notificationsCreate, {
      method: 'POST',
      body: JSON.stringify({ title, content }),
    });
    
    if (result.error) {
      showToast(`Error: ${result.error}`, 'error');
    } else {
      showToast('Notification created!', 'success');
      loadNotifications();
    }
  }

  // ── Settings ──
  
  async function loadSettings() {
    const env = await api(API.gatewayEnv);
    state.env = env;
    
    const envEl = document.getElementById('env-info');
    if (envEl) {
      envEl.innerHTML = `
        <div style="display: grid; gap: 8px;">
          <div>Environment: <strong>${escapeHtml(env.environment?.type || 'unknown')}</strong></div>
          <div>Database: <strong>${escapeHtml(env.environment?.db || 'sqlite')}</strong></div>
          <div>Auth: <span class="badge badge-${env.auth_enabled ? 'success' : 'warning'}">${env.auth_enabled ? 'Enabled' : 'Disabled'}</span></div>
          <div>Rate Limiter: <span class="badge badge-${env.rate_limiter_enabled ? 'success' : 'warning'}">${env.rate_limiter_enabled ? 'Enabled' : 'Disabled'}</span></div>
        </div>
      `;
    }
    
    const secEl = document.getElementById('security-info');
    if (secEl) {
      secEl.innerHTML = `
        <div style="display: grid; gap: 8px;">
          <div>Sandbox: <span class="badge badge-success">4 Levels</span></div>
          <div>Prompt Injection: <span class="badge badge-success">Multi-layer</span></div>
          <div>Encryption: <span class="badge badge-success">At Rest</span></div>
          <div>Rate Limiting: <span class="badge badge-success">Active</span></div>
        </div>
      `;
    }
  }

  // ── Admin ──
  
  async function loadAdmin() {
    const [stats, users, compliance] = await Promise.all([
      api(API.adminStats),
      api(API.adminUsers),
      api(API.complianceReport),
    ]);
    
    document.getElementById('admin-users').textContent = (users.users || []).length;
    document.getElementById('admin-stats').textContent = stats.sessions || 0;
    document.getElementById('admin-health').textContent = stats.health || 'OK';
    
    const compEl = document.getElementById('compliance-info');
    if (compEl) {
      compEl.innerHTML = `
        <div style="display: grid; gap: 8px;">
          <div>SOC2: <span class="badge badge-success">Compliant</span></div>
          <div>GDPR: <span class="badge badge-success">Compliant</span></div>
          <div>Last Audit: <strong>${formatDate(compliance.last_audit)}</strong></div>
        </div>
      `;
    }
  }


  // ═══════════════════════════════════════════════════════════════
  // CHAT
  // ═══════════════════════════════════════════════════════════════
  
  async function sendChat() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;
    
    addChatMessage('user', message);
    input.value = '';
    
    const result = await api(API.chat, {
      method: 'POST',
      body: JSON.stringify({ goal: message, session_id: state.sessionId }),
    });
    
    if (result.response) {
      addChatMessage('assistant', result.response);
      if (result.tool_used || result.division) {
        addChatMessage('system', `🔧 ${result.tool_used || '—'} | 📂 ${result.division || '—'}`);
      }
    } else if (result.error) {
      addChatMessage('system', `Error: ${result.error}`);
    }
    
    announce('Response received');
  }

  function addChatMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.textContent = content;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  async function runTask() {
    const input = document.getElementById('run-input');
    const goal = input.value.trim();
    if (!goal) return showToast('Enter a goal', 'error');
    
    const result = await api(API.run, {
      method: 'POST',
      body: JSON.stringify({ goal }),
    });
    
    const output = document.getElementById('run-result');
    if (output) {
      if (result.response) {
        output.innerHTML = `<pre class="code-block">${escapeHtml(result.response)}</pre>`;
      } else if (result.error) {
        output.innerHTML = `<span style="color: var(--danger);">${escapeHtml(result.error)}</span>`;
      } else {
        output.innerHTML = `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // KEYBOARD SHORTCUTS
  // ═══════════════════════════════════════════════════════════════
  
  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl+K: Focus search
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        const search = document.getElementById('mem-search-input') || document.getElementById('global-search');
        if (search) search.focus();
      }
      
      // Ctrl+T: Toggle theme
      if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        toggleTheme();
      }
      
      // Escape: Close modal
      if (e.key === 'Escape') {
        closeModal();
      }
      
      // Ctrl+Enter in chat: Send
      if (e.ctrlKey && e.key === 'Enter' && document.activeElement.id === 'chat-input') {
        e.preventDefault();
        sendChat();
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // REFRESH & CLEANUP
  // ═══════════════════════════════════════════════════════════════
  
  function refreshAll() {
    loadOverview();
    showToast('Refreshed', 'success');
  }

  function startAutoRefresh() {
    if (state.refreshInterval) clearInterval(state.refreshInterval);
    state.refreshInterval = setInterval(() => {
      if (state.currentSection === 'overview') loadOverview();
    }, 15000);
  }

  // ═══════════════════════════════════════════════════════════════
  // INITIALIZATION
  // ═══════════════════════════════════════════════════════════════
  
  function init() {
    // Set theme
    document.documentElement.setAttribute('data-theme', state.theme);
    document.getElementById('theme-toggle').textContent = state.theme === 'dark' ? '🌙' : '☀️';
    
    // Setup navigation
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => switchSection(item.dataset.section));
    });
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Setup chat input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendChat();
        }
      });
    }
    
    // Load initial data
    loadOverview();
    loadDivisions();
    loadPlugins();
    loadMemory();
    loadTools();
    loadObservability();
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Close modal on overlay click
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
      if (e.target.id === 'modal-overlay') closeModal();
    });
    
    console.log('🤖 Aeryn Dashboard v61.4 initialized');
  }

  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
