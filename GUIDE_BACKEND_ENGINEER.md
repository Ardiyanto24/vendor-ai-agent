# Panduan Implementasi — Backend Engineer

**Project:** AI Vendor Selection System  
**Role:** Backend Engineer  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-12  
**Referensi Utama:** BE-02, BE-03, MILESTONE_PLAN v5.0.0

---

## Tentang Dokumen Ini

Panduan ini adalah panduan kerja operasional untuk Backend Engineer — mencakup **satu service**: Next.js API Routes (`apps/api`) yang berperan sebagai BFF (Backend-for-Frontend) layer. Dokumen ini menjelaskan apa yang perlu dibangun per fitur, bagaimana API Routes berkoordinasi dengan FastAPI service, dan hal-hal kritis yang tidak boleh terlewat.

Backend Engineer bertanggung jawab atas semua yang ada di `vendor-ai/apps/api`: validasi input, autentikasi, otorisasi, CRUD ke Supabase, dan proxy ke FastAPI. **Tidak ada kode Python di sini** — semua yang berhubungan dengan AI agent, scoring, RAG, dan LLM adalah tanggung jawab AI Engineer di repo `vendor-ai-agent`.

Semua task mengacu ke spec resmi. Jika ada konflik antara panduan ini dan dokumen spec, dokumen spec yang berlaku.

---

## Prasyarat Sebelum Memulai

**Monorepo `vendor-ai` — `apps/api` (Next.js API Routes):**
- Workspace sudah diinisialisasi dengan pnpm workspaces (`pnpm-workspace.yaml` di root) — koordinasi dengan Frontend Engineer di F-00
- `apps/api` diinisialisasi dengan Next.js 14+ App Router
- Setup TypeScript, Zod untuk validasi, Supabase JS Client
- Struktur folder `app/api/v1/` untuk semua route handlers
- `packages/types` tersedia dan bisa diimport dari `apps/api`
- File `.env.example` di root `vendor-ai` dengan semua variabel yang dibutuhkan (lihat BE-03 section 4 dan FE-01 section 11.1)
- File `FEATURE_STATUS.md` sudah ada di root `vendor-ai` (dibuat bersama di F-00)
- Branch `develop` dibuat dari `main`

**Environment variables yang wajib ada sebelum F-00 selesai:**

| Variabel | Keterangan |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL project Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon key untuk client-side |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role untuk operasi admin |
| `FASTAPI_URL` | URL internal FastAPI service |
| `SERVICE_TO_SERVICE_TOKEN` | Token shared dengan AI Engineer untuk komunikasi internal |

---

## Konvensi Penting

**Tanggung jawab yang jelas:**
- **Next.js API Routes** — validasi input, autentikasi/otorisasi, CRUD ke Supabase, proxy ke FastAPI. Tidak ada LLM call, tidak ada scoring.
- **FastAPI (AI Engineer)** — semua yang melibatkan AI: agent, scoring, ekstraksi dokumen, RAG, SSE chat.

**Defense in depth untuk auth (BE-06 section 5.2):** Middleware Next.js cek token → handler cek ulang role secara eksplisit → Supabase RLS sebagai lapisan terakhir.

**Error codes harus konsisten:** Gunakan error codes dari BE-02 section 12.3. Frontend bergantung pada kode ini.

**Format response seragam:** Semua response menggunakan struktur `{ success, data, meta }` untuk sukses dan `{ success: false, error: { code, message } }` untuk error.

---

## F-00 — Environment Setup

**Tier:** 0 | **Estimasi:** 2–3 hari (paralel dengan AI Engineer dan Database Engineer)

### Yang Perlu Dibuat

#### 1. Inisialisasi Monorepo `vendor-ai`

Inisialisasi monorepo dengan pnpm workspaces — buat struktur `apps/web`, `apps/api`, `packages/types`. Koordinasi dengan Frontend Engineer yang akan menginisialisasi `apps/web` di saat yang bersamaan.

#### 2. Inisialisasi `apps/api`

