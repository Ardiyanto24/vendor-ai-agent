# Milestone Plan — AI Vendor Selection System

**Project:** AI Vendor Selection System  
**Dokumen:** Milestone Plan  
**Versi:** 5.0.0  
**Tanggal:** 2026-06-12  
**Status:** Draft

---

## Tentang Dokumen Ini

Milestone Plan ini mengorganisir pekerjaan sebagai **daftar fitur berurutan** — bukan sebagai layer teknis berurutan. Setiap fitur adalah unit kerja vertikal yang memotong database, backend, dan frontend secara bersamaan dan diselesaikan dalam satu jendela waktu pendek.

Model ini disebut feature-based development. Project dikerjakan dalam **dua track** sesuai ADR-036: track **Fullstack** mengerjakan seluruh repo `vendor-ai` (database via Supabase CLI di `supabase/migrations/`, backend di `apps/api`, frontend di `apps/web`) secara sequential per lapisan dalam setiap fitur — DB dahulu, lalu BE, lalu FE. Track **AI Engineer** mengerjakan repo `vendor-ai-agent` (FastAPI) secara terpisah untuk semua fitur yang melibatkan AI. Koordinasi antar track dilakukan melalui konvensi branch yang seragam dan `FEATURE_STATUS.md` yang terdefinisi di SH-02 section 6.

**Cara membaca dokumen ini:**

Setiap fitur memiliki kode unik (F-XX), daftar dependency ke fitur lain, estimasi durasi, task per lapisan teknis (DB → BE → FE) dan per track (Fullstack vs AI Engineer), dan kriteria selesai. Fitur dikelompokkan dalam **tier** berdasarkan dependency — fitur di tier yang lebih tinggi tidak boleh dimulai sebelum semua prerequisite di tier sebelumnya selesai.

---

## Gambaran Tier & Dependency

```
TIER 0 — Fondasi (tidak ada prerequisite)
  F-00  Environment Setup
  F-01  Auth & Login
  F-02  Layout & AppShell
  F-03  Konfigurasi Kriteria (Settings P-08)

TIER 1 — Butuh F-01 + F-02
  F-04  Dashboard (P-02)
  F-05  Riwayat Evaluasi (P-06)
  F-06  Buat Evaluasi — Requirement & Vendor (P-03 Step 1–2 tanpa upload)

TIER 2 — Butuh Tier 1
  F-07  Upload Dokumen & Ekstraksi (P-03 Step 2 dengan upload)
  F-08  Form Preferensi Opsional (P-03 Step 1 tambahan field)
  F-09  Submit & Approval Workflow (P-03 Step 3, P-05 tombol kirim, P-07)

TIER 3 — Butuh Tier 2 + FastAPI pipeline
  F-10  AI Processing & Progress (P-04 — 7 agent + Realtime)
  F-11  Hasil TOPSIS & Reasoning (P-05 Bagian 1–2–6)
  F-12  Profil Kualitatif (P-05 Bagian 3–4)
  F-13  Rekomendasi Preferensi & Conflict Callout (P-05 Bagian 5)
  F-14  AI Chat Panel + RAG (AIPanel semua halaman)
```

---

## F-00 — Environment Setup

**Tier:** 0 (tidak ada prerequisite)  
**Tipe:** Setup — semua track bekerja bersama  
**Estimasi durasi:** 2–3 hari  
**Dokumen referensi:** SH-02 section 5, BE-03 section 10, DB-02 section 4–5, FE-01 section 5–6–11

---

### Tujuan

Memastikan kedua track (Fullstack dan AI Engineer) bisa menjalankan service masing-masing secara lokal, terhubung ke Supabase dev, dan sudah mengikuti konvensi branch feature-based sebelum coding fitur dimulai.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Buat dua Supabase project: development dan staging
- Install dan hubungkan Supabase CLI ke kedua project
- Aktifkan pgvector: `CREATE EXTENSION IF NOT EXISTS vector` — ini harus jadi migration pertama
- Buat migration untuk dua tabel awal yang tidak punya dependency: `user` dan `konfigurasi_kriteria`
- Buat seed file untuk konfigurasi kriteria default semua kategori (5 kriteria, bobot 30/25/20/15/10)
- Aktifkan Supabase Realtime untuk tabel `agent_progress`
- Pastikan file migration tersimpan di `supabase/migrations/` dalam repo `vendor-ai`
- Buat file `FEATURE_STATUS.md` di root `vendor-ai` dengan template kosong

**[BE] Fullstack — Backend:**
- Inisialisasi monorepo `vendor-ai` dengan pnpm workspaces: buat struktur `apps/web`, `apps/api`, `packages/types`
- Inisialisasi `apps/api` dengan Next.js 14 App Router (khusus `app/api/v1/`)
- Buat `.env.example` untuk `vendor-ai` (variabel `apps/web` + `apps/api`) dengan semua variabel yang dibutuhkan
- Buat `GET /api/health` di `apps/api` yang memeriksa koneksi ke Supabase
- Generate service-to-service token dan simpan di environment `apps/api` (koordinasi dengan AI Engineer)
- Buat file `FEATURE_STATUS.md` di root `vendor-ai` dengan template kosong

**[AI] AI Engineer:**
- Inisialisasi repository `vendor-ai-agent` dengan FastAPI Python 3.11+
- Setup virtual environment dan `requirements.txt` dengan semua dependencies: fastapi, uvicorn, langchain, langgraph, openai, google-generativeai, tavily-python, supabase, pdfplumber, numpy, scipy, pydantic
- Buat struktur folder: `agents/`, `scoring/`, `rag/`, `prompts/`, `tests/`
- Buat `.env.example` untuk `vendor-ai-agent` dengan semua variabel yang dibutuhkan
- Buat `GET /health` di FastAPI yang memeriksa koneksi ke Supabase, OpenRouter, Google Gemini, dan Tavily
- Simpan service-to-service token di environment `vendor-ai-agent` (koordinasi dengan track Fullstack)
- Buat file `FEATURE_STATUS.md` di root `vendor-ai-agent` dengan template kosong

**[FE] Fullstack — Frontend:**
- Inisialisasi `apps/web` di monorepo `vendor-ai` dengan Next.js 14 App Router (monorepo sudah dibuat di task [BE] di atas)
- Install semua dependency di `apps/web`: shadcn/ui, Tailwind, TanStack Query, Zustand, Chart.js, MSW
- Konfigurasi design tokens di `tailwind.config.ts`
- Setup Zustand stores: `authStore`, `chatStore`, `notificationStore`
- Setup TanStack Query client dengan konfigurasi global
- Setup MSW: install, konfigurasi, buat folder `test/handlers/` per domain
- Verifikasi `packages/types` dapat diimport dari `apps/web`

### Kriteria selesai F-00

