# Panduan Implementasi — Fullstack

**Project:** AI Vendor Selection System  
**Track:** Fullstack (repo `vendor-ai`)  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-13  
**Referensi Utama:** BE-01, BE-02, BE-03, BE-04, DB-01, DB-02, DB-03, FE-01, FE-02, FE-03, FE-04, FE-05, MILESTONE_PLAN v6.0.0

---

## Tentang Dokumen Ini

Panduan ini adalah panduan kerja operasional untuk track Fullstack — satu orang yang mengerjakan **satu repository**: `vendor-ai`. Repository ini mencakup tiga lapisan teknis: database (Supabase migrations di `supabase/migrations/`), backend API Routes (Next.js di `apps/api`), dan frontend (Next.js di `apps/web`).

Dokumen ini **tidak menggantikan** GUIDE_DATABASE_ENGINEER, GUIDE_BACKEND_ENGINEER, dan GUIDE_FRONTEND_ENGINEER — ketiga panduan tersebut tetap menjadi referensi teknis per lapisan dan bisa dibaca secara mendalam sesuai lapisan yang sedang dikerjakan. Dokumen ini mengintegrasikan ketiganya menjadi **satu alur kerja per fitur**: urutan mana yang dikerjakan duluan, apa yang perlu disiapkan oleh satu lapisan agar lapisan berikutnya bisa berjalan, dan bagaimana tanda "lapisan ini selesai" ditetapkan sebelum pindah.

**Tidak ada kode Python di sini.** Semua yang menyangkut AI agent, scoring TOPSIS, RAG pipeline, dan SSE chat adalah tanggung jawab AI Engineer di repo `vendor-ai-agent`, dengan koordinasi yang terdefinisi di MILESTONE_PLAN.

---

## Prinsip Kerja: Sequential Per Lapisan

Dalam setiap fitur, urutan baku adalah **DB → BE → FE**:

```
DB (migration + RLS + index)
  ↓  skema tersedia
BE (API Routes + validasi + proxy ke FastAPI)
  ↓  endpoint tersedia di staging
FE (komponen + halaman + integrasi API)
  ↓  fitur selesai end-to-end
```

**Mengapa sequential dan bukan paralel?** Setiap lapisan bergantung pada lapisan sebelumnya secara nyata: query tidak bisa dijalankan tanpa skema, endpoint tidak bisa ditest tanpa tabel, dan UI tidak bisa terkoneksi tanpa endpoint. Mengerjakan paralel sebagai satu orang tidak menghemat waktu — hanya menambah context switching. 

**Pengecualian:** Frontend boleh dikerjakan lebih awal menggunakan **MSW mock** berdasarkan kontrak di BE-02. MSW memungkinkan komponen UI dibangun dan ditest tanpa endpoint nyata. Tapi FE hanya dinyatakan **selesai** setelah switch dari MSW ke API staging nyata berhasil.

---

## Prasyarat Sebelum Memulai

**Tools yang harus sudah terinstall:**

- Node.js 18+, pnpm 8+
- Supabase CLI (`supabase` command) sudah login ke akun Supabase
- Git dengan akses ke repo `vendor-ai`

**Yang harus ada sebelum coding F-00:**

- Dua Supabase project sudah dibuat: `vendor-ai-dev` (development) dan `vendor-ai-staging` (staging)
- Akses ke dashboard kedua project tersebut

**Environment variables (`vendor-ai`):**

| Variabel | Keterangan | Digunakan oleh |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL project Supabase | `apps/web` + `apps/api` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon key untuk client-side | `apps/web` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role untuk operasi admin | `apps/api` |
| `FASTAPI_URL` | URL internal FastAPI service | `apps/api` |
| `SERVICE_TO_SERVICE_TOKEN` | Token shared dengan AI Engineer | `apps/api` |

---

## Konvensi Penting

**Migration:**
- Format nama file: `YYYYMMDDHHMMSS_deskripsi_singkat.sql`
- Setiap file migration wajib menyertakan komentar rollback di header
- Jangan pernah mengedit migration file yang sudah dijalankan — buat migration baru
- RLS policy dibuat dalam migration file yang sama dengan tabel yang dilindungi

**Backend (BE-02, BE-03):**
- Defense in depth untuk auth: middleware Next.js → handler cek role → Supabase RLS
- Error codes harus konsisten sesuai BE-02 section 12.3
- Format response seragam: `{ success, data, meta }` untuk sukses, `{ success: false, error: { code, message } }` untuk error
- Tidak ada LLM call, scoring, atau RAG di `apps/api` — semua itu adalah domain AI Engineer

**Frontend (FE-02, FE-03, FE-04):**
- MSW dulu untuk setiap fitur baru, switch ke API nyata setelah staging siap
- Server Component sebagai default, `'use client'` hanya jika benar-benar perlu
- Komponen presentasional menerima data via props — tidak mengambil data sendiri
- MSW handler dinonaktifkan (bukan dihapus) setelah switch ke API nyata

**Branch:**
- Satu branch `develop` untuk semua pekerjaan di `vendor-ai` — tidak ada pemisahan per lapisan
- Format feature branch: `feature/F-XX-nama-singkat`
- Merge ke `develop` setelah satu fitur selesai end-to-end (DB + BE + FE semua ✅)

---

## F-00 — Environment Setup

**Tier:** 0 | **Estimasi:** 2–3 hari | **Koordinasi:** AI Engineer setup repo `vendor-ai-agent` secara paralel

### Urutan Pengerjaan

#### [DB] Inisialisasi Supabase

1. Inisialisasi Supabase CLI di root repo `vendor-ai`: `supabase init` — ini membuat folder `supabase/` dengan subfolder `migrations/`
2. Link ke project dev: `supabase link --project-ref [ref-dev]`
3. **Migration pertama (WAJIB migration paling awal):** Aktifkan pgvector

```
File: 20260607090000_enable_pgvector.sql
Isi: CREATE EXTENSION IF NOT EXISTS vector;
```

Tanpa ekstensi ini aktif pertama, migration apapun yang menggunakan kolom `vector(768)` akan gagal.

4. **Migration kedua:** Tabel `user`
   - Kolom: `id` (UUID PK = auth.users.id), `nama`, `email` (unik), `role` (enum: `staff`|`manager`), `avatar_url` (nullable), `created_at`, `updated_at`, `deleted_at`
   - RLS: SELECT milik sendiri (`id = auth.uid()`), UPDATE milik sendiri, INSERT via Auth trigger

5. **Migration ketiga:** Tabel `konfigurasi_kriteria`
   - Kolom: `id`, `kategori` (enum), `kriteria` (JSONB), `updated_by` (FK ke user.id), kolom standar
   - Index B-tree pada kolom `kategori`
   - RLS: SELECT semua authenticated, UPDATE manager only

6. Seed file `supabase/seed.sql` — isi konfigurasi kriteria default semua kategori (5 kriteria per kategori, bobot 30/25/20/15/10)
7. Aktifkan Supabase Realtime untuk tabel `agent_progress` (tabelnya dibuat di F-06, tapi konfigurasi Realtime bisa disiapkan sekarang)
8. Jalankan: `supabase db push` ke dev