Inisialisasi Next.js 14+ App Router untuk `apps/api` dengan struktur folder `app/api/v1/`. Buat `packages/types` dengan type definitions awal yang akan di-share antara `apps/api` dan `apps/web`.

#### 3. GET /api/health

Endpoint health check yang memeriksa koneksi ke Supabase dan keterbacaan semua environment variable. Digunakan seluruh tim untuk memverifikasi setup.

#### 4. Service-to-Service Token

Generate token statis yang kuat (min 32 karakter random hex). Simpan di `SERVICE_TO_SERVICE_TOKEN` di `apps/api`. Koordinasikan nilai token yang sama dengan AI Engineer untuk disimpan di `vendor-ai-agent`.

#### 5. File `.env.example`

Buat file `.env.example` di root `vendor-ai` dengan semua variabel untuk `apps/web` dan `apps/api`. AI Engineer membuat `.env.example` terpisah di root `vendor-ai-agent`.

### Kriteria Selesai F-00 [BE]

```
□ Struktur monorepo vendor-ai terbuat: apps/web, apps/api, packages/types
□ GET /api/health (apps/api) mengembalikan 200 dengan status Supabase
□ Service-to-service token terkonfigurasi di apps/api
□ packages/types dapat diimport dari apps/api tanpa error
□ .env.example di root vendor-ai terisi semua variabel apps/api
□ FEATURE_STATUS.md ada di root vendor-ai
```

---

## F-01 — Auth & Login

**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 2–3 hari

### Yang Perlu Dibuat (Next.js)

#### 1. Middleware Route Guard

Di `middleware.ts` (root project Next.js):
- Baca JWT dari cookie `sb-access-token` atau header `Authorization`
- Verifikasi token dengan Supabase Auth
- Route `/login` tidak butuh auth — skip
- Route `/api/v1/auth/*` tidak butuh auth — skip  
- Semua route lain: jika tidak ada token valid → redirect ke `/login` (untuk page routes) atau kembalikan 401 (untuk API routes)
- Route khusus manager (`/api/v1/konfigurasi`, `/api/v1/evaluasi/:id/approval`): jika role bukan `manager` → kembalikan 403

#### 2. POST /api/v1/auth/login

Input: `{ email, password }`  
Proses: teruskan ke Supabase Auth `signInWithPassword()`  
Output: `{ accessToken, user: { id, nama, email, role, avatarUrl } }`

Setelah Supabase Auth berhasil:
- Simpan refresh token di cookie HttpOnly `sb-refresh-token` (7 hari, Secure, SameSite=Strict)
- Kembalikan access token di response body — frontend menyimpannya di Zustand

**Rate limiting:** 5 request per menit per IP. Kembalikan `RATE_LIMIT_EXCEEDED` (429) jika terlampaui.

**Security headers:** Semua response dari endpoint ini harus menyertakan security headers sesuai BE-03 section 6.5.

#### 3. POST /api/v1/auth/logout

Proses: panggil Supabase Auth `signOut()`, hapus cookie HttpOnly refresh token.

#### 4. POST /api/v1/auth/refresh

Input: baca refresh token dari cookie HttpOnly `sb-refresh-token`  
Proses: teruskan ke Supabase Auth untuk mendapatkan access token baru  
Output: `{ accessToken }`  

Jika refresh token tidak ada atau tidak valid: kembalikan 401 dengan code `INVALID_REFRESH_TOKEN`.

#### 5. GET /api/v1/users/me

Auth required. Kembalikan data user dari tabel `user` berdasarkan `auth.uid()` dari JWT.

### Kriteria Selesai F-01 [BE]

```
□ POST /auth/login menghasilkan JWT dengan field 'role' di payload
□ Refresh token tersimpan di cookie HttpOnly (verifikasi: tidak bisa dibaca dari JavaScript)
□ POST /auth/refresh menghasilkan access token baru yang valid
□ POST /auth/logout menghapus cookie dan invalidasi sesi di Supabase
□ Request ke-6 login dalam 1 menit dari IP yang sama mengembalikan 429
□ Security headers tersedia di semua response auth
□ Middleware: request ke /api/v1/evaluasi tanpa token dikembalikan 401
□ Middleware: staff yang akses PUT /api/v1/konfigurasi/kriteria dikembalikan 403
```