```
□ [DB] pgvector aktif di Supabase dev
□ [DB] Tabel 'user' dan 'konfigurasi_kriteria' terbuat di dev
□ [DB] Seed data konfigurasi kriteria tersedia untuk semua kategori
□ [DB] Supabase Realtime aktif untuk tabel agent_progress
□ [DB] File migration tersimpan di supabase/migrations/ dalam vendor-ai
□ [BE] Struktur monorepo vendor-ai terbuat: apps/web, apps/api, packages/types
□ [BE] GET /api/health (apps/api) merespons 200 di lokal
□ [BE] Service-to-service token terkonfigurasi di apps/api
□ [AI] GET /health (vendor-ai-agent) merespons 200 di lokal
□ [AI] Service-to-service token terkonfigurasi di vendor-ai-agent
□ [AI] Struktur folder vendor-ai-agent terbuat: agents/, scoring/, rag/, prompts/, tests/
□ [FE] apps/web berjalan di lokal tanpa error console
□ [FE] MSW terkonfigurasi dan tidak throw error saat startup
□ [FE] Zustand stores terinisialisasi tanpa error
□ [FE] packages/types dapat diimport dari apps/web tanpa error
□ [ALL] Branch structure ada: develop di vendor-ai dan develop di vendor-ai-agent
□ [ALL] FEATURE_STATUS.md ada di root vendor-ai dan root vendor-ai-agent
□ [ALL] Kedua track bisa menjalankan service masing-masing lokal tanpa bantuan
```

---

## F-01 — Auth & Login

**Tier:** 0  
**Prerequisite:** F-00  
**Tipe:** Fitur vertikal — DB + BE + FE  
**Estimasi durasi:** 2–3 hari  
**Dokumen referensi:** BE-02 section 6, BE-03 section 4–5–6, FE-03 P-01, FE-01 section 7.3, SH-03 section 6

---

### Tujuan

Membangun sistem autentikasi end-to-end: tabel user di database, endpoint login/logout/refresh di backend, dan halaman login di frontend dengan route guard.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Verifikasi tabel `user` dari F-00 sudah memiliki RLS yang benar: user hanya bisa baca data dirinya sendiri
- Buat seed data: dua akun test — satu staff, satu manager — untuk digunakan selama development

**[BE] Fullstack — Backend:**
- Implementasi `POST /api/v1/auth/login` — integrasi Supabase Auth, kembalikan JWT + role
- Implementasi `POST /api/v1/auth/logout` — invalidasi sesi di Supabase
- Implementasi `POST /api/v1/auth/refresh` — perbarui access token
- Implementasi `GET /api/v1/users/me` — data profil user aktif
- JWT payload harus menyertakan field `role`
- Simpan refresh token di cookie HttpOnly
- Rate limiting 5 req/menit di endpoint login
- Security headers di semua response

**[FE] Fullstack — Frontend:**
- Buat MSW handler untuk semua endpoint auth (format sesuai BE-02 section 6)
- Implementasi halaman P-01 Login: form email + password, error inline
- Konfigurasi middleware route guard: redirect ke `/login` jika tidak autentikasi
- Implementasi token injection di base fetch wrapper
- Implementasi token refresh otomatis saat access token expired
- Setelah BE ready: switch dari MSW ke API staging, nonaktifkan handler auth

### Kriteria selesai F-01

```
□ [DB] Dua akun test (staff + manager) tersedia di Supabase dev
□ [DB] RLS: user hanya bisa SELECT data dirinya sendiri
□ [BE] POST /auth/login menghasilkan JWT dengan field 'role'
□ [BE] Refresh token tersimpan di cookie HttpOnly
□ [BE] POST /auth/refresh menghasilkan access token baru yang valid
□ [BE] Request ke-6 login dalam 1 menit mengembalikan 429
□ [BE] Security headers tersedia di response login
□ [FE] P-01: login berhasil redirect ke /dashboard
□ [FE] P-01: login gagal menampilkan error inline (bukan alert browser)
□ [FE] Route guard: akses /dashboard tanpa token redirect ke /login
□ [FE] Token refresh: request dengan token expired otomatis di-refresh
□ [ALL] FEATURE_STATUS.md diperbarui: F-01 semua ✅
```

---

## F-02 — Layout & AppShell

**Tier:** 0  
**Prerequisite:** F-00  
**Tipe:** Fitur FE-only — tidak butuh BE atau DB baru  
**Estimasi durasi:** 2–3 hari  
**Dokumen referensi:** FE-02 section 9, FE-03 section 5, FE-02 section 7

---

### Tujuan

Membangun kerangka visual aplikasi yang konsisten di semua halaman: layout 3-panel, sidebar dengan navigasi role-aware, panel AI placeholder, dan atomic components yang digunakan di mana-mana.

### Task per lapisan & track

**[DB] Fullstack — Database:** Tidak ada task DB.

**[BE] Fullstack — Backend:** Tidak ada task BE.

**[FE] Fullstack — Frontend:**
- Bangun `AppShell`: layout 3-panel — sidebar (220px) + konten (fleksibel) + panel AI (360px)
- Bangun `Sidebar`: logo, menu navigasi, info user; menu Approval dan Settings hanya muncul untuk Manager
- Bangun `AIPanel` placeholder: input chat, area pesan, loading state — koneksi SSE belum aktif
- Bangun atomic components: `StatusBadge` (6 variant), `ScoreBar` (warna per rentang), `RankBadge`, `AgentStatusIcon` (4 status + animasi running)
- Verifikasi layout konsisten di semua ukuran layar yang didukung
- Zero axe-core violation di AppShell dan Sidebar

### Kriteria selesai F-02

```
□ [FE] AppShell: layout 3-panel ter-render konsisten
□ [FE] Sidebar: menu Manager (Approval, Settings) tidak muncul untuk role staff
□ [FE] Sidebar: active state benar sesuai route aktif
□ [FE] AIPanel: placeholder ter-render, input dapat diketik
□ [FE] StatusBadge: 6 variant warna sesuai design tokens
□ [FE] ScoreBar: warna berubah sesuai rentang nilai
□ [FE] AgentStatusIcon: animasi berjalan saat status 'running'
□ [FE] Zero axe-core violation di semua komponen
□ [ALL] FEATURE_STATUS.md diperbarui: F-02 FE ✅ (tidak ada DB/BE)
```

---

## F-03 — Konfigurasi Kriteria (Settings P-08)

**Tier:** 0  
**Prerequisite:** F-00  
**Tipe:** Fitur vertikal — DB + BE + FE  
**Estimasi durasi:** 2–3 hari  
**Dokumen referensi:** BE-02 section 7 (GET/PUT konfigurasi), DB-01 section 6.1, FE-03 P-08, FE-02 section 8.3

---

### Tujuan

Membangun halaman Settings P-08 tempat Manager mengkonfigurasi bobot kriteria per kategori. Fitur ini independen dari fitur evaluasi sehingga bisa dikerjakan sejak awal.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Verifikasi tabel `konfigurasi_kriteria` dari F-00 sudah memiliki index dan RLS yang benar
- RLS: hanya Manager yang bisa UPDATE, semua role authenticated bisa SELECT

**[BE] Fullstack — Backend:**
- Implementasi `GET /api/v1/konfigurasi/kriteria` — ambil bobot aktif per kategori
- Implementasi `PUT /api/v1/konfigurasi/kriteria` — simpan perubahan bobot (Manager only)
- Validasi: total semua bobot harus tepat 100, kembalikan `INVALID_WEIGHT_TOTAL` jika tidak
- `GET /api/v1/kategori-pengadaan` — daftar kategori untuk dropdown

