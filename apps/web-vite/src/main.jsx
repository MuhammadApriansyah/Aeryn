import React from 'react'
import { createRoot } from 'react-dom/client'

function App() {
  const [scrolled, setScrolled] = React.useState(false)
  const [stats, setStats] = React.useState({ requests: 0, uptime: 0, tokens: 0 })

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
          setStats(s => ({ requests: data.requests || s.requests, uptime: data.uptime || s.uptime, tokens: data.tokens || s.tokens + 100 }))
        }
      } catch (e) {}
    }
    const interval = setInterval(fetchStats, 5000)
    fetchStats()
    return () => clearInterval(interval)
  }, [])

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="app">
      <nav className={`top-nav ${scrolled ? 'scrolled' : ''}`}>
        <div className="nav-inner">
          <div className="nav-logo">🌀 Aeryn</div>
          <div className="nav-links">
            <a href="#systems">Systems</a><a href="#work">Work</a><a href="#stack">Stack</a>
            <a href="#chat">Chat</a><a href="#dossier">Dossier</a>
          </div>
          <div className="nav-actions"><button>🌙</button><button>ID</button></div>
        </div>
      </nav>

      <section className="sec-cover">
        <div className="cover-bg"><div className="grid-overlay"></div><div className="noise"></div></div>
        <div className="cover-content">
          <div className="cover-case"><span>CASE № 2026/<b>001</b></span><span>STATUS: <b className="online">PRODUCTION</b></span></div>
          <div className="cover-clock">Jakarta {new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}</div>
          <h1 className="cover-title"><span className="title-line">The best agents</span><span className="title-line">are <em>managed</em>,</span><span className="title-line">not improvised.</span></h1>
          <div className="cover-stats">
            <div className="stat-card"><div className="stat-ico">⚡</div><div className="stat-val">{stats.requests}</div><div className="stat-lbl">Requests</div></div>
            <div className="stat-card"><div className="stat-ico">👥</div><div className="stat-val">5</div><div className="stat-lbl">Divisions</div></div>
            <div className="stat-card"><div className="stat-ico">⏱️</div><div className="stat-val">{stats.uptime}s</div><div className="stat-lbl">Uptime</div></div>
            <div className="stat-card"><div className="stat-ico">🎯</div><div className="stat-val">{stats.tokens}</div><div className="stat-lbl">Tokens</div></div>
          </div>
          <div className="cover-live"><span className="dot"></span> LIVE — 0 req/s · 0ms · 0MB</div>
          <div className="cover-cta">
            <button className="btn-pri" onClick={() => scrollTo('systems')}>Enter the Systems →</button>
            <button className="btn-sec" onClick={() => scrollTo('work')}>See the Work</button>
          </div>
        </div>
        <div className="cover-scroll"><span>SCROLL TO EXPLORE</span><div className="scroll-line"></div></div>
      </section>

      <section className="sec-practice" id="systems">
        <div className="container">
          <div className="hdr"><div className="num">01</div><h2>The Practice</h2><p>A private firm, holding a limited number of engagements.</p></div>
          <div className="practice-grid">
            <div className="practice-card"><div className="practice-ico">🎯</div><h3>Engagement</h3><p>We hold a limited number of engagements to ensure quality.</p></div>
            <div className="practice-card"><div className="practice-ico">🏗️</div><h3>Design & Build</h3><p>For each engagement, we design, build and manage the systems.</p></div>
            <div className="practice-card"><div className="practice-ico">🔧</div><h3>Manage</h3><p>We don't just ship — we manage the software and operations.</p></div>
          </div>
        </div>
      </section>

      <section className="sec-work" id="work">
        <div className="container">
          <div className="hdr"><div className="num">02</div><h2>The Work</h2><p>Real products, live in days — and then in motion.</p></div>
          <div className="work-list">
            <div className="work-item" onClick={(e) => e.currentTarget.classList.toggle('open')}>
              <div className="work-header"><div className="work-title">Chat</div><div className="work-toggle">+</div></div>
              <div className="work-detail"><div className="chat-demo"><div className="bubble sys">Halo! Saya Aeryn v61.5. Ada yang bisa kubantu?</div></div></div>
            </div>
          </div>
        </div>
      </section>

      <section className="sec-stack" id="stack">
        <div className="container">
          <div className="hdr"><div className="num">03</div><h2>The Stack</h2><p>We don't sell one tool. We direct the whole stack.</p></div>
          <div className="stack-grid">
            <div className="stack-cat"><h4>Backend</h4><div className="stack-items"><span>FastAPI</span><span>Python 3.11</span></div></div>
            <div className="stack-cat"><h4>AI / LLM</h4><div className="stack-items"><span>Gemini</span><span>Claude</span></div></div>
            <div className="stack-cat"><h4>Frontend</h4><div className="stack-items"><span>React</span><span>TypeScript</span></div></div>
          </div>
        </div>
      </section>

      <section className="sec-chat" id="chat">
        <div className="container">
          <div className="hdr"><div className="num">04</div><h2>Ask Aeryn</h2><p>The intelligence engine. Ask anything.</p></div>
          <div className="chat-box">
            <div className="chat-win"><div className="msg sys"><div className="bubble">Halo! Saya Aeryn v61.5. Apa yang mau kerjakan hari ini?</div></div></div>
          </div>
        </div>
      </section>

      <section className="sec-dossier" id="dossier">
        <div className="container">
          <div className="hdr"><div className="num">05</div><h2>Dossier</h2><p>Subject: Aeryn AI Platform. Classification: Production.</p></div>
          <div className="dossier-grid">
            <div className="dossier-card"><div className="dossier-lbl">Status</div><div className="dossier-val">Production</div></div>
            <div className="dossier-card"><div className="dossier-lbl">Version</div><div className="dossier-val">v61.5</div></div>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <div className="footer-bottom"><span>© 2026 Aeryn AI</span><span>CASE № 2026/001 · MMXXVI</span></div>
        </div>
      </footer>
    </div>
  )
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)
