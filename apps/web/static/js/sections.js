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
    box.appendChild(el('div', 'section-title', '🔧 Tools'));

    // Execute form
    var form = el('div', 'section-form-stack');
    var toolSel = el('select', 'section-select');
    var toolOptPlaceholder = el('option', null, 'Pilih tool…');
    toolOptPlaceholder.value = '';
    toolSel.appendChild(toolOptPlaceholder);
    var paramsInput = el('textarea', 'section-textarea', '');
    paramsInput.placeholder = 'Params JSON (contoh: {"path": "/etc/hostname"})';
    paramsInput.rows = 2;
    var execBtn = el('button', 'section-btn', 'Execute');
    var execResult = el('div', 'section-result', '');

    form.appendChild(toolSel);
    form.appendChild(paramsInput);
    form.appendChild(execBtn);
    box.appendChild(form);
    box.appendChild(execResult);

    // Load tool list ke dropdown.
    try {
      var tools = await getJSON(BASE + '/tools/list');
      var list = tools && (tools.tools || tools.result || tools);
      if (Array.isArray(list)) {
        list.forEach(function (t) {
          var name = typeof t === 'string' ? t : (t.name || t.id || String(t));
          var o = el('option', null, name);
          o.value = name;
          toolSel.appendChild(o);
        });
      }
    } catch (e) {
      box.appendChild(errorBox('Gagal load tool list: ' + e.message));
    }

    async function doExecute() {
      var tool = toolSel.value;
      if (!tool) { execResult.textContent = 'Pilih tool dulu.'; return; }
      var params = {};
      try {
        params = paramsInput.value.trim() ? JSON.parse(paramsInput.value) : {};
      } catch (e) {
        execResult.textContent = 'Invalid JSON params: ' + e.message;
        return;
      }
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
    execBtn.addEventListener('click', doExecute);

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
    // Settings: provider/model (client-side, sama seperti chat.html settings).
    var box = el('div', 'section-stack');
    box.appendChild(el('div', 'section-title', '⚙ Settings'));

    var provider = el('select', 'section-select');
    ['gemini', 'openai', 'anthropic', 'deepseek'].forEach(function (p) {
      var o = el('option', null, p);
      o.value = p;
      provider.appendChild(o);
    });
    box.appendChild(labelRow('Provider', provider));

    var model = el('select', 'section-select');
    ['auto', 'gemini-3.5-flash-lite', 'gpt-4o', 'claude-sonnet-4', 'deepseek-chat'].forEach(function (m) {
      var o = el('option', null, m);
      o.value = m;
      model.appendChild(o);
    });
    box.appendChild(labelRow('Model', model));

    return box;
  }

  function labelRow(label, control) {
    var row = el('div', 'section-field');
    row.appendChild(el('label', 'section-label', label));
    row.appendChild(control);
    return row;
  }

  // === Registry & entry ===
  var LOADERS = {
    memory: loadMemory,
    tools: loadTools,
    agents: loadAgents,
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