#### [BE] Inisialisasi Monorepo

1. Buat struktur monorepo di root `vendor-ai`:

```
vendor-ai/
├── apps/
│   ├── api/    ← Next.js API Routes
│   └── web/    ← Next.js frontend
├── packages/
│   └── types/  ← Shared TypeScript types
├── supabase/   ← Sudah ada dari langkah DB
└── pnpm-workspace.yaml
```

2. Inisialisasi `apps/api` dengan Next.js 14+ App Router — struktur folder `app/api/v1/`
3. Setup TypeScript, Zod, Supabase JS Client di `apps/api`
4. Buat `GET /api/health` yang memeriksa koneksi ke Supabase
5. Generate service-to-service token (min 32 karakter random hex) — simpan di `SERVICE_TO_SERVICE_TOKEN`. Koordinasikan nilai yang sama dengan AI Engineer untuk disimpan di `vendor-ai-agent`
6. Buat `.env.example` di root `vendor-ai` dengan semua variabel yang dibutuhkan (lihat tabel di atas)
7. Buat file `FEATURE_STATUS.md` di root `vendor-ai` dengan template kosong

#### [FE] Inisialisasi Frontend

1. Inisialisasi `apps/web` di monorepo yang sudah dibuat di langkah BE
2. Install dependencies: shadcn/ui, Tailwind, TanStack Query, Zustand, Chart.js, MSW
3. Konfigurasi design tokens di `tailwind.config.ts` sesuai FE-02 section 5
4. Buat struktur folder di `apps/web/`: `app/`, `components/atomic/`, `components/composite/`, `components/layout/`, `components/feature/`, `components/charts/`, `hooks/`, `stores/`, `lib/api/`, `lib/constants/`, `test/handlers/`
5. Setup MSW: `msw init public/`, konfigurasi service worker untuk browser dan Node test environment
6. Inisialisasi tiga Zustand stores: `authStore`, `chatStore`, `notificationStore`
7. Setup TanStack Query `QueryClient` di layout root
8. Buat `lib/api/client.ts` sebagai base fetch wrapper dengan auth header injection dari `authStore`
9. Verifikasi `packages/types` dapat diimport dari `apps/web` tanpa error TypeScript

### Kriteria Selesai F-00

```
□ [DB] pgvector aktif di Supabase dev (SELECT * FROM pg_extension WHERE extname='vector')
□ [DB] Tabel 'user' dan 'konfigurasi_kriteria' terbuat dengan RLS aktif
□ [DB] Seed data konfigurasi tersedia untuk semua kategori
□ [DB] Supabase Realtime dikonfigurasi untuk tabel agent_progress
□ [DB] Semua migration berjalan bersih dari awal di environment dev fresh
□ [BE] Struktur monorepo vendor-ai terbuat: apps/web, apps/api, packages/types
□ [BE] GET /api/health mengembalikan 200 dengan status Supabase
□ [BE] Service-to-service token terkonfigurasi di apps/api
□ [FE] apps/web berjalan di lokal tanpa error console
□ [FE] MSW terkonfigurasi dan tidak throw error saat startup
□ [FE] Zustand stores terinisialisasi tanpa error
□ [ALL] Branch develop ada di repo vendor-ai
□ [ALL] FEATURE_STATUS.md ada di root vendor-ai
□ [ALL] Kedua track bisa menjalankan service masing-masing lokal tanpa bantuan
```

---

## F-01 — Auth & Login

**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 2–3 hari  
**Referensi:** BE-02 section 6, BE-03 section 4–5–6, DB-01 section 6.1, FE-03 P-01, SH-03 section 6

### Urutan Pengerjaan

#### [DB]

1. Verifikasi RLS tabel `user` dari F-00 sudah benar — uji manual: login sebagai user A, SELECT tabel user, harus hanya melihat baris miliknya sendiri
2. Buat dua akun test melalui Supabase Auth (bukan langsung ke tabel `user`):
   - `test-staff@vendor-ai.dev` — role: `staff`
   - `test-manager@vendor-ai.dev` — role: `manager`
   
   Password disimpan di password manager, tidak pernah di version control.

#### [BE]

1. Middleware route guard di `middleware.ts`: baca JWT, verifikasi dengan Supabase Auth, redirect/401 jika tidak valid, 403 jika role tidak cukup untuk route manager
2. `POST /api/v1/auth/login` — integrasi Supabase Auth `signInWithPassword()`, simpan refresh token di cookie HttpOnly, kembalikan access token + user dengan field `role`
3. `POST /api/v1/auth/logout` — `signOut()`, hapus cookie
4. `POST /api/v1/auth/refresh` — baca refresh token dari cookie, kembalikan access token baru
5. `GET /api/v1/users/me` — data user aktif dari tabel `user`
6. Rate limiting 5 req/menit di endpoint login. Security headers sesuai BE-03 section 6.5 di semua response auth

#### [FE]

1. Buat MSW handler untuk semua endpoint auth (format sesuai BE-02 section 6)
2. Implementasi halaman P-01 Login: form email + password, validasi inline, error state
3. Konfigurasi middleware route guard di Next.js: redirect ke `/login` jika tidak autentikasi
4. Implementasi token injection di `lib/api/client.ts` — baca token dari `authStore`
5. Implementasi token refresh otomatis saat access token expired
6. **Switch:** Setelah BE staging siap — ganti MSW dengan API nyata, nonaktifkan handler auth

### Kriteria Selesai F-01

```
□ [DB] Dua akun test (staff + manager) tersedia di Supabase dev
□ [DB] RLS: user A tidak bisa SELECT data user B (diuji manual)
□ [BE] POST /auth/login menghasilkan JWT dengan field 'role'
□ [BE] Refresh token tersimpan di cookie HttpOnly
□ [BE] POST /auth/refresh menghasilkan access token baru
□ [BE] Request ke-6 login dalam 1 menit mengembalikan 429
□ [FE] P-01: login berhasil redirect ke /dashboard
□ [FE] P-01: login gagal menampilkan error inline (bukan alert browser)
□ [FE] Route guard: akses /dashboard tanpa token redirect ke /login
□ [FE] Token refresh: request dengan token expired otomatis di-refresh
□ [ALL] FEATURE_STATUS.md: F-01 semua ✅
```

---

## F-02 — Layout & AppShell

**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 2–3 hari  
**Referensi:** FE-02 section 9, FE-03 section 5, FE-02 section 7

**DB:** Tidak ada task.  
**BE:** Tidak ada task.

#### [FE]

1. Bangun `AppShell`: layout 3-panel — sidebar (220px) + konten (fleksibel) + panel AI (360px)
2. Bangun `Sidebar`: logo, menu navigasi, info user. Menu Approval dan Settings hanya untuk Manager
3. Bangun `AIPanel` placeholder: input chat, area pesan, loading state — koneksi SSE belum aktif
4. Bangun atomic components: `StatusBadge` (6 variant), `ScoreBar` (warna per rentang nilai), `RankBadge`, `AgentStatusIcon` (5 status: idle/waiting/running/done/error)
5. Zero axe-core violation di AppShell dan Sidebar

