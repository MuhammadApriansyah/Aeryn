const Aeryn = {
    currentPage: 'dashboard',
    startTime: Date.now(),
    retryCount: 0,
    maxRetries: 3,

    init() {
        this.bindNavigation();
        this.checkHealth();
        this.startUptimeCounter();
        setInterval(() => this.checkHealth(), 30000);
    },

    bindNavigation() {
        document.querySelectorAll('.nav-links li').forEach(li => {
            li.addEventListener('click', (e) => {
                e.preventDefault();
                const page = li.dataset.page;
                this.showPage(page);
            });
        });
    },

    showPage(pageName) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
        
        const page = document.getElementById(`page-${pageName}`);
        if (page) page.classList.add('active');
        
        const navLi = document.querySelector(`[data-page="${pageName}"]`);
        if (navLi) navLi.classList.add('active');
        
        this.currentPage = pageName;
        this.loadPageData(pageName);
    },

    loadPageData(page) {
        switch(page) {
            case 'workspaces': this.loadWorkspaces(); break;
            case 'plugins': this.loadPlugins(); break;
            case 'audit': this.loadAudit(); break;
        }
    },

    async checkHealth() {
        try {
            const res = await fetch('/api/py/health');
            if (!res.ok) throw new Error('Health check failed');
            const data = await res.json();
            
            const dot = document.getElementById('backend-dot');
            const text = document.getElementById('backend-text');
            const status = document.getElementById('stat-backend');
            
            if (dot) { dot.className = 'status-indicator online'; dot.style.background = '#00ff88'; }
            if (text) text.textContent = 'Online';
            if (status) { status.textContent = 'Online'; status.className = 'stat-value online'; }
            
            document.getElementById('stat-memory').textContent = `${data.memory_mb || '-'} MB`;
            document.getElementById('stat-version').textContent = data.version || '-';
            
            this.retryCount = 0;
        } catch (err) {
            this.retryCount++;
            const dot = document.getElementById('backend-dot');
            const text = document.getElementById('backend-text');
            const status = document.getElementById('stat-backend');
            
            if (dot) { dot.className = 'status-indicator'; dot.style.background = '#ff6464'; }
            if (text) text.textContent = this.retryCount >= this.maxRetries ? 'Offline' : 'Retrying...';
            if (status) { status.textContent = 'Offline'; status.className = 'stat-value'; status.style.color = '#ff6464'; }
            
            if (this.retryCount >= this.maxRetries) {
                this.showToast('Backend offline. Some features may be unavailable.', 'error');
            }
        }
    },

    startUptimeCounter() {
        setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const h = Math.floor(elapsed / 3600);
            const m = Math.floor((elapsed % 3600) / 60);
            const s = elapsed % 60;
            const el = document.getElementById('stat-uptime');
            if (el) el.textContent = `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
        }, 1000);
    },

    async loadWorkspaces() {
        const tbody = document.getElementById('workspaces-tbody');
        if (!tbody) return;
        tbody.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';
        
        try {
            // Simulated data - replace with actual API call when available
            const workspaces = [
                { name: 'Default', description: 'Default workspace', created_at: new Date().toLocaleDateString() }
            ];
            
            if (workspaces.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="empty-state">No workspaces found</td></tr>';
                return;
            }
            
            tbody.innerHTML = workspaces.map(ws => 
                `<tr><td>${ws.name}</td><td>${ws.description || '-'}</td><td>${ws.created_at || '-'}</td></tr>`
            ).join('');
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="3" class="empty-state">Error: ${err.message}</td></tr>`;
        }
    },

    async loadPlugins() {
        const tbody = document.getElementById('plugins-tbody');
        if (!tbody) return;
        tbody.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';
        
        try {
            const plugins = [
                { name: 'auth', version: '1.0.0', status: 'Active' },
                { name: 'rate-limiting', version: '1.0.0', status: 'Active' },
                { name: 'workspace', version: '1.0.0', status: 'Active' }
            ];
            
            tbody.innerHTML = plugins.map(p => 
                `<tr><td>${p.name}</td><td>${p.version}</td><td><span class="status-indicator online" style="display:inline-block;margin-right:5px"></span>${p.status}</td></tr>`
            ).join('');
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="3" class="empty-state">Error: ${err.message}</td></tr>`;
        }
    },

    async loadAudit() {
        const tbody = document.getElementById('audit-tbody');
        if (!tbody) return;
        tbody.innerHTML = '<tr><td colspan="4">Loading...</td></tr>';
        
        try {
            const logs = [
                { timestamp: new Date().toLocaleString(), user: 'admin', action: 'login', resource: 'system' },
                { timestamp: new Date().toLocaleString(), user: 'admin', action: 'view_dashboard', resource: 'dashboard' }
            ];
            
            tbody.innerHTML = logs.map(log => 
                `<tr><td>${log.timestamp}</td><td>${log.user}</td><td>${log.action}</td><td>${log.resource}</td></tr>`
            ).join('');
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="4" class="empty-state">Error: ${err.message}</td></tr>`;
        }
    },

    refresh() {
        this.checkHealth();
        this.loadPageData(this.currentPage);
        this.showToast('Refreshed!', 'success');
    },

    createProject() {
        this.showToast('Project wizard coming soon!', 'success');
    },

    createWorkspace() {
        const name = prompt('Workspace name:');
        if (!name) return;
        this.showToast(`Workspace "${name}" created!`, 'success');
    },

    chatKeypress(e) {
        if (e.key === 'Enter') this.sendChat();
    },

    sendChat() {
        const input = document.getElementById('chat-input');
        const messages = document.getElementById('chat-messages');
        if (!input || !messages || !input.value.trim()) return;
        
        const msg = input.value.trim();
        messages.innerHTML += `<div class="chat-message user">${msg}</div>`;
        messages.innerHTML += `<div class="chat-system">Thinking...</div>`;
        input.value = '';
        messages.scrollTop = messages.scrollHeight;
        
        setTimeout(() => {
            const replies = messages.querySelectorAll('.chat-system');
            const last = replies[replies.length - 1];
            if (last) last.textContent = `Aeryn: I received "${msg}" (backend integration coming soon)`;
        }, 500);
    },

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        
        setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
    }
};

document.addEventListener('DOMContentLoaded', () => Aeryn.init());