---

## F-02 — Layout & AppShell

Tidak ada task Backend Engineer di fitur ini.

---

## F-03 — Konfigurasi Kriteria (Settings P-08)

**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 1–2 hari

### Yang Perlu Dibuat (Next.js)

#### 1. GET /api/v1/kategori-pengadaan

Kembalikan daftar enum kategori pengadaan dari Supabase. Data ini sangat statis — pertimbangkan caching 24 jam di Next.js server cache.

#### 2. GET /api/v1/konfigurasi/kriteria?kategori=X

Auth required. Query tabel `konfigurasi_kriteria` berdasarkan `kategori`. Kembalikan konfigurasi aktif (yang tidak soft-deleted).

Caching: 10 menit di Next.js server cache. Cache diinvalidasi saat PUT berhasil.

#### 3. PUT /api/v1/konfigurasi/kriteria

Manager only (cek di handler, bukan hanya di middleware).  
Input: `{ kategori, kriteria: [{ key, label, bobot, threshold_min }] }`  
Validasi: total semua `bobot` harus tepat 100 → kembalikan `INVALID_WEIGHT_TOTAL` (400) jika tidak.  
Proses: UPSERT ke tabel `konfigurasi_kriteria`, set `updated_by` dari JWT.  
Setelah berhasil: invalidasi server cache untuk key `konfigurasi-kriteria-{kategori}`.

### Kriteria Selesai F-03 [BE]

```
□ GET /konfigurasi/kriteria mengembalikan bobot aktif per kategori
□ PUT /konfigurasi/kriteria dengan total ≠ 100 mengembalikan INVALID_WEIGHT_TOTAL
□ PUT /konfigurasi/kriteria oleh staff mengembalikan 403
□ Caching konfigurasi terkonfigurasi (verifikasi: request kedua tidak hit database)
```

---

## F-04 — Dashboard (P-02)

**Tier:** 1 | **Prerequisite:** F-01, F-02 | **Estimasi:** 1–2 hari

### Yang Perlu Dibuat (Next.js)

#### 1. GET /api/v1/evaluasi

Auth required. Filter dan pagination lengkap.

Query params yang didukung: `status`, `kategori`, `search` (partial match pada judul), `dateFrom`, `dateTo`, `page` (default 1), `limit` (default 20, max 50).

**Aturan penting:** Untuk role `staff`, filter `created_by = auth.uid()` selalu diterapkan secara otomatis di backend — tidak peduli apa yang dikirim frontend. Staff tidak boleh bisa melihat evaluasi orang lain meskipun mereka memanipulasi query params.

Response: `{ data: [...], meta: { page, limit, total, totalPages } }`

#### 2. GET /api/v1/evaluasi/summary

Auth required. Query agregat jumlah evaluasi per status.

Untuk staff: hanya menghitung evaluasi miliknya. Untuk manager: semua evaluasi.

Response: `{ draft: N, processing: N, selesai: N, menunggu_approval: N, approved: N, butuh_revisi: N }`

### Kriteria Selesai F-04 [BE]

```
□ GET /evaluasi mengembalikan daftar sesuai role (staff hanya lihat miliknya)
□ GET /evaluasi dengan filter status mengembalikan data yang difilter dengan benar
□ GET /evaluasi/summary mengembalikan jumlah yang akurat per status
□ Pagination: page, limit, total, totalPages ada di meta
□ Staff yang coba akses evaluasi milik staff lain via GET /evaluasi/:id mendapat 403
```

---

## F-05 — Riwayat Evaluasi (P-06)

**Tier:** 1 | **Prerequisite:** F-04 | **Estimasi:** Tidak ada task baru

Endpoint `GET /api/v1/evaluasi` dari F-04 sudah mencakup semua kebutuhan P-06 — verifikasi semua kombinasi filter (status, kategori, search, tanggal) berfungsi dengan benar.

---

## F-06 — Buat Evaluasi: Requirement & Vendor Manual

