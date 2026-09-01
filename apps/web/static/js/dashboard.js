/**
 * Aeryn Dashboard v61.4 — Massive SPA
 * Comprehensive UI for all Aeryn modules
 */
(function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════
  
  const state = {
    currentSection: 'overview',
    sidebarCollapsed: false,
    sessionId: 'web_' + Date.now(),
    theme: localStorage.getItem('theme') || 'dark',
    refreshInterval: null,
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
    health: '/health',
    gatewayEnv: '/gateway/env',
    chat: '/chat',
    run: '/run',
    search: (q) => `/search?q=${encodeURIComponent(q)}`,
    divisions: '/divisions',
    executeDivision: (name) => `/divisions/${name}/execute`,
    workflows: '/workflows',
    workflow: (id) => `/workflows/${id}`,
    workflowStep: (id) => `/workflows/${id}/step`,
    plugins: '/plugins',
    pluginRun: '/plugins/run',
    pgStats: '/v1/postgres-memory/stats',
    pgRemember: '/v1/postgres-memory/remember',
    pgRecall: (q, limit) => `/v1/postgres-memory/recall?q=${encodeURIComponent(q)}&limit=${limit || 10}`,
    pgForget: (key) => `/v1/postgres-memory/forget?key=${encodeURIComponent(key)}`,
    tools: '/tools/list',
    toolsExecute: '/tools/execute',
    toolsDiscover: (q) => `/tools/discover?q=${encodeURIComponent(q)}`,
    agents: '/agents',
    agentTasks: '/agents/tasks',
    traces: '/observability/traces',
    traceStats: '/observability/stats',
    performance: '/performance/stats',
    workspaces: '/workspaces',
    planningTasks: '/planning/tasks',
    sharedTasks: '/shared/tasks',
    sharedReminders: '/shared/reminders',
    billingPricing: '/billing/pricing',
    billingQuota: '/billing/quota',
    notifications: '/notifications/pending',
    notificationsCreate: '/notifications/create',
    adminStats: '/admin/stats',
    adminUsers: '/admin/users',
    selfImprovementStats: '/self-improvement/stats',
    selfImprovementAdapt: '/self-improvement/adapt',
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

  // ═══════════════════════════════════════════════════════════════
  // NAVIGATION
  // ═══════════════════════════════════════════════════════════════
  
  function switchSection(sectionName) {
    state.currentSection = sectionName;
    
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.section === sectionName);
    });
    
    document.querySelectorAll('.page-section').forEach(section => {
      section.classList.toggle('active', section.id === `section-${sectionName}`);
    });
    
    const titles = {
      overview: 'Dashboard',
      analytics: 'Analytics',
      activity: 'Activity',
      chat: 'Chat',
      divisions: 'Cognitive Divisions',
      agents: 'Agents',
      memory: 'Memory',
      projects: 'Projects',
      workflows: 'Workflows',
      workspaces: 'Workspaces',
      plugins: 'Plugins',
      tools: 'Tools',
      integrations: 'Integrations',
      observability: 'Observability',
      billing: 'Billing',
      notifications: 'Notifications',
      settings: 'Settings',
    };
    
    const titleEl = document.getElementById('breadcrumb-current');
    if (titleEl) titleEl.textContent = titles[sectionName] || sectionName;
    
    loadSectionData(sectionName);
  }

  function toggleSidebar() {
    state.sidebarCollapsed = !state.sidebarCollapsed;
    document.getElementById('sidebar').classList.toggle('collapsed', state.sidebarCollapsed);
  }

  function toggleTheme() {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
  }

  function setTheme(theme) {
    state.theme = theme;
    if (theme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
      document.documentElement.setAttribute('data-theme', theme);
    }
    localStorage.setItem('theme', theme);
    document.getElementById('theme-icon').textContent = state.theme === 'dark' ? '🌙' : '☀️';
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
      analytics: loadAnalytics,
      chat: () => {},
      divisions: loadDivisions,
      agents: loadAgents,
      memory: loadMemory,
      projects: loadProjects,
      workflows: loadWorkflows,
      workspaces: loadWorkspaces,
      plugins: loadPlugins,
      tools: loadTools,
      integrations: () => {},
      observability: loadObservability,
      billing: loadBilling,
      notifications: loadNotifications,
      settings: loadSettings,
    };
    
    if (loaders[section]) loaders[section]();
  }

  // ── Overview ──
  
  async function loadOverview() {
    const health = await api(API.health);
    state.health = health;
    
    document.getElementById('stat-status').textContent = health.status || 'unknown';
    document.getElementById('stat-plugins').textContent = state.plugins.length || '—';
    
    const traceStats = await api(API.traceStats);
    document.getElementById('stat-traces').textContent = traceStats.total_traces || 0;
    
    const isHealthy = health.status === 'healthy';
    document.getElementById('status-dot').className = `status-dot ${isHealthy ? 'online' : ''}`;
    document.getElementById('status-text').textContent = isHealthy ? 'System Online' : 'Offline';
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
      showModal('Division Result', `<pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre>`);
    }
  }

  // ── Agents ──
  
  async function loadAgents() {
    const [agents, tasks] = await Promise.all([
      api(API.agents),
      api(API.agentTasks),
    ]);
    
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

  // ── Memory ──
  
  async function loadMemory() {
    const stats = await api(API.pgStats);
    
    document.getElementById('mem-sessions').textContent = stats.total_sessions || 0;
    document.getElementById('mem-total').textContent = stats.total_memories || 0;
    document.getElementById('mem-hot').textContent = stats.hot_memories || 0;
    document.getElementById('mem-warm').textContent = stats.warm_memories || 0;
    document.getElementById('mem-cold').textContent = stats.cold_memories || 0;
  }

  async function searchMemories() {
    const q = document.getElementById('mem-search-input').value;
    if (!q) return;
    
    const result = await api(API.pgRecall(q, 20));
    const list = document.getElementById('mem-search-results');
    if (!list) return;
    
    if (!result.results || result.results.length === 0) {
      list.innerHTML = '<p style="color: var(--text2);">No memories found</p>';
      return;
    }
    
    list.innerHTML = result.results.map(m => `
      <div style="padding: 12px; background: var(--bg3); border-radius: 6px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
          <strong>${escapeHtml(m.key)}</strong>
          <span class="badge badge-${m.tier === 'hot' ? 'danger' : m.tier === 'warm' ? 'warning' : 'info'}">${m.tier}</span>
        </div>
        <p style="font-size: 13px; color: var(--text2);">${escapeHtml(m.value?.substring(0, 150) || '')}</p>
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

  // ── Projects ──
  
  async function loadProjects() {
    const [planning, shared, reminders] = await Promise.all([
      api(API.planningTasks),
      api(API.sharedTasks),
      api(API.sharedReminders),
    ]);
    
    const planningList = document.getElementById('planning-list');
    if (planningList) {
      const tasks = planning.tasks || [];
      planningList.innerHTML = tasks.length ? tasks.map(t => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(t.name || 'Untitled')}</strong>
          <span class="badge badge-${t.status === 'completed' ? 'success' : 'warning'}" style="margin-left: 8px;">${t.status || 'pending'}</span>
        </div>
      `).join('') : '<p style="color: var(--text2);">No tasks</p>';
    }
    
    const sharedList = document.getElementById('shared-tasks-list');
    if (sharedList) {
      const tasks = shared.tasks || [];
      sharedList.innerHTML = tasks.length ? tasks.map(t => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(t.name || 'Untitled')}</strong>
          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(t.description || '')}</p>
        </div>
      `).join('') : '<p style="color: var(--text2);">No shared tasks</p>';
    }
    
    const remindersList = document.getElementById('reminders-list');
    if (remindersList) {
      const rems = reminders.reminders || [];
      remindersList.innerHTML = rems.length ? rems.map(r => `
        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
          <strong>${escapeHtml(r.text || 'Reminder')}</strong>
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
      list.innerHTML = '<p style="color: var(--text2);">No workflows yet</p>';
      return;
    }
    
    list.innerHTML = state.workflows.map(w => `
      <div style="padding: 12px; background: var(--bg3); border-radius: 6px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong>${escapeHtml(w.name || 'Untitled')}</strong>
          <span class="badge badge-${w.status === 'completed' ? 'success' : 'warning'}">${w.status || 'active'}</span>
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

  // ── Workspaces ──
  
  async function loadWorkspaces() {
    const result = await api(API.workspaces);
    state.workspaces = result.workspaces || [];
    
    const list = document.getElementById('workspaces-list');
    if (!list) return;
    
    if (!state.workspaces.length) {
      list.innerHTML = '<p style="color: var(--text2);">No workspaces yet</p>';
      return;
    }
    
    list.innerHTML = state.workspaces.map(ws => `
      <div style="padding: 12px; background: var(--bg3); border-radius: 6px; margin-bottom: 8px;">
        <strong>${escapeHtml(ws.name)}</strong>
        <p style="font-size: 12px; color: var(--text2);">${escapeHtml(ws.description || '')}</p>
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

  // ── Plugins ──
  
  async function loadPlugins() {
    const result = await api(API.plugins);
    state.plugins = result.tools || result.plugins || [];
    
    document.getElementById('installed-count').textContent = state.plugins.length;
    
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
        output.innerHTML = `<pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
      }
    }
  }

  // ── Tools ──
  
  async function loadTools() {
    const result = await api(API.toolsDiscover(''));
    state.tools = result.tools || [];
    
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
      output.innerHTML = `<pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
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
        <div style="padding: 12px; background: var(--bg3); border-radius: 6px; margin-bottom: 8px;">
          <div style="display: flex; justify-content: space-between;">
            <strong>${escapeHtml(t.id)}</strong>
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
  }

  // ── Notifications ──
  
  async function loadNotifications() {
    const result = await api(API.notifications);
    state.notifications = result.notifications || [];
    
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
  }

  function addChatMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    div.textContent = content;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  async function runQuickTask(goal) {
    addChatMessage('user', goal);
    
    const result = await api(API.run, {
      method: 'POST',
      body: JSON.stringify({ goal }),
    });
    
    if (result.response) {
      addChatMessage('assistant', result.response);
    } else if (result.error) {
      addChatMessage('system', `Error: ${result.error}`);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // INITIALIZATION
  // ═══════════════════════════════════════════════════════════════
  
  function init() {
    setTheme(state.theme);
    
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => switchSection(item.dataset.section));
    });
    
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendChat();
        }
      });
    }
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });
    
    loadOverview();
    loadDivisions();
    loadPlugins();
    loadMemory();
    loadTools();
    loadObservability();
    
    console.log('🤖 Aeryn Dashboard v61.4 initialized');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
