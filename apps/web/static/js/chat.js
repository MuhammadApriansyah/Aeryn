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
    abortController: null,   // P5: untuk stop streaming
  };

  // DOM Elements
  const elements = {
    sessionsList: document.getElementById('sessionsList'),
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    chatEmpty: document.getElementById('chatEmpty'),
    chatTitle: document.getElementById('chatTitle'),
    chatStatusText: document.getElementById('chatStatusText'),
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

    async chatStream(message, sessionId, onChunk, signal) {
      const res = await fetch('/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId }),
        signal: signal || undefined,
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
      // Render markdown untuk pesan assistant (user tetap plain text).
      if (msg.role === 'assistant' && window.AerynMarkdown) {
        text.innerHTML = window.AerynMarkdown.renderMarkdown(msg.content || '', true);
      } else {
        text.textContent = msg.content || '';
      }

      content.appendChild(role);
      content.appendChild(text);
      div.appendChild(avatar);
      div.appendChild(content);
      elements.chatMessages.appendChild(div);
    });

    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  // P4: tool call card (expandable + status). Map tool_calls → card.
  const _activeToolCards = {}; // track card per tool untuk update status.

  function addToolCall(toolName, args) {
    const card = document.createElement('div');
    card.className = 'tool-card';

    const header = document.createElement('div');
    header.className = 'tool-card-header';
    header.setAttribute('role', 'button');
    header.setAttribute('tabindex', '0');
    header.setAttribute('aria-expanded', 'false');

    const chevron = document.createElement('span');
    chevron.className = 'tool-card-chevron';
    chevron.textContent = '▶';

    const name = document.createElement('span');
    name.className = 'tool-card-name';
    name.textContent = '⚡ ' + toolName;

    const status = document.createElement('span');
    status.className = 'tool-card-status running';
    status.textContent = 'running';

    header.appendChild(chevron);
    header.appendChild(name);
    header.appendChild(status);

    const body = document.createElement('div');
    body.className = 'tool-card-body';
    const argsLabel = document.createElement('div');
    argsLabel.className = 'tool-card-section-label';
    argsLabel.textContent = 'Arguments';
    const argsDiv = document.createElement('div');
    argsDiv.textContent = typeof args === 'string' ? args : JSON.stringify(args, null, 2);
    body.appendChild(argsLabel);
    body.appendChild(argsDiv);

    card.appendChild(header);
    card.appendChild(body);

    header.onclick = () => {
      const open = card.classList.toggle('open');
      header.setAttribute('aria-expanded', open ? 'true' : 'false');
    };
    header.onkeydown = (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); header.click(); }
    };

    elements.chatMessages.appendChild(card);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    _activeToolCards[toolName] = card;
  }

  function addToolResult(toolName, result) {
    const card = _activeToolCards[toolName];
    const resultText = typeof result === 'string' ? result : JSON.stringify(result, null, 2);

    if (card) {
      // Update card: status → success, tambah hasil ke body.
      const status = card.querySelector('.tool-card-status');
      if (status) { status.className = 'tool-card-status success'; status.textContent = 'done'; }
      const body = card.querySelector('.tool-card-body');
      const resLabel = document.createElement('div');
      resLabel.className = 'tool-card-section-label';
      resLabel.textContent = 'Result';
      const resDiv = document.createElement('div');
      resDiv.textContent = resultText;
      body.appendChild(resLabel);
      body.appendChild(resDiv);
      delete _activeToolCards[toolName];
    } else {
      // Fallback: tool result tanpa call card (mis. langkah terpisah).
      const div = document.createElement('div');
      div.className = 'tool-result';
      div.textContent = resultText;
      elements.chatMessages.appendChild(div);
    }
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
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

  // === P1: token-by-token streaming ===

  // Bridge dari SSE token delta → frame-batched DOM update (hindari layout thrash).
  // Buffer token per-frame via requestAnimationFrame (lihat AYDesign/Risearch 2026).
  function makeStreamBuffer(onBatch) {
    let buf = '';
    let rafId = null;
    const flush = () => {
      rafId = null;
      if (buf) { const t = buf; buf = ''; onBatch(t); }
    };
    return {
      push(token) {
        buf += token;
        if (rafId === null) rafId = requestAnimationFrame(flush);
      },
      flushNow() {
        if (rafId !== null) cancelAnimationFrame(rafId);
        flush();
      },
    };
  }

  // Buat elemen pesan assistant yang bisa di-append token secara live.
  function createStreamingMessage() {
    const div = document.createElement('div');
    div.className = 'message assistant';
    div.id = 'streamingMessage';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '✦';

    const content = document.createElement('div');
    content.className = 'message-content';

    const role = document.createElement('div');
    role.className = 'message-role';
    role.textContent = 'Aeryn';

    const text = document.createElement('div');
    text.className = 'message-text';

    const cursor = document.createElement('span');
    cursor.className = 'streaming-cursor';
    cursor.setAttribute('aria-hidden', 'true');

    content.appendChild(role);
    content.appendChild(text);
    div.appendChild(avatar);
    div.appendChild(content);

    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return { div, text, cursor };
  }

  function appendCursor(textEl, cursorEl) {
    if (!textEl.contains(cursorEl)) textEl.appendChild(cursorEl);
  }

  function removeCursor(textEl, cursorEl) {
    if (cursorEl.parentNode === textEl) textEl.removeChild(cursorEl);
  }

  function finishStreaming(textEl, cursorEl, fullContent) {
    // Hapus cursor, render markdown FINAL (final=true).
    removeCursor(textEl, cursorEl);
    textEl.innerHTML = window.AerynMarkdown
      ? window.AerynMarkdown.renderMarkdown(fullContent, true)
      : window.AerynMarkdown.escapeHtml(fullContent);
    const msgEl = document.getElementById('streamingMessage');
    if (msgEl) msgEl.id = '';  // jadikan pesan permanen
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }

  function setPhase(text) {
    if (elements.chatStatusText) elements.chatStatusText.textContent = text;
  }

  function resetPhase() {
    if (elements.chatStatusText) elements.chatStatusText.textContent = 'Online';
  }

  function stopStreaming() {
    if (state.abortController) {
      state.abortController.abort();
    }
  }

  async function sendMessage() {
    const text = elements.chatInput.value.trim();
    if (!text || state.streaming) return;

    if (!state.sessionId) {
      state.sessionId = 'session_' + Date.now();
    }

    // Tambah user message + render (pakai renderMessages penuh)
    state.messages.push({ role: 'user', content: text });
    renderMessages();

    elements.chatInput.value = '';
    state.streaming = true;
    // P3/P5: send button tetap aktif (jadi stop), jangan disabled.
    elements.sendBtn.classList.add('stop');
    setPhase('Riset…');

    // P5: AbortController agar bisa stop.
    state.abortController = new AbortController();
    const signal = state.abortController.signal;

    // Buat elemen streaming (menggantikan indikator 3 titik)
    const { text: textEl, cursor: cursorEl } = createStreamingMessage();

    // Buffer token delta per frame, render markdown parsial (P2).
    // fullContent di-akumulasi, lalu render parsial (final=false) tiap frame.
    const tokenBuffer = makeStreamBuffer((batch) => {
      const html = window.AerynMarkdown
        ? window.AerynMarkdown.renderMarkdown(fullContent, false)
        : batch;
      textEl.innerHTML = html;
      appendCursor(textEl, cursorEl);
      elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    });

    let fullContent = '';
    let errored = false;

    try {
      await api.chatStream(text, state.sessionId, (chunk) => {
        if (chunk.type === 'token') {
          // Token delta → buffer & append live
          fullContent += chunk.content;
          tokenBuffer.push(chunk.content);
          setPhase('Menulis…');
        } else if (chunk.type === 'message_complete') {
          // Marker konten lengkap (untuk sinkronisasi akhir)
          if (chunk.content) fullContent = chunk.content;
        } else if (chunk.type === 'tool_calls' && chunk.tool_calls) {
          chunk.tool_calls.forEach(tc => addToolCall(tc.function.name, tc.function.arguments));
          setPhase('Menjalankan tool…');
        } else if (chunk.type === 'tool_call') {
          addToolCall(chunk.tool, chunk.args);
          setPhase('Menjalankan tool…');
        } else if (chunk.type === 'tool_result') {
          addToolResult(chunk.tool, chunk.result);
          setPhase('Tool selesai…');
        } else if (chunk.type === 'error') {
          errored = true;
          if (!fullContent) fullContent = 'Error: ' + (chunk.error || 'unknown');
          setPhase('Error');
        }
        // 'done' — biarkan loop selesai, finalisasi di bawah
      }, signal);
    } catch (e) {
      if (e.name === 'AbortError') {
        // P5: user stop — tandai sebagai dihentikan, bukan error.
        fullContent = fullContent || '_(dihentikan oleh pengguna)_';
      } else {
        errored = true;
        fullContent = 'Error: ' + e.message;
      }
    }

    // Flush sisa token buffer
    tokenBuffer.flushNow();

    // Finalisasi: hapus cursor, set teks final, push ke state
    finishStreaming(textEl, cursorEl, fullContent || '(tidak ada respons)');

    if (fullContent) {
      state.messages.push({ role: 'assistant', content: fullContent });
    }

    state.streaming = false;
    elements.sendBtn.classList.remove('stop');
    state.abortController = null;
    resetPhase();
    renderSessions();
  }

  // Event Listeners
  elements.sendBtn.addEventListener('click', () => {
    if (state.streaming) {
      // P5: sedang streaming → jadikan sebagai tombol stop.
      stopStreaming();
    } else {
      sendMessage();
    }
  });

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