**Tier:** 1 | **Prerequisite:** F-01, F-02, F-04 | **Estimasi:** 2–3 hari

### Yang Perlu Dibuat (Next.js)

#### 1. POST /api/v1/evaluasi

Auth required. Validasi semua field wajib dengan Zod.  
Input: `{ judul, kategori, deskripsi, budgetMin?, budgetMax, deadline, prioritasKriteria?, lampiranUrl?, preferensiPerusahaan? }`

Field `preferensiPerusahaan` opsional, max 1.000 karakter → kembalikan `PREFERENCE_TOO_LONG` (400) jika lebih.

Set `created_by = auth.uid()` dan `status = 'draft'` di backend — tidak boleh dari input client.

Response: evaluasi yang baru dibuat.

#### 2. GET /api/v1/evaluasi/:id

Auth required. Ambil detail evaluasi + daftar vendor aktif (yang tidak soft-deleted).

**Resource-level auth:** Jika `evaluasi.created_by !== auth.uid()` dan role bukan `manager` → kembalikan 403. Jangan 404.

#### 3. POST /api/v1/evaluasi/:id/vendor

Auth required. Tambah vendor ke evaluasi yang masih berstatus `draft`.

Validasi:
- Evaluasi harus milik user (atau user adalah manager)
- Status harus `draft` → kembalikan `EVALUASI_NOT_EDITABLE` (409) jika tidak
- Jumlah vendor aktif saat ini < 10 → kembalikan `VENDOR_LIMIT_EXCEEDED` (400) jika sudah 10

Input: `{ namaPerusahaan, kontakAtauWebsite?, hargaPenawaran, catatan?, sumberInput }`  
`sumberInput` harus `manual` atau `extracted`.

#### 4. DELETE /api/v1/evaluasi/:id/vendor/:vendorId

Auth required. Soft delete vendor dengan set `deleted_at = NOW()`.

Validasi: evaluasi harus `draft`, vendor harus milik evaluasi yang benar.

Response: 204 No Content.

#### 5. POST /api/v1/evaluasi/:id/submit

Auth required. Memulai proses evaluasi AI.

Validasi:
- Evaluasi milik user
- Status harus `draft` → `EVALUASI_NOT_EDITABLE` jika tidak
- Jumlah vendor aktif >= 2 → `INSUFFICIENT_VENDORS` jika tidak
- Status tidak boleh sudah `processing` → `ALREADY_SUBMITTED`

Proses:
1. Update status evaluasi ke `processing`
2. Buat 7 row di tabel `agent_progress` dengan status `idle` (satu per agent)
3. Kirim request async ke FastAPI `POST /v1/agent/evaluasi/:id/start` dengan payload evaluasi lengkap (termasuk `preferensi_perusahaan`)
4. Response langsung 202 Accepted ke frontend — tidak perlu menunggu FastAPI selesai

**Stub di F-06:** FastAPI endpoint belum ada. Gunakan stub yang langsung return 202 untuk step 3. FastAPI endpoint nyata baru diimplementasikan di F-10.

#### 6. Payload ke FastAPI

Saat submit evaluasi, Next.js mengirim payload ini ke FastAPI:

```
{
  evaluasiId,
  judul,
  deskripsi,
  kategori,
  budgetMin,
  budgetMax,
  deadline,
  preferensiPerusahaan (nullable),
  vendors: [{ id, namaPerusahaan, hargaPenawaran, catatan, sumberInput }],
  konfigurasiKriteria: { kriteria: [...] }  // snapshot konfigurasi aktif saat submit
}
```

Konfigurasi harus di-snapshot saat submit — ambil dari database saat itu, bukan saat scoring selesai. Ini memastikan perubahan konfigurasi oleh manager setelah evaluasi disubmit tidak mempengaruhi hasil evaluasi yang sedang berjalan.

### Kriteria Selesai F-06 [BE]