**[FE] Fullstack — Frontend:**
- Buat MSW handler untuk GET/PUT konfigurasi dan GET kategori
- Implementasi `CriteriaWeightInput`: field bobot per kriteria dengan indikator total real-time
- Implementasi halaman P-08: dropdown kategori, tabel kriteria, tombol simpan
- Tombol simpan disabled selama total ≠ 100%
- Route guard: redirect staff yang akses `/settings` ke `/dashboard`
- Setelah BE ready: switch dari MSW ke API staging

### Kriteria selesai F-03

```
□ [DB] RLS: Manager bisa UPDATE konfigurasi, staff hanya SELECT
□ [BE] GET /konfigurasi/kriteria mengembalikan bobot aktif per kategori
□ [BE] PUT /konfigurasi/kriteria dengan total ≠ 100 mengembalikan INVALID_WEIGHT_TOTAL
□ [BE] Staff yang akses PUT mengembalikan 403
□ [FE] P-08: total bobot diperbarui real-time saat input berubah
□ [FE] P-08: tombol simpan disabled saat total ≠ 100%
□ [FE] P-08: tidak bisa diakses oleh staff (redirect ke dashboard)
□ [ALL] FEATURE_STATUS.md diperbarui: F-03 semua ✅
```

---

## F-04 — Dashboard (P-02)

**Tier:** 1  
**Prerequisite:** F-01, F-02  
**Tipe:** Fitur vertikal — DB + BE + FE  
**Estimasi durasi:** 2–3 hari  
**Dokumen referensi:** BE-02 section 7 (GET evaluasi, GET summary), FE-03 P-02, DB-01 section 6.2

---

### Tujuan

Membangun halaman Dashboard sebagai landing page setelah login: stat cards per status dan daftar evaluasi terbaru. Ini adalah halaman pertama yang membutuhkan data dari tabel `evaluasi`.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Buat migration tabel `evaluasi` (foreign key ke `user`)
- Buat migration tabel `vendor` (foreign key ke `evaluasi`)
- RLS: staff hanya bisa SELECT evaluasi miliknya, Manager bisa SELECT semua
- Index: `(created_by, status, deleted_at)` di tabel evaluasi

**[BE] Fullstack — Backend:**
- Implementasi `GET /api/v1/evaluasi` — daftar evaluasi dengan filter dan pagination
- Implementasi `GET /api/v1/evaluasi/summary` — jumlah per status
- Filter created_by di-enforce di backend berdasarkan role (staff tidak bisa lihat milik orang lain)

**[FE] Fullstack — Frontend:**
- Buat MSW handler untuk GET evaluasi dan GET summary
- Implementasi komponen `EvaluasiRow`
- Implementasi halaman P-02: 4 stat cards + daftar evaluasi terbaru
- Klik baris evaluasi → navigasi ke halaman relevan berdasarkan status
- Refresh otomatis data setiap 30 detik
- Badge khusus untuk Manager jika ada evaluasi menunggu approval
- Setelah BE ready: switch dari MSW ke API staging

### Kriteria selesai F-04

```
□ [DB] Tabel evaluasi dan vendor terbuat dengan RLS dan index
□ [DB] RLS: staff A tidak bisa SELECT evaluasi milik staff B
□ [BE] GET /evaluasi mengembalikan daftar sesuai role (staff lihat miliknya saja)
□ [BE] GET /evaluasi/summary mengembalikan jumlah per status
□ [FE] P-02: stat cards menampilkan jumlah yang benar
□ [FE] P-02: klik evaluasi dengan status 'processing' → navigasi ke /evaluasi/:id/proses
□ [FE] P-02: data refresh otomatis tanpa reload halaman
□ [ALL] FEATURE_STATUS.md diperbarui: F-04 semua ✅
```

---

## F-05 — Riwayat Evaluasi (P-06)

**Tier:** 1  
**Prerequisite:** F-01, F-02, F-04 (butuh tabel evaluasi)  
**Tipe:** Fitur vertikal — BE + FE (DB tidak ada task baru)  
**Estimasi durasi:** 1–2 hari  
**Dokumen referensi:** BE-02 section 7 (GET evaluasi), FE-03 P-06

---

### Tujuan

Membangun halaman Riwayat P-06 sebagai view yang lebih lengkap dari daftar evaluasi — dengan filter, search, dan pagination penuh.

### Task per lapisan & track

**[DB] Fullstack — Database:** Tidak ada migration baru. Tabel evaluasi sudah ada dari F-04.

**[BE] Fullstack — Backend:**
- `GET /api/v1/evaluasi` sudah diimplementasi di F-04 — verifikasi semua filter (status, kategori, search, tanggal) berfungsi dengan benar

**[FE] Fullstack — Frontend:**
- Buat MSW handler untuk GET evaluasi dengan berbagai kombinasi filter
- Implementasi halaman P-06: tabel evaluasi, filter sidebar, search bar, pagination 20 item per halaman
- Reuse komponen `EvaluasiRow` dari F-04
- Setelah BE ready: switch dari MSW ke API staging (bisa piggyback dengan F-04 jika sudah switch)

### Kriteria selesai F-05

```
□ [BE] Filter status, kategori, tanggal, dan search berfungsi di GET /evaluasi
□ [BE] Pagination bekerja dengan benar (page, limit, total)
□ [FE] P-06: filter mengubah daftar yang ditampilkan
□ [FE] P-06: search real-time atau via tombol
□ [FE] P-06: pagination 20 item per halaman
□ [ALL] FEATURE_STATUS.md diperbarui: F-05 semua ✅
```

---

## F-06 — Buat Evaluasi: Requirement & Vendor Manual (P-03 Step 1–2 tanpa upload)

**Tier:** 1  
**Prerequisite:** F-01, F-02, F-04 (butuh tabel evaluasi + vendor)  
**Tipe:** Fitur vertikal — DB + BE + FE  
**Estimasi durasi:** 3–4 hari  
**Dokumen referensi:** BE-02 section 7 (POST evaluasi, POST vendor, DELETE vendor, POST submit), FE-03 P-03, FE-02 section 10.1 (EvaluasiStepper) dan 8.2 (VendorInputCard)

---

### Tujuan

Membangun alur pembuatan evaluasi baru — stepper 3 langkah, input requirement, tambah/hapus vendor secara manual, dan konfirmasi submit. Upload dokumen belum termasuk (itu F-07).

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Buat migration tabel `agent_progress` (foreign key ke `evaluasi`) — dibutuhkan saat submit
- Buat migration tabel `hasil_evaluasi` dan `hasil_vendor` — dibutuhkan saat scoring selesai (bisa disiapkan lebih awal)
- Verifikasi constraint: minimal 2 vendor divalidasi di level aplikasi, bukan database

**[BE] Fullstack — Backend:**
- `POST /api/v1/evaluasi` — buat evaluasi baru (status: draft), termasuk field `preferensi_perusahaan` (nullable)
- `GET /api/v1/evaluasi/:id` — detail evaluasi beserta daftar vendor
- `POST /api/v1/evaluasi/:id/vendor` — tambah vendor (max 10)
- `DELETE /api/v1/evaluasi/:id/vendor/:vendorId` — hapus vendor
- `POST /api/v1/evaluasi/:id/submit` — validasi minimal 2 vendor, ubah status ke processing, panggil FastAPI async (FastAPI endpoint belum ada — gunakan stub yang langsung return 202)
- `GET /api/v1/kategori-pengadaan` — daftar kategori untuk dropdown