### Kriteria Selesai F-02

```
□ [FE] AppShell: layout 3-panel ter-render konsisten
□ [FE] Sidebar: menu Manager tidak muncul untuk role staff
□ [FE] Sidebar: active state benar sesuai route aktif
□ [FE] AIPanel: placeholder ter-render, input dapat diketik
□ [FE] StatusBadge: 6 variant warna sesuai design tokens
□ [FE] AgentStatusIcon: animasi berjalan saat status 'running'
□ [FE] Zero axe-core violation di semua komponen ini
□ [ALL] FEATURE_STATUS.md: F-02 FE ✅ (DB/BE tidak ada task)
```

---

## F-03 — Konfigurasi Kriteria (Settings P-08)

**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 2–3 hari  
**Referensi:** BE-02 section 7, DB-01 section 6.1, FE-03 P-08, FE-02 section 8.3

### Urutan Pengerjaan

#### [DB]

1. Verifikasi index B-tree pada kolom `kategori` di `konfigurasi_kriteria` sudah ada dan digunakan (`EXPLAIN ANALYZE SELECT * FROM konfigurasi_kriteria WHERE kategori = 'X' AND deleted_at IS NULL` — harus Index Scan, bukan Seq Scan)
2. Verifikasi RLS memblokir UPDATE dari role `staff` (uji manual: login sebagai staff, coba UPDATE → harus error)

#### [BE]

1. `GET /api/v1/konfigurasi/kriteria` — ambil bobot aktif per kategori
2. `PUT /api/v1/konfigurasi/kriteria` — simpan perubahan bobot (Manager only). Validasi total semua bobot = 100, kembalikan `INVALID_WEIGHT_TOTAL` jika tidak
3. `GET /api/v1/kategori-pengadaan` — daftar kategori untuk dropdown

#### [FE]

1. Buat MSW handler untuk GET/PUT konfigurasi dan GET kategori
2. Implementasi `CriteriaWeightInput`: field bobot per kriteria dengan indikator total real-time
3. Implementasi halaman P-08: dropdown kategori, tabel kriteria, tombol simpan
4. Tombol simpan disabled selama total ≠ 100%
5. Route guard: redirect staff yang akses `/settings` ke `/dashboard`
6. **Switch:** Setelah BE staging siap — ganti MSW

### Kriteria Selesai F-03

```
□ [DB] EXPLAIN ANALYZE query konfigurasi menggunakan index (bukan Seq Scan)
□ [DB] Staff yang coba UPDATE konfigurasi mendapat error RLS
□ [BE] GET /konfigurasi/kriteria mengembalikan bobot aktif per kategori
□ [BE] PUT dengan total ≠ 100 mengembalikan INVALID_WEIGHT_TOTAL
□ [BE] Staff yang akses PUT mengembalikan 403
□ [FE] P-08: total bobot diperbarui real-time saat input berubah
□ [FE] P-08: tombol simpan disabled saat total ≠ 100%
□ [FE] P-08: tidak bisa diakses oleh staff (redirect ke dashboard)
□ [ALL] FEATURE_STATUS.md: F-03 semua ✅
```

---

## F-04 — Dashboard (P-02)

**Tier:** 1 | **Prerequisite:** F-01, F-02 | **Estimasi:** 2–3 hari  
**Referensi:** BE-02 section 7, DB-01 section 6.2, FE-03 P-02

### Urutan Pengerjaan

#### [DB]

1. Tabel `evaluasi` — kolom: `id`, `judul`, `kategori` (enum), `deskripsi`, `status` (enum lifecycle: `draft→processing→selesai→menunggu_approval→approved|butuh_revisi`), `budget_min` (nullable), `budget_max`, `deadline`, `prioritas_kriteria` (Text[], nullable), `lampiran_url` (nullable), `created_by` (FK user.id), `preferensi_perusahaan` (Text, nullable), kolom standar
   - Index composite B-tree: `(created_by, status, deleted_at)`
   - Index partial: `(deleted_at) WHERE deleted_at IS NULL`
   - RLS: staff SELECT miliknya, manager SELECT semua; INSERT authenticated; UPDATE sesuai role; DELETE tidak diizinkan (soft delete)

2. Tabel `vendor` — kolom: `id`, `evaluasi_id` (FK), `nama_perusahaan`, `kontak_atau_website` (nullable), `harga_penawaran` (BigInt IDR), `catatan` (nullable), `sumber_input` (enum: `manual`|`extracted`), kolom standar
   - Index B-tree pada `evaluasi_id`
   - RLS: mengikuti evaluasi induk

#### [BE]

1. `GET /api/v1/evaluasi` — daftar evaluasi dengan filter dan pagination. Filter `created_by` di-enforce berdasarkan role
2. `GET /api/v1/evaluasi/summary` — jumlah per status

#### [FE]

1. Buat MSW handler untuk GET evaluasi dan GET summary
2. Implementasi `EvaluasiRow` component
3. Implementasi halaman P-02: 4 stat cards + daftar evaluasi terbaru
4. Klik baris evaluasi → navigasi ke halaman relevan berdasarkan status
5. Refresh otomatis data setiap 30 detik (TanStack Query `refetchInterval`)
6. Badge khusus untuk Manager jika ada evaluasi menunggu approval
7. **Switch:** Setelah BE staging siap

### Kriteria Selesai F-04

```
□ [DB] Tabel evaluasi dan vendor terbuat dengan RLS dan index
□ [DB] RLS: staff A tidak bisa SELECT evaluasi milik staff B
□ [DB] EXPLAIN ANALYZE query daftar evaluasi < 100ms (dari DB-03 section 10)
□ [BE] GET /evaluasi mengembalikan daftar sesuai role
□ [BE] GET /evaluasi/summary mengembalikan jumlah per status
□ [FE] P-02: stat cards menampilkan jumlah yang benar
□ [FE] P-02: klik evaluasi status 'processing' → navigasi ke /evaluasi/:id/proses
□ [FE] P-02: data refresh otomatis tanpa reload halaman
□ [ALL] FEATURE_STATUS.md: F-04 semua ✅
```

---

## F-05 — Riwayat Evaluasi (P-06)

**Tier:** 1 | **Prerequisite:** F-01, F-02, F-04 | **Estimasi:** 1–2 hari  
**Referensi:** BE-02 section 7, FE-03 P-06

**DB:** Tidak ada migration baru. Verifikasi query dengan kombinasi filter (status + kategori + search + tanggal) masih memenuhi target performa.

#### [BE]

1. Verifikasi `GET /api/v1/evaluasi` dari F-04 — pastikan semua filter (status, kategori, search, tanggal) dan pagination berfungsi benar

#### [FE]

1. Buat MSW handler untuk GET evaluasi dengan berbagai kombinasi filter
2. Implementasi halaman P-06: tabel evaluasi, filter sidebar, search bar, pagination 20 item per halaman
3. Reuse `EvaluasiRow` dari F-04
4. **Switch:** Bisa piggyback dengan F-04 jika sudah switch

