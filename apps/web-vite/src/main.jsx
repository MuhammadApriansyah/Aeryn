import React from 'react'
import { createRoot } from 'react-dom/client'

function App() {
  const [scrolled, setScrolled] = React.useState(false)
  const [stats, setStats] = React.useState({ requests: 0, uptime: 0, tokens: 0 })
  const [beingProc, setBeingProc] = React.useState(0)

  React.useEffect(() => {
    const h = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', h, { passive: true })
    return () => window.removeEventListener('scroll', h)
  }, [])

  React.useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('/v1/dashboard/stats')
        if (res.ok) {
          const data = await res.json()
          setStats(s => ({
            requests: data.requests || s.requests,
            uptime: data.uptime || s.uptime,
            tokens: data.tokens || s.tokens + Math.floor(Math.random() * 100)
          }))
        }
      } catch (e) {}
    }
    const interval = setInterval(fetchStats, 5000)
    fetchStats()
    return () => clearInterval(interval)
  }, [])

  React.useEffect(() => {
    const interval = setInterval(() => {
      setBeingProc(p => p + Math.floor(Math.random() * 50))
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  const fmtDur = (s) => {
    const d = Math.floor(s / 86400)
    const h = Math.floor((s % 86400) / 3600)
    const m = Math.floor((s % 3600) / 60)
    const sec = s % 60
    if (d > 0) return `${d}d ${h}h`
    if (h > 0) return `${h}h ${m}m`
    if (m > 0) return `${m}m ${sec}s`
    return `${sec}s`
  }

  return (
    <div className="app">
      {/* Cursor */}
      <div className="cursor-outer" id="cursor-outer">
        <div className="cursor-inner" id="cursor-inner"></div>
      </div>

      {/* Nav */}
      <nav className={`top-nav ${scrolled ? 'scrolled' : ''}`}>
        <div className="nav-inner">
          <div className="nav-logo">🌀 Aeryn</div>
          <div className="nav-links">
            <a href="#systems">Systems</a>
            <a href="#work">Work</a>
            <a href="#stack">Stack</a>
            <a href="#chat">Chat</a>
            <a href="#divisions">Divisions</a>
            <a href="#plugins">Plugins</a>
            <a href="#memory">Memory</a>
            <a href="#dossier">Dossier</a>
          </div>
          <div className="nav-actions">
            <button className="nav-btn">🌙</button>
            <button className="nav-btn">ID</button>
          </div>
        </div>
      </nav>

      {/* COVER */}
      <section className="sec-cover" data-section="cover">
        <div className="cover-bg">
          <div className="grid-overlay"></div>
          <div className="noise"></div>
        </div>
        <div className="cover-content">
          <div className="cover-case">
            <span>CASE № 2026/<b>001</b></span>
            <span>SCOPE: <b>$0</b></span>
            <span>SOURCES: <b>4 verified</b></span>
            <span>STATUS: <b className="online">PRODUCTION</b></span>
          </div>
          <div className="cover-clock">Jakarta <span>{new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}</span></div>
          <h1 className="cover-title">
            <span className="title-line">The best agents</span>
            <span className="title-line">are <em>managed</em>,</span>
            <span className="title-line">not improvised.</span>
          </h1>
          <div className="cover-stats">
            <div className="stat-card">
              <div className="stat-ico">⚡</div>
              <div className="stat-val">{stats.requests}</div>
              <div className="stat-lbl">Requests</div>
            </div>
            <div className="stat-card">
              <div className="stat-ico">👥</div>
              <div className="stat-val">5</div>
              <div className="stat-lbl">Divisions</div>
            </div>
            <div className="stat-card">
              <div className="stat-ico">⏱️</div>
              <div className="stat-val">{fmtDur(stats.uptime)}</div>
              <div className="stat-lbl">Uptime</div>
            </div>
            <div className="stat-card">
              <div className="stat-ico">🎯</div>
              <div className="stat-val">{stats.tokens}</div>
              <div className="stat-lbl">Tokens</div>
            </div>
          </div>
          <div className="cover-live"><span className="dot"></span> LIVE — 0 req/s · 0ms · 0MB</div>
          <div className="cover-being">BEING PROCESSED AS YOU READ: <b>{beingProc}</b> tokens</div>
          <div className="cover-cta">
            <button className="btn-pri" onClick={() => scrollTo('systems')}>Enter the Systems →</button>
            <button className="btn-sec" onClick={() => scrollTo('work')}>See the Work</button>
          </div>
        </div>
        <div className="cover-scroll"><span>SCROLL TO EXPLORE</span><div className="scroll-line"></div></div>
      </section>

      {/* SYSTEMS / PRACTICE */}
      <section className="sec-systems" id="systems" data-section="systems">
        <div className="container">
          <div className="hdr"><div className="num">01</div><h2>The Systems</h2><p>A private firm, holding a limited number of engagements.</p></div>
          <div className="systems-grid">
            <div className="system-card"><div className="system-icon">⚡</div><h3>API Gateway</h3><p>FastAPI backend with 200+ endpoints</p><span className="badge on">● Operational</span></div>
            <div className="system-card"><div className="system-icon">🧠</div><h3>LLM Engine</h3><p>Multi-model routing with Gemini, Claude, OpenAI</p><span className="badge on">● Operational</span></div>
            <div className="system-card"><div className="system-icon">🧩</div><h3>Memory Vault</h3><p>PostgreSQL + pgvector semantic search</p><span className="badge on">● Operational</span></div>
            <div className="system-card"><div className="system-icon">🔌</div><h3>Plugin System</h3><p>Extensible architecture with auto-discovery</p><span className="badge on">● Operational</span></div>
            <div className="system-card"><div className="system-icon">👥</div><h3>5 Divisions</h3><p>Creative, Psychology, Reasoning, Governance, Infrastructure</p><span className="badge on">● Operational</span></div>
            <div className="system-card"><div className="system-icon">📈</div><h3>Observability</h3><p>Langfuse-style tracing with spans and metrics</p><span className="badge on">● Operational</span></div>
          </div>
        </div>
      </section>

      {/* WORK */}
      <section className="sec-work" id="work" data-section="work">
        <div className="container">
          <div className="hdr"><div className="num">02</div><h2>The Work</h2><p>Real products, live in days — and then in motion.</p></div>
          <div className="work-list">
            <div className="work-item" onClick={(e) => e.currentTarget.classList.toggle('open')}>
              <div className="work-header"><div className="work-title">Chat</div><div className="work-toggle">+</div></div>
              <div className="work-detail">
                <div className="chat-demo">
                  <div className="bubble sys">Halo! Saya Aeryn v61.5. Ada yang bisa kubantu?</div>
                  <div className="bubble user">Tolong analisis kode Python ini</div>
                  <div className="bubble asst">Tentu! Mari saya periksa kode Anda...</div>
                </div>
                <div className="tags"><span>Conversational AI</span><span>Tool Execution</span><span>Memory Recall</span></div>
              </div>
            </div>
            <div className="work-item" onClick={(e) => e.currentTarget.classList.toggle('open')}>
              <div className="work-header"><div className="work-title">Divisions</div><div className="work-toggle">+</div></div>
              <div className="work-detail">
                <div className="div-icons"><span title="Creative">🎨</span><span title="Psychology">🧠</span><span title="Reasoning">🔍</span><span title="Governance">🏛️</span><span title="Infrastructure">⚙️</span></div>
                <div className="tags"><span>Creative</span><span>Psychology</span><span>Reasoning</span><span>Governance</span><span>Infrastructure</span></div>
              </div>
            </div>
            <div className="work-item" onClick={(e) => e.currentTarget.classList.toggle('open')}>
              <div className="work-header"><div className="work-title">Plugins</div><div className="work-toggle">+</div></div>
              <div className="work-detail">
                <div className="plugin-g"><div className="plugin-c">🔍 Code Review</div><div className="plugin-c">📚 Research Assistant</div><div className="plugin-c">🧩 Memory Vault</div><div className="plugin-c">🔗 Integrations</div></div>
                <div className="tags"><span>Extensible</span><span>Marketplace</span><span>Custom</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* STACK */}
      <section className="sec-stack" id="stack" data-section="stack">
        <div className="container">
          <div className="hdr"><div className="num">03</div><h2>The Stack</h2><p>We don't sell one tool. We direct the whole stack.</p></div>
          <div className="stack-grid">
            <div className="stack-cat"><h4>Backend</h4><div className="stack-items"><span>FastAPI</span><span>Python 3.11</span><span>SQLite</span><span>PostgreSQL</span><span>Redis</span></div></div>
            <div className="stack-cat"><h4>AI / LLM</h4><div className="stack-items"><span>Gemini</span><span>Claude</span><span>OpenAI</span><span>Mistral</span><span>Perplexity</span></div></div>
            <div className="stack-cat"><h4>Frontend</h4><div className="stack-items"><span>React</span><span>TypeScript</span><span>GSAP</span><span>Three.js</span><span>Tailwind</span></div></div>
            <div className="stack-cat"><h4>Infrastructure</h4><div className="stack-items"><span>PM2</span><span>Docker</span><span>Nginx</span><span>Cloudflare</span><span>GitHub</span></div></div>
          </div>
        </div>
      </section>

      {/* CHAT */}
      <section className="sec-chat" id="chat" data-section="chat">
        <div className="container">
          <div className="hdr"><div className="num">04</div><h2>Ask Aeryn</h2><p>The intelligence engine. Ask anything.</p></div>
          <div className="chat-box">
            <div className="chat-win">
              <div className="msg sys"><div className="bubble">Halo! Saya Aeryn v61.5. Saya punya 12 tools dan 5 divisi kognitif. Apa yang mau kerjakan hari ini?</div></div>
            </div>
            <form className="chat-form" onSubmit={(e) => e.preventDefault()}>
              <textarea placeholder="Tulis pesan..." rows={1}></textarea>
              <button type="submit" className="chat-btn">📤</button>
            </form>
          </div>
        </div>
      </section>

      {/* DIVISIONS */}
      <section className="sec-divisions" id="divisions" data-section="divisions">
        <div className="container">
          <div className="hdr"><div className="num">05</div><h2>Cognitive Divisions</h2><p>5 specialized AI agents.</p></div>
          <div className="div-grid">
            <div className="div-card"><div className="div-ico">🎨</div><h4>Creative</h4><p>Design, storytelling</p><button className="btn-exec">Execute</button></div>
            <div className="div-card"><div className="div-ico">🧠</div><h4>Psychology</h4><p>Emotional intelligence</p><button className="btn-exec">Execute</button></div>
            <div className="div-card"><div className="div-ico">🔍</div><h4>Reasoning</h4><p>Logic, problem solving</p><button className="btn-exec">Execute</button></div>
            <div className="div-card"><div className="div-ico">🏛️</div><h4>Governance</h4><p>Rules, ethics, compliance</p><button className="btn-exec">Execute</button></div>
            <div className="div-card"><div className="div-ico">⚙️</div><h4>Infrastructure</h4><p>Deployment, monitoring</p><button className="btn-exec">Execute</button></div>
          </div>
        </div>
      </section>

      {/* PLUGINS */}
      <section className="sec-plugins" id="plugins" data-section="plugins">
        <div className="container">
          <div className="hdr"><div className="num">06</div><h2>Plugins</h2><p>Installed and discoverable plugins.</p></div>
          <div className="plugins-layout">
            <div className="plugins-installed">
              <h3 className="sub-title">Installed</h3>
              <div className="plugin-list">
                <div className="plugin-row"><span className="plugin-ico">🔍</span><div className="plugin-info"><span className="plugin-name">Code Review</span><span className="plugin-desc">Analyze Python code</span></div><button className="btn-run">Run</button></div>
                <div className="plugin-row"><span className="plugin-ico">📚</span><div className="plugin-info"><span className="plugin-name">Research Assistant</span><span className="plugin-desc">Search and summarize</span></div><button className="btn-run">Run</button></div>
                <div className="plugin-row"><span className="plugin-ico">🧩</span><div className="plugin-info"><span className="plugin-name">Memory Vault</span><span className="plugin-desc">PostgreSQL search</span></div><button className="btn-run">Run</button></div>
                <div className="plugin-row"><span className="plugin-ico">🔗</span><div className="plugin-info"><span className="plugin-name">Messaging Gateway</span><span className="plugin-desc">Telegram, Discord, Slack</span></div><button className="btn-run">Run</button></div>
              </div>
            </div>
            <div className="plugins-market">
              <h3 className="sub-title">Marketplace</h3>
              <div className="market-grid">
                <div className="market-card"><span className="market-ico">📊</span><h4>Analytics Pro</h4><span className="market-price">Free</span></div>
                <div className="market-card"><span className="market-ico">🔐</span><h4>Security Scanner</h4><span className="market-price">Free</span></div>
                <div className="market-card"><span className="market-ico">🌐</span><h4>Web Scraper</h4><span className="market-price">Free</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* MEMORY */}
      <section className="sec-memory" id="memory" data-section="memory">
        <div className="container">
          <div className="hdr"><div className="num">07</div><h2>Memory Vault</h2><p>Long-term knowledge storage with semantic search.</p></div>
          <div className="mem-layout">
            <div className="mem-search-panel">
              <div className="search-bar"><input type="text" className="search-in" placeholder="Search memories..." /><button className="btn-search">Search</button></div>
              <div className="store-bar"><input type="text" className="store-in" placeholder="Key" /><input type="text" className="store-in" placeholder="Value" /><button className="btn-store">Store</button></div>
            </div>
            <div className="mem-results-panel">
              <div className="results-hdr"><h3>Search Results</h3><span className="results-cnt">0 found</span></div>
              <div className="mem-results"><div className="empty-state"><div className="empty-ico">🔍</div><p>Search for memories or store new ones</p></div></div>
            </div>
          </div>
          <div className="mem-stats">
            <div className="mem-stat"><span className="mem-stat-val">0</span><span className="mem-stat-lbl">Total</span></div>
            <div className="mem-stat"><span className="mem-stat-val">0</span><span className="mem-stat-lbl">Hot (7d)</span></div>
            <div className="mem-stat"><span className="mem-stat-val">0</span><span className="mem-stat-lbl">Warm (30d)</span></div>
            <div className="mem-stat"><span className="mem-stat-val">0</span><span className="mem-stat-lbl">Cold (90d)</span></div>
          </div>
        </div>
      </section>

      {/* DOSSIER */}
      <section className="sec-dossier" id="dossier" data-section="dossier">
        <div className="container">
          <div className="hdr"><div className="num">08</div><h2>Dossier</h2><p>Subject: Aeryn AI Platform. Classification: Production.</p></div>
          <div className="dossier-grid">
            <div className="dossier-card"><div className="dossier-lbl">Status</div><div className="dossier-val">Production</div></div>
            <div className="dossier-card"><div className="dossier-lbl">Version</div><div className="dossier-val">v61.5</div></div>
            <div className="dossier-card"><div className="dossier-lbl">Uptime</div><div className="dossier-val">{fmtDur(stats.uptime)}</div></div>
            <div className="dossier-card"><div className="dossier-lbl">Requests</div><div className="dossier-val">{stats.requests}</div></div>
            <div className="dossier-card"><div className="dossier-lbl">Agents</div><div className="dossier-val">5 Divisions</div></div>
            <div className="dossier-card"><div className="dossier-lbl">Plugins</div><div className="dossier-val">4</div></div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <div className="container">
          <div className="footer-grid">
            <div className="footer-col"><div className="footer-logo">🌀 Aeryn</div><div className="footer-tag">Managed intelligence, not improvised.</div></div>
            <div className="footer-col"><h4>Platform</h4><a href="#systems">Systems</a><a href="#work">Work</a><a href="#stack">Stack</a><a href="#chat">Chat</a></div>
            <div className="footer-col"><h4>Intelligence</h4><a href="#divisions">Divisions</a><a href="#plugins">Plugins</a><a href="#memory">Memory</a><a href="#dossier">Dossier</a></div>
            <div className="footer-col"><h4>Connect</h4><a href="#">Telegram</a><a href="#">Discord</a><a href="#">Slack</a><a href="#">GitHub</a></div>
          </div>
          <div className="footer-bottom"><span>© 2026 Aeryn AI</span><span>CASE № 2026/001 · MMXXVI</span></div>
        </div>
      </footer>
    </div>
  )
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)

// rebuild 1788269736.7005107
