

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
