1|/**
2| * Aeryn Dashboard v61.4 — Massive SPA
3| * Comprehensive UI for all Aeryn modules with WCAG 2.1 AA accessibility
4| */
5|(function() {
6|  'use strict';
7|
8|  // ═══════════════════════════════════════════════════════════════
9|  // STATE
10|  // ═══════════════════════════════════════════════════════════════
11|  
12|  const state = {
13|    currentSection: 'overview',
14|    sidebarCollapsed: false,
15|    sidebarMobileOpen: false,
16|    sessionId: 'web_' + Date.now(),
17|    theme: localStorage.getItem('theme') || 'dark',
18|    refreshInterval: null,
19|    ws: null,
20|    traces: [],
21|    workflows: [],
22|    tools: [],
23|    divisions: {},
24|    plugins: [],
25|    memories: [],
26|    workspaces: [],
27|    notifications: [],
28|    health: null,
29|    env: null,
30|  };
31|
32|  const API = {
33|    // Core
34|    health: '/health',
35|    gatewayEnv: '/gateway/env',
36|    
37|    // Chat & Execution
38|    chat: '/chat',
39|    run: '/run',
40|    search: (q) => `/search?q=${encodeURIComponent(q)}`,
41|    compile: '/compile',
42|    digest: '/digest',
43|    
44|    // Divisions & Workflows
45|    divisions: '/divisions',
46|    executeDivision: (name) => `/divisions/${name}/execute`,
47|    workflows: '/workflows',
48|    workflow: (id) => `/workflows/${id}`,
49|    workflowStep: (id) => `/workflows/${id}/step`,
50|    workflowApprove: (id) => `/workflows/${id}/approve`,
51|    
52|    // Plugins
53|    plugins: '/plugins',
54|    pluginRun: '/plugins/run',
55|    pluginDiscover: (q) => `/plugins/discover?q=${encodeURIComponent(q)}`,
56|    
57|    // Memory (PostgreSQL)
58|    pgStats: '/v1/postgres-memory/stats',
59|    pgRemember: '/v1/postgres-memory/remember',
60|    pgRecall: (q, limit) => `/v1/postgres-memory/recall?q=${encodeURIComponent(q)}&limit=${limit || 10}`,
61|    pgSessions: (q, limit) => `/v1/postgres-memory/sessions?q=${encodeURIComponent(q)}&limit=${limit || 5}`,
62|    pgForget: (key) => `/v1/postgres-memory/forget?key=${encodeURIComponent(key)}`,
63|    pgIndex: '/v1/postgres-memory/index',
64|    
65|    // Memory (Vault)
66|    memoryRecall: (q) => `/memory/recall?q=${encodeURIComponent(q)}`,
67|    vaultSearch: (q) => `/vault/search?q=${encodeURIComponent(q)}`,
68|    vaultEntries: '/vault/entries',
69|    
70|    // Tools
71|    tools: '/tools/list',
72|    toolsExecute: '/tools/execute',
73|    toolsDiscover: (q) => `/tools/discover?q=${encodeURIComponent(q)}`,
74|    
75|    // Agents
76|    agents: '/agents',
77|    agentTasks: '/agents/tasks',
78|    
79|    // Observability
80|    traces: '/observability/traces',
81|    trace: (id) => `/observability/traces/${id}`,
82|    traceStats: '/observability/stats',
83|    performance: '/performance/stats',
84|    
85|    // Workspaces
86|    workspaces: '/workspaces',
87|    workspace: (id) => `/workspaces/${id}`,
88|    
89|    // Projects & Tasks
90|    planningTasks: '/planning/tasks',
91|    sharedTasks: '/shared/tasks',
92|    sharedReminders: '/shared/reminders',
93|    
94|    // Billing
95|    billingPricing: '/billing/pricing',
96|    billingQuota: '/billing/quota',
97|    usageSummary: '/usage/summary',
98|    
99|    // Notifications
100|    notifications: '/notifications/pending',
101|    notificationsCreate: '/notifications/create',
102|    
103|    // Admin
104|    adminStats: '/admin/stats',
105|    adminUsers: '/admin/users',
106|    complianceReport: '/admin/compliance/report',
107|    
108|    // Self-Improvement
109|    selfImprovementStats: '/self-improvement/stats',
110|    selfImprovementAdapt: '/self-improvement/adapt',
111|    selfImprovementPatterns: '/self-improvement/patterns',
112|    
113|    // Experience Transfer
114|    experienceStatus: '/v1/experience/status',
115|    experienceLessons: '/v1/experience/lessons',
116|    experiencePreferences: '/v1/experience/preferences',
117|    experienceInitialize: '/v1/experience/initialize',
118|    
119|    // Messaging
120|    messagingStatus: '/v1/messaging/status',
121|    messagingSend: (platform) => `/v1/messaging/send/${platform}`,
122|  };
123|
124|  // ═══════════════════════════════════════════════════════════════
125|  // UTILITIES
126|  // ═══════════════════════════════════════════════════════════════
127|  
128|  async function api(url, options = {}) {
129|    try {
130|      const response = await fetch(url, {
131|        headers: { 'Content-Type': 'application/json' },
132|        ...options,
133|      });
134|      return await response.json();
135|    } catch (err) {
136|      console.error(`API Error [${url}]:`, err);
137|      return { error: err.message };
138|    }
139|  }
140|
141|  function showToast(message, type = 'info') {
142|    const container = document.getElementById('toast-container');
143|    const toast = document.createElement('div');
144|    toast.className = `toast toast-${type}`;
145|    toast.textContent = message;
146|    toast.setAttribute('role', 'alert');
147|    container.appendChild(toast);
148|    setTimeout(() => toast.remove(), 3000);
149|  }
150|
151|  function announce(message) {
152|    const announcer = document.createElement('div');
153|    announcer.setAttribute('role', 'status');
154|    announcer.setAttribute('aria-live', 'polite');
155|    announcer.className = 'sr-only';
156|    announcer.textContent = message;
157|    document.body.appendChild(announcer);
158|    setTimeout(() => announcer.remove(), 1000);
159|  }
160|
161|  function escapeHtml(str) {
162|    if (!str) return '';
163|    const div = document.createElement('div');
164|    div.textContent = str;
165|    return div.innerHTML;
166|  }
167|
168|  function formatDuration(ms) {
169|    if (!ms) return '—';
170|    if (ms < 1000) return `${ms}ms`;
171|    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
172|    return `${(ms / 60000).toFixed(1)}m`;
173|  }
174|
175|  function formatDate(dateStr) {
176|    if (!dateStr) return '—';
177|    try {
178|      return new Date(dateStr).toLocaleString('id-ID');
179|    } catch {
180|      return dateStr;
181|    }
182|  }
183|
184|  // ═══════════════════════════════════════════════════════════════
185|  // NAVIGATION
186|  // ═══════════════════════════════════════════════════════════════
187|  
188|  function switchSection(sectionName) {
189|    state.currentSection = sectionName;
190|    
191|    // Update nav items
192|    document.querySelectorAll('.nav-item').forEach(item => {
193|      item.classList.toggle('active', item.dataset.section === sectionName);
194|    });
195|    
196|    // Update sections
197|    document.querySelectorAll('.section').forEach(section => {
198|      section.classList.toggle('active', section.id === `section-${sectionName}`);
199|    });
200|    
201|    // Update header title
202|    const titles = {
203|      overview: 'Overview',
204|      chat: 'Chat',
205|      divisions: 'Cognitive Divisions',
206|      workspaces: 'Workspaces',
207|      projects: 'Projects',
208|      workflows: 'Workflows',
209|      plugins: 'Plugins',
210|      memory: 'Memory',
211|      tools: 'Tools',
212|      agents: 'Agents',
213|      observability: 'Observability',
214|      billing: 'Billing & Usage',
215|      notifications: 'Notifications',
216|      settings: 'Settings',
217|      admin: 'Admin',
218|    };
219|    document.getElementById('page-title').textContent = titles[sectionName] || sectionName;
220|    
221|    announce(`Switched to ${titles[sectionName] || sectionName}`);
222|    
223|    // Load section data
224|    loadSectionData(sectionName);
225|  }
226|
227|  function toggleSidebar() {
228|    state.sidebarCollapsed = !state.sidebarCollapsed;
229|    document.getElementById('sidebar').classList.toggle('collapsed', state.sidebarCollapsed);
230|  }
231|
232|  function toggleTheme() {
233|    const html = document.documentElement;
234|    const current = html.getAttribute('data-theme');
235|    const next = current === 'dark' ? 'light' : 'dark';
236|    html.setAttribute('data-theme', next);
237|    localStorage.setItem('theme', next);
238|    document.getElementById('theme-toggle').textContent = next === 'dark' ? '🌙' : '☀️';
239|  }
240|
241|  function showModal(title, content) {
242|    document.getElementById('modal-title').textContent = title;
243|    document.getElementById('modal-body').innerHTML = content;
244|    document.getElementById('modal-overlay').classList.add('active');
245|  }
246|
247|  function closeModal() {
248|    document.getElementById('modal-overlay').classList.remove('active');
249|  }
250|
251|  // ═══════════════════════════════════════════════════════════════
252|  // SECTION LOADERS
253|  // ═══════════════════════════════════════════════════════════════
254|  
255|  function loadSectionData(section) {
256|    const loaders = {
257|      overview: loadOverview,
258|      chat: () => {},
259|      divisions: loadDivisions,
260|      workspaces: loadWorkspaces,
261|      projects: loadProjects,
262|      workflows: loadWorkflows,
263|      plugins: loadPlugins,
264|      memory: loadMemory,
265|      tools: loadTools,
266|      agents: loadAgents,
267|      observability: loadObservability,
268|      billing: loadBilling,
269|      notifications: loadNotifications,
270|      settings: loadSettings,
271|      admin: loadAdmin,
272|    };
273|    
274|    if (loaders[section]) loaders[section]();
275|  }
276|
277|  // ── Overview ──
278|  
279|  async function loadOverview() {
280|    const health = await api(API.health);
281|    state.health = health;
282|    
283|    document.getElementById('ov-status').textContent = health.status || 'unknown';
284|    document.getElementById('ov-memory').textContent = (health.memory_mb || 0) + ' MB';
285|    document.getElementById('ov-plugins').textContent = state.plugins.length || '—';
286|    
287|    const traceStats = await api(API.traceStats);
288|    document.getElementById('ov-traces').textContent = traceStats.total_traces || 0;
289|    
290|    const healthDetails = document.getElementById('ov-health-details');
291|    if (healthDetails) {
292|      healthDetails.innerHTML = `
293|        <div style="display: grid; gap: 8px;">
294|          <div><span class="badge badge-${health.status === 'healthy' ? 'success' : 'danger'}">${health.status}</span></div>
295|          <div>Memory: <strong>${health.memory_mb} MB</strong></div>
296|          <div>Version: <strong>${health.version}</strong></div>
297|        </div>
298|      `;
299|    }
300|    
301|    // Update status dot
302|    const isHealthy = health.status === 'healthy';
303|    document.getElementById('status-dot').className = `status-dot ${isHealthy ? 'online' : ''}`;
304|    document.getElementById('status-text').textContent = isHealthy ? 'Online' : 'Offline';
305|  }
306|
307|  // ── Divisions ──
308|  
309|  async function loadDivisions() {
310|    const result = await api(API.divisions);
311|    state.divisions = result;
312|  }
313|
314|  async function executeDivision(name) {
315|    const goal = prompt(`Enter task for ${name} division:`);
316|    if (!goal) return;
317|    
318|    showToast(`Executing ${name}...`, 'info');
319|    const result = await api(API.executeDivision(name), {
320|      method: 'POST',
321|      body: JSON.stringify({ goal }),
322|    });
323|    
324|    if (result.error) {
325|      showToast(`Error: ${result.error}`, 'error');
326|    } else {
327|      showToast(`Completed: ${result.completed}/${result.tasks} tasks`, 'success');
328|      showModal('Division Result', `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`);
329|    }
330|  }
331|
332|  // ── Workspaces ──
333|  
334|  async function loadWorkspaces() {
335|    const result = await api(API.workspaces);
336|    state.workspaces = result.workspaces || [];
337|    
338|    const list = document.getElementById('workspaces-list');
339|    if (!list) return;
340|    
341|    if (!state.workspaces.length) {
342|      list.innerHTML = '<p style="color: var(--text2);">No workspaces yet. Create one to get started.</p>';
343|      return;
344|    }
345|    
346|    list.innerHTML = state.workspaces.map(ws => `
347|      <div class="card" style="margin-bottom: 8px;">
348|        <div style="display: flex; justify-content: space-between; align-items: center;">
349|          <div>
350|            <strong>${escapeHtml(ws.name)}</strong>
351|            <p style="color: var(--text2); font-size: 12px;">${escapeHtml(ws.description || '')}</p>
352|          </div>
353|          <span class="badge badge-${ws.status === 'active' ? 'success' : 'warning'}">${ws.status || 'unknown'}</span>
354|        </div>
355|      </div>
356|    `).join('');
357|  }
358|
359|  async function createWorkspace() {
360|    const name = document.getElementById('ws-name').value;
361|    const desc = document.getElementById('ws-desc').value;
362|    if (!name) return showToast('Name required', 'error');
363|    
364|    const result = await api(API.workspaces, {
365|      method: 'POST',
366|      body: JSON.stringify({ name, description: desc }),
367|    });
368|    
369|    if (result.error) {
370|      showToast(`Error: ${result.error}`, 'error');
371|    } else {
372|      showToast('Workspace created!', 'success');
373|      loadWorkspaces();
374|    }
375|  }
376|
377|  // ── Projects ──
378|  
379|  async function loadProjects() {
380|    const [planning, shared, reminders] = await Promise.all([
381|      api(API.planningTasks),
382|      api(API.sharedTasks),
383|      api(API.sharedReminders),
384|    ]);
385|    
386|    document.getElementById('planning-count').textContent = (planning.tasks || []).length;
387|    document.getElementById('shared-count').textContent = (shared.tasks || []).length;
388|    document.getElementById('reminders-count').textContent = (reminders.reminders || []).length;
389|    
390|    const planningList = document.getElementById('planning-list');
391|    if (planningList) {
392|      const tasks = planning.tasks || [];
393|      planningList.innerHTML = tasks.length ? tasks.map(t => `
394|        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
395|          <strong>${escapeHtml(t.name || t.title || 'Untitled')}</strong>
396|          <span class="badge badge-${t.status === 'completed' ? 'success' : 'warning'}" style="margin-left: 8px;">${t.status || 'pending'}</span>
397|        </div>
398|      `).join('') : '<p style="color: var(--text2);">No tasks</p>';
399|    }
400|    
401|    const sharedList = document.getElementById('shared-tasks-list');
402|    if (sharedList) {
403|      const tasks = shared.tasks || [];
404|      sharedList.innerHTML = tasks.length ? tasks.map(t => `
405|        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
406|          <strong>${escapeHtml(t.name || t.title || 'Untitled')}</strong>
407|          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(t.description || '')}</p>
408|        </div>
409|      `).join('') : '<p style="color: var(--text2);">No shared tasks</p>';
410|    }
411|    
412|    const remindersList = document.getElementById('reminders-list');
413|    if (remindersList) {
414|      const rems = reminders.reminders || [];
415|      remindersList.innerHTML = rems.length ? rems.map(r => `
416|        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
417|          <strong>${escapeHtml(r.text || r.title || 'Reminder')}</strong>
418|          <span style="font-size: 11px; color: var(--text2); margin-left: 8px;">${formatDate(r.due_at || r.created_at)}</span>
419|        </div>
420|      `).join('') : '<p style="color: var(--text2);">No reminders</p>';
421|    }
422|  }
423|
424|  // ── Workflows ──
425|  
426|  async function loadWorkflows() {
427|    const result = await api(API.workflows);
428|    state.workflows = result.workflows || [];
429|    
430|    const list = document.getElementById('workflows-list');
431|    if (!list) return;
432|    
433|    if (!state.workflows.length) {
434|      list.innerHTML = '<p style="color: var(--text2);">No workflows yet. Create one to get started.</p>';
435|      return;
436|    }
437|    
438|    list.innerHTML = state.workflows.map(w => `
439|      <div class="card" style="margin-bottom: 8px;">
440|        <div style="display: flex; justify-content: space-between; align-items: center;">
441|          <div>
442|            <strong>${escapeHtml(w.name || 'Untitled')}</strong>
443|            <span class="badge badge-${w.status === 'completed' ? 'success' : 'warning'}" style="margin-left: 8px;">${w.status || 'active'}</span>
444|          </div>
445|          <div style="display: flex; gap: 4px;">
446|            <button class="btn btn-sm btn-secondary" onclick="stepWorkflow('${w.id}')">Step</button>
447|            <button class="btn btn-sm btn-primary" onclick="viewWorkflow('${w.id}')">View</button>
448|          </div>
449|        </div>
450|      </div>
451|    `).join('');
452|  }
453|
454|  async function createWorkflow() {
455|    const name = document.getElementById('wf-name').value;
456|    const idea = document.getElementById('wf-idea').value;
457|    if (!name || !idea) return showToast('Name and idea required', 'error');
458|    
459|    const result = await api(API.workflows, {
460|      method: 'POST',
461|      body: JSON.stringify({ name, idea }),
462|    });
463|    
464|    if (result.error) {
465|      showToast(`Error: ${result.error}`, 'error');
466|    } else {
467|      showToast('Workflow created!', 'success');
468|      loadWorkflows();
469|    }
470|  }
471|
472|  async function stepWorkflow(id) {
473|    const result = await api(API.workflowStep(id), { method: 'POST' });
474|    showToast(`Step: ${result.status}`, 'info');
475|    loadWorkflows();
476|  }
477|
478|  async function viewWorkflow(id) {
479|    const result = await api(API.workflow(id));
480|    showModal('Workflow Details', `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`);
481|  }
482|
483|  // ── Plugins ──
484|  
485|  async function loadPlugins() {
486|    const result = await api(API.plugins);
487|    state.plugins = result.tools || result.plugins || [];
488|    
489|    document.getElementById('ov-plugins').textContent = state.plugins.length;
490|    document.getElementById('plugin-count').textContent = state.plugins.length;
491|    document.getElementById('installed-plugins-count').textContent = state.plugins.length;
492|    
493|    const list = document.getElementById('installed-plugins-list');
494|    if (list) {
495|      list.innerHTML = state.plugins.length ? state.plugins.map(p => `
496|        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
497|          <strong>${escapeHtml(p.name)}</strong>
498|          <span class="badge badge-info" style="margin-left: 8px;">v${p.version || '1.0'}</span>
499|          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(p.description || '')}</p>
500|        </div>
501|      `).join('') : '<p style="color: var(--text2);">No plugins installed</p>';
502|    }
503|  }
504|
505|  async function runPlugin(name) {
506|    let input, outputId;
507|    
508|    if (name === 'code-review') {
509|      input = document.getElementById('plugin-code-review-input').value;
510|      outputId = 'plugin-code-review-output';
511|    } else if (name === 'research-assistant') {
512|      input = document.getElementById('plugin-research-input').value;
513|      outputId = 'plugin-research-output';
514|    }
515|    
516|    if (!input) return showToast('Input required', 'error');
517|    
518|    const result = await api(API.pluginRun, {
519|      method: 'POST',
520|      body: JSON.stringify({ name, input }),
521|    });
522|    
523|    const output = document.getElementById(outputId);
524|    if (output) {
525|      if (result.error) {
526|        output.innerHTML = `<span style="color: var(--danger);">${escapeHtml(result.error)}</span>`;
527|      } else {
528|        output.innerHTML = `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
529|      }
530|    }
531|  }
532|
533|  // ── Memory ──
534|  
535|  async function loadMemory() {
536|    const stats = await api(API.pgStats);
537|    
538|    document.getElementById('mem-sessions').textContent = stats.total_sessions || 0;
539|    document.getElementById('mem-total').textContent = stats.total_memories || 0;
540|    document.getElementById('mem-hot').textContent = stats.hot_memories || 0;
541|    document.getElementById('mem-warm').textContent = stats.warm_memories || 0;
542|  }
543|
544|  async function searchMemories() {
545|    const q = document.getElementById('mem-search-input').value;
546|    if (!q) return;
547|    
548|    const result = await api(API.pgRecall(q, 20));
549|    const list = document.getElementById('mem-search-results');
550|    if (!list) return;
551|    
552|    if (!result.results || !result.results.length) {
553|      list.innerHTML = '<p style="color: var(--text2);">No memories found</p>';
554|      return;
555|    }
556|    
557|    list.innerHTML = result.results.map(m => `
558|      <div class="card" style="margin-bottom: 8px;">
559|        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
560|          <strong>${escapeHtml(m.key)}</strong>
561|          <span class="badge badge-${m.tier === 'hot' ? 'danger' : m.tier === 'warm' ? 'warning' : 'info'}">${m.tier}</span>
562|        </div>
563|        <p style="font-size: 13px; color: var(--text2);">${escapeHtml(m.value?.substring(0, 150) || '')}</p>
564|        <div style="font-size: 11px; color: var(--text2); margin-top: 4px;">
565|          Type: ${m.type || 'fact'} | Importance: ${(m.importance || 0).toFixed(2)} | Similarity: ${(m.similarity || 0).toFixed(2)}
566|        </div>
567|      </div>
568|    `).join('');
569|  }
570|
571|  async function storeMemory() {
572|    const key = document.getElementById('mem-key').value;
573|    const value = document.getElementById('mem-value').value;
574|    const type = document.getElementById('mem-type').value;
575|    
576|    if (!key || !value) return showToast('Key and value required', 'error');
577|    
578|    const result = await api(API.pgRemember, {
579|      method: 'POST',
580|      body: JSON.stringify({ key, value, type, importance: 0.7, skip_embedding: true }),
581|    });
582|    
583|    if (result.error) {
584|      showToast(`Error: ${result.error}`, 'error');
585|    } else {
586|      showToast('Memory stored!', 'success');
587|      loadMemory();
588|    }
589|  }
590|
591|  // ── Tools ──
592|  
593|  async function loadTools() {
594|    const result = await api(API.toolsDiscover(''));
595|    state.tools = result.tools || [];
596|    
597|    document.getElementById('tools-count').textContent = state.tools.length;
598|    
599|    const list = document.getElementById('tools-list');
600|    if (list) {
601|      list.innerHTML = state.tools.length ? state.tools.map(t => `
602|        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
603|          <strong>${escapeHtml(t.name)}</strong>
604|          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(t.description || '')}</p>
605|        </div>
606|      `).join('') : '<p style="color: var(--text2);">No tools available</p>';
607|    }
608|    
609|    const select = document.getElementById('tool-select');
610|    if (select) {
611|      select.innerHTML = state.tools.map(t => `<option value="${escapeHtml(t.name)}">${escapeHtml(t.name)}</option>`).join('');
612|    }
613|  }
614|
615|  async function executeTool() {
616|    const name = document.getElementById('tool-select').value;
617|    const inputStr = document.getElementById('tool-input').value;
618|    
619|    if (!name) return showToast('Select a tool', 'error');
620|    
621|    let input = {};
622|    try {
623|      if (inputStr) input = JSON.parse(inputStr);
624|    } catch {
625|      input = { query: inputStr };
626|    }
627|    
628|    const result = await api(API.toolsExecute, {
629|      method: 'POST',
630|      body: JSON.stringify({ name, ...input }),
631|    });
632|    
633|    const output = document.getElementById('tool-output');
634|    if (output) {
635|      output.innerHTML = `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
636|    }
637|  }
638|
639|  // ── Agents ──
640|  
641|  async function loadAgents() {
642|    const [agents, tasks] = await Promise.all([
643|      api(API.agents),
644|      api(API.agentTasks),
645|    ]);
646|    
647|    document.getElementById('agents-count').textContent = (agents.agents || []).length;
648|    document.getElementById('agent-tasks-count').textContent = (tasks.tasks || []).length;
649|    
650|    const agentsList = document.getElementById('agents-list');
651|    if (agentsList) {
652|      const agentList = agents.agents || [];
653|      agentsList.innerHTML = agentList.length ? agentList.map(a => `
654|        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
655|          <strong>${escapeHtml(a.name || 'Agent')}</strong>
656|          <span class="badge badge-${a.status === 'active' ? 'success' : 'warning'}" style="margin-left: 8px;">${a.status || 'idle'}</span>
657|        </div>
658|      `).join('') : '<p style="color: var(--text2);">No agents registered</p>';
659|    }
660|    
661|    const tasksList = document.getElementById('agent-tasks-list');
662|    if (tasksList) {
663|      const taskList = tasks.tasks || [];
664|      tasksList.innerHTML = taskList.length ? taskList.map(t => `
665|        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
666|          <strong>${escapeHtml(t.name || 'Task')}</strong>
667|          <span class="badge badge-${t.status === 'completed' ? 'success' : 'warning'}" style="margin-left: 8px;">${t.status || 'pending'}</span>
668|        </div>
669|      `).join('') : '<p style="color: var(--text2);">No tasks</p>';
670|    }
671|  }
672|
673|  // ── Observability ──
674|  
675|  async function loadObservability() {
676|    const [traceStats, traces, perf] = await Promise.all([
677|      api(API.traceStats),
678|      api(API.traces + '?limit=10'),
679|      api(API.performance),
680|    ]);
681|    
682|    document.getElementById('obs-traces').textContent = traceStats.total_traces || 0;
683|    document.getElementById('obs-spans').textContent = traceStats.total_spans || 0;
684|    document.getElementById('obs-avg').textContent = formatDuration(traceStats.avg_duration || 0);
685|    
686|    const tracesList = document.getElementById('traces-list');
687|    if (tracesList) {
688|      const traceList = traces.traces || [];
689|      tracesList.innerHTML = traceList.length ? traceList.map(t => `
690|        <div class="card" style="margin-bottom: 8px;">
691|          <div style="display: flex; justify-content: space-between; align-items: center;">
692|            <div>
693|              <strong>${escapeHtml(t.id)}</strong>
694|              <span style="font-size: 12px; color: var(--text2); margin-left: 8px;">${escapeHtml(t.session_id || 'default')}</span>
695|            </div>
696|            <span class="badge badge-info">${t.spans || 0} spans</span>
697|          </div>
698|        </div>
699|      `).join('') : '<p style="color: var(--text2);">No traces yet</p>';
700|    }
701|    
702|    const perfEl = document.getElementById('performance-metrics');
703|    if (perfEl) {
704|      perfEl.innerHTML = `
705|        <div style="display: grid; gap: 8px;">
706|          <div>Memory: <strong>${perf.memory_mb || 0} MB</strong></div>
707|          <div>CPU: <strong>${perf.cpu_percent || 0}%</strong></div>
708|          <div>Uptime: <strong>${formatDuration(perf.uptime_ms || 0)}</strong></div>
709|        </div>
710|      `;
711|    }
712|  }
713|
714|  // ── Billing ──
715|  
716|  async function loadBilling() {
717|    const [pricing, quota, usage] = await Promise.all([
718|      api(API.billingPricing),
719|      api(API.billingQuota),
720|      api(API.usageSummary),
721|    ]);
722|    
723|    document.getElementById('billing-plan').textContent = pricing.plan || 'Free';
724|    document.getElementById('billing-quota').textContent = quota.used ? `${quota.used}%` : '—';
725|    document.getElementById('billing-cost').textContent = usage.cost ? `$${usage.cost}` : '$0';
726|    
727|    const plans = document.getElementById('pricing-plans');
728|    if (plans) {
729|      const planList = pricing.plans || [];
730|      plans.innerHTML = `<div class="grid grid-3">${planList.map(p => `
731|        <div class="card">
732|          <div class="card-title">${escapeHtml(p.name)}</div>
733|          <div class="card-value">$${p.price || 0}</div>
734|          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(p.description || '')}</p>
735|        </div>
736|      `).join('')}</div>`;
737|    }
738|  }
739|
740|  // ── Notifications ──
741|  
742|  async function loadNotifications() {
743|    const result = await api(API.notifications);
744|    state.notifications = result.notifications || [];
745|    
746|    document.getElementById('pending-notifs-count').textContent = state.notifications.length;
747|    document.getElementById('notif-count').textContent = state.notifications.length;
748|    
749|    const list = document.getElementById('pending-notifs-list');
750|    if (list) {
751|      list.innerHTML = state.notifications.length ? state.notifications.map(n => `
752|        <div style="padding: 8px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px;">
753|          <strong>${escapeHtml(n.title || 'Notification')}</strong>
754|          <p style="font-size: 12px; color: var(--text2);">${escapeHtml(n.content || n.message || '')}</p>
755|        </div>
756|      `).join('') : '<p style="color: var(--text2);">No pending notifications</p>';
757|    }
758|  }
759|
760|  async function createNotification() {
761|    const title = document.getElementById('notif-title').value;
762|    const content = document.getElementById('notif-content').value;
763|    if (!title) return showToast('Title required', 'error');
764|    
765|    const result = await api(API.notificationsCreate, {
766|      method: 'POST',
767|      body: JSON.stringify({ title, content }),
768|    });
769|    
770|    if (result.error) {
771|      showToast(`Error: ${result.error}`, 'error');
772|    } else {
773|      showToast('Notification created!', 'success');
774|      loadNotifications();
775|    }
776|  }
777|
778|  // ── Settings ──
779|  
780|  async function loadSettings() {
781|    const env = await api(API.gatewayEnv);
782|    state.env = env;
783|    
784|    const envEl = document.getElementById('env-info');
785|    if (envEl) {
786|      envEl.innerHTML = `
787|        <div style="display: grid; gap: 8px;">
788|          <div>Environment: <strong>${escapeHtml(env.environment?.type || 'unknown')}</strong></div>
789|          <div>Database: <strong>${escapeHtml(env.environment?.db || 'sqlite')}</strong></div>
790|          <div>Auth: <span class="badge badge-${env.auth_enabled ? 'success' : 'warning'}">${env.auth_enabled ? 'Enabled' : 'Disabled'}</span></div>
791|          <div>Rate Limiter: <span class="badge badge-${env.rate_limiter_enabled ? 'success' : 'warning'}">${env.rate_limiter_enabled ? 'Enabled' : 'Disabled'}</span></div>
792|        </div>
793|      `;
794|    }
795|    
796|    const secEl = document.getElementById('security-info');
797|    if (secEl) {
798|      secEl.innerHTML = `
799|        <div style="display: grid; gap: 8px;">
800|          <div>Sandbox: <span class="badge badge-success">4 Levels</span></div>
801|          <div>Prompt Injection: <span class="badge badge-success">Multi-layer</span></div>
802|          <div>Encryption: <span class="badge badge-success">At Rest</span></div>
803|          <div>Rate Limiting: <span class="badge badge-success">Active</span></div>
804|        </div>
805|      `;
806|    }
807|  }
808|
809|  // ── Admin ──
810|  
811|  async function loadAdmin() {
812|    const [stats, users, compliance] = await Promise.all([
813|      api(API.adminStats),
814|      api(API.adminUsers),
815|      api(API.complianceReport),
816|    ]);
817|    
818|    document.getElementById('admin-users').textContent = (users.users || []).length;
819|    document.getElementById('admin-stats').textContent = stats.sessions || 0;
820|    document.getElementById('admin-health').textContent = stats.health || 'OK';
821|    
822|    const compEl = document.getElementById('compliance-info');
823|    if (compEl) {
824|      compEl.innerHTML = `
825|        <div style="display: grid; gap: 8px;">
826|          <div>SOC2: <span class="badge badge-success">Compliant</span></div>
827|          <div>GDPR: <span class="badge badge-success">Compliant</span></div>
828|          <div>Last Audit: <strong>${formatDate(compliance.last_audit)}</strong></div>
829|        </div>
830|      `;
831|    }
832|  }
833|1|
2|
3|  // ═══════════════════════════════════════════════════════════════
4|  // CHAT
5|  // ═══════════════════════════════════════════════════════════════
6|  
7|  async function sendChat() {
8|    const input = document.getElementById('chat-input');
9|    const message = input.value.trim();
10|    if (!message) return;
11|    
12|    addChatMessage('user', message);
13|    input.value = '';
14|    
15|    const result = await api(API.chat, {
16|      method: 'POST',
17|      body: JSON.stringify({ goal: message, session_id: state.sessionId }),
18|    });
19|    
20|    if (result.response) {
21|      addChatMessage('assistant', result.response);
22|      if (result.tool_used || result.division) {
23|        addChatMessage('system', `🔧 ${result.tool_used || '—'} | 📂 ${result.division || '—'}`);
24|      }
25|    } else if (result.error) {
26|      addChatMessage('system', `Error: ${result.error}`);
27|    }
28|    
29|    announce('Response received');
30|  }
31|
32|  function addChatMessage(role, content) {
33|    const container = document.getElementById('chat-messages');
34|    const div = document.createElement('div');
35|    div.className = `chat-message ${role}`;
36|    div.textContent = content;
37|    container.appendChild(div);
38|    container.scrollTop = container.scrollHeight;
39|  }
40|
41|  async function runTask() {
42|    const input = document.getElementById('run-input');
43|    const goal = input.value.trim();
44|    if (!goal) return showToast('Enter a goal', 'error');
45|    
46|    const result = await api(API.run, {
47|      method: 'POST',
48|      body: JSON.stringify({ goal }),
49|    });
50|    
51|    const output = document.getElementById('run-result');
52|    if (output) {
53|      if (result.response) {
54|        output.innerHTML = `<pre class="code-block">${escapeHtml(result.response)}</pre>`;
55|      } else if (result.error) {
56|        output.innerHTML = `<span style="color: var(--danger);">${escapeHtml(result.error)}</span>`;
57|      } else {
58|        output.innerHTML = `<pre class="code-block">${escapeHtml(JSON.stringify(result, null, 2))}</pre>`;
59|      }
60|    }
61|  }
62|
63|  // ═══════════════════════════════════════════════════════════════
64|  // KEYBOARD SHORTCUTS
65|  // ═══════════════════════════════════════════════════════════════
66|  
67|  function setupKeyboardShortcuts() {
68|    document.addEventListener('keydown', (e) => {
69|      // Ctrl+K: Focus search
70|      if (e.ctrlKey && e.key === 'k') {
71|        e.preventDefault();
72|        const search = document.getElementById('mem-search-input') || document.getElementById('global-search');
73|        if (search) search.focus();
74|      }
75|      
76|      // Ctrl+T: Toggle theme
77|      if (e.ctrlKey && e.key === 't') {
78|        e.preventDefault();
79|        toggleTheme();
80|      }
81|      
82|      // Escape: Close modal
83|      if (e.key === 'Escape') {
84|        closeModal();
85|      }
86|      
87|      // Ctrl+Enter in chat: Send
88|      if (e.ctrlKey && e.key === 'Enter' && document.activeElement.id === 'chat-input') {
89|        e.preventDefault();
90|        sendChat();
91|      }
92|    });
93|  }
94|
95|  // ═══════════════════════════════════════════════════════════════
96|  // REFRESH & CLEANUP
97|  // ═══════════════════════════════════════════════════════════════
98|  
99|  function refreshAll() {
100|    loadOverview();
101|    showToast('Refreshed', 'success');
102|  }
103|
104|  function startAutoRefresh() {
105|    if (state.refreshInterval) clearInterval(state.refreshInterval);
106|    state.refreshInterval = setInterval(() => {
107|      if (state.currentSection === 'overview') loadOverview();
108|    }, 15000);
109|  }
110|
111|  // ═══════════════════════════════════════════════════════════════
112|  // INITIALIZATION
113|  // ═══════════════════════════════════════════════════════════════
114|  
115|  function init() {
116|    // Set theme
117|    document.documentElement.setAttribute('data-theme', state.theme);
118|    document.getElementById('theme-toggle').textContent = state.theme === 'dark' ? '🌙' : '☀️';
119|    
120|    // Setup navigation
121|    document.querySelectorAll('.nav-item').forEach(item => {
122|      item.addEventListener('click', () => switchSection(item.dataset.section));
123|    });
124|    
125|    // Setup keyboard shortcuts
126|    setupKeyboardShortcuts();
127|    
128|    // Setup chat input
129|    const chatInput = document.getElementById('chat-input');
130|    if (chatInput) {
131|      chatInput.addEventListener('keydown', (e) => {
132|        if (e.key === 'Enter' && !e.shiftKey) {
133|          e.preventDefault();
134|          sendChat();
135|        }
136|      });
137|    }
138|    
139|    // Load initial data
140|    loadOverview();
141|    loadDivisions();
142|    loadPlugins();
143|    loadMemory();
144|    loadTools();
145|    loadObservability();
146|    
147|    // Start auto-refresh
148|    startAutoRefresh();
149|    
150|    // Close modal on overlay click
151|    document.getElementById('modal-overlay').addEventListener('click', (e) => {
152|      if (e.target.id === 'modal-overlay') closeModal();
153|    });
154|    
155|    console.log('🤖 Aeryn Dashboard v61.4 initialized');
156|  }
157|
158|  // Start when DOM is ready
159|  if (document.readyState === 'loading') {
160|    document.addEventListener('DOMContentLoaded', init);
161|  } else {
162|    init();
163|  }
164|})();
165|