/**
 * home.js — Homepage animation engine (Awwwards-style).
 * Lenis smooth scroll + GSAP ScrollTrigger parallax + reveal + count-up +
 * magnetic cursor + Three.js particle background.
 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasGsap = typeof window.gsap !== 'undefined';
  var hasScrollTrigger = typeof window.ScrollTrigger !== 'undefined';
  var hasLenis = typeof window.Lenis !== 'undefined';

  // Register GSAP plugins.
  if (hasGsap && hasScrollTrigger) {
    window.gsap.registerPlugin(window.ScrollTrigger);
  }
  if (hasGsap && typeof window.CustomEase !== 'undefined') {
    window.gsap.registerPlugin(window.CustomEase);
  }

  // === 1. LENIS SMOOTH SCROLL ===
  var lenis = null;
  function initLenis() {
    if (!hasLenis || reduceMotion) return;
    lenis = new window.Lenis({
      duration: 1.2,
      easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
      smoothWheel: true,
    });

    // Sync Lenis RAF dengan GSAP ticker (mulus 60fps).
    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    if (hasGsap) {
      lenis.on('scroll', window.ScrollTrigger.update);
      window.gsap.ticker.add(function (time) { lenis.raf(time * 1000); });
      window.gsap.ticker.lagSmoothing(0);
    }
  }

  // === 2. SCROLLTRIGGER — PARALLAX & REVEAL ===
  function initScrollAnimations() {
    if (!hasGsap || !hasScrollTrigger || reduceMotion) {
      // Fallback: tampilkan semua tanpa animasi.
      document.querySelectorAll('[data-reveal]').forEach(function (el) { el.style.opacity = 1; el.style.transform = 'none'; });
      return;
    }

    // Reveal: elemen [data-reveal] masuk saat scroll.
    document.querySelectorAll('[data-reveal]').forEach(function (el) {
      gsap.to(el, {
        opacity: 1,
        y: 0,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: el,
          start: 'top 85%',
          once: true,
        },
      });
    });

    // Parallax: elemen [data-parallax] bergeser beda kecepatan.
    document.querySelectorAll('[data-parallax]').forEach(function (el) {
      var amount = parseFloat(el.getAttribute('data-parallax')) || 0.1;
      gsap.to(el, {
        yPercent: amount * 100,
        ease: 'none',
        scrollTrigger: {
          trigger: el.parentElement,
          start: 'top bottom',
          end: 'bottom top',
          scrub: true,
        },
      });
    });

    // Hero 1 title: line reveal (clip).
    document.querySelectorAll('.hero-title .line > span').forEach(function (span) {
      gsap.from(span, {
        yPercent: 120,
        duration: 1.2,
        ease: 'power4.out',
        stagger: 0.12,
        delay: 0.2,
      });
    });
  }

  // === 2b. SECTION TRANSITIONS (pin + scrub antar hero) ===
  function initSectionTransitions() {
    if (!hasGsap || !hasScrollTrigger || reduceMotion) return;

    // Setiap hero-section scale + fade saat keluar viewport (scrub), membuat
    // transisi antar section terasa sinematik (section sebelumnya 'mengecil'
    // sementara section berikutnya masuk).
    document.querySelectorAll('.hero').forEach(function (section, i) {
      var isFirst = i === 0;
      var isLast = i === document.querySelectorAll('.hero').length - 1;

      if (!isLast) {
        // Section ke-i turun/mengecil halus saat scroll melewatinya.
        gsap.to(section.querySelector('.hero-inner'), {
          opacity: 0.15,
          scale: 0.96,
          y: -60,
          ease: 'none',
          scrollTrigger: {
            trigger: section,
            start: 'top top',
            end: 'bottom top',
            scrub: true,
          },
        });
      }
    });

    // Section berikutnya masuk dengan reveal dari bawah (stagger komponen).
    document.querySelectorAll('.hero').forEach(function (section) {
      var els = section.querySelectorAll('.hero-inner > *');
      gsap.from(els, {
        opacity: 0,
        y: 60,
        duration: 0.8,
        ease: 'power3.out',
        stagger: 0.08,
        scrollTrigger: {
          trigger: section,
          start: 'top 75%',
          once: true,
        },
      });
    });
  }

  // === 3. SCROLL PROGRESS ===
  function initScrollProgress() {
    var bar = document.querySelector('.scroll-progress-bar');
    if (!bar) return;
    function update() {
      var scrollable = document.documentElement.scrollHeight - window.innerHeight;
      var pct = scrollable > 0 ? (window.scrollY / scrollable) * 100 : 0;
      bar.style.width = pct + '%';
    }
    if (window.lenis) {
      window.lenis.on('scroll', update);
    } else {
      window.addEventListener('scroll', update);
    }
    update();
  }

  // === 4. COUNT-UP STATS ===
  function initCountUp() {
    if (reduceMotion || !hasGsap) {
      // Tanpa animasi — set angka final langsung.
      document.querySelectorAll('.stat').forEach(function (stat) {
        var target = parseInt(stat.getAttribute('data-count') || '0', 10);
        stat.querySelector('.stat-num').textContent = target;
      });
      return;
    }
    document.querySelectorAll('.stat').forEach(function (stat) {
      var numEl = stat.querySelector('.stat-num');
      var target = parseInt(stat.getAttribute('data-count') || '0', 10);
      var obj = { val: 0 };
      gsap.to(obj, {
        val: target,
        duration: 2,
        ease: 'power2.out',
        scrollTrigger: { trigger: stat, start: 'top 85%', once: true },
        onUpdate: function () { numEl.textContent = Math.floor(obj.val); },
        onComplete: function () { numEl.textContent = target; },
      });
    });
  }

  // === 5. MAGNETIC CURSOR ===
  function initCursor() {
    if (reduceMotion) return;
    var outer = document.querySelector('.cursor-outer');
    var inner = document.querySelector('.cursor-inner');
    if (!outer || !inner) return;

    var mx = 0, my = 0, ox = 0, oy = 0, ix = 0, iy = 0;
    document.addEventListener('mousemove', function (e) {
      mx = e.clientX; my = e.clientY;
    });

    function animate() {
      ox += (mx - ox) * 0.12;
      oy += (my - oy) * 0.12;
      ix += (mx - ix) * 0.25;
      iy += (my - iy) * 0.25;
      outer.style.transform = 'translate(' + ox + 'px,' + oy + 'px) translate(-50%,-50%)';
      inner.style.transform = 'translate(' + ix + 'px,' + iy + 'px) translate(-50%,-50%)';
      requestAnimationFrame(animate);
    }
    animate();

    document.querySelectorAll('[data-cursor-hover]').forEach(function (el) {
      el.addEventListener('mouseenter', function () { outer.classList.add('hovering'); });
      el.addEventListener('mouseleave', function () { outer.classList.remove('hovering'); });
    });
  }

  // === 6. THREE.JS PARTICLE BACKGROUND ===
  function initParticles() {
    if (reduceMotion || typeof window.THREE === 'undefined') return;
    var container = document.getElementById('particleBg');
    if (!container) return;

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
    var renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    var count = 2500;
    var pos = new Float32Array(count * 3);
    for (var i = 0; i < count; i++) {
      pos[i*3] = (Math.random() - 0.5) * 30;
      pos[i*3+1] = (Math.random() - 0.5) * 30;
      pos[i*3+2] = (Math.random() - 0.5) * 20;
    }
    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    var mat = new THREE.PointsMaterial({
      size: 0.06, color: 0x6d5cff, transparent: true, opacity: 0.5,
      blending: THREE.AdditiveBlending, sizeAttenuation: true,
    });
    var pts = new THREE.Points(geo, mat);
    scene.add(pts);
    camera.position.z = 12;

    function animate() {
      requestAnimationFrame(animate);
      pts.rotation.y += 0.0004;
      pts.rotation.x += 0.0002;
      renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', function () {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  // === INIT ===
  function init() {
    initLenis();
    initScrollAnimations();
    initSectionTransitions();
    initScrollProgress();
    initCountUp();
    initCursor();
    initParticles();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();