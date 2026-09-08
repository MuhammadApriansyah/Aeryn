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
    // Recall memory + list entities (jika endpoint ada).
    var box = el('div', 'section-stack');
    try {
      var mem = await getJSON(BASE + '/memory/entities');
      var title = el('div', 'section-title', '🧠 Memory — Entities');
      box.appendChild(title);
      if (mem && mem.entities) {
        mem.entities.forEach(function (e) {
          box.appendChild(el('div', 'section-row', (e.name || e.id || JSON.stringify(e))));
        });
      } else {
        box.appendChild(el('div', 'section-row', JSON.stringify(mem)));
      }
    } catch (e) {
      box.appendChild(errorBox('Memory endpoint belum tersedia atau gagal: ' + e.message));
    }
    return box;
  }

  async function loadTools(container) {
    var box = el('div', 'section-stack');
    try {
      var tools = await getJSON(BASE + '/tools/list');
      var title = el('div', 'section-title', '🔧 Tools (terdaftar)');
      box.appendChild(title);
      var list = tools && (tools.tools || tools.result || tools);
      if (Array.isArray(list)) {
        list.forEach(function (t) {
          var name = typeof t === 'string' ? t : (t.name || t.id || JSON.stringify(t));
          box.appendChild(el('div', 'section-row', name));
        });
      } else {
        box.appendChild(el('div', 'section-row', JSON.stringify(tools)));
      }
    } catch (e) {
      box.appendChild(errorBox('Tools endpoint gagal: ' + e.message));
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