# Aeryn — Penanganan Next.js 16 + Turbopack Error

> Dokumen ini berisi analisis dan solusi untuk mengatasi Bus Error / Crash pada Next.js 16 + Turbopack di ARM64.
> **Bukan untuk implementasi** — hanya dokumentasi perencanaan.

---

## 🔍 Root Cause Analysis

### Apa yang Terjukti

| Gejala | Penyebab |
|--------|----------|
| `Bus Error` saat `next dev` / `next build` | Turbopack mencoba membaca binary file (esbuild, swc) sebagai UTF-8 text |
| `invalid utf-8 sequence of 1 bytes from index 0` | Turbopack parser crash saat parse binary |
| Crash di ARM64, works di x64 | Perilaku berbeda native bindings |
| `next start` 404 di API routes | Next.js 16 production server routing bug |

### Issue Tracking

| Issue | Status | Deskripsi |
|-------|--------|-----------|
| [vercel/next.js#85110](https://github.com/vercel/next.js/issues/85110) | **Closed/Fixed** | Turbopack + PayloadCMS crash di ARM64 |
| [vercel/next.js#85110 (comment)](https://github.com/vercel/next.js/issues/85110#issuecomment-5284422051) | Fixed in 16.1.0-canary.3 | Transitive serverExternalPackages |

---

## ✅ Solusi yang Direkomendasikan

### Prioritas 1: Cache Cleanup (works 80% of time)

**Penyebab**: Cache lama conflict dengan Turbopack baru.

```bash
# Stop PM2 process
pm2 stop aeryn-web

# Clean all caches
cd /home/sen/aeryn-core-agent/aeryn-web
rm -rf .next
rm -rf node_modules/.cache
rm -rf .turbo
npm cache clean --force

# Restart
pm2 start aeryn-web
```

**Risk**: Low
**Time**: 5 minutes
**Effect**: Clear all build caches, force fresh build

---

### Prioritas 2: Update ke Next.js 16.1.0+

**Penyebab**: Bug di Turbopack sudah di-fix di versi baru.

```bash
cd /home/sen/aeryn-core-agent/aeryn-web
npm install next@16.3.3  # atau latest stable
npm install react@19 react-dom@19
rm -rf .next
npm run build
```

**Risk**: Low-Medium
**Time**: 10 minutes
**Effect**: Dapat semua bug fixes terbaru

---

### Prioritas 3: Webpack Fallback

**Penyebab**: Jika Turbopack masih crash, fallback ke Webpack.

```bash
# Option A: Dev mode dengan webpack
next dev --webpack --port 3020

# Option B: Production build dengan webpack
next build --webpack
```

**Risk**: Low
**Time**: 5 minutes
**Effect**: Build lebih lambat tapi lebih stabil

**Verify**: Cek header output — harusnya `(webpack)` bukan `(Turbopack)`

---

### Prioritas 4: Next.js 16 Config Update

**Penyebab**: Flag `experimental.turbopack` perlu di-update.

```javascript
// next.config.js
const nextConfig = {
  reactStrictMode: false,
  poweredByHeader: false,
  // Hapus experimental.turbopack jika masih ada
  // Cukup gunakan --webpack flag jika diperlukan
};
```

---

### Prioritas 5: Ignore Problematic Files

**Penyebab**: Turbopack membaca file binary (esbuild binary, README.md, dll).

```javascript
// next.config.js
const nextConfig = {
  turbopack: {
    rules: {
      '*.md': {
        loaders: ['ignore-loader'],
        as: '*.js',
      },
    },
  },
  serverExternalPackages: ['esbuild', 'esbuild-register'],
};
```

---

## 📊 Keputusan: Next.js atau SPA?

| Faktor | Next.js 16 + Turbopack | SPA HTML/CSS/JS (Saat ini) |
|--------|------------------------|----------------------------|
| Build stability | ❌ Crash di ARM64 | ✅ Works |
| Dev speed | ✅ Fast (kalau jalan) | ✅ Fast (PM2 managed) |
| Production build | ❌ Buggy | ✅ Works |
| SSR/SSG | ✅ Yes | ❌ No (CSR only) |
| Maintenance | ⚠️ High (breaks often) | ✅ Low |
| Test coverage | ✅ 661 tests | ✅ 661 tests |
| Deploy | ❌ Complex | ✅ Simple |

---

## 🛠️ Action Plan

### Phase 1: Cache Cleanup (Jika Next.js masih diperlukan)

1. Stop PM2 `aeryn-web`
2. `rm -rf aeryn-web/.next`
3. `rm -rf aeryn-web/node_modules/.cache`
4. Restart PM2

### Phase 2: Next.js 16.3.3 Update (Jika crash berlanjut)

1. Backup current Next.js config
2. `npm install next@16.3.3`
3. `rm -rf .next && npm run build`
4. Verify with `next start --port 3020`

### Phase 3: Webpack Fallback (Jika Turbopack masih crash)

1. Tambah flag `--webpack` ke scripts atau PM2 config
2. Verify header output: `(webpack)` bukan `(Turbopack)`
3. Test semua routes

### Phase 4: Evaluasi Ulang

Jika setelah 3 phase Next.js masih bermasalah:
- Tetap di SPA HTML/CSS/JS
- Manfaatkan backend API sebagai single source of truth
- Dashboard SPA cukup untuk use case Aeryn

---

## 📚 Referensi

- [Next.js Turbopack Docs](https://nextjs.org/docs/app/api-reference/turbopack)
- [GitHub Issue #85110](https://github.com/vercel/next.js/issues/85110)
- [Next.js Turbopack Stuck Fix](https://www.iloveblogs.blog/post/nextjs-turbopack-stuck-fix)
- [StackOverflow: SWC Binary](https://stackoverflow.com/questions/69816589/next-failed-to-load-swc-binary)

---

*Dokumen ini akan diperbarui sesuai hasil testing*
*Dokumen ini dibuat: 2026-08-30*