**[FE] Fullstack — Frontend:**
- Buat MSW handler untuk semua endpoint di atas
- Implementasi `EvaluasiStepper`: navigasi antar step, data persists saat bolak-balik
- Implementasi `VendorInputCard` mode manual: form input, tombol hapus
- Implementasi halaman P-03: Step 1 (requirement + field preferensi opsional), Step 2 (tambah vendor manual), Step 3 (konfirmasi ringkasan + tombol submit)
- Validasi per step sebelum bisa lanjut
- Setelah submit: redirect ke P-04 (belum ada konten, tampilkan loading state)
- Setelah BE ready: switch dari MSW ke API staging

### Kriteria selesai F-06

```
□ [DB] Tabel agent_progress, hasil_evaluasi, hasil_vendor terbuat
□ [BE] POST /evaluasi membuat record baru dengan status 'draft'
□ [BE] POST /evaluasi/:id/vendor dengan 11 vendor mengembalikan VENDOR_LIMIT_EXCEEDED
□ [BE] POST /evaluasi/:id/submit dengan 1 vendor mengembalikan INSUFFICIENT_VENDORS
□ [BE] Staff tidak bisa akses evaluasi milik staff lain (403)
□ [FE] P-03: step 1 tidak bisa lanjut jika field wajib kosong
□ [FE] P-03: data step 1 tetap ada saat user kembali dari step 2
□ [FE] P-03: vendor bisa ditambah dan dihapus di step 2
□ [FE] P-03: step 3 menampilkan ringkasan yang benar
□ [FE] P-03: submit berhasil redirect ke /evaluasi/:id/proses
□ [ALL] FEATURE_STATUS.md diperbarui: F-06 semua ✅
```

---

## F-07 — Upload Dokumen & Ekstraksi

**Tier:** 2  
**Prerequisite:** F-06 (butuh evaluasi dan vendor flow yang berfungsi)  
**Tipe:** Fitur vertikal — DB + BE + FE  
**Estimasi durasi:** 3–4 hari  
**Dokumen referensi:** BE-02 section 7 (POST dokumen, GET status ekstraksi), BE-04 section 3 (Supabase Storage), AI-01 section 9 (ekstraksi + RAG indexing), DB-01 section 6.4 (dokumen_upload), DB-01 section 6.5 (dokumen_chunk)

---

### Tujuan

Memungkinkan user mengupload dokumen penawaran PDF/Excel. AI mengekstrak data vendor secara otomatis (async), hasilnya ditampilkan untuk dikonfirmasi user. Pipeline RAG indexing juga berjalan setelah ekstraksi selesai.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Buat migration tabel `dokumen_upload`
- Buat migration tabel `dokumen_chunk` (butuh pgvector yang sudah diaktifkan di F-00)
- Aktifkan Supabase Storage: buat bucket `vendor-documents` sebagai private

**[BE] Fullstack — Backend:**
- `POST /api/v1/evaluasi/:id/dokumen` — upload ke Supabase Storage, panggil FastAPI ekstraksi async
- `GET /api/v1/evaluasi/:id/dokumen/:uploadId/status` — polling status ekstraksi dan RAG indexing
- Validasi: hanya PDF dan Excel, max 10MB
- Signed URL untuk akses file di Supabase Storage

**[AI] AI Engineer:**
- FastAPI `POST /v1/agent/ekstrak-dokumen` — ekstrak field dari PDF/Excel via LLM, simpan hasil ke `dokumen_upload`, lalu mulai RAG indexing (simpan chunks ke `dokumen_chunk`)

**[FE] Fullstack — Frontend:**
- Update MSW handler untuk upload dan status polling
- Update `VendorInputCard` untuk mode upload: tampilkan status extracting/extracted/error
- Polling status ekstraksi setiap 3 detik setelah upload
- Tampilkan hasil ekstraksi yang bisa diedit sebelum disimpan
- Indikator RAG indexing setelah ekstraksi selesai
- Setelah BE ready: switch dari MSW ke API staging

### Kriteria selesai F-07

```
□ [DB] Tabel dokumen_upload dan dokumen_chunk terbuat
□ [DB] Bucket vendor-documents terkonfigurasi sebagai private
□ [BE] Upload file > 10MB mengembalikan FILE_TOO_LARGE
□ [BE] Upload file bukan PDF/Excel mengembalikan INVALID_FILE_TYPE
□ [BE] File tersimpan di Supabase Storage (verifikasi via dashboard)
□ [BE] Ekstraksi berjalan async — POST dokumen mengembalikan 202 segera
□ [BE] Status polling menunjukkan perubahan dari 'processing' ke 'done'
□ [AI] RAG indexing: chunks tersimpan di tabel dokumen_chunk setelah ekstraksi selesai
□ [FE] VendorInputCard: status 'extracting' tampil setelah upload
□ [FE] VendorInputCard: hasil ekstraksi ditampilkan dan bisa diedit
□ [ALL] FEATURE_STATUS.md diperbarui: F-07 semua ✅
```

---

## F-08 — Form Preferensi Opsional

**Tier:** 2  
**Prerequisite:** F-06 (butuh form P-03 Step 1 yang sudah ada)  
**Tipe:** Fitur kecil — DB + BE + FE  
**Estimasi durasi:** 1 hari  
**Dokumen referensi:** FE-03 P-03 Step 1, FE-02 section (PreferenceInput), DB-01 section 6.2 (kolom preferensi_perusahaan), BE-02 section 7 (POST evaluasi)

---

### Tujuan

Menambahkan field textarea opsional di P-03 Step 1 untuk preferensi bisnis perusahaan. Field ini bersifat additive — tidak mengubah alur yang sudah ada, hanya menambah field nullable.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Tambah kolom `preferensi_perusahaan` (TEXT, nullable) ke tabel `evaluasi` via migration baru

**[BE] Fullstack — Backend:**
- Update `POST /api/v1/evaluasi` untuk menerima field `preferensi_perusahaan` (opsional)
- Validasi: max 1.000 karakter, kembalikan `PREFERENCE_TOO_LONG` jika lebih

**[FE] Fullstack — Frontend:**
- Implementasi komponen `PreferenceInput`: textarea dengan counter karakter dan placeholder contoh
- Tambahkan `PreferenceInput` ke P-03 Step 1, di bawah field requirement lain
- Field tidak wajib — validasi step 1 tidak berubah

### Kriteria selesai F-08

```
□ [DB] Kolom preferensi_perusahaan ada di tabel evaluasi (nullable)
□ [BE] POST /evaluasi menerima preferensi_perusahaan opsional
□ [BE] POST /evaluasi dengan preferensi > 1.000 karakter mengembalikan PREFERENCE_TOO_LONG
□ [FE] P-03 Step 1: textarea preferensi tampil dengan counter karakter
□ [FE] P-03 Step 1: form bisa disubmit tanpa mengisi preferensi
□ [ALL] FEATURE_STATUS.md diperbarui: F-08 semua ✅
```

---