### Kriteria Selesai F-05

```
□ [BE] Filter status, kategori, tanggal, search berfungsi
□ [BE] Pagination bekerja (page, limit, total)
□ [FE] P-06: filter mengubah daftar yang ditampilkan
□ [FE] P-06: pagination 20 item per halaman
□ [ALL] FEATURE_STATUS.md: F-05 semua ✅
```

---

## F-06 — Buat Evaluasi: Requirement & Vendor Manual (P-03 Step 1–2)

**Tier:** 1 | **Prerequisite:** F-01, F-02, F-04 | **Estimasi:** 3–4 hari  
**Referensi:** BE-02 section 7, DB-01 section 6.6–6.7–6.8, FE-03 P-03, FE-02 section 10.1–8.2

### Urutan Pengerjaan

#### [DB]

1. Tabel `agent_progress` — kolom: `id`, `evaluasi_id` (FK), `agent_key` (enum 7 nilai: `data_collector, financial_analyzer, risk_assessor, performance_scorer, negotiation_assistant, qualitative_analyzer, preference_matcher`), `status` (enum: `idle|running|done|error`), `progress` (Integer 0–100), `pesan_terakhir` (nullable), `error_detail` (nullable), `started_at` (nullable), `finished_at` (nullable), kolom standar
   - Constraint unik: `(evaluasi_id, agent_key)`
   - Index B-tree pada `evaluasi_id`
   - Aktifkan Supabase Realtime untuk tabel ini (verifikasi dari dashboard: Database → Replication)

2. Tabel `hasil_evaluasi` — kolom sesuai DB-01 section 6.7 termasuk `summary_komparatif_kualitatif` (nullable), `preference_matching_result` (JSONB, nullable), `conflict_callout` (JSONB, nullable)
   - Constraint UNIQUE pada `evaluasi_id`
   - RLS: mengikuti evaluasi induk

3. Tabel `hasil_vendor` — kolom sesuai DB-01 section 6.8 termasuk `unique_offerings` (JSONB, nullable), `profil_kualitatif` (Text, nullable), `tingkat_kesesuaian_preferensi` (enum: `tinggi|sedang|rendah|tidak_relevan`, nullable)
   - Index B-tree pada `hasil_evaluasi_id`
   - RLS: mengikuti evaluasi induk

#### [BE]

1. `POST /api/v1/evaluasi` — buat evaluasi baru (status: draft), termasuk field `preferensi_perusahaan` (nullable)
2. `GET /api/v1/evaluasi/:id` — detail evaluasi + daftar vendor
3. `POST /api/v1/evaluasi/:id/vendor` — tambah vendor (max 10)
4. `DELETE /api/v1/evaluasi/:id/vendor/:vendorId` — hapus vendor
5. `POST /api/v1/evaluasi/:id/submit` — validasi minimal 2 vendor, ubah status ke `processing`, panggil FastAPI async (gunakan stub yang return 202 jika FastAPI belum siap)
6. `GET /api/v1/kategori-pengadaan` — daftar kategori

#### [FE]

1. Buat MSW handler untuk semua endpoint di atas
2. Implementasi `EvaluasiStepper`: navigasi antar step, data persists saat bolak-balik
3. Implementasi `VendorInputCard` mode manual: form input, tombol hapus
4. Implementasi halaman P-03: Step 1 (requirement + field preferensi opsional sesuai ADR-030), Step 2 (tambah vendor manual), Step 3 (konfirmasi ringkasan + tombol submit)
5. Validasi per step sebelum bisa lanjut
6. Setelah submit: redirect ke P-04 (tampilkan loading state)
7. **Switch:** Setelah BE staging siap

### Kriteria Selesai F-06

```
□ [DB] Tabel agent_progress terbuat dengan enum agent_key (7 nilai) dan unique constraint
□ [DB] Tabel hasil_evaluasi terbuat dengan UNIQUE constraint pada evaluasi_id
□ [DB] Tabel hasil_vendor terbuat dengan kolom kualitatif dan preferensi
□ [DB] Supabase Realtime aktif untuk tabel agent_progress
□ [BE] POST /evaluasi membuat record baru dengan status 'draft'
□ [BE] POST /evaluasi/:id/vendor dengan 11 vendor mengembalikan VENDOR_LIMIT_EXCEEDED
□ [BE] POST /evaluasi/:id/submit dengan 1 vendor mengembalikan INSUFFICIENT_VENDORS
□ [FE] P-03: step 1 tidak bisa lanjut jika field wajib kosong
□ [FE] P-03: data step 1 tetap ada saat user kembali dari step 2
□ [FE] P-03: vendor bisa ditambah dan dihapus di step 2
□ [FE] P-03: submit berhasil redirect ke /evaluasi/:id/proses
□ [ALL] FEATURE_STATUS.md: F-06 semua ✅
```

---

## F-07 — Upload Dokumen & Ekstraksi

**Tier:** 2 | **Prerequisite:** F-06 | **Estimasi:** 3–4 hari  
**Referensi:** BE-02 section 7, BE-04 section 3, AI-01 section 9, DB-01 section 6.4–6.5  
**Koordinasi AI Engineer:** AI Engineer mengerjakan `POST /v1/agent/ekstrak-dokumen` secara paralel

### Urutan Pengerjaan

#### [DB]

1. Tabel `dokumen_upload` — kolom sesuai DB-01 section 6.4 termasuk `indexing_rag_status` dan `chunk_count`
   - Index B-tree pada `evaluasi_id`
   - RLS: mengikuti evaluasi induk

2. Tabel `dokumen_chunk` — kolom sesuai DB-01 section 6.5 termasuk `embedding vector(768)` dan `teks_search tsvector`

   **Ikuti urutan ini dengan teliti (risiko self-referential FK):**
   
   - Langkah 1: Buat tabel tanpa self-referential FK (`parent_chunk_id` sebagai UUID nullable biasa)
   - Langkah 2: Setelah tabel terbuat, tambahkan FK constraint: `ALTER TABLE dokumen_chunk ADD CONSTRAINT fk_parent_chunk FOREIGN KEY (parent_chunk_id) REFERENCES dokumen_chunk(id)`
   - Langkah 3: Buat index B-tree dasar dalam migration yang sama: `evaluasi_id`, `vendor_id`, `parent_chunk_id`

3. Index vector dan full-text (**migration terpisah** karena karakteristik khusus):
   - Index HNSW pada `embedding` untuk vector similarity search (parameter: m=16, ef_construction=64)
   - Index GIN pada `teks_search` untuk full-text search

4. Bucket Supabase Storage: buat bucket `vendor-documents` sebagai **private**. Tambahkan storage policy: user hanya bisa akses file dari evaluasi miliknya

#### [BE]