```
□ POST /evaluasi membuat record baru dengan status 'draft'
□ POST /evaluasi/:id/vendor dengan 11 vendor mengembalikan VENDOR_LIMIT_EXCEEDED
□ POST /evaluasi/:id/submit dengan 1 vendor mengembalikan INSUFFICIENT_VENDORS
□ POST /evaluasi/:id/submit mengubah status ke 'processing' dan membuat 7 row agent_progress
□ Staff tidak bisa akses evaluasi milik staff lain (403, bukan 404)
□ POST /evaluasi/:id/vendor di evaluasi berstatus 'processing' mengembalikan EVALUASI_NOT_EDITABLE
□ preferensiPerusahaan > 1.000 karakter mengembalikan PREFERENCE_TOO_LONG
```

---

## F-07 — Upload Dokumen & Ekstraksi

**Tier:** 2 | **Prerequisite:** F-06 | **Estimasi:** 2–3 hari

### Yang Perlu Dibuat (Next.js)

#### 1. POST /api/v1/evaluasi/:id/dokumen

Auth required. Menerima file upload (multipart/form-data).

Validasi sebelum diteruskan ke Storage:
- Tipe file: hanya PDF dan Excel (.xlsx, .xls) → `INVALID_FILE_TYPE` (400)
- Ukuran file: max 10MB → `FILE_TOO_LARGE` (400)
- Evaluasi harus milik user dan berstatus `draft`

Proses:
1. Upload file ke Supabase Storage bucket `vendor-documents` dengan path `evaluasi/{evaluasiId}/{uploadId}_{namaFile}`
2. Buat row di tabel `dokumen_upload` dengan `status_ekstraksi = 'pending'` dan `indexing_rag_status = 'pending'`
3. Panggil FastAPI `POST /v1/agent/ekstrak-dokumen` secara async (tidak menunggu response) — kirim storage URL dan metadata
4. Kembalikan 202 dengan `uploadId` ke frontend

**Signed URL:** Saat frontend perlu akses file, generate signed URL dengan masa berlaku 1 jam via Supabase Storage API. File tidak boleh diakses secara publik.

#### 2. GET /api/v1/evaluasi/:id/dokumen/:uploadId/status

Auth required. Polling status ekstraksi dan RAG indexing.

Response: `{ status: 'pending' | 'processing' | 'done' | 'done_partial' | 'failed', hasilEkstraksi?: {...}, confidenceScore?: float, indexingRagStatus?: string, chunkCount?: int }`

> **Catatan koordinasi:** Endpoint ini membaca status yang ditulis oleh AI Engineer (`vendor-ai-agent`). Pastikan nama kolom di tabel `dokumen_upload` konsisten dengan apa yang ditulis FastAPI.

### Kriteria Selesai F-07 [BE]

```
□ Upload file > 10MB mengembalikan FILE_TOO_LARGE
□ Upload file bukan PDF/Excel mengembalikan INVALID_FILE_TYPE
□ File tersimpan di Supabase Storage di path yang benar
□ POST dokumen mengembalikan 202 segera (tidak blocking)
□ Status polling: mengembalikan nilai terkini dari tabel dokumen_upload
```

---

## F-08 — Form Preferensi Opsional

**Tier:** 2 | **Prerequisite:** F-06 | **Estimasi:** Tidak ada task baru yang signifikan

`POST /api/v1/evaluasi` dari F-06 sudah menerima field `preferensi_perusahaan` (opsional) dan validasinya (max 1.000 karakter) sudah ada. Verifikasi bahwa field ini tersimpan dengan benar ke kolom `preferensi_perusahaan` di tabel `evaluasi`.

---

## F-09 — Submit, Status Flow & Approval

**Tier:** 2 | **Prerequisite:** F-06, F-04 | **Estimasi:** 2–3 hari

### Yang Perlu Dibuat (Next.js)

#### 1. PATCH /api/v1/evaluasi/:id/status

Auth required. Mengubah status evaluasi untuk aksi spesifik.

Satu-satunya transisi yang diizinkan untuk staff: `selesai → menunggu_approval`.

Validasi: evaluasi milik user, status saat ini harus `selesai` → `NOT_PENDING_APPROVAL` (409) jika tidak.