## F-09 — Submit, Status Flow & Approval (P-03 Step 3, P-05 tombol kirim, P-07)

**Tier:** 2  
**Prerequisite:** F-06, F-04 (butuh evaluasi yang bisa dikirim dan dilihat)  
**Tipe:** Fitur vertikal — DB + BE + FE  
**Estimasi durasi:** 3–4 hari  
**Dokumen referensi:** BE-02 section 7 (PATCH status, POST approval), FE-03 P-07, FE-02 section 8.4 (ApprovalCard), DB-01 section 6.9 (approval_log)

---

### Tujuan

Membangun seluruh approval workflow: tombol "Kirim ke Manager" di P-05, halaman P-07 untuk Manager mereview dan memutuskan, dan perubahan status evaluasi yang mengikutinya.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Buat migration tabel `approval_log`
- Pastikan transisi status di tabel evaluasi sesuai dengan aturan di DB-01 section 8

**[BE] Fullstack — Backend:**
- `PATCH /api/v1/evaluasi/:id/status` — ubah status dari 'selesai' ke 'menunggu_approval' (Staff only)
- `POST /api/v1/evaluasi/:id/approval` — approve atau reject (Manager only), komentar wajib jika reject
- Pastikan filter `?status=menunggu_approval` di GET evaluasi berfungsi untuk P-07

**[FE] Fullstack — Frontend:**
- Buat MSW handler untuk PATCH status dan POST approval
- Implementasi komponen `ApprovalCard`: ringkasan evaluasi + form keputusan
- Implementasi halaman P-07: tab "Menunggu" dan "Sudah Diproses", ApprovalCard per evaluasi
- Tombol "Kirim ke Manager" di P-05 (placeholder konten P-05 dulu, tombol sudah bisa diklik)
- Komentar wajib saat reject — tombol reject disabled jika komentar kosong
- Setelah BE ready: switch dari MSW ke API staging

### Kriteria selesai F-09

```
□ [DB] Tabel approval_log terbuat
□ [BE] PATCH /evaluasi/:id/status oleh Manager mengembalikan 403
□ [BE] POST /approval reject tanpa komentar mengembalikan VALIDATION_ERROR
□ [BE] POST /approval approve mengubah status evaluasi ke 'approved'
□ [FE] P-07: hanya bisa diakses Manager (staff redirect ke dashboard)
□ [FE] P-07: tab "Menunggu" menampilkan evaluasi dengan status menunggu_approval
□ [FE] P-07: tombol reject disabled jika komentar kosong
□ [FE] P-07: setelah approve, card hilang dari tab "Menunggu"
□ [FE] P-05: tombol "Kirim ke Manager" mengubah status dan disable dirinya sendiri
□ [ALL] FEATURE_STATUS.md diperbarui: F-09 semua ✅
```

---

## Checkpoint Integrasi Tier 1–2

Sebelum memulai Tier 3, lakukan verifikasi integrasi menyeluruh dari semua fitur Tier 0–2.

**Yang diverifikasi:**

```
Happy path lengkap tanpa AI:
1. Login sebagai Staff
2. Buat evaluasi baru (isi requirement + preferensi opsional)
3. Tambah 3 vendor manual + upload 1 dokumen PDF
4. Konfirmasi ekstraksi hasil dokumen
5. Submit evaluasi → redirect ke P-04 (loading state)
6. Login sebagai Manager
7. P-07: evaluasi muncul setelah staff kirim ke approval
8. Approve evaluasi → status berubah ke 'approved'
9. P-08: ubah bobot, simpan, buka lagi, bobot tersimpan
10. P-06: evaluasi muncul di riwayat dengan status yang benar
```

```
Security checks:
□ Staff tidak bisa akses evaluasi milik staff lain (403)
□ Staff tidak bisa akses P-07 dan P-08 (redirect)
□ RLS memblokir akses langsung ke database tanpa melalui aplikasi
□ Upload file > 10MB ditolak dengan pesan yang benar
```

```
Technical checks:
□ Semua query utama menggunakan index yang benar (EXPLAIN ANALYZE)
□ TanStack Query cache invalidation bekerja setelah mutasi
□ Token refresh otomatis berjalan saat access token expired
□ Tidak ada console error saat menjalankan happy path
□ E2E test happy path staff dan approval manager lulus di Playwright
□ Semua pipeline CI di kedua repository hijau
```

---

## F-10 — AI Processing & Progress Real-time (P-04)

**Tier:** 3  
**Prerequisite:** F-06 (submit evaluasi), F-07 (dokumen sudah terindeks), Checkpoint Tier 1–2  
**Tipe:** Fitur vertikal — AI Engineer + BE + FE  
**Estimasi durasi:** 8–12 hari (milestone terpanjang)  
**Dokumen referensi:** AI-01 semua section, AI-02 section 3–4–5–7–8, AI-04 section 5–6–7, FE-03 P-04, FE-02 section 10.2 (AgentProgressPanel), FE-04 section 8.1, FE-05 section 9

---

### Tujuan

Membangun seluruh pipeline AI — 7 agent dengan dependency graph, LangGraph orchestration, update progress real-time ke Supabase, dan halaman P-04 yang menampilkan status setiap agent secara live.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Verifikasi tabel `agent_progress` memiliki enum `agent_key` yang mencakup semua 7 agent
- Verifikasi index di tabel `agent_progress` untuk query per `evaluasi_id`

**[AI] AI Engineer:**
- Setup LangGraph dengan 7 node agent dan dependency graph:
  DC → paralel (FA + RA + PS) → paralel (NA + QA) → PM terakhir
- Implementasi Orchestrator: inisialisasi 7 row `agent_progress` sebelum agent mulai
- Buat struktur folder `prompts/` sesuai AI-02 section 8.2
- Tulis system prompt dan user template untuk 5 agent pertama (DC, FA, RA, PS, NA)
- Tulis prompt ekstraksi dokumen (AI-02 section 7)
- Implementasi masing-masing agent: Data Collector (Tavily API, max 4 query per vendor), Financial Analyzer, Risk Assessor, Performance Scorer, Negotiation Assistant
- Setiap agent: load prompt dari file, retry 2x exponential backoff, timeout 3 menit, fallback jika gagal
- Update progress ke `agent_progress` secara bertahap (0%, 25%, 50%, 75%, 100%)
- FastAPI endpoint `POST /v1/agent/evaluasi/:id/start` — terima payload dari Next.js dan mulai pipeline
- Integrasi circuit breaker dan logging untuk Tavily dan OpenRouter API

**[BE] Fullstack — Backend:**
- Update `POST /api/v1/evaluasi/:id/submit`: ganti stub dengan panggilan nyata ke FastAPI `/v1/agent/evaluasi/:id/start`

**[FE] Fullstack — Frontend:**
- Implementasi `AgentProgressPanel`: subscribe Supabase Realtime channel `evaluasi-progress-{evaluasiId}`, tampilkan 7 agent dengan status dan progress masing-masing, state `waiting` untuk agent yang menunggu giliran
- Implementasi halaman P-04 lengkap: daftar 7 agent, pesan per agent, estimasi waktu, warning jika ada agent error
- Auto-redirect ke P-05 saat semua agent `done`
- Unsubscribe Realtime saat komponen unmount (wajib, cegah memory leak)