1. `POST /api/v1/evaluasi/:id/dokumen` — terima upload multipart, validasi tipe (PDF/Excel) dan ukuran (max 10MB), upload ke Supabase Storage (`vendor-documents/evaluasi/{evaluasi_id}/{upload_id}_{nama_file}`), simpan metadata ke `dokumen_upload`, panggil FastAPI `POST /v1/agent/ekstrak-dokumen` async
2. `GET /api/v1/evaluasi/:id/dokumen/:uploadId/status` — polling status ekstraksi dan RAG indexing
3. Generate signed URL untuk akses file (masa berlaku 1 jam)

#### [FE]

1. Update MSW handler untuk upload dan status polling
2. Update `VendorInputCard` untuk mode upload: tampilkan status extracting/extracted/error
3. Polling status ekstraksi setiap 3 detik setelah upload (TanStack Query `refetchInterval`)
4. Tampilkan hasil ekstraksi yang bisa diedit sebelum disimpan
5. Indikator RAG indexing setelah ekstraksi selesai
6. **Switch:** Setelah BE dan AI Engineer staging siap

### Kriteria Selesai F-07

```
□ [DB] Tabel dokumen_upload terbuat dengan semua enum status
□ [DB] Tabel dokumen_chunk terbuat dengan urutan yang benar (tabel → self-ref FK → index)
□ [DB] Index HNSW pada embedding aktif; Index GIN pada teks_search aktif
□ [DB] Bucket 'vendor-documents' terbuat sebagai private
□ [BE] Upload file > 10MB mengembalikan FILE_TOO_LARGE
□ [BE] Upload file bukan PDF/Excel mengembalikan INVALID_FILE_TYPE
□ [BE] File tersimpan di Supabase Storage (verifikasi via dashboard)
□ [BE] POST dokumen mengembalikan 202 segera (async)
□ [BE] Status polling menunjukkan perubahan dari 'processing' ke 'done'
□ [FE] VendorInputCard: status 'extracting' tampil setelah upload
□ [FE] VendorInputCard: hasil ekstraksi ditampilkan dan bisa diedit
□ [ALL] FEATURE_STATUS.md: F-07 DB ✅, BE ✅, FE ✅ — koordinasikan AI ✅ dengan AI Engineer
```

---

## F-08 — Form Preferensi Opsional

**Tier:** 2 | **Prerequisite:** F-06 | **Estimasi:** 1 hari  
**Referensi:** FE-03 P-03 Step 1, DB-01 section 6.2, BE-02 section 7

### Urutan Pengerjaan

#### [DB]

Migration additive — tambah kolom nullable ke tabel yang sudah ada:

```sql
-- Migration: tambah kolom preferensi_perusahaan ke tabel evaluasi
-- Rollback: ALTER TABLE evaluasi DROP COLUMN preferensi_perusahaan;
ALTER TABLE evaluasi ADD COLUMN preferensi_perusahaan TEXT;
```

Catatan: Kolom ini sebenarnya sudah didefinisikan di skema F-04. Jika sudah ada, skip migration ini. Jika belum, tambahkan sekarang.

#### [BE]

1. Update `POST /api/v1/evaluasi` untuk menerima field `preferensi_perusahaan` (opsional)
2. Validasi: max 1.000 karakter, kembalikan `PREFERENCE_TOO_LONG` jika lebih

#### [FE]

1. Implementasi `PreferenceInput`: textarea dengan counter karakter dan placeholder contoh
2. Tambahkan ke P-03 Step 1, di bawah field requirement lain
3. Field tidak wajib — validasi step 1 tidak berubah

### Kriteria Selesai F-08

```
□ [DB] Kolom 'preferensi_perusahaan' ada di tabel evaluasi (TEXT, nullable)
□ [BE] POST /evaluasi menerima preferensi_perusahaan opsional
□ [BE] POST /evaluasi dengan preferensi > 1.000 karakter → PREFERENCE_TOO_LONG
□ [FE] P-03 Step 1: textarea preferensi tampil dengan counter karakter
□ [FE] P-03 Step 1: form bisa disubmit tanpa mengisi preferensi
□ [ALL] FEATURE_STATUS.md: F-08 semua ✅
```

---

## F-09 — Submit, Status Flow & Approval (P-03 Step 3, P-05 tombol kirim, P-07)

**Tier:** 2 | **Prerequisite:** F-06, F-04 | **Estimasi:** 3–4 hari  
**Referensi:** BE-02 section 7, DB-01 section 6.10, FE-03 P-07, FE-02 section 8.4

### Urutan Pengerjaan

#### [DB]

1. Tabel `approval_log` — kolom: `id`, `evaluasi_id` (FK), `manager_id` (FK user.id), `keputusan` (enum: `approved`|`rejected`), `komentar` (nullable di DB, wajib di aplikasi jika rejected), kolom standar
   - Index B-tree pada `evaluasi_id`
   - RLS: staff SELECT dari evaluasinya, manager SELECT semua + INSERT

2. Verifikasi transisi status evaluasi mengikuti lifecycle yang benar:  
   `draft → processing → selesai → menunggu_approval → approved | butuh_revisi`

#### [BE]

1. `PATCH /api/v1/evaluasi/:id/status` — ubah status dari `selesai` ke `menunggu_approval` (Staff only)
2. `POST /api/v1/evaluasi/:id/approval` — approve atau reject (Manager only), komentar wajib jika reject
3. Verifikasi filter `?status=menunggu_approval` di GET evaluasi berfungsi untuk P-07

#### [FE]

1. Buat MSW handler untuk PATCH status dan POST approval
2. Implementasi `ApprovalCard`: ringkasan evaluasi + form keputusan
3. Implementasi halaman P-07: tab "Menunggu" dan "Sudah Diproses", ApprovalCard per evaluasi
4. Tombol "Kirim ke Manager" di P-05 (placeholder konten P-05 dulu, tombol sudah bisa diklik)
5. Komentar wajib saat reject — tombol reject disabled jika komentar kosong
6. **Switch:** Setelah BE staging siap

### Kriteria Selesai F-09

```
□ [DB] Tabel approval_log terbuat dengan FK, index, dan RLS
□ [DB] RLS: staff tidak bisa INSERT ke approval_log
□ [BE] PATCH /evaluasi/:id/status oleh Manager mengembalikan 403
□ [BE] POST /approval reject tanpa komentar → VALIDATION_ERROR
□ [BE] POST /approval approve mengubah status evaluasi ke 'approved'
□ [FE] P-07: hanya bisa diakses Manager (staff redirect ke dashboard)
□ [FE] P-07: tab "Menunggu" menampilkan evaluasi dengan status menunggu_approval
□ [FE] P-07: tombol reject disabled jika komentar kosong
□ [FE] P-05: tombol "Kirim ke Manager" mengubah status dan disable dirinya sendiri
□ [ALL] FEATURE_STATUS.md: F-09 semua ✅
```

---

## Checkpoint Integrasi Tier 1–2

Sebelum memulai Tier 3, verifikasi integrasi menyeluruh dari F-00 s/d F-09.

**Happy path lengkap tanpa AI:**