Proses: UPDATE `status = 'menunggu_approval'` di tabel `evaluasi`.

#### 2. POST /api/v1/evaluasi/:id/approval

Manager only (cek eksplisit di handler).

Input: `{ keputusan: 'approved' | 'rejected', komentar?: string }`

Validasi:
- Hanya manager
- Evaluasi harus berstatus `menunggu_approval` → `NOT_PENDING_APPROVAL` (409)
- Jika `keputusan = 'rejected'` dan `komentar` kosong → `VALIDATION_ERROR` (400)

Proses dalam satu transaksi:
1. Buat row baru di tabel `approval_log` dengan keputusan dan komentar
2. Update status evaluasi:
   - `approved` → status = `'approved'`
   - `rejected` → status = `'butuh_revisi'`

Response: evaluasi yang sudah diupdate.

### Kriteria Selesai F-09 [BE]

```
□ PATCH /evaluasi/:id/status oleh manager mengembalikan 403
□ PATCH /evaluasi/:id/status dari status 'draft' mengembalikan NOT_PENDING_APPROVAL
□ POST /approval reject tanpa komentar mengembalikan VALIDATION_ERROR
□ POST /approval approve mengubah status evaluasi ke 'approved'
□ POST /approval reject mengubah status ke 'butuh_revisi' dan membuat row di approval_log
□ POST /approval pada evaluasi yang tidak 'menunggu_approval' mengembalikan NOT_PENDING_APPROVAL
```

---

## Checkpoint Integrasi Tier 1–2

Sebelum masuk Tier 3, verifikasi penuh alur tanpa AI:

```
□ Login staff → dashboard dengan evaluasi data
□ Buat evaluasi (POST /evaluasi) → tambah 2 vendor → submit → 7 row agent_progress terbuat
□ Upload dokumen → polling status → status berubah ke 'done' atau 'done_partial'
□ Login manager → GET /evaluasi (semua evaluasi tampil) → GET /evaluasi/{id}/approval OK
□ Kirim evaluasi ke approval (PATCH /status) → POST /approval berhasil → status 'approved'
□ Ubah konfigurasi (PUT /konfigurasi/kriteria dengan total 100) → berhasil
□ Security: staff A tidak bisa GET /evaluasi/{id milik staff B} → 403
□ Security: staff tidak bisa PUT /konfigurasi/kriteria → 403
□ Security: rate limit login berfungsi (5 request/menit)
```

---

## F-10 — AI Processing & Progress Real-time (P-04)

**Tier:** 3 | **Prerequisite:** F-06, F-07, Checkpoint Tier 1–2 | **Estimasi:** 1–2 hari (Next.js side)

### Yang Perlu Dibuat (Next.js)

#### Update POST /api/v1/evaluasi/:id/submit

Ganti stub FastAPI dengan panggilan nyata ke `POST /v1/agent/evaluasi/:id/start` yang sudah diimplementasikan AI Engineer. Sertakan `X-Service-Token` di header request.

Payload yang dikirim ke FastAPI sudah terdefinisi di F-06 section 6. Pastikan `preferensi_perusahaan` ikut disertakan.

Jika FastAPI tidak tersedia (timeout atau error 5xx): kembalikan `AGENT_SERVICE_ERROR` (503) ke frontend.

### Kriteria Selesai F-10 [BE]

```
□ POST /evaluasi/:id/submit memanggil FastAPI /v1/agent/evaluasi/:id/start dengan payload benar
□ Header X-Service-Token disertakan di request ke FastAPI
□ Jika FastAPI tidak tersedia: response 503 dengan AGENT_SERVICE_ERROR
□ Payload menyertakan preferensi_perusahaan (nullable)
```

---

## F-11 — Hasil TOPSIS & Reasoning (P-05 Bagian 1–2–6)

**Tier:** 3 | **Prerequisite:** F-10 | **Estimasi:** 1–2 hari (Next.js side)

### Yang Perlu Dibuat (Next.js)

#### GET /api/v1/evaluasi/:id/hasil

Auth required. Proxy ke FastAPI `GET /v1/scoring/evaluasi/:id/hasil`.