### Kriteria selesai F-10

```
□ [DB] Enum agent_key mencakup semua 7 agent
□ [BE] Submit evaluasi berhasil memanggil FastAPI /v1/agent/evaluasi/:id/start
□ [AI] DC, FA, RA berjalan paralel (verifikasi dari timestamp log)
□ [AI] PS mulai setelah DC selesai
□ [AI] NA dan QA berjalan paralel setelah PS selesai
□ [AI] PM berjalan terakhir setelah NA dan QA selesai
□ [AI] Progress tiap agent ter-update di tabel agent_progress
□ [AI] Satu agent gagal: evaluasi tetap selesai dengan flag di agent tersebut
□ [AI] Agent melewati 3 menit: dianggap gagal, pipeline lanjut
□ [AI] Semua prompt tersimpan sebagai file di folder prompts/ (tidak hardcoded)
□ [AI] Unit test semua agent dengan LLM mock lulus
□ [FE] P-04: status 7 agent update real-time tanpa reload
□ [FE] P-04: agent yang menunggu tampil dengan state 'waiting' yang berbeda
□ [FE] P-04: warning tampil (bukan error fatal) jika ada agent yang gagal
□ [FE] P-04: auto-redirect ke P-05 saat semua agent done
□ [FE] P-04: Realtime unsubscribe saat navigasi ke halaman lain
□ [ALL] FEATURE_STATUS.md diperbarui: F-10 semua ✅
```

---

## F-11 — Hasil TOPSIS & Reasoning (P-05 Bagian 1–2–6)

**Tier:** 3  
**Prerequisite:** F-10 (agent selesai, ada output untuk discoring)  
**Tipe:** Fitur vertikal — AI Engineer + BE + FE  
**Estimasi durasi:** 5–7 hari  
**Dokumen referensi:** AI-03 semua section, AI-02 section 5 (Negotiation Assistant output), BE-02 section 9, FE-03 P-05 Bagian 1–2–6, FE-02 section 10.3–10.4–10.5–11.1–11.2

---

### Tujuan

Membangun scoring engine TOPSIS dan halaman P-05 untuk menampilkan ranking vendor, reasoning AI, dan rekomendasi negosiasi. Ini adalah output inti sistem.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Verifikasi schema `hasil_evaluasi` dan `hasil_vendor` sudah sesuai dengan data yang akan ditulis scoring engine

**[AI] AI Engineer:**
- Implementasi scoring engine: normalisasi output agent ke skala 0–100, 6 tahap TOPSIS, threshold minimum, penanganan data tidak lengkap
- Generasi reasoning naratif via LLM setelah skor terbentuk (bukan sebelum)
- Tulis hasil ke `hasil_evaluasi` dan `hasil_vendor` dalam satu transaksi atomik
- `GET /v1/scoring/evaluasi/:id/hasil` — kembalikan hasil lengkap

**[BE] Fullstack — Backend:**
- `GET /api/v1/evaluasi/:id/hasil` — proxy ke FastAPI hasil scoring

**[FE] Fullstack — Frontend:**
- Buat MSW handler untuk GET hasil
- Implementasi `RecommendationCard`: vendor rank 1 prominan, skor, reasoning 2 kalimat
- Implementasi `VendorRankingTable`: semua vendor terurut skor, sort per kolom, expand/collapse detail per baris
- Expand baris: `ScoreBar` per kriteria, catatan AI per kriteria, `CriteriaBarChart`
- Implementasi `AIReasoningPanel`: reasoning utama, kelemahan, rekomendasi negosiasi
- Implementasi `ScoreRadarChart` sebagai alternatif view
- P-05 Bagian 1 (narasi pengantar placeholder), Bagian 2 (RecommendationCard), Bagian 6 (AIReasoningPanel)
- Setelah BE ready: switch dari MSW ke API staging

### Kriteria selesai F-11

```
□ [DB] Data di hasil_evaluasi dan hasil_vendor konsisten dengan schema DB-01
□ [AI] Ranking vendor benar (diverifikasi manual dengan kalkulator TOPSIS)
□ [AI] Threshold diterapkan setelah TOPSIS (vendor tidak lolos punya flag)
□ [AI] Reasoning naratif dihasilkan dalam Bahasa Indonesia
□ [AI] Hasil ditulis dalam satu transaksi atomik
□ [AI] Unit test semua 6 tahap TOPSIS dengan nilai terverifikasi manual lulus
□ [AI] Skenario data tidak lengkap (agent gagal): fallback benar, tidak crash
□ [AI] Biaya token per evaluasi dicatat ke database
□ [BE] GET /evaluasi/:id/hasil berhasil proxy ke FastAPI dan kembalikan data lengkap
□ [FE] P-05: RecommendationCard menampilkan vendor rank 1 dengan skor dan reasoning
□ [FE] P-05: VendorRankingTable menampilkan semua vendor terurut dari skor tertinggi
□ [FE] P-05: expand baris menampilkan ScoreBar dan catatan per kriteria
□ [FE] P-05: sort kolom berfungsi
□ [FE] P-05: AIReasoningPanel menampilkan tiga bagian reasoning
□ [ALL] FEATURE_STATUS.md diperbarui: F-11 semua ✅
```

---

## F-12 — Profil Kualitatif (P-05 Bagian 3–4)

**Tier:** 3  
**Prerequisite:** F-10 (agent pipeline berjalan), F-11 (P-05 sudah ada strukturnya)  
**Tipe:** Fitur vertikal — AI Engineer + FE  
**Estimasi durasi:** 3–4 hari  
**Dokumen referensi:** AI-06 (Qualitative Analyzer Agent), AI-02 section 5.6, FE-03 P-05 Bagian 3–4, FE-02 (QualitativeProfileCard, QualitativeSummaryPanel)

---

### Tujuan

Menambahkan Qualitative Analyzer Agent ke pipeline dan menampilkan output kualitatif di P-05: unique offerings per vendor dan summary komparatif antar vendor.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Verifikasi kolom `unique_offerings` dan `profil_kualitatif` sudah ada di tabel `hasil_vendor`

**[AI] AI Engineer:**
- Tambahkan Qualitative Analyzer ke dependency graph LangGraph (paralel dengan NA setelah PS)
- Tulis system prompt dan user template untuk Qualitative Analyzer
- Qualitative Analyzer menerima RAG context dari dokumen penawaran (query ke pgvector)
- Output: `unique_offerings` (JSONB) dan `profil_kualitatif` (teks naratif) per vendor
- Tambah `summary_komparatif_kualitatif` ke output scoring engine

**[FE] Fullstack — Frontend:**
- Implementasi `QualitativeProfileCard`: tampilkan unique offerings dan profil kualitatif per vendor
- Implementasi `QualitativeSummaryPanel`: summary komparatif semua vendor
- Tambahkan ke P-05 Bagian 3 dan Bagian 4
- Update expand baris VendorRankingTable untuk menyertakan profil kualitatif

### Kriteria selesai F-12