```
1. Login sebagai Staff
2. Buat evaluasi baru (isi requirement + preferensi opsional)
3. Tambah 3 vendor manual + upload 1 dokumen PDF
4. Konfirmasi ekstraksi hasil dokumen
5. Submit evaluasi → redirect ke P-04 (loading state)
6. Login sebagai Manager
7. P-07: evaluasi muncul setelah staff kirim ke approval
8. Approve evaluasi → status berubah ke 'approved'
9. P-08: ubah bobot, simpan, buka lagi — bobot tersimpan
10. P-06: evaluasi muncul di riwayat dengan status yang benar
```

**Security checks:**

```
□ Staff tidak bisa akses evaluasi milik staff lain (403)
□ Staff tidak bisa akses P-07 dan P-08 (redirect)
□ RLS memblokir akses langsung ke database tanpa melalui aplikasi
□ Upload file > 10MB ditolak dengan pesan yang benar
```

**Technical checks:**

```
□ Semua query utama menggunakan index yang benar (EXPLAIN ANALYZE)
□ TanStack Query cache invalidation bekerja setelah mutasi
□ Token refresh otomatis berjalan saat access token expired
□ Tidak ada console error saat menjalankan happy path
□ E2E test happy path staff dan approval manager lulus di Playwright
□ Pipeline CI di repo vendor-ai hijau
```

---

## F-10 — AI Processing & Progress Real-time (P-04)

**Tier:** 3 | **Prerequisite:** F-06, F-07, Checkpoint | **Estimasi:** 8–12 hari  
**Referensi:** AI-01, AI-02 section 3–4–5, AI-04 section 5–6–7, FE-03 P-04, FE-02 section 10.2, FE-04 section 8.1, FE-05 section 9  
**Koordinasi AI Engineer:** AI Engineer mengerjakan seluruh pipeline 7 agent secara paralel

### Urutan Pengerjaan

#### [DB]

1. Verifikasi enum `agent_key` mencakup semua 7 agent dengan nama yang tepat
2. Verifikasi index `evaluasi_id` di `agent_progress` digunakan (EXPLAIN ANALYZE)
3. Verifikasi Supabase Realtime aktif: Dashboard → Database → Replication → agent_progress ada di daftar

#### [BE]

1. Update `POST /api/v1/evaluasi/:id/submit`: ganti stub dengan panggilan nyata ke FastAPI `POST /v1/agent/evaluasi/:id/start`

#### [FE]

1. Implementasi `AgentProgressPanel`:
   - Subscribe Supabase Realtime channel `evaluasi-progress-{evaluasiId}`
   - Tampilkan 7 agent dengan status dan progress masing-masing
   - State `waiting` untuk agent yang menunggu dependency sebelumnya (berbeda dari `idle`)
   - **Wajib:** Unsubscribe saat komponen unmount (`useEffect` cleanup) untuk mencegah memory leak
2. Implementasi halaman P-04 lengkap: daftar 7 agent, pesan per agent, estimasi waktu, warning jika ada agent error
3. Auto-redirect ke P-05 saat semua agent `done`

### Kriteria Selesai F-10

```
□ [DB] Enum agent_key mencakup semua 7 agent
□ [DB] Supabase Realtime aktif dan bisa menerima broadcast dari agent_progress
□ [BE] Submit evaluasi berhasil memanggil FastAPI /v1/agent/evaluasi/:id/start
□ [FE] P-04: status 7 agent update real-time tanpa reload
□ [FE] P-04: agent yang menunggu tampil dengan state 'waiting' yang berbeda dari 'idle'
□ [FE] P-04: warning tampil (bukan error fatal) jika ada agent yang gagal
□ [FE] P-04: auto-redirect ke P-05 saat semua agent done
□ [FE] P-04: Realtime unsubscribe saat navigasi ke halaman lain
□ [ALL] FEATURE_STATUS.md: F-10 DB ✅, BE ✅, FE ✅ — koordinasikan AI ✅ dengan AI Engineer
```

---

## F-11 — Hasil TOPSIS & Reasoning (P-05 Bagian 1–2–6)

**Tier:** 3 | **Prerequisite:** F-10 | **Estimasi:** 5–7 hari  
**Referensi:** AI-03, AI-02 section 5, BE-02 section 9, FE-03 P-05 Bagian 1–2–6, FE-02 section 10.3–10.5–11.1–11.2  
**Koordinasi AI Engineer:** AI Engineer mengerjakan scoring engine secara paralel

### Urutan Pengerjaan

#### [DB]

1. Verifikasi schema `hasil_evaluasi` konsisten dengan yang akan ditulis scoring engine: semua kolom ada, tipe data benar, UNIQUE constraint pada `evaluasi_id` aktif
2. Verifikasi schema `hasil_vendor` konsisten: kolom kualitatif dan preferensi ada

#### [BE]

1. `GET /api/v1/evaluasi/:id/hasil` — proxy ke FastAPI `GET /v1/scoring/evaluasi/:id/hasil`, kembalikan hasil lengkap ke frontend

#### [FE]

1. Buat MSW handler untuk GET hasil
2. Implementasi `RecommendationCard`: vendor rank 1 prominan, skor, reasoning 2 kalimat
3. Implementasi `VendorRankingTable`: semua vendor terurut skor, sort per kolom, expand/collapse detail per baris. Expand: `ScoreBar` per kriteria, catatan AI, `CriteriaBarChart`
4. Implementasi `AIReasoningPanel`: reasoning utama, kelemahan, rekomendasi negosiasi
5. Implementasi `ScoreRadarChart` sebagai alternatif view
6. P-05 Bagian 1 (narasi pengantar placeholder), Bagian 2 (RecommendationCard), Bagian 6 (AIReasoningPanel)
7. **Switch:** Setelah BE dan AI Engineer staging siap

### Kriteria Selesai F-11

```
□ [DB] Schema hasil_evaluasi dan hasil_vendor konsisten dengan output scoring engine
□ [DB] UNIQUE constraint pada hasil_evaluasi.evaluasi_id aktif dan diuji
□ [BE] GET /evaluasi/:id/hasil berhasil proxy ke FastAPI dan kembalikan data lengkap
□ [FE] P-05: RecommendationCard menampilkan vendor rank 1 dengan skor dan reasoning
□ [FE] P-05: VendorRankingTable menampilkan semua vendor terurut dari skor tertinggi
□ [FE] P-05: expand baris menampilkan ScoreBar dan catatan per kriteria
□ [FE] P-05: sort kolom berfungsi
□ [FE] P-05: AIReasoningPanel menampilkan tiga bagian reasoning
□ [ALL] FEATURE_STATUS.md: F-11 DB ✅, BE ✅, FE ✅ — koordinasikan AI ✅
```

---

## F-12 — Profil Kualitatif (P-05 Bagian 3–4)

**Tier:** 3 | **Prerequisite:** F-10, F-11 | **Estimasi:** 3–4 hari  
**Referensi:** AI-06 (Qualitative Analyzer Agent), AI-02 section 5.6, FE-03 P-05 Bagian 3–4, FE-02 (QualitativeProfileCard, QualitativeSummaryPanel)  
**Koordinasi AI Engineer:** AI Engineer mengimplementasi Qualitative Analyzer Agent secara paralel

