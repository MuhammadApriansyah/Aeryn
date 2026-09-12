/**
 * sections.js — Loader konten modal per modul (memory/tools/agents/safety/
 * trace/eval/plugins/settings). Dipanggil app.js via window.AerynSection.load().
 *
 * Iterasi 1: tampilkan data dasar nyata dari endpoint API yang ada (bukan mock).
 * Vanilla (ES5), fetch API.
 */
(function () {
  'use strict';

  var BASE = '/v1';

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function loading() {
    return '<div class="modal-loading">Memuat…</div>';
  }

  function errorBox(msg) {
    var d = el('div', 'section-error');
    d.textContent = msg || 'Gagal memuat.';
    return d;
  }

  async function getJSON(url) {
    var res = await fetch(url);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  }

  // === Section loaders (mengembalikan DOM node) ===

  async function loadMemory(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '🧠 Memory'));

    // Search form
    var form = el('div', 'section-form');
    var input = el('input', 'section-input');
    input.type = 'text';
    input.placeholder = 'Query untuk cari di vault…';
    var btn = el('button', 'section-btn', 'Cari');
    var result = el('div', 'section-result', '');
    form.appendChild(input);
    form.appendChild(btn);
    box.appendChild(form);
    box.appendChild(result);

    async function doSearch() {
      var q = input.value.trim();
      if (!q) { result.textContent = 'Masukkan query dulu.'; return; }
      result.textContent = 'Mencari…';
      try {
        var r = await getJSON(BASE + '/vault/search?query=' + encodeURIComponent(q));
        var rows = r && r.results;
        result.innerHTML = '';
        if (Array.isArray(rows) && rows.length) {
          rows.forEach(function (m) {
            result.appendChild(el('div', 'section-row', typeof m === 'string' ? m : (m.content || JSON.stringify(m))));
          });
        } else {
          result.textContent = 'Tidak ada hasil untuk "' + q + '".';
        }
      } catch (e) {
        result.innerHTML = '';
        result.appendChild(errorBox('Search gagal: ' + e.message));
      }
    }
    btn.addEventListener('click', doSearch);
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') doSearch(); });

    // Entities list (di bawah form)
    var entTitle = el('div', 'section-subtitle', 'Entities');
    box.appendChild(entTitle);
    var entBox = el('div', 'section-stack');
    box.appendChild(entBox);
    try {
      var mem = await getJSON(BASE + '/memory/entities');
      var ents = mem && mem.entities;
      if (Array.isArray(ents) && ents.length) {
        ents.forEach(function (e) {
          entBox.appendChild(el('div', 'section-row', e.name || e.id || JSON.stringify(e)));
        });
      } else {
        entBox.appendChild(el('div', 'section-row', '(belum ada entity)'));
      }
    } catch (e) {
      entBox.appendChild(errorBox('Entities gagal: ' + e.message));
    }

    return box;
  }

  async function loadTools(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '🔧 Tools — Eksekusi Cepat'));

    // Hint param per tool bawaan (petunjuk UX, bukan schema backend).
    var HINTS = {
      fs_read:   { desc: 'Baca file',                   hint: '{"path": "/etc/hostname"}' },
      fs_write:  { desc: 'Tulis file',                  hint: '{"path": "/tmp/a.txt", "content": "halo"}' },
      fs_list:   { desc: 'List direktori',              hint: '{"path": "/tmp"}' },
      terminal:  { desc: 'Jalankan perintah shell',     hint: '{"command": "ls -la"}' },
      web_search:{ desc: 'Cari di web',                 hint: '{"query": "berita terbaru"}' },
      web_fetch: { desc: 'Baca halaman web',            hint: '{"url": "https://example.com"}' },
      python:    { desc: 'Eksekusi kode Python',        hint: '{"code": "print(2+2)"}' },
    };

    var form = el('div', 'section-form-stack');
    var row = el('div', 'section-form');
    var toolSel = el('select', 'section-select');
    var ph = el('option', null, 'Pilih tool…'); ph.value = ''; toolSel.appendChild(ph);
    var runBtn = el('button', 'section-btn', 'Run');
    row.appendChild(toolSel); row.appendChild(runBtn);

    var hintBox = el('div', 'section-hint', '');
    var paramsInput = el('textarea', 'section-textarea', '');
    paramsInput.placeholder = 'Params JSON';
    paramsInput.rows = 2;
    var execResult = el('div', 'section-result', '');

    form.appendChild(row);
    form.appendChild(hintBox);
    form.appendChild(paramsInput);
    box.appendChild(form);
    box.appendChild(execResult);

    // Load tool list ke dropdown. Saat pilih → tampilkan hint + desc.
    try {
      var tools = await getJSON(BASE + '/tools/list');
      var list = tools && (tools.tools || tools.result || tools);
      if (Array.isArray(list)) {
        list.forEach(function (t) {
          var name = typeof t === 'string' ? t : (t.name || t.id || String(t));
          var o = el('option', null, name + (HINTS[name] ? ' — ' + HINTS[name].desc : ''));
          o.value = name; toolSel.appendChild(o);
        });
      }
    } catch (e) { box.appendChild(errorBox('Gagal load tool list: ' + e.message)); }

    function showHint() {
      var name = toolSel.value;
      var h = HINTS[name];
      hintBox.textContent = h ? (h.desc + ' — contoh params:  ' + h.hint) : '';
      if (h && h.hint && !paramsInput.value) paramsInput.value = h.hint;
    }
    toolSel.addEventListener('change', showHint);

    async function doExecute() {
      var tool = toolSel.value;
      if (!tool) { execResult.textContent = 'Pilih tool dulu.'; return; }
      var params = {};
      try { params = paramsInput.value.trim() ? JSON.parse(paramsInput.value) : {}; }
      catch (e) { execResult.textContent = 'Invalid JSON params: ' + e.message; return; }
      execResult.textContent = 'Menjalankan ' + tool + '…';
      try {
        var r = await fetch(BASE + '/tools/execute?tool=' + encodeURIComponent(tool), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params),
        });
        var data = await r.json();
        execResult.innerHTML = '';
        var out = el('pre', 'section-output');
        out.textContent = JSON.stringify(data, null, 2);
        execResult.appendChild(out);
      } catch (e) {
        execResult.innerHTML = '';
        execResult.appendChild(errorBox('Execute gagal: ' + e.message));
      }
    }
    runBtn.addEventListener('click', doExecute);
    return box;
  }

  async function loadSkills(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '🧩 Skills — Terpasang'));
    try {
      var r = await getJSON(BASE + '/skills');
      var skills = r && (r.skills || r.result);
      if (Array.isArray(skills) && skills.length) {
        skills.forEach(function (s) {
          box.appendChild(el('div', 'section-row', typeof s === 'string' ? s : (s.name || s.id || JSON.stringify(s))));
        });
      } else {
        box.appendChild(el('div', 'section-row', 'Belum ada skill terpasang / API kosong.'));
      }
    } catch (e) {
      box.appendChild(errorBox('Skills gagal: ' + e.message));
    }
    return box;
  }

  async function loadAgents(container) {
    var box = el('div', 'section-stack');
    try {
      var divs = await getJSON(BASE + '/divisions');
      var title = el('div', 'section-title', '🤖 Agents — Divisions');
      box.appendChild(title);
      var arr = divs && (divs.divisions || divs.result || (Array.isArray(divs) ? divs : null));
      if (Array.isArray(arr)) {
        arr.forEach(function (d) {
          var name = typeof d === 'string' ? d : (d.name || d.id || d.division || JSON.stringify(d));
          box.appendChild(el('div', 'section-row', name));
        });
      } else {
        box.appendChild(el('div', 'section-row', JSON.stringify(divs)));
      }
    } catch (e) {
      box.appendChild(errorBox('Divisions endpoint gagal: ' + e.message));
    }
    return box;
  }

  async function loadSafety(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '🛡 Safety — Status'));
    try {
      var h = await getJSON(BASE + '/safety/health');
      box.appendChild(el('div', 'section-row', JSON.stringify(h)));
    } catch (e) {
      // fallback: guardrail status
      try {
        var g = await getJSON(BASE + '/safety/guardrail/status');
        box.appendChild(el('div', 'section-row', JSON.stringify(g)));
      } catch (e2) {
        box.appendChild(errorBox('Safety endpoint gagal: ' + e.message));
      }
    }
    return box;
  }

  async function loadTrace(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '📈 Trace — Spans (OTel GenAI)'));
    try {
      var t = await getJSON(BASE + '/tracing/traces');
      box.appendChild(el('div', 'section-row', JSON.stringify(t).slice(0, 500)));
    } catch (e) {
      box.appendChild(errorBox('Trace endpoint gagal: ' + e.message));
    }
    return box;
  }

  async function loadEval(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '🏆 Evaluation — Benchmarks'));
    try {
      var ev = await getJSON(BASE + '/eval/benchmarks');
      box.appendChild(el('div', 'section-row', JSON.stringify(ev).slice(0, 500)));
    } catch (e) {
      box.appendChild(errorBox('Eval endpoint gagal: ' + e.message));
    }
    return box;
  }

  async function loadPlugins(container) {
    var box = el('div', 'section-stack');
    try {
      var pl = await getJSON(BASE + '/plugins/installed');
      var title = el('div', 'section-title', '🧩 Plugins (terpasang)');
      box.appendChild(title);
      var arr = pl && (pl.plugins || pl.installed || (Array.isArray(pl) ? pl : null));
      if (Array.isArray(arr)) {
        arr.forEach(function (p) {
          var name = typeof p === 'string' ? p : (p.name || p.id || p.plugin_id || JSON.stringify(p));
          box.appendChild(el('div', 'section-row', name));
        });
      } else {
        box.appendChild(el('div', 'section-row', JSON.stringify(pl)));
      }
    } catch (e) {
      box.appendChild(errorBox('Plugins endpoint gagal: ' + e.message));
    }
    return box;
  }

  async function loadSettings(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '⚙ Settings — Provider & Model'));

    function save() {
      try {
        localStorage.setItem('aeryn.provider', provider.value);
        localStorage.setItem('aeryn.model', model.value);
      } catch (e) { /* ignore */ }
    }

    var provider = el('select', 'section-select');
    ['gemini', 'openai', 'anthropic', 'deepseek'].forEach(function (p) {
      var o = el('option', null, p); o.value = p; provider.appendChild(o);
    });
    var savedProvider = null, savedModel = null;
    try { savedProvider = localStorage.getItem('aeryn.provider'); savedModel = localStorage.getItem('aeryn.model'); } catch (e) {}
    if (savedProvider) provider.value = savedProvider;
    box.appendChild(labelRow('Provider', provider));

    var model = el('select', 'section-select');
    ['auto', 'gemini-3.5-flash-lite', 'gpt-4o', 'claude-sonnet-4', 'deepseek-chat'].forEach(function (m) {
      var o = el('option', null, m); o.value = m; model.appendChild(o);
    });
    if (savedModel) model.value = savedModel;
    box.appendChild(labelRow('Model', model));

    provider.addEventListener('change', save);
    model.addEventListener('change', save);

    // Test koneksi LLM — cek nyata via /v1/chat/stream.
    var testRow = el('div', 'section-form');
    var testBtn = el('button', 'section-btn', 'Test Koneksi');
    var testOut = el('div', 'section-hint', 'Preferensi tersimpan lokal. Test kirim ping ke LLM.');
    testRow.appendChild(testBtn);
    box.appendChild(testRow);
    box.appendChild(testOut);

    testBtn.addEventListener('click', async function () {
      testOut.textContent = 'Menguji koneksi LLM…';
      testBtn.disabled = true;
      try {
        var res = await fetch('/v1/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: 'ping', session_id: 'connectivity_test_' + Date.now() }),
        });
        var text = await res.text();
        var gotData = text.indexOf('"type"') !== -1 && (text.indexOf('"token"') !== -1 || text.indexOf('"done"') !== -1);
        testOut.textContent = gotData ? '✓ Koneksi LLM OK (stream berjalan).' : '⚠ Streaming kosong/tidak ada respons.';
      } catch (e) {
        testOut.textContent = '✗ Gagal: ' + e.message;
      } finally {
        testBtn.disabled = false;
      }
    });

    return box;
  }

  function labelRow(label, control) {
    var row = el('div', 'section-field');
    row.appendChild(el('label', 'section-label', label));
    row.appendChild(control);
    return row;
  }

  function settingsRow(k, v) {
    var row = el('div', 'section-row');
    row.appendChild(el('span', null, k + ': '));
    row.appendChild(el('strong', null, String(v)));
    return row;
  }

  async function loadSessions(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '💬 Sessions — Lanjutkan Percakapan'));
    try {
      var r = await getJSON(BASE + '/sessions');
      var sessions = r && r.sessions;
      if (Array.isArray(sessions) && sessions.length) {
        sessions.forEach(function (s) {
          var id = s.session_id;
          var row = el('div', 'session-row');
          var info = el('div', 'session-info');
          var title = s.title || ('Session ' + String(id).slice(0, 10));
          info.appendChild(el('div', 'session-name', title));
          info.appendChild(el('div', 'session-meta', 'Msg: ' + s.message_count));
          var actions = el('div', 'session-actions');
          var resume = el('button', 'session-btn', 'Lanjutkan');
          resume.addEventListener('click', function () {
            if (window.AerynApp && window.AerynApp.openSession) window.AerynApp.openSession(id);
          });
          var del = el('button', 'session-btn danger', 'Hapus');
          del.addEventListener('click', async function () {
            try {
              await fetch(BASE + '/sessions/' + encodeURIComponent(id), { method: 'DELETE' });
              row.remove();
            } catch (e2) {
              row.appendChild(errorBox('Gagal hapus: ' + e2.message));
            }
          });
          actions.appendChild(resume);
          actions.appendChild(del);
          row.appendChild(info);
          row.appendChild(actions);
          box.appendChild(row);
        });
      } else {
        box.appendChild(el('div', 'section-row', 'Belum ada sesi. Mulai chat dulu.'));
      }
    } catch (e) {
      box.appendChild(errorBox('Sessions gagal: ' + e.message));
    }
    return box;
  }

  async function loadHealth(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '🩺 Health — Status Sistem'));
    try {
      var h = await getJSON('/health');
      Object.keys(h).forEach(function (k) { box.appendChild(settingsRow(k, h[k])); });
    } catch (e) {
      box.appendChild(errorBox('Health gagal: ' + e.message));
    }
    return box;
  }

  async function loadTasks(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '📋 Tasks — Antrean Berjalan'));
    try {
      var t = await getJSON(BASE + '/queue/tasks');
      box.appendChild(el('div', 'section-row', JSON.stringify(t, null, 2)));
    } catch (e) {
      box.appendChild(errorBox('Tasks gagal: ' + e.message));
    }
    return box;
  }

  // === Registry & entry ===
  var LOADERS = {
    health: loadHealth,
    memory: loadMemory,
    tools: loadTools,
    agents: loadAgents,
    sessions: loadSessions,
    skills: loadSkills,
    tasks: loadTasks,
    safety: loadSafety,
    trace: loadTrace,
    eval: loadEval,
    plugins: loadPlugins,
    settings: loadSettings,
  };

  async function load(id, container) {
    container.innerHTML = loading();
    var fn = LOADERS[id];
    if (!fn) {
      container.innerHTML = '';
      container.appendChild(errorBox('Modul "' + id + '" belum diimplementasi.'));
      return;
    }
    try {
      var node = await fn(container);
      container.innerHTML = '';
      container.appendChild(node);
    } catch (e) {
      container.innerHTML = '';
      container.appendChild(errorBox('Error: ' + e.message));
    }
  }

  window.AerynSection = { load: load };
})();