```
□ [DB] Kolom unique_offerings dan profil_kualitatif ada di hasil_vendor
□ [AI] QA berjalan paralel dengan NA setelah PS selesai (verifikasi log)
□ [AI] QA menghasilkan unique_offerings dan profil_kualitatif per vendor
□ [AI] Output QA tersimpan ke hasil_vendor
□ [FE] P-05: QualitativeProfileCard tampil per vendor
□ [FE] P-05: QualitativeSummaryPanel tampil sebagai bagian 4
□ [FE] VendorRankingTable expand: menyertakan profil kualitatif
□ [ALL] FEATURE_STATUS.md diperbarui: F-12 semua ✅
```

---

## F-13 — Rekomendasi Preferensi & Conflict Callout (P-05 Bagian 5)

**Tier:** 3  
**Prerequisite:** F-08 (preferensi tersimpan), F-12 (output QA tersedia sebagai input PM)  
**Tipe:** Fitur vertikal — AI Engineer + FE  
**Estimasi durasi:** 3–4 hari  
**Dokumen referensi:** AI-07 (Preference Matcher Agent), AI-02 section 5.7, FE-03 P-05 Bagian 1–5, FE-02 (PreferenceRecommendationCard, ConflictCallout)

---

### Tujuan

Menambahkan Preference Matcher Agent sebagai agent terakhir dalam pipeline. Menghasilkan rekomendasi berbasis preferensi dan mendeteksi konflik dengan ranking TOPSIS.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Verifikasi kolom `preference_matching_result`, `conflict_callout` ada di `hasil_evaluasi`
- Verifikasi kolom `tingkat_kesesuaian_preferensi` ada di `hasil_vendor`

**[AI] AI Engineer:**
- Tambahkan Preference Matcher sebagai node terakhir di LangGraph (setelah QA selesai)
- Tulis dua user template: `user_template_neutral.md` (tanpa preferensi) dan `user_template_opinionated.md` (dengan preferensi)
- PM menerima: teks preferensi (nullable), output semua agent sebelumnya, output QA lengkap
- Output: `preference_matching_result`, `conflict_callout` (nullable), `tingkat_kesesuaian_preferensi` per vendor
- Update narasi pengantar P-05 Bagian 1: berbeda berdasarkan mode netral vs opinionated

**[FE] Fullstack — Frontend:**
- Implementasi `PreferenceRecommendationCard`: rekomendasi berbasis preferensi
- Implementasi `ConflictCallout`: warning prominan dengan warna peringatan, tidak bisa di-dismiss
- Tambahkan ke P-05 Bagian 5 (hanya tampil jika preferensi diisi)
- Update VendorRankingTable: tambah indikator `tingkat_kesesuaian_preferensi` di expand
- Update P-05 Bagian 1: tampilkan narasi sesuai mode

### Kriteria selesai F-13

```
□ [DB] Kolom preference_matching_result, conflict_callout, tingkat_kesesuaian_preferensi ada
□ [AI] PM berjalan terakhir setelah QA selesai
□ [AI] Mode netral (tanpa preferensi): PM menghasilkan output tanpa rekomendasi berbasis preferensi
□ [AI] Mode opinionated (dengan preferensi): PM menghasilkan rekomendasi 1–3 vendor
□ [AI] Konflik terdeteksi: vendor dengan preferensi tinggi tapi TOPSIS rendah menghasilkan conflict_callout
□ [FE] P-05: Bagian 5 hanya tampil jika preferensi diisi
□ [FE] P-05: ConflictCallout tampil prominan jika ada konflik, tidak bisa di-dismiss
□ [FE] P-05: Bagian 1 narasi berbeda antara mode netral dan opinionated
□ [FE] VendorRankingTable expand: indikator kesesuaian preferensi tampil
□ [ALL] FEATURE_STATUS.md diperbarui: F-13 semua ✅
```

---

## F-14 — AI Chat Panel + RAG

**Tier:** 3  
**Prerequisite:** F-07 (dokumen terindeks di pgvector), F-11 (hasil evaluasi tersedia untuk konteks)  
**Tipe:** Fitur vertikal — AI Engineer + FE  
**Estimasi durasi:** 3–4 hari  
**Dokumen referensi:** AI-05 (RAG Specification), AI-02 section 6, BE-02 section 10–11.2, FE-02 section 9.3 (AIPanel), FE-04 section 8.2, FE-05 section 10

---

### Tujuan

Mengaktifkan AIPanel di semua halaman dengan SSE streaming, dan menambahkan kemampuan RAG di P-05 agar AI bisa menjawab pertanyaan berbasis dokumen penawaran vendor.

### Task per lapisan & track

**[DB] Fullstack — Database:**
- Verifikasi index vector di tabel `dokumen_chunk` untuk hybrid search (pgvector + full-text)

**[AI] AI Engineer:**
- Tulis prompt AI Chat Panel dengan context per halaman (AI-02 section 6)
- Implementasi `POST /v1/chat/stream` dengan SSE: context injection per halaman, stream token demi token, format event `type: token`, `type: done`, `type: error`
- Implementasi `POST /v1/rag/query` (internal): hybrid search (vector + BM25) dengan filter `evaluasi_id`, kembalikan chunks relevan
- RAG context digunakan di P-05 — AI dapat menjawab tentang isi dokumen penawaran

**[FE] Fullstack — Frontend:**
- Aktifkan AIPanel: buka koneksi SSE saat user kirim pesan, akumulasi token ke buffer, tampilkan typing indicator
- Setelah event `done`: pindahkan pesan lengkap dari buffer ke chatStore
- Reset chatStore saat user berpindah evaluasi
- Context injection otomatis berdasarkan halaman aktif
- Sertakan riwayat chat maks 10 pesan di setiap request
- Tutup SSE saat komponen unmount

### Kriteria selesai F-14

```
□ [DB] Index vector di dokumen_chunk berfungsi untuk similarity search
□ [AI] POST /v1/chat/stream: koneksi terbuka dan token muncul bertahap
□ [AI] Context halaman berbeda menghasilkan opening message AI yang berbeda
□ [AI] RAG retrieval: query tentang vendor mengembalikan chunks relevan dari dokumen yang sudah diindex
□ [AI] Kegagalan RAG indexing tidak memblokir chat — fallback ke context tanpa dokumen
□ [FE] AIPanel: pesan user dan respons AI tampil berurutan
□ [FE] AIPanel: typing indicator tampil selama streaming berlangsung
□ [FE] AIPanel: pesan tidak duplikat saat streaming selesai
□ [FE] AIPanel: reset saat user berpindah ke evaluasi berbeda
□ [FE] AIPanel: koneksi SSE tertutup saat navigasi ke halaman lain
□ [ALL] FEATURE_STATUS.md diperbarui: F-14 semua ✅
```

---

## Checkpoint Final — Release Readiness

Setelah semua fitur Tier 3 selesai, lakukan verifikasi menyeluruh sebelum deployment production.

### Happy path end-to-end dengan data realistis

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
Kirim ke Manager
  ↓
Login sebagai Manager → P-07 → baca reasoning → Approve
  ↓
