/**
 * effects.js — Premium visual effects, dipreservasi dari dashboard legacy.
 * 1. Magnetic cursor (outer + inner, smooth follow).
 * 2. Three.js particle field background (5000 partikel, additive blending).
 * Keduanya gate di belakang prefers-reduced-motion.
 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // === 1. MAGNETIC CURSOR ===
  function initCursor() {
    if (reduceMotion) return;
    var outer = document.querySelector('.cursor-outer');
    var inner = document.querySelector('.cursor-inner');
    if (!outer && !inner) {
      // Buat cursor element kalau belum ada di DOM.
      outer = document.createElement('div'); outer.className = 'cursor-outer';
      inner = document.createElement('div'); inner.className = 'cursor-inner';
      document.body.appendChild(outer);
      document.body.appendChild(inner);
    }

    var mouseX = 0, mouseY = 0, outerX = 0, outerY = 0, innerX = 0, innerY = 0;

    document.addEventListener('mousemove', function (e) {
      mouseX = e.clientX; mouseY = e.clientY;
    });

    function animate() {
      outerX += (mouseX - outerX) * 0.12;
      outerY += (mouseY - outerY) * 0.12;
      innerX += (mouseX - innerX) * 0.25;
      innerY += (mouseY - innerY) * 0.25;
      if (outer) { outer.style.left = outerX + 'px'; outer.style.top = outerY + 'px'; }
      if (inner) { inner.style.left = innerX + 'px'; inner.style.top = innerY + 'px'; }
      requestAnimationFrame(animate);
    }
    animate();

    // Hover effect: [data-cursor-hover] → perbesar outer cursor.
    document.querySelectorAll('[data-cursor-hover]').forEach(function (el) {
      el.addEventListener('mouseenter', function () { if (outer) outer.classList.add('hovering'); });
      el.addEventListener('mouseleave', function () { if (outer) outer.classList.remove('hovering'); });
    });
  }

  // === 2. THREE.JS PARTICLE FIELD (background) ===
  function initParticles() {
    if (reduceMotion || typeof THREE === 'undefined') return;

    // Container: buat canvas layer di belakang konten.
    var container = document.createElement('div');
    container.id = 'cover-3d';
    container.style.cssText = 'position:fixed;inset:0;z-index:0;pointer-events:none;';
    document.body.insertBefore(container, document.body.firstChild);

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    var renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    var count = 5000;
    var positions = new Float32Array(count * 3);
    var colors = new Float32Array(count * 3);

    for (var i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 20;
      var t = Math.random();
      if (t < 0.33) { colors[i*3]=0.39; colors[i*3+1]=0.4; colors[i*3+2]=0.95; }
      else if (t < 0.66) { colors[i*3]=0.02; colors[i*3+1]=0.71; colors[i*3+2]=0.83; }
      else { colors[i*3]=0.92; colors[i*3+1]=0.28; colors[i*3+2]=0.6; }
    }

    var geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    var material = new THREE.PointsMaterial({
      size: 0.04, vertexColors: true, transparent: true, opacity: 0.7,
      blending: THREE.AdditiveBlending, sizeAttenuation: true
    });
    var particles = new THREE.Points(geometry, material);
    scene.add(particles);

    camera.position.z = 8;

    var mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', function (e) {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    });

    function animate() {
      requestAnimationFrame(animate);
      particles.rotation.y += 0.0006;
      particles.rotation.x += 0.0003;
      camera.position.x += (mouseX - camera.position.x) * 0.02;
      camera.position.y += (-mouseY - camera.position.y) * 0.02;
      camera.lookAt(scene.position);
      renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', function () {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  // === Init (defer agar tidak blokir render) ===
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initCursor();
      // Defer 3D supaya UI interaktif dulu, lalu partikel render.
      setTimeout(initParticles, 200);
    });
  } else {
    initCursor();
    setTimeout(initParticles, 200);
  }
})();