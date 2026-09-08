/**
 * markdown.js — Stable incremental markdown renderer (P2).
 *
 * Menangani markdown yang streamed token-by-token tanpa flicker/layout-jank.
 * Pola dari riset Markstream: render parsial saat streaming (final=false),
 * defer blok yang belum lengkap (code fence belum tertutup) supaya tidak
 * render sebagai block lose, lalu render final saat konten stabil.
 *
 * Vanilla, no build step. Bergantung pada global `marked` (vendor/marked.min.js).
 */

(function () {
  'use strict';

  /**
   * Render markdown ke HTML.
   * @param {string} md      - teks markdown (bisa parsial).
   * @param {boolean} isFinal - true saat streaming selesai (render penuh).
   * @returns {string} HTML
   */
  function renderMarkdown(md, isFinal) {
    if (typeof marked === 'undefined') {
      // Fallback: plain text (escape) jika marked belum termuat.
      return escapeHtml(md);
    }

    if (isFinal) {
      // Final: render penuh, pakai marked biasa.
      return marked.parse(md);
    }

    // Streaming: stabilkan partial markdown sebelum render.
    const stable = stabilizePartial(md);
    return marked.parse(stable);
  }

  /**
   * Stabilkan markdown parsial: tutup sementara code fence / list yang
   * belum lengkap supaya marked tidak render jadi block error.
   * Defer blok yang belum "selesai" menjadi inline text.
   */
  function stabilizePartial(md) {
    // 1. Code fence belum ketutup (``` tanpa penutup) → tutup sementara.
    const fenceCount = (md.match(/^```/gm) || []).length;
    let out = md;
    if (fenceCount % 2 === 1) {
      // Ada fence terbuka → tutup supaya tidak menelan sisa teks.
      out = md + '\n```';
    }

    // 2. Tanda list yang baru mulai (baris terakhir "- " / "* " / "1. ")
    //    tanpa isi → biarkan, marked menanganinya sebagai list kosong.

    return out;
  }

  /**
   * Escape HTML entity (fallback kalau marked tidak ada).
   */
  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  /**
   * Deteksi apakah teks saat ini sedang di dalam code block (fence belum selesai).
   * Berguna untuk memutuskan kapan "defer" render block.
   */
  function isInsideCodeBlock(md) {
    const fences = md.match(/^```/gm) || [];
    return fences.length % 2 === 1;
  }

  // Expose global (non-module, sesuai konvensi ES5 Aeryn).
  window.AerynMarkdown = {
    renderMarkdown: renderMarkdown,
    stabilizePartial: stabilizePartial,
    escapeHtml: escapeHtml,
    isInsideCodeBlock: isInsideCodeBlock,
  };
})();