Resource-level check: staff hanya bisa ambil hasil evaluasi miliknya (cek `created_by`).

Response: teruskan response dari FastAPI ke frontend tanpa transformasi. Seluruh struktur data termasuk field kualitatif dan preferensi sudah terdefinisi di BE-02 section 9.

### Kriteria Selesai F-11 [BE]

```
□ GET /evaluasi/:id/hasil berhasil proxy ke FastAPI dan mengembalikan data lengkap
□ Staff tidak bisa mengakses hasil evaluasi milik staff lain (403)
□ Response shape sesuai BE-02 section 9
```

---

## F-12 — Profil Kualitatif (P-05 Bagian 3–4)

**Tier:** 3 | **Prerequisite:** F-10, F-11 | **Estimasi:** Tidak ada task baru

Tidak ada task Backend Engineer di fitur ini. Output Qualitative Analyzer Agent sudah ikut dikembalikan di `GET /evaluasi/:id/hasil` yang dibangun di F-11.

---

## F-13 — Rekomendasi Preferensi & Conflict Callout (P-05 Bagian 5)

**Tier:** 3 | **Prerequisite:** F-08, F-12 | **Estimasi:** Tidak ada task baru

Tidak ada task Backend Engineer di fitur ini. Output Preference Matcher Agent sudah ikut dikembalikan di `GET /evaluasi/:id/hasil`.

---

## F-14 — AI Chat Panel + RAG

**Tier:** 3 | **Prerequisite:** F-07, F-11 | **Estimasi:** Tidak ada task baru di Next.js

Tidak ada task Backend Engineer di fitur ini. Endpoint `POST /v1/chat/stream` diakses langsung dari browser ke FastAPI (bukan via Next.js), sesuai arsitektur di AI-04 section 6.

> **Catatan koordinasi:** Pastikan konfigurasi CORS di FastAPI (`ALLOWED_ORIGINS`) sudah menyertakan origin domain frontend. Koordinasikan nilai ini dengan AI Engineer.

---

## Checkpoint Final — Release Readiness

### Verifikasi Security Komprehensif (Next.js)

Jalankan semua skenario dari SH-03 section 11.1:

```
□ JWT yang expired mengembalikan 401
□ JWT yang dimanipulasi mengembalikan 401
□ Staff mengakses evaluasi milik orang lain: 403
□ Staff mengakses endpoint Manager: 403
□ Request ke FastAPI tanpa service token: 401
□ Rate limit login: request ke-6 dalam 1 menit dari IP yang sama: 429
□ File upload > 10MB: 400
□ Bukan PDF/Excel: 400
□ SQL injection via query params: tidak ada error server, hanya data kosong
```

### Checklist Final [BE]

```
□ Semua skenario security test lulus
□ Rate limiting sesuai konfigurasi di BE-03 section 6.2
□ Audit trail: semua event di BE-03 section 9.2 tercatat
□ Spending alert Anthropic dan Tavily terkonfigurasi (koordinasi dengan AI Engineer)
□ Pipeline CI vendor-ai hijau (type check, lint, build, test)
□ CODEOWNERS terkonfigurasi: apps/api → Backend Engineer
```

---

## Referensi Cepat — Endpoint per Fitur

| Fitur | Next.js Endpoints | FastAPI Dipanggil (oleh BE) |
|---|---|---|
| F-00 | GET /api/health | — |
| F-01 | POST /auth/login, POST /auth/logout, POST /auth/refresh, GET /users/me | — |
| F-03 | GET /kategori-pengadaan, GET /konfigurasi/kriteria, PUT /konfigurasi/kriteria | — |
| F-04 | GET /evaluasi, GET /evaluasi/summary | — |
| F-06 | POST /evaluasi, GET /evaluasi/:id, POST /evaluasi/:id/vendor, DELETE /evaluasi/:id/vendor/:vendorId, POST /evaluasi/:id/submit | POST /v1/agent/evaluasi/:id/start (stub) |
| F-07 | POST /evaluasi/:id/dokumen, GET /evaluasi/:id/dokumen/:uploadId/status | POST /v1/agent/ekstrak-dokumen |
| F-09 | PATCH /evaluasi/:id/status, POST /evaluasi/:id/approval | — |
| F-10 | Update submit → panggil FastAPI nyata | POST /v1/agent/evaluasi/:id/start (real) |
| F-11 | GET /evaluasi/:id/hasil | GET /v1/scoring/evaluasi/:id/hasil |

