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

    // Knowledge Graph (Bitemporal) — dari /v1/facts
    var kgTitle = el('div', 'section-subtitle', 'Knowledge Graph (bitemporal)');
    box.appendChild(kgTitle);
    var kgWrap = el('div', 'section-stack');
    box.appendChild(kgWrap);
    try {
      var ent = await getJSON(BASE + '/facts/entities');
      var kents = ent && ent.entities;
      if (Array.isArray(kents) && kents.length) {
        var chips = el('div', 'kg-chips');
        kents.forEach(function (x) {
          var c = el('button', 'kg-chip', x.entity + ' (' + x.facts + ')');
          c.addEventListener('click', async function () {
            kgWrap.innerHTML = '';
            var detail = el('div', 'section-stack');
            detail.appendChild(el('div', 'section-row', 'Fakta ' + x.entity + ':'));
            var cur = await getJSON(BASE + '/facts/' + encodeURIComponent(x.entity));
            (cur && cur.facts || []).forEach(function (f) {
              var r = el('div', 'kg-row', '▪ ' + f.predicate + ' = ' + f.fact + '  <span class="kg-src">' + (f.source || '') + '</span>');
              r.innerHTML = '▪ <b>' + f.predicate + '</b> = ' + f.fact + (f.source ? '  <span class="kg-src">[' + f.source + ']</span>' : '');
              detail.appendChild(r);
            });
            // tombol history
            var hbtn = el('button', 'section-btn', 'Riwayat (audit trail)');
            hbtn.addEventListener('click', async function () {
              var hist = await getJSON(BASE + '/facts/' + encodeURIComponent(x.entity) + '/history');
              var hbox = el('div', 'section-stack');
              (hist && hist.history || []).forEach(function (v) {
                var r = el('div', 'kg-row', v.ts);
                r.innerHTML = '↳ ' + v.tx_from + ' → <b>' + v.predicate + '</b> = ' + v.fact + (v.valid_to ? ' (valid s/d ' + v.valid_to + ')' : ' (berlaku)');
                hbox.appendChild(r);
              });
              detail.appendChild(hbox);
            });
            detail.appendChild(hbtn);
            kgWrap.appendChild(detail);
          });
          chips.appendChild(c);
        });
        kgWrap.appendChild(chips);
      } else {
        kgWrap.appendChild(el('div', 'section-row', 'Knowledge graph kosong.'));
      }
    } catch (e) {
      kgWrap.appendChild(errorBox('Knowledge graph gagal: ' + e.message));
    }

    // Vault manager — list entri + edit + hapus
    var vt = el('div', 'section-subtitle', 'Vault — Kelola Entri');
    box.appendChild(vt);
    var vbox = el('div', 'section-stack');
    box.appendChild(vbox);

    async function loadVault() {
      vbox.innerHTML = '';
      try {
        var r = await getJSON(BASE + '/memory/vault/entries?limit=300');
        var ents = r && r.results;
        if (Array.isArray(ents) && ents.length) {
          ents.forEach(function (e) {
            var rw = el('div', 'section-row', '');
            var lab = el('span', null, '');
            lab.innerHTML = '📄 <b>' + e.title + '</b> <span class="kg-src">(' + e.layer + ' · ' + (e.size || 0) + 'B)</span>';
            var act = el('div', 'session-actions');
            var ebtn = el('button', 'session-btn', 'Edit');
            var dbtn = el('button', 'session-btn danger', 'Hapus');
            ebtn.addEventListener('click', async function () {
              var body = prompt('Isi baru untuk "' + e.title + '":', 'isi entri');
              if (body === null) return;
              try {
                await fetch(BASE + '/memory/vault/' + encodeURIComponent(e.id), {
                  method: 'PUT', headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ body: body }) });
                loadVault();
              } catch (e2) { }
            });
            dbtn.addEventListener('click', async function () {
              if (!confirm('Hapus "' + e.title + '"?')) return;
              try {
                await fetch(BASE + '/memory/vault/' + encodeURIComponent(e.id), { method: 'DELETE' });
                loadVault();
              } catch (e2) { }
            });
            act.appendChild(ebtn); act.appendChild(dbtn);
            rw.appendChild(lab); rw.appendChild(act);
            vbox.appendChild(rw);
          });
        } else {
          vbox.appendChild(el('div', 'section-row', '(vault kosong)'));
        }
      } catch (e3) {
        vbox.appendChild(errorBox('Vault gagal: ' + e3.message));
      }
    }
    loadVault();

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

  async function loadLogs(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '📜 Console — Log Percakapan'));

    // Pilih sesi dari /api/monitoring/sessions.
    var sel = el('select', 'section-select');
    var ph = el('option', null, 'Pilih sesi…'); ph.value = ''; sel.appendChild(ph);
    box.appendChild(sel);

    var logBox = el('div', 'section-stack');
    logBox.appendChild(el('div', 'section-row', 'Pilih sesi untuk lihat log real-time (polling 4s).'));
    box.appendChild(logBox);

    try {
      var s = await getJSON('/api/monitoring/sessions');
      var sess = s && s.sessions;
      if (Array.isArray(sess)) {
        sess.forEach(function (x) {
          var o = el('option', null, x.session_id + ' (' + x.messages + ' msg)');
          o.value = x.session_id; sel.appendChild(o);
        });
      }
    } catch (e) { box.appendChild(errorBox('Gagal load sesi monitoring: ' + e.message)); }

    var timer = null;
    function formatTime(t) { return t ? String(t).slice(5, 19) : ''; }
    async function loadHistory(sessionId) {
      try {
        var h = await getJSON('/api/monitoring/history?session_id=' + encodeURIComponent(sessionId) + '&limit=50');
        var msgs = h && h.history;
        logBox.innerHTML = '';
        if (Array.isArray(msgs) && msgs.length) {
          msgs.forEach(function (m) {
            var row = el('div', 'log-row ' + (m.role === 'user' ? 'user' : 'agent'));
            var badge = el('span', 'log-badge', m.role === 'user' ? 'YOU' : 'AERYN');
            var content = el('span', 'log-text', m.content || '');
            var time = el('span', 'log-time', formatTime(m.created_at));
            row.appendChild(badge);
            row.appendChild(content);
            row.appendChild(time);
            logBox.appendChild(row);
          });
        } else {
          logBox.appendChild(el('div', 'section-row', 'Belum ada pesan di sesi ini.'));
        }
      } catch (e2) {
        logBox.innerHTML = '';
        logBox.appendChild(errorBox('Gagal load history: ' + e2.message));
      }
    }

    sel.addEventListener('change', function () {
      if (timer) window.clearInterval(timer);
      if (!sel.value) return;
      loadHistory(sel.value);
      timer = window.setInterval(function () { loadHistory(sel.value); }, 4000); // polling real-time
    });

    // Bersihkan timer saat container dimuat ulang (pakai rilis focus method).
    window.AerynSection._cleanup = function () { if (timer) window.clearInterval(timer); };
    return box;
  }

  async function loadAuth(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '🔐 Auth — Masuk / Daftar'));

    // State login tersimpan (dari localStorage).
    function getMe() {
      try { var s = localStorage.getItem('aeryn.user'); return s ? JSON.parse(s) : null; } catch (e) { return null; }
    }
    var me = getMe();

    var statusBox = el('div', 'section-hint', me ? ('Masuk sebagai: ' + (me.display_name || me.email)) : 'Belum masuk.');
    box.appendChild(statusBox);

    if (me) {
      var out = el('button', 'section-btn danger', 'Keluar');
      out.addEventListener('click', function () {
        try { localStorage.removeItem('aeryn.user'); } catch (e) {}
        statusBox.textContent = 'Belum masuk.';
        out.remove();
        var h = el('div', 'section-hint', 'Kamu keluar. Muat ulang (F5) untuk masuk lagi.');
        box.appendChild(h);
      });
      box.appendChild(out);
    }
    if (!me) {
      box.appendChild(el('div', 'section-form', (function () {
        var b = el('div', 'section-form-stack');
        var mode = 'login';
        var loginForm = el('div', 'section-form-stack');
        var eMail = el('input', 'section-input'); eMail.placeholder = 'Email'; eMail.type = 'email';
        var ePass = el('input', 'section-input'); ePass.placeholder = 'Password'; ePass.type = 'password';
        var eBtn = el('button', 'section-btn', 'Masuk');
        loginForm.appendChild(eMail); loginForm.appendChild(ePass); loginForm.appendChild(eBtn);
        var regForm = el('div', 'section-form-stack'); regForm.style.display = 'none';
        var rMail = el('input', 'section-input'); rMail.placeholder = 'Email'; rMail.type = 'email';
        var rName = el('input', 'section-input'); rName.placeholder = 'Nama tampilan';
        var rPass = el('input', 'section-input'); rPass.placeholder = 'Password'; rPass.type = 'password';
        var rBtn = el('button', 'section-btn', 'Daftar');
        regForm.appendChild(rMail); regForm.appendChild(rName); regForm.appendChild(rPass); regForm.appendChild(rBtn);
        var tgl = el('button', 'section-btn', 'Punya akun? Masuk');
        b.appendChild(loginForm); b.appendChild(regForm); b.appendChild(tgl);

        function setMode(m) {
          mode = m;
          loginForm.style.display = m === 'login' ? '' : 'none';
          regForm.style.display = m === 'register' ? '' : 'none';
          tgl.textContent = m === 'login' ? 'Daftar akun baru' : 'Punya akun? Masuk';
        }
        tgl.addEventListener('click', function () { setMode(mode === 'login' ? 'register' : 'login'); });

        var out2 = el('div', 'section-result');
        b.appendChild(out2);
        async function doLogin() {
          out2.textContent = 'Memeriksa…';
          try {
            var r = await fetch('/v1/auth/login?username=' + encodeURIComponent(eMail.value) + '&password=' + encodeURIComponent(ePass.value), { method: 'POST' });
            var d = await r.json();
            if (d.status === 'success' && d.token) {
              try { localStorage.setItem('aeryn.user', JSON.stringify(d.token)); } catch (e2) {}
              out2.textContent = '✓ Masuk berhasil sebagai ' + (d.token.display_name || d.token.email) + '.';
              setTimeout(function () { location.reload(); }, 900);
            } else {
              out2.textContent = 'Login gagal: ' + (d.error || d.detail || JSON.stringify(d));
              out2.className = 'section-result error';
            }
          } catch (e2) { out2.textContent = 'Error: ' + e2.message; }
        }
        async function doRegister() {
          out2.textContent = 'Membuat akun…';
          try {
            var r = await fetch('/v1/auth/register?username=' + encodeURIComponent(rMail.value) + '&password=' + encodeURIComponent(rPass.value) + '&role=user', { method: 'POST' });
            var d = await r.json();
            if (d.status === 'created' && d.user_id && d.user_id.id) {
              out2.textContent = '✓ Akun dibuat. Silakan masuk dengan email & password.';
            } else {
              out2.textContent = 'Daftar gagal: ' + JSON.stringify(d);
              out2.className = 'section-result error';
            }
          } catch (e2) { out2.textContent = 'Error: ' + e2.message; }
        }
        eBtn.addEventListener('click', doLogin);
        rBtn.addEventListener('click', doRegister);
        return b;
      })()));
    }

    return box;
  }

  async function loadCron(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '⏰ Cron — Jadwal Berulang'));

    // Form tambah job
    var form = el('div', 'section-stack');
    var n = el('input', 'section-input'); n.placeholder = 'Nama job';
    var sc = el('input', 'section-input'); sc.placeholder = 'Cron (mis. "0 9 * * *")'; sc.value = '0 9 * * *';
    var u = el('input', 'section-input'); u.placeholder = 'URL tujuan (action)'; u.value = 'http://127.0.0.1:3010/v1/facts/entities';
    var row = el('div', 'section-form');
    var add = el('button', 'section-btn', '+ Tambah');
    row.appendChild(add);
    form.appendChild(n); form.appendChild(sc); form.appendChild(u); form.appendChild(row);
    box.appendChild(form);

    var list = el('div', 'section-stack');
    box.appendChild(list);
    var status = el('div', 'section-hint', '');
    box.appendChild(status);

    async function refresh() {
      list.innerHTML = '';
      try {
        var r = await getJSON(BASE + '/cron/jobs');
        var jobs = r && r.jobs;
        if (Array.isArray(jobs) && jobs.length) {
          jobs.forEach(function (j) {
            var rowEl = el('div', 'section-row', '');
            var info = el('span', null, '<b>' + j.name + '</b>  ' + j.schedule + '  → ' + j.action_url + '  · ' + (j.enabled ? 'ON' : 'OFF') + ' · run:' + (j.run_count || 0) + ' · ' + (j.last_status || '-'));
            info.innerHTML = '<b>' + j.name + '</b> <span class="kg-src">' + j.schedule + '</span><br>' + j.action_url + '<br>status: <b>' + (j.last_status || '-') + '</b> · run:' + (j.run_count || 0) + ' · next: ' + (j.next_run || '-');
            var del = el('button', 'session-btn danger', '✕');
            del.addEventListener('click', async function () {
              await fetch(BASE + '/cron/jobs/' + encodeURIComponent(j.id), { method: 'DELETE' });
              refresh();
            });
            rowEl.appendChild(info);
            rowEl.appendChild(del);
            list.appendChild(rowEl);
          });
        } else {
          list.appendChild(el('div', 'section-row', 'Belum ada job cron. Tambah di atas.'));
        }
      } catch (e) {
        list.appendChild(errorBox('Cron gagal: ' + e.message));
      }
    }

    add.addEventListener('click', async function () {
      status.textContent = 'Membuat job…';
      try {
        var r = await fetch(BASE + '/cron/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: n.value || 'unnamed', schedule: sc.value, url: u.value, method: 'GET' }),
        });
        var d = await r.json();
        status.textContent = d.status === 'created' ? '✓ Job dibuat: ' + d.id : 'Gagal: ' + JSON.stringify(d);
        n.value = '';
        refresh();
      } catch (e2) { status.textContent = 'Error: ' + e2.message; }
    });

    refresh();
    return box;
  }

  async function loadObs(container) {
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '📊 Observability — Dashboard'));

    var dash = el('div', 'section-stack');
    box.appendChild(dash);

    var statsBox = el('div', 'section-stack');
    box.appendChild(statsBox);
    var recent = el('div', 'section-stack');
    box.appendChild(recent);
    var refresh = el('button', 'section-btn', '↻ Muat ulang');
    box.appendChild(refresh);

    async function renderDash() {
      dash.innerHTML = '';
      try {
        var d = await getJSON(BASE + '/obs/summary?window_hours=24');
        var app = d.app && d.app.status;
        var appColor = app === 'healthy' ? 'var(--ok)' : (app === 'down' ? 'var(--accent-3)' : 'var(--accent-2)');
        var title = el('div', 'section-subtitle', 'Kesehatan');
        title.style.fontSize = '15px';
        dash.appendChild(title);

        var row = el('div', 'section-row', '');
        row.innerHTML = 'App: <b style="color:' + appColor + '">' + app + '</b> · ' +
          'PG: <b style="color:' + ((d.pg && d.pg.status === 'up') ? 'var(--ok)' : 'var(--accent-3)') + '">' + (d.pg ? d.pg.status : '?') + '</b>';
        dash.appendChild(row);

        // Subsystem chips
        var subs = d.subsystems || {};
        var names = { memory: 'Memori', engine: 'Engine', safety: 'Keamanan', agents: 'Agen', platform: 'Platform' };
        var chipsWrap = el('div', 'kg-chips', '');
        Object.keys(subs).forEach(function (k) {
          var st = subs[k] && subs[k].status;
          var c = (st === 'healthy' || st === 'up') ? 'var(--ok)' : (st === 'down' ? 'var(--accent-3)' : 'var(--accent-2)');
          var ch = document.createElement('span');
          ch.className = 'kg-chip';
          ch.style.borderColor = c;
          ch.style.color = c;
          ch.textContent = (names[k] || k) + ' · ' + st;
          chipsWrap.appendChild(ch);
        });
        dash.appendChild(chipsWrap);

        // Metrics agregat
        var rq = d.requests || {};
        var m = el('div', 'section-stack', '');
        m.innerHTML = '<div>Request: <b>' + (rq.total || 0) + '</b> · Error: <b>' +
          (rq.error_rate || 0) + '%</b> · Rata2: <b>' + (rq.avg_ms || 0) + 'ms</b></div>' +
          '<div>Facts bitemporal: <b>' + (d.facts || 0) + '</b> · Cron aktif: <b>' + (d.cron ? d.cron.active : 0) + '</b>/' + (d.cron ? d.cron.total : 0) + '</div>';
        dash.appendChild(m);

        if (Array.isArray(d.errors) && d.errors.length) {
          var eh = el('div', 'section-subtitle', 'Error terbaru');
          dash.appendChild(eh);
          d.errors.forEach(function (r2) {
            dash.appendChild(el('div', 'kg-row', '⚠ ' + r2.method + ' ' + r2.path + ' → ' + r2.status));
          });
        }
      } catch (e) { dash.appendChild(errorBox('Dashboard gagal: ' + e.message)); }
    }

    async function load() {
      // Stats
      statsBox.innerHTML = '';
      try {
        var s = await getJSON(BASE + '/logging/stats?window_hours=24');
        var card = el('div', 'section-row', '');
        card.innerHTML = 'Total: <b>' + s.total + '</b> · Error 5xx: <b>' + s.err5xx + '</b> (' + s.error_rate + '%) · 4xx: <b>' + s.err4xx + '</b> · Rata2: <b>' + s.avg_ms + 'ms</b> · Max: <b>' + s.max_ms + 'ms</b>';
        statsBox.appendChild(card);
        if (s.slowest && s.slowest.length) {
          var sh = el('div', 'section-subtitle', 'Paling lambat');
          statsBox.appendChild(sh);
          (s.slowest || []).forEach(function (r) {
            statsBox.appendChild(el('div', 'kg-row', '⏱ ' + r.duration_ms + 'ms · ' + r.method + ' ' + r.path + ' (' + r.status + ')'));
          });
        }
        if (s.top_error_paths && s.top_error_paths.length) {
          var th = el('div', 'section-subtitle', 'Untuk error 5xx');
          statsBox.appendChild(th);
          (s.top_error_paths || []).forEach(function (r) {
            statsBox.appendChild(el('div', 'kg-row', '⚠ ' + r.path + ' → ' + r.n + 'x'));
          });
        }
      } catch (e) { statsBox.appendChild(errorBox('Stats gagal: ' + e.message)); }

      // Recent
      recent.innerHTML = '';
      try {
        var l = await getJSON(BASE + '/logging/recent?limit=30');
        var logs = l && l.logs;
        if (Array.isArray(logs) && logs.length) {
          (logs || []).forEach(function (r) {
            var c = r.status >= 500 ? 'var(--accent-3)' : (r.status >= 400 ? 'var(--accent-2)' : 'inherit');
            recent.appendChild(el('div', 'kg-row', '<span style="color:' + c + '">' + r.status + '</span> ' + r.method + ' ' + r.path + ' · ' + r.duration_ms + 'ms · ' + r.ts));
          });
        } else {
          recent.appendChild(el('div', 'section-row', 'Belum ada log.'));
        }
      } catch (e2) { recent.appendChild(errorBox('Recent gagal: ' + e2.message)); }
    }

    refresh.addEventListener('click', function () { renderDash(); load(); });
    renderDash();
    load();
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
    logs: loadLogs,
    auth: loadAuth,
    cron: loadCron,
    obs: loadObs,
    tasks: loadTasks,
    safety: loadSafety,
    trace: loadTrace,
    eval: loadEval,
    plugins: loadPlugins,
    settings: loadSettings,
  };

  async function load(id, container) {
    // Bersihkan timer (mis. polling log) sebelum render section baru.
    if (window.AerynSection._cleanup) { try { window.AerynSection._cleanup(); } catch (e) {} window.AerynSection._cleanup = null; }
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