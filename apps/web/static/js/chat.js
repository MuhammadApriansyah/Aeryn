/**
 * Aeryn Chat — Frontend JavaScript
 * Handles sessions, messages, streaming, settings
 */

(function() {
  'use strict';

  // State
  const state = {
    sessionId: null,
    messages: [],
    streaming: false,
    sessions: [],
  };

  // DOM Elements
  const elements = {
    sessionsList: document.getElementById('sessionsList'),
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    chatEmpty: document.getElementById('chatEmpty'),
    chatTitle: document.getElementById('chatTitle'),
    newChatBtn: document.getElementById('newChatBtn'),
    settingsOverlay: document.getElementById('settingsOverlay'),
    settingsPanel: document.getElementById('settingsPanel'),
    settingsClose: document.getElementById('settingsClose'),
    providerSelect: document.getElementById('providerSelect'),
    modelSelect: document.getElementById('modelSelect'),
    systemPromptInput: document.getElementById('systemPromptInput'),
  };

  // API
  const api = {
    async chat(message, sessionId) {
      const res = await fetch('/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId }),
      });
      return res.json();
    },

    async chatStream(message, sessionId, onChunk) {
      const res = await fetch('/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId }),
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') return;
            try { onChunk(JSON.parse(data)); } catch {}
          }
        }
      }
    },

    async getSessions() {
      const res = await fetch('/v1/sessions');
      return res.json();
    },

    async getSessionHistory(sessionId) {
      const res = await fetch(`/v1/sessions/${sessionId}/history`);
      return res.json();
    },
  };

  // UI Functions
  function renderSessions() {
    elements.sessionsList.innerHTML = '';
    state.sessions.forEach(session => {
      const div = document.createElement('div');
      div.className = 'session-item' + (session.session_id === state.sessionId ? ' active' : '');
      div.textContent = session.session_id === 'default' ? 'New Chat' : `Session ${session.session_id.slice(0, 8)}`;
      div.onclick = () => loadSession(session.session_id);
      elements.sessionsList.appendChild(div);
    });
  }

  function renderMessages() {
    if (state.messages.length === 0) {
      elements.chatEmpty.style.display = 'flex';
      elements.chatMessages.innerHTML = '';
      elements.chatMessages.appendChild(elements.chatEmpty);
      return;
    }

    elements.chatEmpty.style.display = 'none';
    elements.chatMessages.innerHTML = '';

    state.messages.forEach(msg => {
      const div = document.createElement('div');
      div.className = `message ${msg.role}`;

      const avatar = document.createElement('div');
      avatar.className = 'message-avatar';
      avatar.textContent = msg.role === 'user' ? 'U' : '✦';

      const content = document.createElement('div');
      content.className = 'message-content';

      const role = document.createElement('div');
      role.className = 'message-role';
      role.textContent = msg.role === 'user' ? 'You' : 'Aeryn';

      const text = document.createElement('div');
      text.className = 'message-text';
      text.textContent = msg.content || '';

      content.appendChild(role);
      content.appendChild(text);
      div.appendChild(avatar);
      div.appendChild(content);
      elements.chatMessages.appendChild(div);
    });

    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  function addToolCall(toolName, args) {
    const div = document.createElement('div');
    div.className = 'tool-call';
    div.innerHTML = `<div class="tool-call-header">⚡ ${toolName}</div><div class="tool-call-args">${JSON.stringify(args)}</div>`;
    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  function addToolResult(toolName, result) {
    const div = document.createElement('div');
    div.className = 'tool-result';
    div.textContent = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  function addStreamingIndicator() {
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'streamingMessage';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '✦';

    const content = document.createElement('div');
    content.className = 'streaming-indicator';
    content.innerHTML = '<div class="streaming-dot"></div><div class="streaming-dot"></div><div class="streaming-dot"></div>';

    div.appendChild(avatar);
    div.appendChild(content);
    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  function removeStreamingIndicator() {
    const el = document.getElementById('streamingMessage');
    if (el) el.remove();
  }

  // Actions
  async function loadSession(sessionId) {
    state.sessionId = sessionId;
    const history = await api.getSessionHistory(sessionId);
    state.messages = history.history || [];
    renderMessages();
    renderSessions();
  }

  async function newChat() {
    state.sessionId = 'session_' + Date.now();
    state.messages = [];
    elements.chatTitle.textContent = 'New Conversation';
    renderMessages();
    renderSessions();
  }

  async function sendMessage() {
    const text = elements.chatInput.value.trim();
    if (!text || state.streaming) return;

    if (!state.sessionId) {
      state.sessionId = 'session_' + Date.now();
    }

    // Add user message
    state.messages.push({ role: 'user', content: text });
    renderMessages();

    elements.chatInput.value = '';
    state.streaming = true;
    elements.sendBtn.disabled = true;
    addStreamingIndicator();

    let assistantContent = '';

    try {
      await api.chatStream(text, state.sessionId, (chunk) => {
        if (chunk.type === 'tool_calls') {
          chunk.tool_calls.forEach(tc => {
            addToolCall(tc.function.name, tc.function.arguments);
          });
        } else if (chunk.type === 'tool_call') {
          addToolCall(chunk.tool, chunk.args);
        } else if (chunk.type === 'tool_result') {
          addToolResult(chunk.tool, chunk.result);
        } else if (chunk.type === 'message') {
          assistantContent = chunk.content || '';
        }
      });
    } catch (e) {
      assistantContent = 'Error: ' + e.message;
    }

    removeStreamingIndicator();

    if (assistantContent) {
      state.messages.push({ role: 'assistant', content: assistantContent });
    }

    state.streaming = false;
    elements.sendBtn.disabled = false;
    renderMessages();
    renderSessions();
  }

  // Event Listeners
  elements.sendBtn.addEventListener('click', sendMessage);

  elements.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  elements.newChatBtn.addEventListener('click', newChat);

  elements.settingsOverlay.addEventListener('click', () => {
    elements.settingsPanel.classList.remove('open');
    elements.settingsOverlay.classList.remove('open');
  });

  elements.settingsClose.addEventListener('click', () => {
    elements.settingsPanel.classList.remove('open');
    elements.settingsOverlay.classList.remove('open');
  });

  // Initialize
  async function init() {
    state.sessionId = 'default';
    renderSessions();
    renderMessages();
  }

  init();
})();
