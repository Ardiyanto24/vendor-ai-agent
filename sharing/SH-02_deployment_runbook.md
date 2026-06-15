# SH-02 — Deployment Runbook

**Project:** AI Vendor Selection System  
**Dokumen:** SH-02 — Deployment Runbook  
**Versi:** 4.0.0  
**Tanggal:** 2026-06-12  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Gambaran Infrastruktur](#3-gambaran-infrastruktur)
4. [Environment yang Dikelola](#4-environment-yang-dikelola)
5. [Setup Environment Baru](#5-setup-environment-baru)
6. [Branching Strategy](#6-branching-strategy)
7. [Deployment Frontend (Vercel)](#7-deployment-frontend-vercel)
8. [Deployment Backend Next.js API Routes](#8-deployment-backend-nextjs-api-routes)
9. [Deployment FastAPI](#9-deployment-fastapi)
10. [Deployment Database (Supabase Migration)](#10-deployment-database-supabase-migration)
11. [Urutan Deployment yang Benar](#11-urutan-deployment-yang-benar)
12. [Rollback Procedure](#12-rollback-procedure)
13. [Health Check & Smoke Test](#13-health-check--smoke-test)
14. [Prosedur Deployment Production](#14-prosedur-deployment-production)
15. [Prosedur Darurat](#15-prosedur-darurat)
16. [Checklist Deployment Production](#16-checklist-deployment-production)
17. [Aturan & Larangan](#17-aturan--larangan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **prosedur operasional lengkap** untuk men-deploy, mengupdate, dan me-rollback sistem di semua environment — dari development lokal hingga production.

Dokumen ini menjawab pertanyaan: bagaimana setup environment baru dari nol, bagaimana urutan deployment yang benar, apa yang dilakukan saat deployment gagal, dan apa yang dilakukan saat ada insiden di production.

Dokumen ini dirancang agar siapapun di tim dapat menjalankan prosedur dengan benar — termasuk engineer yang baru bergabung atau dalam kondisi darurat saat engineer utama tidak tersedia.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-01 | UI Architecture | Stack dan struktur repository frontend |
| BE-02 | API Contract | Endpoint yang perlu diverifikasi setelah deployment |
| BE-06 | Auth & Security | Environment variables dan secret yang perlu dikonfigurasi |
| DB-02 | Migration Strategy | Prosedur migration database |
| DB-04 | Backup & Retention | Backup yang wajib ada sebelum deployment production |
| SH-03 | Testing Strategy | Test yang harus lulus sebelum deployment |
| SH-04 | Cost & Usage Guide | Monitoring biaya setelah deployment |

---

## 3. Gambaran Infrastruktur

```
┌─────────────────────────────────────────────────────────────┐
│  Repository: vendor-ai (monorepo TypeScript)                │
│  apps/web → Platform: Vercel                                │
│  apps/api → Platform: Vercel (API Routes)                   │
│  Trigger: Push ke branch main/staging/PR                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────┐
│  Repository: vendor-ai-agent                                │
│  Platform: Railway atau Fly.io (FastAPI)                    │
│  Trigger: Push ke branch main/staging                       │
└────────┬────────────────────────────────────────────────────┘
         │ Supabase JS Client
┌────────▼────────────────────────────────────────────────────┐
│  Supabase Project                                           │
│  Database (PostgreSQL) + Storage + Auth + Realtime          │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Environment yang Dikelola

Sistem memiliki tiga environment dengan tujuan berbeda:

| Environment | Tujuan | Database | Auto-deploy |
|---|---|---|---|
| **Development (lokal)** | Development dan testing lokal | Supabase dev project | Tidak |
| **Staging** | Integrasi, QA, dan demo | Supabase staging project | Ya (dari branch `staging`) |
| **Production** | Pengguna nyata | Supabase production project | Tidak (manual + approval) |

**Prinsip isolasi:** Setiap environment menggunakan Supabase project yang terpisah — tidak ada sharing database antar environment. Ini memastikan data production tidak pernah tercampur dengan data testing.

---

## 5. Setup Environment Baru

Bagian ini mendokumentasikan langkah-langkah untuk setup environment dari nol — berguna saat onboarding developer baru atau setup staging baru.

### 5.1 Prasyarat

Sebelum memulai, pastikan tersedia:
- Akses ke Supabase dashboard untuk membuat project baru
- Akses ke OpenRouter dashboard untuk membuat API key (LLM)
- Akses ke Google AI Studio untuk membuat API key (embedding)
- Akses ke Tavily dashboard untuk API key
- Akses ke Vercel untuk deployment frontend
- Akses ke platform FastAPI hosting (Railway atau Fly.io)
- Node.js 18+, Python 3.11+, dan Supabase CLI terinstal secara lokal

### 5.2 Langkah setup Supabase

```
1. Buat Supabase project baru di dashboard
2. Catat: project URL, anon key, service role key
3. Aktifkan Realtime untuk tabel agent_progress:
   Dashboard → Database → Replication → aktifkan tabel agent_progress
4. Jalankan semua migration dari awal:
   supabase db push --linked
5. Jalankan seed data:
   supabase db seed
6. Verifikasi semua tabel terbuat dengan benar
7. Verifikasi RLS aktif di semua tabel
```

### 5.3 Langkah setup environment variables

Setiap repository memiliki file `.env.example` yang berisi daftar variabel yang perlu diisi. Salin file tersebut menjadi `.env.local` (untuk development) atau konfigurasi di platform deployment (untuk staging/production).

**vendor-ai — `apps/web` (`.env.local`):**

| Variabel | Keterangan |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | URL Supabase project |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Anon key Supabase |
| `NEXT_PUBLIC_FASTAPI_URL` | URL FastAPI service |

**vendor-ai — `apps/api` (server-only, variabel tambahan di luar `apps/web`):**

| Variabel | Keterangan |
|---|---|
| `SUPABASE_URL` | URL Supabase project |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (rahasia!) |
| `FASTAPI_INTERNAL_URL` | URL internal FastAPI |
| `SERVICE_TOKEN` | Service-to-service token |
| `JWT_SECRET` | Secret untuk validasi JWT (dari Supabase) |

**vendor-ai-agent (FastAPI):**

| Variabel | Keterangan |
|---|---|
| `SUPABASE_URL` | URL Supabase project |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key |
| `OPENROUTER_API_KEY` | API key OpenRouter untuk LLM (rahasia!) |
| `GOOGLE_API_KEY` | API key Google Gemini untuk embedding (rahasia!) |
| `TAVILY_API_KEY` | API key Tavily |
| `SERVICE_TOKEN` | Service-to-service token (sama dengan apps/api) |
| `ALLOWED_ORIGINS` | CORS origins yang diizinkan |

### 5.4 Verifikasi setup

Setelah semua environment variable dikonfigurasi, jalankan health check untuk memverifikasi semua komponen terhubung dengan benar:

```
1. Jalankan frontend development server: npm run dev
2. Akses halaman login — pastikan tidak ada error console
3. Login dengan akun test — verifikasi redirect ke dashboard
4. Buka halaman buat evaluasi — verifikasi dropdown kategori muncul
5. Verifikasi Supabase Realtime terhubung (tidak ada error di console)
6. Test chat panel — verifikasi SSE berfungsi (teks muncul bertahap)
```

---

## 6. Branching Strategy

### 6.1 Prinsip dasar

Project ini dikerjakan dalam **dua track** sesuai ADR-036: track **Fullstack** (satu orang mengerjakan seluruh repo `vendor-ai` — database, backend, dan frontend) dan track **AI Engineer** (repo `vendor-ai-agent`). Strategi branching mencerminkan realita ini — sederhana untuk satu orang, dengan tetap mempertahankan kejelasan alur perubahan menuju staging dan production.

Model yang diadopsi adalah **feature-based development di atas 2-repo**: setiap fitur adalah unit kerja vertikal yang dikerjakan end-to-end — database → backend → frontend — sebelum pindah ke fitur berikutnya. Fitur yang melibatkan AI Engineer juga dikerjakan bersamaan di `vendor-ai-agent` dengan nama branch yang seragam.

Kunci agar model ini bekerja:
- Setiap fitur memiliki **nomor fitur yang seragam** (F-XX) sebagai identifier tunggal lintas repo
- Repo `vendor-ai` dikerjakan oleh satu developer Fullstack — satu `develop` branch cukup, tidak perlu dipisah per lapisan
- Repo `vendor-ai-agent` dikerjakan eksklusif oleh AI Engineer — branch `develop` di repo ini adalah milik AI Engineer
- Urutan kerja per fitur di `vendor-ai`: **DB → BE → FE** — skema harus ada sebelum endpoint dibuat, endpoint harus ada sebelum UI bisa connect ke API nyata
- Frontend menggunakan **MSW mock** sementara selama DB dan BE belum siap — ini memungkinkan FE dibangun dan ditest lebih awal dalam jendela yang sama

### 6.2 Branch utama

**Repository `vendor-ai` (monorepo TypeScript):**

| Branch | Pemilik | Auto-deploy | Protection |
|---|---|---|---|
| `main` | Fullstack (via PR) | Production (manual) | Protected — hanya via PR |
| `staging` | Fullstack (via PR) | Staging (otomatis) | Protected — hanya via PR |
| `develop` | Fullstack | Tidak | Semi-protected |

**Repository `vendor-ai-agent` (FastAPI):**

| Branch | Pemilik | Auto-deploy | Protection |
|---|---|---|---|
| `main` | AI Engineer (via PR) | Production (manual) | Protected — hanya via PR |
| `staging` | AI Engineer (via PR) | Staging (otomatis) | Protected — hanya via PR |
| `develop` | AI Engineer | Tidak | Semi-protected |

**Catatan:** Migration database (`supabase/migrations/`) disimpan di dalam repo `vendor-ai` dan dikerjakan oleh Fullstack sebagai bagian dari flow DB → BE → FE. Tidak ada branch terpisah untuk database — migration berjalan bersama feature branch `vendor-ai`.

### 6.3 Branch untuk fitur

Setiap fitur membuat branch dengan **nama yang seragam di kedua repository**:

```
vendor-ai        →  feature/F-XX-nama-fitur   (DB + BE + FE dalam satu branch)
vendor-ai-agent  →  feature/F-XX-nama-fitur   (AI Engineer, jika fitur menyentuh agent/scoring/RAG)
```

Fitur yang hanya menyentuh `vendor-ai` (tidak ada perubahan FastAPI) cukup membuat branch di `vendor-ai`. Fitur yang melibatkan perubahan AI service juga membuat branch di `vendor-ai-agent` dengan nama yang sama.

**Konvensi penamaan:**
- Feature: `feature/F-XX-nama-singkat` — contoh: `feature/F-06-buat-evaluasi`
- Bug fix (dalam konteks fitur aktif): `fix/F-XX-deskripsi` — contoh: `fix/F-06-validasi-vendor`
- Hotfix production: `hotfix/deskripsi` — dibuat langsung dari `main`, bypass staging hanya untuk kondisi kritis

### 6.4 Feature window: urutan kerja dalam satu fitur

Setiap fitur dikerjakan secara **sequential** dalam satu jendela waktu. Urutan baku adalah DB → BE → FE, dengan MSW sebagai scaffolding sementara:

```
Tahap 1 — DB
  Buat dan jalankan migration di Supabase dev
  Verifikasi skema, RLS, dan seed data

Tahap 2 — BE
  Implementasi endpoint Next.js API Routes (apps/api)
  Test endpoint secara lokal dengan Supabase dev

Tahap 2 (paralel, jika fitur menyentuh vendor-ai-agent)
  AI Engineer: implementasi FastAPI endpoint dan pipeline AI
  Koordinasi payload dengan BE via AI-01 dan BE-02 sebagai kontrak

Tahap 3 — FE
  Bangun komponen dan halaman (apps/web)
  Gunakan MSW mock selama BE belum siap di staging
  Switch dari MSW ke API nyata begitu endpoint tersedia di staging

Tahap 4 — Verifikasi end-to-end
  Verifikasi fitur bekerja penuh: DB → BE → FE
  Update FEATURE_STATUS.md
  Merge feature branch ke develop
```

**Mengapa bukan paralel?** Untuk solo developer, mengerjakan DB, BE, dan FE secara paralel dalam satu fitur bukan menghemat waktu — justru menambah context-switching. Sequential lebih efisien karena setiap lapisan memberikan fondasi nyata bagi lapisan berikutnya. MSW memungkinkan FE dibangun tanpa menunggu BE — tapi FE baru bisa diverifikasi end-to-end setelah BE selesai.

### 6.5 Feature handshake: tracking status fitur

Setiap repo menyimpan file `FEATURE_STATUS.md` di root untuk melacak status setiap fitur, terutama koordinasi antara track Fullstack dan AI Engineer.

**Format FEATURE_STATUS.md:**

```markdown
# Feature Status

| Fitur | DB | BE | FE | AI | Notes |
|-------|----|----|----|----|-------|
| F-01 Auth & Login | ✅ 2026-06-15 | ✅ 2026-06-16 | ✅ 2026-06-17 | — | AI tidak terlibat |
| F-06 Buat Evaluasi | ✅ 2026-06-18 | ✅ 2026-06-19 | ✅ 2026-06-20 | — | FE sudah switch dari MSW |
| F-10 AI Processing | ✅ 2026-06-25 | ✅ 2026-06-26 | ⏳ menunggu AI | 🔄 in progress | |
```

Kolom `AI` hanya relevan untuk fitur yang menyentuh `vendor-ai-agent` — untuk fitur lain, isi dengan `—`.

**Kapan setiap kolom dinyatakan ✅:**
- **DB:** Migration sudah berjalan di environment staging
- **BE:** Semua endpoint untuk fitur ini merespons dengan benar di staging
- **FE:** UI sudah connect ke API nyata (bukan MSW), fitur bisa digunakan end-to-end
- **AI:** FastAPI endpoint dan pipeline AI untuk fitur ini sudah berjalan di staging

### 6.6 Dependency antar fitur

Fitur-fitur memiliki dependency — branch `feature/F-XX` selalu dibuat dari `develop` yang sudah berisi hasil merge fitur-fitur prerequisite-nya. Daftar dependency lengkap per fitur ada di MILESTONE_PLAN.

PR description untuk setiap fitur wajib mencantumkan: *"Depends on: F-XX (merged)"* — reviewer menolak merge jika dependency belum ada di `develop`.

### 6.7 Integration point — merge ke staging dan main

```
vendor-ai: develop ──→ PR ke staging → integration test + E2E → PR ke main
                        (auto-deploy)   (harus lulus semua)     (manual)

vendor-ai-agent: develop ──→ PR ke staging (jika fitur menyentuh AI)
```

Syarat siap merge ke `staging`:
- Migration terkait sudah diverifikasi di Supabase dev
- FEATURE_STATUS.md menunjukkan DB ✅, BE ✅, FE ✅
- FEATURE_STATUS.md di `vendor-ai-agent` menunjukkan AI ✅ (jika fitur melibatkan AI Engineer)
- Unit dan integration test di develop branch lulus

### 6.8 Aturan PR dan review

Merge ke `staging` dan `main` hanya melalui Pull Request. Karena dikerjakan solo, self-review diperbolehkan — tapi checklist berikut harus dilengkapi sebelum merge:

```
□ Semua kriteria selesai di MILESTONE_PLAN untuk fitur ini sudah dicentang
□ FEATURE_STATUS.md diperbarui
□ Unit test baru untuk kode baru lulus
□ Tidak ada console.error atau Python traceback di log
□ Verifikasi manual end-to-end di staging berhasil
```
- Lulus semua pipeline CI yang relevan
- Di-approve secara eksplisit oleh reviewer

Merge dari feature branch ke develop branch masing-masing cukup direview oleh satu engineer dari role yang sama.

**Catatan untuk vendor-ai (monorepo):** Satu PR bisa mencakup perubahan di `apps/web` dan `apps/api` sekaligus. Gunakan CODEOWNERS untuk memastikan perubahan di `apps/web` selalu di-review oleh FE Engineer, dan perubahan di `apps/api` oleh BE Engineer — meskipun dalam PR yang sama.

**Catatan untuk vendor-ai-agent:** PR di repo ini di-review oleh AI Engineer. Untuk fitur yang melibatkan koordinasi ketat antara Next.js dan FastAPI (seperti F-10, F-11), direkomendasikan PR di kedua repo di-review dalam waktu berdekatan sebelum salah satunya di-merge.

**Catatan untuk lintas-repo:** Jangan merge satu sisi jauh sebelum sisi lainnya siap — terutama untuk fitur Tier 3 yang ketergantungan BE (Next.js) terhadap AI Engineer sangat erat.

### 6.9 Alur lengkap

```
[vendor-ai] — Track Fullstack
  feature/F-XX (DB + BE + FE) → develop ────→ PR ke staging
                                               (auto-deploy)
                                                    ↓
                                         integration test lulus
                                                    ↓
                                         PR ke main (manual)
                                                    ↓
                                              production

[vendor-ai-agent] — Track AI Engineer (jika fitur menyentuh AI — F-07, F-10, F-11, F-12, F-13, F-14)
  feature/F-XX (AI Engineer) → develop ─────→ PR ke staging (koordinasi dengan vendor-ai)
                                                    ↓
                                         PR ke main (manual)
                                                    ↓
                                              production

hotfix/*  ─────────────────────────────────────────→ main (bypass staging, kritis saja)
```

---

## 7. Deployment Frontend (Vercel)

### 7.1 Deployment otomatis

Vercel dikonfigurasi untuk deploy otomatis dari dua branch:
- `staging` → staging environment (URL: `staging.vendor-ai.vercel.app`)
- `main` → production environment (URL: domain produksi)

Setiap Pull Request juga mendapat preview deployment dengan URL unik yang di-generate otomatis.

### 7.2 Konfigurasi Vercel

**Build settings:**
- Framework: Next.js (auto-detected)
- Build command: `npm run build`
- Output directory: `.next` (auto-detected)
- Install command: `npm ci`

**Environment variables:**
Semua environment variable dikonfigurasi di Vercel dashboard per environment (Production, Preview, Development). Variabel sensitive tidak pernah di-commit ke repository.

### 7.3 Domain dan SSL

- Vercel menangani SSL secara otomatis untuk semua domain
- Custom domain dikonfigurasi di Vercel dashboard
- Redirect HTTP → HTTPS dikonfigurasi di `next.config.js`

### 7.4 Rollback frontend

Jika deployment baru bermasalah, Vercel memungkinkan instant rollback ke deployment sebelumnya melalui dashboard tanpa perlu push kode baru.

---

## 8. Deployment Backend Next.js API Routes

Frontend (`apps/web`) dan API Routes (`apps/api`) berada dalam satu repository `vendor-ai`. Keduanya di-deploy bersama melalui Vercel sebagai satu Next.js project — tidak ada deployment terpisah.

Vercel dikonfigurasi dengan **root directory** menunjuk ke `apps/web` (atau ke root jika menggunakan Turborepo dengan Vercel integration). API Routes (`app/api/v1/`) otomatis ter-deploy sebagai bagian dari Next.js deployment yang sama.

**Yang perlu diverifikasi setelah deployment backend:**
- Health check endpoint tersedia dan merespons 200
- Koneksi ke Supabase berfungsi
- Koneksi ke FastAPI berfungsi
- Endpoint auth dapat menerima login request

---

## 9. Deployment FastAPI

### 9.1 Platform

FastAPI di-deploy ke **Railway** atau **Fly.io** — keduanya mendukung deployment Python dengan konfigurasi minimal.

**Railway** lebih direkomendasikan untuk kemudahan setup. **Fly.io** lebih direkomendasikan jika butuh kontrol lebih atas region dan scaling.

### 9.2 Konfigurasi deployment FastAPI

**Requirements:**
- Python 3.11+
- File `requirements.txt` atau `pyproject.toml` untuk dependency
- `Procfile` atau konfigurasi platform untuk start command

**Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 9.3 Environment variables FastAPI

Semua environment variable dikonfigurasi melalui dashboard Railway/Fly.io — tidak pernah di-commit ke repository.

### 9.4 Health check FastAPI

FastAPI menyediakan endpoint `GET /health` yang mengembalikan status sistem:
- Status koneksi ke Supabase
- Status koneksi ke OpenRouter API (ping sederhana)
- Status koneksi ke Google Gemini Embedding API (ping sederhana)
- Versi aplikasi
- Uptime

Platform hosting menggunakan endpoint ini untuk health monitoring otomatis.

### 9.5 Deploy dari Git

Railway dan Fly.io mendukung auto-deploy dari GitHub. Setiap push ke branch `main` atau `staging` memicu deployment otomatis sesuai konfigurasi.

---

## 10. Deployment Database (Supabase Migration)

### 10.1 Migration di staging

Migration di staging dijalankan secara **otomatis** sebagai bagian dari CI/CD pipeline setiap kali ada merge ke branch `staging`.

Urutan di pipeline:
```
1. Jalankan semua test (unit, integration)
2. Build aplikasi
3. Jalankan migration di staging database
4. Deploy aplikasi ke staging
5. Jalankan smoke test
```

Jika migration gagal, pipeline berhenti dan deployment tidak dilanjutkan.

### 10.2 Migration di production

Migration di production **tidak dijalankan secara otomatis**. Prosedur lengkap ada di section 14 (Prosedur Deployment Production).

Secara ringkas, migration production dijalankan secara manual menggunakan Supabase CLI setelah semua prasyarat terpenuhi.

### 10.3 Verifikasi setelah migration

Setelah migration berhasil, verifikasi berikut wajib dilakukan:
- Semua tabel baru terbuat dengan benar
- RLS masih aktif di semua tabel
- Index yang diperlukan ada
- Sample query berjalan dengan benar dan performa dalam batas target (DB-03)

---

## 11. Urutan Deployment yang Benar

Urutan deployment penting untuk mencegah kondisi di mana frontend mengharapkan API atau skema database yang belum tersedia.

### 11.1 Untuk perubahan yang melibatkan semua komponen

```
1. Backup production database
2. Jalankan migration database (Supabase)
3. Deploy FastAPI (vendor-ai-agent)
4. Verifikasi FastAPI health check
5. Deploy vendor-ai ke Vercel (frontend + API Routes dalam satu deployment)
6. Verifikasi health check Next.js
7. Jalankan smoke test
8. Monitor 15 menit pertama
```

**Mengapa database dulu:** Skema database yang baru harus tersedia sebelum kode baru yang menggunakannya di-deploy. Jika dibalik, kode baru akan error saat mencoba mengakses tabel atau kolom yang belum ada.

**Mengapa FastAPI sebelum Next.js:** Next.js API Routes memanggil FastAPI. Jika Next.js di-deploy dulu, ada periode di mana Next.js memanggil FastAPI versi lama yang mungkin belum kompatibel.

### 11.2 Untuk perubahan hanya di frontend

```
1. Deploy Frontend (Vercel)
2. Verifikasi halaman utama dapat diakses
3. Monitor error rate 10 menit pertama
```

### 11.3 Untuk perubahan hanya di backend (tanpa skema baru)

```
1. Deploy FastAPI (jika ada perubahan di vendor-ai-agent)
2. Deploy vendor-ai ke Vercel (jika ada perubahan di apps/api)
3. Jalankan smoke test endpoint yang berubah
4. Monitor error rate 10 menit pertama
```

---

## 12. Rollback Procedure

### 12.1 Rollback frontend

Vercel menyimpan riwayat semua deployment. Rollback dapat dilakukan dalam < 1 menit melalui Vercel dashboard tanpa perlu push kode baru.

**Kapan rollback frontend:** Jika ada error yang terlihat di UI, halaman tidak bisa diakses, atau error rate meningkat signifikan setelah deployment.

### 12.2 Rollback FastAPI

Railway dan Fly.io menyimpan riwayat deployment. Rollback dilakukan melalui dashboard platform dengan memilih deployment sebelumnya.

Jika platform tidak mendukung rollback instan, rollback dilakukan dengan men-deploy ulang commit sebelumnya:
```
git revert <commit-hash> atau git checkout <previous-tag>
git push origin main
```

### 12.3 Rollback database migration

Rollback migration menggunakan rollback command yang sudah terdokumentasikan di header setiap migration file (sesuai DB-02 section 9.2).

**Prosedur:**
```
1. Identifikasi migration yang perlu di-rollback
2. Jalankan rollback command dari header file migration
3. Verifikasi skema database kembali ke state sebelumnya
4. Deploy ulang versi aplikasi yang kompatibel dengan skema lama
```

**Keputusan rollback:** Rollback database harus diputuskan dalam **15 menit** setelah deployment. Setelah 15 menit, investigasi lebih lanjut dilakukan dulu sebelum memutuskan rollback atau forward fix.

### 12.4 Rollback penuh (semua komponen)

Jika masalah melibatkan semua komponen, rollback dilakukan dalam urutan terbalik dari deployment:

```
1. Rollback Frontend (Vercel instant rollback)
2. Rollback Backend/API Routes
3. Rollback FastAPI
4. Rollback migration database (jika diperlukan)
```

---

## 13. Health Check & Smoke Test

### 13.1 Health check endpoints

Setiap service menyediakan endpoint health check yang mengembalikan status singkat:

| Service | Endpoint | Response sukses |
|---|---|---|
| Next.js | `GET /api/health` | `{ "status": "ok" }` |
| FastAPI | `GET /health` | `{ "status": "ok", "db": "connected", "anthropic": "reachable" }` |

Health check dipanggil otomatis oleh platform hosting untuk monitoring, dan secara manual setelah setiap deployment.

### 13.2 Smoke test setelah deployment

Smoke test adalah serangkaian pengecekan minimal untuk memverifikasi fungsi utama sistem masih berjalan setelah deployment:

**Smoke test manual (5 menit):**

```
1. Buka halaman login — pastikan form muncul
2. Login dengan akun test — pastikan berhasil masuk ke dashboard
3. Buka halaman buat evaluasi — pastikan form step 1 muncul dan kategori ter-load
4. Buat evaluasi sederhana (2 vendor) — pastikan submit berhasil dan masuk ke processing
5. Tunggu processing selesai (atau cek status agent_progress di Supabase)
6. Verifikasi halaman hasil muncul dengan ranking vendor
7. Buka AI chat panel — ketik pesan sederhana, verifikasi ada respons
```

**Smoke test otomatis:**

Playwright menjalankan subset E2E test yang paling kritis (happy path staff) sebagai smoke test setelah setiap deployment ke staging. Jika smoke test gagal, alert dikirim ke tim.

---

## 14. Prosedur Deployment Production

Deployment production adalah proses yang lebih formal dan membutuhkan persiapan yang lebih matang dari deployment staging.

### 14.1 Prasyarat deployment production

Sebelum memulai deployment production, semua kondisi berikut harus terpenuhi:

- Migration sudah berjalan di staging minimal **24 jam** tanpa masalah
- Integration test di staging lulus dalam **run terakhir** (bukan run lama)
- Backup production terbaru ada dan diverifikasi tidak lebih dari **24 jam yang lalu**
- Minimal **dua engineer** tersedia selama proses deployment
- Jendela maintenance dipilih pada jam traffic rendah
- Semua stakeholder yang relevan diberitahu tentang deployment

### 14.2 Prosedur step-by-step

**Fase 1 — Persiapan (H-1 jam):**
```
□ Konfirmasi dua engineer siap
□ Verifikasi backup terbaru ada dan bisa di-restore (restore test ke environment terpisah)
□ Review perubahan yang akan di-deploy (changelog)
□ Pastikan rollback command untuk setiap migration sudah siap
□ Buka monitoring dashboard (Supabase, Vercel, Railway/Fly.io)
□ Buka channel komunikasi tim
```

**Fase 2 — Database migration (jika ada):**
```
□ Announce ke tim: "Memulai migration production"
□ Jalankan migration via Supabase CLI:
   supabase db push --linked --project-ref <production-project-ref>
□ Verifikasi migration berhasil (cek tabel, index, RLS)
□ Jalankan sample query untuk memverifikasi performa masih dalam batas
□ Jika gagal: jalankan rollback dan batalkan deployment
```

**Fase 3 — Deploy service:**
```
□ Deploy FastAPI ke production (vendor-ai-agent)
□ Tunggu FastAPI health check hijau
□ Deploy vendor-ai ke Vercel (frontend + API Routes)
□ Tunggu Vercel deployment selesai dan health check hijau
```

**Fase 4 — Verifikasi:**
```
□ Jalankan smoke test manual (section 13.2)
□ Cek error rate di Vercel analytics (tidak ada lonjakan)
□ Cek log FastAPI (tidak ada error tidak terduga)
□ Cek Supabase dashboard (tidak ada anomali query)
□ Verifikasi Supabase Realtime masih berfungsi
```

**Fase 5 — Monitoring awal (15 menit):**
```
□ Pantau error rate selama 15 menit
□ Pantau response time endpoint utama
□ Pantau Anthropic API usage (tidak ada lonjakan tidak wajar)
□ Siapkan rollback command — jika ada anomali, rollback segera
□ Setelah 15 menit aman: announce ke tim bahwa deployment selesai
```

---

## 15. Prosedur Darurat

### 15.1 Definisi darurat

Kondisi darurat adalah saat sistem production mengalami masalah yang mempengaruhi user aktif dan tidak bisa ditunggu hingga jam kerja normal.

**Kondisi yang dikategorikan darurat:**
- Halaman login tidak bisa diakses (semua user terblokir)
- Error rate > 20% di endpoint utama selama > 5 menit
- Data corruption terdeteksi
- Security breach atau akses tidak sah terdeteksi

### 15.2 Eskalasi

```
Engineer pertama mendeteksi masalah
        ↓
Assess severity (darurat atau bisa tunggu?)
        ↓
Jika darurat: hubungi engineer kedua segera
        ↓
Bersama tentukan: rollback atau forward fix?
        ↓
Jalankan keputusan
        ↓
Dokumentasikan insiden (post-mortem)
```

### 15.3 Rollback darurat

Rollback darurat dilakukan secepat mungkin tanpa menunggu investigasi lengkap:

```
1. Rollback frontend via Vercel dashboard (< 1 menit)
2. Rollback backend/FastAPI via platform dashboard (2-5 menit)
3. Evaluate apakah rollback database diperlukan
4. Jalankan smoke test untuk konfirmasi sistem kembali normal
5. Announce ke stakeholder bahwa sistem kembali normal
6. Mulai investigasi root cause
```

### 15.4 Komunikasi saat insiden

- Engineer yang menangani insiden mengupdate channel tim setiap 15 menit
- Jika insiden berlangsung > 30 menit, stakeholder bisnis diberitahu
- Setelah insiden selesai, post-mortem ditulis dalam 24 jam

### 15.5 Post-mortem insiden

Setiap insiden production — berapapun durasinya — membutuhkan post-mortem yang mencakup:
- Timeline kejadian
- Root cause
- Dampak (berapa lama, berapa user terpengaruh)
- Tindakan yang diambil untuk recovery
- Tindakan pencegahan agar tidak terulang

---

## 16. Checklist Deployment Production

Checklist ini diisi setiap kali deployment production dilakukan. Semua item harus dicentang sebelum deployment dianggap selesai.

### Pra-deployment

```
□ Migration sudah berjalan di staging ≥ 24 jam tanpa masalah
□ Integration test staging lulus (run terbaru)
□ Backup production tersedia dan terverifikasi (≤ 24 jam)
□ Dua engineer hadir dan siap
□ Jendela maintenance dipilih (jam traffic rendah)
□ Stakeholder relevan diberitahu
□ Rollback commands untuk setiap migration sudah disiapkan
□ Monitoring dashboard terbuka
□ Channel komunikasi tim aktif
```

### Selama deployment

```
□ Migration database berhasil
□ Verifikasi skema database (tabel, index, RLS)
□ FastAPI health check hijau
□ Next.js health check hijau (frontend + API Routes)
□ Frontend deployment selesai di Vercel
□ Smoke test manual lulus (semua 7 langkah)
□ Error rate tidak ada lonjakan (5 menit pertama)
```

### Pasca-deployment

```
□ Monitor 15 menit tanpa anomali
□ OpenRouter API usage normal
□ Google Gemini Embedding API usage normal
□ Tavily API usage normal
□ Supabase Realtime berfungsi
□ Announce ke tim: deployment selesai
□ Update changelog atau release notes jika diperlukan
```

---

## 17. Aturan & Larangan

**Dilarang deploy ke production tanpa dua engineer hadir.** Deployment production bukan pekerjaan solo — selalu butuh dua orang.

**Dilarang deploy ke production tanpa backup yang terverifikasi.** Backup yang ada tapi tidak bisa di-restore sama dengan tidak ada backup.

**Dilarang deploy langsung ke main tanpa melalui staging terlebih dahulu** — kecuali hotfix kritis yang tidak bisa menunggu. Hotfix harus tetap melalui PR review dan CI.

**Dilarang menjalankan migration production secara otomatis.** Migration production selalu manual dan disupervisi.

**Dilarang melewatkan smoke test** setelah deployment apapun ke production — meskipun perubahannya tampak kecil.

**Dilarang mengabaikan anomali di monitoring 15 menit pertama.** Jika ada yang tidak normal, investigasi dulu sebelum menyatakan deployment selesai.

**Dilarang menutup insiden tanpa post-mortem.** Setiap insiden adalah kesempatan belajar yang harus didokumentasikan.

**Dilarang merge feature branch ke develop** jika fitur belum selesai di semua sisi yang relevan (DB, BE, FE). Partial merge menciptakan inkonsistensi di develop branch yang menyulitkan integration test.

**Dilarang memulai fitur dengan tier dependency lebih tinggi** sebelum fitur prerequisite-nya di-merge ke semua develop branch. Urutan fitur di MILESTONE_PLAN bukan rekomendasi — ia adalah urutan yang diwajibkan oleh dependency data dan API.

---

*Dokumen ini adalah living document — prosedur akan diperbarui berdasarkan pengalaman deployment aktual dan perubahan infrastruktur.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 1.1.0 | 2026-06-08 | Revisi section 6: branching strategy diperbarui untuk mengakomodasi 3 role developer (FE, BE, DB) bekerja paralel dengan develop branch terpisah per role | — |
| 2.0.0 | 2026-06-11 | Revisi section 6: adopsi feature-based development — branch naming seragam lintas repo (feature/F-XX), feature window, feature handshake via FEATURE_STATUS.md, dependency antar fitur; tambah aturan merge fitur di section 17 | — |
| 3.0.0 | 2026-06-12 | Adopsi 2-repo (ADR-031): perbarui section 3 (diagram infrastruktur), section 5.3 (env vars), section 6 (branching strategy dari polyrepo ke 2-repo), section 8 (deployment backend), section 11 (urutan deployment), section 14.2 (fase deploy), section 16 (checklist), section 17 (aturan merge) | — |
| 4.0.0 | 2026-06-12 | Adopsi 4 role (ADR-032): perbarui section 6.1 (tiga → empat role, tambah AI Engineer); perbarui tabel branch vendor-ai-agent (pemilik develop: Backend Engineer → AI Engineer); perbarui section 6.3 (FastAPI → AI Engineer); perbarui section 6.4 (tambah baris AI Engineer di feature window); perbarui section 6.5 (tambah kolom AI ready di FEATURE_STATUS.md); perbarui section 6.7 (tambah blok alur kerja AI Engineer); perbarui section 6.8 (tambah syarat AI ready di integration point); perbarui section 6.9 (tambah catatan vendor-ai-agent); perbarui section 6.10 (tambah label AI Engineer di alur lengkap) | — |
| 5.0.0 | 2026-06-13 | Adopsi 2 track solo developer (ADR-036): tulis ulang seluruh section 6 (branching dari fe/develop+be/develop → satu develop branch; feature window dari paralel 4 role → sequential DB→BE→FE; FEATURE_STATUS.md format disederhanakan; alur kerja tiap role dihapus, diganti narasi single developer); perbarui section 5.1 (Anthropic Console → OpenRouter + Google AI Studio); perbarui section 5.3 env vars FastAPI (ANTHROPIC_API_KEY, OPENAI_API_KEY → OPENROUTER_API_KEY, GOOGLE_API_KEY); perbarui section 9.4 health check FastAPI; perbarui section 16 checklist pasca-deployment (Anthropic → OpenRouter + Google Gemini) | — |