### Urutan Pengerjaan

#### [DB]

Verifikasi kolom kualitatif ada di `hasil_vendor`. Jika belum, tambahkan via migration additive:

```sql
-- Jika belum ada dari F-06
ALTER TABLE hasil_vendor ADD COLUMN IF NOT EXISTS unique_offerings JSONB;
ALTER TABLE hasil_vendor ADD COLUMN IF NOT EXISTS profil_kualitatif TEXT;
```

#### [BE]

Tidak ada endpoint baru — data kualitatif sudah termasuk di response `GET /evaluasi/:id/hasil`.

#### [FE]

1. Implementasi `QualitativeProfileCard`: tampilkan unique offerings dan profil kualitatif per vendor
2. Implementasi `QualitativeSummaryPanel`: summary komparatif semua vendor
3. Tambahkan ke P-05 Bagian 3 dan Bagian 4
4. Update expand baris `VendorRankingTable` untuk menyertakan profil kualitatif

### Kriteria Selesai F-12

```
□ [DB] Kolom unique_offerings dan profil_kualitatif ada di hasil_vendor
□ [FE] P-05: QualitativeProfileCard tampil per vendor
□ [FE] P-05: QualitativeSummaryPanel tampil sebagai Bagian 4
□ [FE] VendorRankingTable expand: menyertakan profil kualitatif
□ [ALL] FEATURE_STATUS.md: F-12 DB ✅, FE ✅ — koordinasikan AI ✅
```

---

## F-13 — Rekomendasi Preferensi & Conflict Callout (P-05 Bagian 5)

**Tier:** 3 | **Prerequisite:** F-08, F-12 | **Estimasi:** 3–4 hari  
**Referensi:** AI-07 (Preference Matcher Agent), AI-02 section 5.7, FE-03 P-05 Bagian 1–5, FE-02 (PreferenceRecommendationCard, ConflictCallout)  
**Koordinasi AI Engineer:** AI Engineer mengimplementasi Preference Matcher Agent secara paralel

### Urutan Pengerjaan

#### [DB]

Verifikasi kolom preferensi ada. Jika belum, tambahkan via migration additive:

```sql
ALTER TABLE hasil_evaluasi ADD COLUMN IF NOT EXISTS preference_matching_result JSONB;
ALTER TABLE hasil_evaluasi ADD COLUMN IF NOT EXISTS conflict_callout JSONB;
ALTER TABLE hasil_vendor ADD COLUMN IF NOT EXISTS tingkat_kesesuaian_preferensi TEXT;
-- Tambahkan CHECK constraint untuk enum jika diperlukan
```

#### [BE]

Tidak ada endpoint baru — data preferensi sudah termasuk di response `GET /evaluasi/:id/hasil`.

#### [FE]

1. Implementasi `PreferenceRecommendationCard`: rekomendasi berbasis preferensi
2. Implementasi `ConflictCallout`: warning prominan, tidak bisa di-dismiss
3. Tambahkan ke P-05 Bagian 5 (hanya tampil jika preferensi diisi dan AI Engineer sudah mengimplementasi PM)
4. Update `VendorRankingTable`: tambah indikator `tingkat_kesesuaian_preferensi` di expand
5. Update P-05 Bagian 1: tampilkan narasi sesuai mode (netral vs opinionated)

### Kriteria Selesai F-13

```
□ [DB] Kolom preference_matching_result, conflict_callout, tingkat_kesesuaian_preferensi ada
□ [FE] P-05: Bagian 5 hanya tampil jika preferensi diisi
□ [FE] P-05: ConflictCallout tampil prominan jika ada konflik, tidak bisa di-dismiss
□ [FE] P-05: Bagian 1 narasi berbeda antara mode netral dan opinionated
□ [FE] VendorRankingTable expand: indikator kesesuaian preferensi tampil
□ [ALL] FEATURE_STATUS.md: F-13 DB ✅, FE ✅ — koordinasikan AI ✅
```

---

## F-14 — AI Chat Panel + RAG

**Tier:** 3 | **Prerequisite:** F-07, F-11 | **Estimasi:** 3–4 hari  
**Referensi:** AI-05 (RAG Specification), AI-02 section 6, BE-02 section 10–11.2, FE-02 section 9.3 (AIPanel), FE-04 section 8.2, FE-05 section 10  
**Koordinasi AI Engineer:** AI Engineer mengerjakan `POST /v1/chat/stream` dan `POST /v1/rag/query` secara paralel

### Urutan Pengerjaan

#### [DB]

1. Verifikasi index HNSW dan GIN pada tabel `dokumen_chunk` ada dan digunakan:

```sql
-- Verifikasi index ada
SELECT indexname, indexdef FROM pg_indexes
WHERE tablename = 'dokumen_chunk' AND (indexname LIKE '%embedding%' OR indexname LIKE '%teks_search%');

-- Test vector similarity search manual
SELECT id, teks_chunk FROM dokumen_chunk 
WHERE evaluasi_id = '[uuid]' AND is_parent = false AND deleted_at IS NULL
ORDER BY embedding <=> '[vektor dummy 768 dimensi]'::vector LIMIT 5;

-- Test full-text search manual
SELECT id, teks_chunk FROM dokumen_chunk
WHERE evaluasi_id = '[uuid]' AND teks_search @@ plainto_tsquery('indonesian', 'harga pengiriman')
AND deleted_at IS NULL LIMIT 5;
```

Kedua query harus menggunakan index (EXPLAIN ANALYZE) dan tidak error.

#### [BE]

Tidak ada endpoint baru di `apps/api`. `POST /v1/chat/stream` diakses langsung dari browser ke FastAPI (bukan via Next.js), sesuai arsitektur di AI-04 section 6.

#### [FE]

1. Aktifkan AIPanel: buka koneksi SSE ke FastAPI langsung saat user kirim pesan
2. Akumulasi token ke buffer, tampilkan typing indicator selama streaming
3. Setelah event `done`: pindahkan pesan lengkap dari buffer ke `chatStore`
4. Reset `chatStore` saat user berpindah evaluasi
5. Context injection otomatis berdasarkan halaman aktif (sesuai FE-04 section 8.2)
6. Sertakan riwayat chat maks 10 pesan di setiap request
7. **Wajib:** Tutup koneksi SSE saat komponen unmount untuk mencegah memory leak

### Kriteria Selesai F-14

```
□ [DB] Index HNSW dan GIN pada dokumen_chunk berfungsi (EXPLAIN ANALYZE tidak Seq Scan)
□ [DB] Query hybrid search manual berjalan tanpa error
□ [FE] AIPanel: pesan user dan respons AI tampil berurutan
□ [FE] AIPanel: typing indicator tampil selama streaming berlangsung
□ [FE] AIPanel: pesan tidak duplikat saat streaming selesai
□ [FE] AIPanel: reset saat user berpindah ke evaluasi berbeda
□ [FE] AIPanel: koneksi SSE tertutup saat navigasi ke halaman lain
□ [ALL] FEATURE_STATUS.md: F-14 DB ✅, FE ✅ — koordinasikan AI ✅ dengan AI Engineer
```