> FastAPI endpoints di F-12, F-13, F-14 dibangun oleh **AI Engineer** dan tidak dipanggil langsung oleh Next.js (kecuali `/v1/chat/stream` yang diakses langsung dari browser).

---

## Referensi Cepat — Error Codes dan HTTP Status

| Code | HTTP | Digunakan di |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Login gagal |
| `INVALID_TOKEN` | 401 | JWT tidak valid |
| `INVALID_REFRESH_TOKEN` | 401 | Refresh token tidak valid |
| `FORBIDDEN` | 403 | Role tidak cukup atau akses resource orang lain |
| `EVALUASI_NOT_FOUND` | 404 | ID evaluasi tidak ditemukan |
| `VENDOR_NOT_FOUND` | 404 | ID vendor tidak ditemukan |
| `VENDOR_LIMIT_EXCEEDED` | 400 | Evaluasi sudah 10 vendor |
| `INSUFFICIENT_VENDORS` | 400 | Kurang dari 2 vendor saat submit |
| `EVALUASI_NOT_EDITABLE` | 409 | Status bukan draft |
| `ALREADY_SUBMITTED` | 409 | Evaluasi sudah pernah disubmit |
| `NOT_PENDING_APPROVAL` | 409 | Status bukan menunggu_approval |
| `INVALID_WEIGHT_TOTAL` | 400 | Total bobot kriteria bukan 100 |
| `FILE_TOO_LARGE` | 400 | File > 10MB |
| `INVALID_FILE_TYPE` | 400 | Bukan PDF atau Excel |
| `AGENT_SERVICE_ERROR` | 503 | FastAPI tidak bisa dijangkau |
| `RATE_LIMIT_EXCEEDED` | 429 | Terlalu banyak request |
| `PREFERENCE_TOO_LONG` | 400 | preferensi_perusahaan > 1.000 karakter |
| `RAG_INDEX_NOT_READY` | 409 | Dokumen belum selesai diindeks |
| `VALIDATION_ERROR` | 400 | Input tidak valid (generic) |

---

*Dokumen ini adalah panduan kerja operasional yang harus selalu sinkron dengan spesifikasi di BE-02 dan BE-03. Jika ada perubahan spec, panduan ini perlu diperbarui sebelum task implementasi dimulai.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-12 | Versi awal | — |
| 2.0.0 | 2026-06-12 | Adopsi 2-repo (ADR-031): perbarui section Prasyarat (vendor-ai-backend → apps/api dalam monorepo vendor-ai), perbarui tabel env vars (kolom Service), perbarui kriteria selesai F-00 (nama file .env.example dan FEATURE_STATUS.md per repo), perbarui referensi MILESTONE_PLAN ke v4.0.0 | — |
| 3.0.0 | 2026-06-12 | Adopsi 4 role (ADR-032): hapus semua konten FastAPI (F-10 s/d F-14, termasuk LangGraph, TOPSIS, RAG, SSE chat) — dipindah ke GUIDE_AI_ENGINEER; perbarui header (referensi hanya BE-02 dan BE-06); perbarui Tentang Dokumen (scope hanya apps/api); perbarui Prasyarat (hapus section vendor-ai-agent); sederhanakan tabel env vars; perbarui F-07 (hapus implementasi FastAPI ekstraksi); perbarui Checkpoint Final (hapus checklist AI) | — |
| 3.0.0 | 2026-06-13 | Adopsi ADR-035 dan ADR-036: ganti `be/develop` → `develop`; ganti semua referensi BE-06 → BE-03 (renumber Auth & Security); ganti referensi BE-07 section 4 → AI-04 section 6 (integrasi AI chat stream) | — |