Verifikasi status berubah ke 'approved' di P-06
```

### Review kualitas AI (judgment call, tidak ada checklist teknis)

- Apakah ranking TOPSIS masuk akal untuk data yang diinput?
- Apakah reasoning naratif spesifik terhadap vendor, bukan generik?
- Apakah profil kualitatif mencerminkan isi dokumen penawaran yang diupload?
- Apakah rekomendasi preferensi sesuai dengan teks preferensi yang diisi?
- Apakah AIPanel menjawab pertanyaan dengan konteks yang relevan?
- Apakah rekomendasi negosiasi konkret dan dapat langsung digunakan?

### Verifikasi teknis final

```
□ [DB] Semua query memenuhi target P95 dari DB-03 section 10
□ [DB] Tidak ada deadlock saat 5 evaluasi diproses bersamaan
□ [DB] Supabase Pro aktif di production, PITR berfungsi
□ [DB] Restore test berhasil: backup terbaru ter-restore dengan data integritas penuh
□ [BE] Semua skenario security test di SH-03 section 11.1 lulus
□ [BE] Rate limiting sesuai konfigurasi di BE-03 section 6.2
□ [BE] Audit trail: semua event di BE-03 section 9.2 tercatat
□ [BE] Spending alert OpenRouter, Tavily, dan Google Gemini terkonfigurasi
□ [AI] Prompt evaluation metric: format compliance >95%, hallucination <5%
□ [AI] Unit test semua 7 agent dengan LLM mock lulus
□ [AI] Unit test scoring engine semua 6 tahap TOPSIS dengan nilai terverifikasi lulus
□ [AI] Semua prompt tersimpan sebagai file (tidak ada hardcode di Python)
□ [FE] Semua 4 critical path E2E lulus di Playwright
□ [FE] Zero axe-core violation di semua 8 halaman
□ [FE] Semua form dapat diisi dengan keyboard saja
□ [FE] Visual regression: tidak ada perbedaan yang tidak disengaja
□ [ALL] Happy path end-to-end dengan 5 vendor (3 manual + 2 upload) berhasil
□ [ALL] Kualitas AI: tim setuju reasoning masuk akal
□ [ALL] Semua pipeline CI di kedua repository hijau
□ [ALL] Checklist deployment production SH-02 section 16 dicentang semua
```

---

## Ringkasan Dependency & Urutan

| Fitur | Prerequisite | Tier | Durasi est. |
|---|---|---|---|
| F-00 Environment Setup | — | 0 | 2–3 hari |
| F-01 Auth & Login | F-00 | 0 | 2–3 hari |
| F-02 Layout & AppShell | F-00 | 0 | 2–3 hari |
| F-03 Konfigurasi Kriteria | F-00 | 0 | 2–3 hari |
| F-04 Dashboard | F-01, F-02 | 1 | 2–3 hari |
| F-05 Riwayat Evaluasi | F-01, F-02, F-04 | 1 | 1–2 hari |
| F-06 Buat Evaluasi (manual) | F-01, F-02, F-04 | 1 | 3–4 hari |
| F-07 Upload & Ekstraksi | F-06 | 2 | 3–4 hari |
| F-08 Form Preferensi | F-06 | 2 | 1 hari |
| F-09 Submit & Approval | F-06, F-04 | 2 | 3–4 hari |
| *Checkpoint Tier 1–2* | F-03–F-09 | — | 1–2 hari |
| F-10 AI Processing (P-04) | F-06, F-07, Checkpoint | 3 | 8–12 hari |
| F-11 Hasil TOPSIS (P-05 core) | F-10 | 3 | 5–7 hari |
| F-12 Profil Kualitatif | F-10, F-11 | 3 | 3–4 hari |
| F-13 Rekomendasi Preferensi | F-08, F-12 | 3 | 3–4 hari |
| F-14 AI Chat + RAG | F-07, F-11 | 3 | 3–4 hari |
| *Checkpoint Final* | Semua F-10–F-14 | — | 2–3 hari |

**Estimasi total: 8–14 minggu** untuk satu developer Fullstack bekerja sequential (DB → BE → FE per fitur), plus track AI Engineer yang berjalan paralel untuk fitur-fitur Tier 2–3.

Estimasi ini lebih panjang dari versi sebelumnya (5–9 minggu) karena sebelumnya diasumsikan empat developer paralel. Fitur-fitur dalam tier yang sama tetap dapat dikerjakan berurutan oleh Fullstack — tidak ada parallelisme di dalam satu developer. Pengecualian: AI Engineer mengerjakan F-07 (AI-side), F-10, F-11, F-12, F-13, F-14 secara bersamaan dengan Fullstack karena berada di repo yang berbeda.

---

*Dokumen ini adalah living document — urutan dan estimasi dapat disesuaikan berdasarkan kemajuan aktual. Kriteria selesai setiap fitur tidak boleh dikurangi tanpa persetujuan eksplisit.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-08 | Versi awal | — |
| 2.0.0 | 2026-06-08 | Revisi lengkap: tambah referensi dokumen per milestone, task detail per role, kriteria selesai komprehensif | — |
| 3.0.0 | 2026-06-11 | Tulis ulang total: adopsi feature-based development — reorganisasi dari 8 milestone berbasis layer menjadi 15 fitur vertikal dalam 4 tier; tambah Checkpoint Integrasi Tier 1–2 dan Checkpoint Final sebagai integration gate; tambah FEATURE_STATUS.md sebagai mekanisme koordinasi lintas repo | — |
| 4.0.0 | 2026-06-12 | Adopsi 2-repo (ADR-031): perbarui paragraf pengantar (polyrepo → 2-repo); perbarui task F-00 Backend Engineer (inisialisasi monorepo vendor-ai + pnpm workspaces, hapus vendor-ai-backend/vendor-ai-frontend); perbarui task F-00 Frontend Engineer (apps/web, packages/types); perbarui task F-00 Database Engineer (supabase/migrations/ dalam vendor-ai); perbarui kriteria selesai F-00 (branch structure, FEATURE_STATUS.md); perbarui Checkpoint Final (ketiga → kedua repository) | — |
| 5.0.0 | 2026-06-12 | Adopsi 4 role (ADR-032): pisah Backend Engineer (FastAPI) → AI Engineer di semua fitur; perbarui paragraf pengantar (tiga → empat developer); pisah task F-00 BE menjadi BE (Next.js) dan AI Engineer; perbarui kriteria selesai F-00 (tambah tag [AI]); rename label dan tag [BE] FastAPI → [AI] di F-07, F-10, F-11, F-12, F-13, F-14; perbarui Checkpoint Final (pisah [BE] prompt/agent → [AI]) | — |
| 6.0.0 | 2026-06-13 | Adopsi ADR-035 (namespace AI) dan ADR-036 (2 track solo developer): tulis ulang paragraf pengantar (empat developer paralel → 2 track Fullstack+AI Engineer); ganti semua header "Task per role" → "Task per lapisan & track"; ganti label Database/Backend/Frontend Engineer → [DB]/[BE]/[FE] Fullstack; perbarui semua referensi dokumen (BE-03→AI-01, BE-04→AI-02, BE-05→AI-03, BE-06→BE-03, BE-07→BE-04/AI-04, BE-08→AI-05, BE-09→AI-06, BE-10→AI-07); perbarui branch structure F-00 (fe/develop+be/develop → develop); perbarui estimasi total (5–9 minggu paralel → 8–14 minggu sequential+AI track); perbarui referensi Anthropic → OpenRouter di task F-00 AI Engineer dan Checkpoint Final | — |