---

## Checkpoint Final — Release Readiness

### Happy Path End-to-End dengan Data Realistis

```
Login sebagai Staff
  ↓
Buat evaluasi baru:
  - Isi requirement lengkap
  - Isi preferensi bisnis (untuk test mode opinionated)
  - Tambah 3 vendor manual + upload 2 dokumen PDF nyata
  ↓
Konfirmasi hasil ekstraksi dokumen — edit jika perlu
  ↓
Submit → pantau P-04 (semua 7 agent harus selesai)
  ↓
Verifikasi P-05:
  - Ranking TOPSIS masuk akal berdasarkan data input
  - Reasoning naratif dalam Bahasa Indonesia dan relevan
  - Profil kualitatif per vendor terpopulasi
  - Rekomendasi preferensi muncul (karena preferensi diisi)
  - Conflict callout muncul jika ada konflik
  ↓
Chat dengan AIPanel — tanya tentang isi dokumen vendor
  ↓
Kirim ke Manager → Login sebagai Manager → P-07 → Approve
  ↓
Verifikasi status berubah ke 'approved' di P-06
```

### Verifikasi Teknis Final

```
□ [DB] Semua query memenuhi target P95 dari DB-03 section 10 (dengan data representatif)
□ [DB] Tidak ada deadlock saat 5 evaluasi diproses bersamaan
□ [DB] Supabase Pro aktif di production, PITR dikonfirmasi berfungsi
□ [DB] Restore test berhasil: backup terbaru ter-restore dengan integritas penuh
□ [BE] Semua skenario security test di SH-03 section 11.1 lulus
□ [BE] Rate limiting sesuai konfigurasi di BE-03 section 6.2
□ [BE] Audit trail: semua event di BE-03 section 9.2 tercatat
□ [BE] Spending alert OpenRouter, Tavily, dan Google Gemini terkonfigurasi
□ [FE] Semua 4 critical path E2E lulus di Playwright
□ [FE] Zero axe-core violation di semua 8 halaman
□ [FE] Semua form dapat diisi dengan keyboard saja
□ [FE] Visual regression: tidak ada perbedaan yang tidak disengaja
□ [ALL] Happy path end-to-end dengan 5 vendor (3 manual + 2 upload) berhasil
□ [ALL] Kualitas AI: reasoning masuk akal (judgment call, bukan checklist teknis)
□ [ALL] Pipeline CI di repo vendor-ai hijau
□ [ALL] Checklist deployment production SH-02 section 16 dicentang semua
```

---

## Referensi Cepat — Urutan Semua Migration

| Urutan | File Migration | Dibuat di Fitur |
|---|---|---|
| 1 | `enable_pgvector.sql` | F-00 |
| 2 | `create_user_table.sql` | F-00 |
| 3 | `create_konfigurasi_kriteria_table.sql` | F-00 |
| 4 | `create_evaluasi_table.sql` | F-04 |
| 5 | `create_vendor_table.sql` | F-04 |
| 6 | `create_agent_progress_table.sql` | F-06 |
| 7 | `create_hasil_evaluasi_table.sql` | F-06 |
| 8 | `create_hasil_vendor_table.sql` | F-06 |
| 9 | `create_dokumen_upload_table.sql` | F-07 |
| 10 | `create_dokumen_chunk_table.sql` | F-07 |
| 11 | `create_dokumen_chunk_indexes.sql` | F-07 (migration terpisah untuk HNSW + GIN) |
| 12 | `add_preferensi_perusahaan_to_evaluasi.sql` | F-08 (jika belum ada di F-04) |
| 13 | `create_approval_log_table.sql` | F-09 |

---

## Referensi Cepat — API Endpoints per Fitur

| Fitur | Endpoint `apps/api` | Keterangan |
|---|---|---|
| F-00 | `GET /api/health` | Verifikasi setup |
| F-01 | `POST /auth/login`, `POST /auth/logout`, `POST /auth/refresh`, `GET /users/me` | Auth flow |
| F-03 | `GET /konfigurasi/kriteria`, `PUT /konfigurasi/kriteria`, `GET /kategori-pengadaan` | Settings |
| F-04 | `GET /evaluasi`, `GET /evaluasi/summary` | Dashboard |
| F-06 | `POST /evaluasi`, `GET /evaluasi/:id`, `POST /evaluasi/:id/vendor`, `DELETE /evaluasi/:id/vendor/:vendorId`, `POST /evaluasi/:id/submit` | Buat evaluasi |
| F-07 | `POST /evaluasi/:id/dokumen`, `GET /evaluasi/:id/dokumen/:uploadId/status` | Upload |
| F-09 | `PATCH /evaluasi/:id/status`, `POST /evaluasi/:id/approval` | Approval |
| F-11 | `GET /evaluasi/:id/hasil` | Proxy ke FastAPI scoring |

**FastAPI endpoints (AI Engineer, bukan tanggung jawab Fullstack):** `POST /v1/agent/ekstrak-dokumen`, `POST /v1/agent/evaluasi/:id/start`, `GET /v1/scoring/evaluasi/:id/hasil`, `POST /v1/rag/query`, `POST /v1/chat/stream`

---

## Referensi Cepat — Koordinasi dengan AI Engineer

Fitur-fitur yang membutuhkan koordinasi eksplisit dengan track AI Engineer:

| Fitur | Yang dikoordinasikan | Cara koordinasi |
|---|---|---|
| F-00 | Service-to-service token | Nilai token yang sama di kedua `.env.example` |
| F-07 | Payload `POST /v1/agent/ekstrak-dokumen` | Kontrak di BE-02 section 7 |
| F-10 | Payload `POST /v1/agent/evaluasi/:id/start` | Kontrak di BE-02 section 8 |
| F-11 | Format response `GET /v1/scoring/evaluasi/:id/hasil` | Kontrak di BE-02 section 9 |
| F-14 | Format event SSE `POST /v1/chat/stream` | Kontrak di BE-02 section 10 |

Saat AI Engineer selesai di staging, update kolom AI di `FEATURE_STATUS.md` dan lakukan verifikasi end-to-end bersama.

---

*Dokumen ini adalah panduan kerja operasional. Untuk detail teknis per lapisan, baca GUIDE_DATABASE_ENGINEER, GUIDE_BACKEND_ENGINEER, dan GUIDE_FRONTEND_ENGINEER. Untuk detail teknis AI Engineer, baca GUIDE_AI_ENGINEER. Jika ada konflik antara panduan ini dan dokumen spec, dokumen spec yang berlaku.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-13 | Versi awal — dibuat sesuai ADR-036 (2 track solo developer); mengintegrasikan GUIDE_DATABASE_ENGINEER, GUIDE_BACKEND_ENGINEER, dan GUIDE_FRONTEND_ENGINEER menjadi satu alur feature-based per lapisan (DB → BE → FE) untuk semua fitur F-00 s/d F-14 | — |
