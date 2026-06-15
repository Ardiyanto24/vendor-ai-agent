# BE-01 — System Architecture Specification

**Project:** AI Vendor Selection System  
**Dokumen:** BE-01 — System Architecture  
**Versi:** 5.0.0  
**Tanggal:** 2026-06-13  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Tentang Dokumen Ini

BE-01 adalah dokumen arsitektur tingkat tinggi yang merangkum seluruh keputusan desain sistem. Dokumen ini ditulis **terakhir** — setelah semua dokumen spesifikasi lain selesai — karena isinya adalah sintesis dari keputusan yang sudah didefinisikan di dokumen-dokumen tersebut.

Dokumen ini menjadi **titik masuk pertama** bagi siapapun yang ingin memahami sistem secara keseluruhan sebelum masuk ke detail spesifik. Setelah membaca dokumen ini, pembaca harus memiliki gambaran yang jelas tentang apa yang dibangun, mengapa dirancang demikian, dan di mana menemukan detail lebih lanjut.

---

## Daftar Isi

1. [Tujuan Sistem](#1-tujuan-sistem)
2. [Konteks & Masalah yang Diselesaikan](#2-konteks--masalah-yang-diselesaikan)
3. [Gambaran Arsitektur Keseluruhan](#3-gambaran-arsitektur-keseluruhan)
4. [Komponen Utama](#4-komponen-utama)
5. [Alur Data End-to-End](#5-alur-data-end-to-end)
6. [Keputusan Arsitektur Kunci](#6-keputusan-arsitektur-kunci)
7. [Stack Teknologi Lengkap](#7-stack-teknologi-lengkap)
8. [Batasan & Scope MVP](#8-batasan--scope-mvp)
9. [Roadmap Pasca-MVP](#9-roadmap-pasca-mvp)
10. [Peta Dokumen Spesifikasi](#10-peta-dokumen-spesifikasi)

---

## 1. Tujuan Sistem

AI Vendor Selection System adalah aplikasi yang mengotomatisasi proses evaluasi dan pemilihan vendor dalam pengadaan barang dan jasa perusahaan. Sistem menggunakan AI agent untuk mengumpulkan data vendor dari berbagai sumber, menganalisa dari berbagai dimensi, dan menghasilkan rekomendasi vendor terbaik yang disertai penjelasan yang dapat diaudit.

**Nilai utama yang diberikan sistem:**

Sistem menggantikan proses evaluasi manual yang lambat, tidak konsisten, dan sulit diaudit — dengan proses yang sistematis, terukur, dan dapat dijelaskan. Setiap rekomendasi disertai skor per kriteria, reasoning naratif, dan catatan risiko yang memungkinkan procurement staff mempertanggungjawabkan keputusannya ke atasan.

**Untuk siapa sistem ini dibuat:**

Procurement staff yang sehari-harinya mengevaluasi vendor — dan manager yang menyetujui keputusan pengadaan. Keduanya mendapat manfaat berbeda: staff mendapat efisiensi dan konsistensi, manager mendapat visibilitas dan audit trail yang lengkap.

---

## 2. Konteks & Masalah yang Diselesaikan

### 2.1 Masalah yang ada saat ini

Proses evaluasi vendor di sebagian besar perusahaan dilakukan secara manual menggunakan kombinasi spreadsheet, email, dan pertimbangan subjektif. Masalah utama yang muncul:

**Tidak konsisten.** Dua staff yang mengevaluasi vendor yang sama bisa menghasilkan kesimpulan yang berbeda karena tidak ada metodologi yang standar. Keputusan bergantung pada pengalaman dan preferensi individu.

**Tidak dapat diaudit.** Sulit untuk menjelaskan *mengapa* vendor A dipilih dibanding vendor B kepada auditor atau manajemen. Jejak keputusan sering tidak terdokumentasi.

**Lambat dan manual.** Mengumpulkan informasi tentang vendor baru — legalitas, track record, harga pasar — membutuhkan waktu yang signifikan dan sering tidak dilakukan secara menyeluruh karena keterbatasan waktu.

**Bergantung pada satu orang.** Pengetahuan tentang vendor sering tersimpan di kepala satu atau dua orang, bukan di sistem yang bisa diakses semua orang.

### 2.2 Pendekatan solusi

Sistem menangani masalah ini melalui lima mekanisme:

**Standarisasi metodologi.** Semua evaluasi menggunakan algoritma TOPSIS dengan kriteria dan bobot yang terdefinisi — hasil tidak bergantung pada siapa yang mengevaluasi.

**Otomasi pengumpulan data.** AI agent mengumpulkan informasi vendor dari sumber publik secara otomatis, mengurangi ketergantungan pada riset manual.

**Analisis kualitatif di luar metrik.** Qualitative Analyzer Agent mengidentifikasi nilai tambah unik tiap vendor yang tidak bisa dikuantifikasi — mencegah keputusan hanya berdasarkan angka dan menangani skenario tie-breaking saat skor TOPSIS berdekatan.

**Explainability by design.** Setiap skor disertai reasoning naratif yang menjelaskan *mengapa* hasilnya demikian. AI Chat Panel dengan kemampuan RAG memungkinkan procurement staff menggali detail dari dokumen penawaran asli secara langsung.

**Kontekstualisasi dengan preferensi bisnis.** Preference Matcher Agent memungkinkan sistem memberikan rekomendasi yang mempertimbangkan konteks strategis perusahaan — bukan hanya metrik standar — melalui form preferensi opsional yang diisi saat membuat evaluasi.

---

## 3. Gambaran Arsitektur Keseluruhan

Sistem terdiri dari dua service yang bekerja bersama, didukung oleh satu platform data terpadu.

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (User)                                                  │
└──────────────┬───────────────────────────────┬──────────────────┘
               │ HTTPS (REST)                  │ SSE (streaming)
               ▼                               ▼
┌──────────────────────────────────┐   ┌──────────────────────────────────┐
│  vendor-ai (monorepo TypeScript) │   │  vendor-ai-agent (FastAPI)       │
│  Vercel                          │   │  Python                          │
│                                  │   │                                  │
│  apps/web                        │   │  - AI agent orchestration (7)    │
│  - UI (React/shadcn)             │   │  - Scoring engine (TOPSIS)       │
│  - Auth middleware               │◄──│  - RAG pipeline (index+retrieval)│
│                                  │   │  - AI chat (SSE + RAG context)   │
│  apps/api                        │   └──────────────┬───────────────────┘
│  - API Routes (BFF)              │                  │
│  - Validasi & otorisasi          │                  │
│  - CRUD ke Supabase              │                  │
│  - Proxy ke FastAPI              │                  │
└──────────────┬───────────────────┘                  │
               │                                      │
               └──────────────┬───────────────────────┘
                              │ Supabase JS Client
                              ▼
               ┌──────────────────────────────────────┐
               │  Supabase (Platform Data)             │
               │                                      │
               │  PostgreSQL + pgvector  │  Storage   │
               │  Auth                  │  Realtime  │
               └──────────────────────────────────────┘
                              │
               ┌──────────────┴──────────────────────┐
               │  External APIs                       │
               │  OpenRouter API │  Tavily API         │
               │  Google Gemini  │  (embedding)        │
               └─────────────────────────────────────┘
```

**Dua service utama:**

`vendor-ai` adalah monorepo TypeScript yang menggabungkan frontend dan BFF dalam satu repository. `apps/web` menangani semua yang berhubungan dengan user — tampilan UI, autentikasi, dan file upload. `apps/api` menangani validasi, otorisasi, CRUD ke Supabase, dan proxy ke FastAPI. Keduanya di-deploy bersama ke Vercel sebagai satu Next.js project.

`vendor-ai-agent` menangani semua yang berhubungan dengan kecerdasan buatan — menjalankan tujuh AI agent dengan dependency graph yang terstruktur, menghitung skor TOPSIS, menjalankan pipeline RAG untuk indexing dan retrieval dokumen, menghasilkan reasoning naratif, dan melayani chat streaming. Berjalan di Railway/Fly.io menggunakan Python.

`Supabase` menjadi platform data terpadu — PostgreSQL (dengan ekstensi pgvector untuk vector store RAG) untuk semua data relasional dan embedding chunk dokumen, Storage untuk file dokumen penawaran, Auth untuk autentikasi user, dan Realtime untuk broadcast progress agent ke frontend secara real-time.

---

## 4. Komponen Utama

### 4.1 Frontend & BFF — Next.js (vendor-ai)

Frontend dan Next.js API Routes (BFF) dibangun dalam satu monorepo TypeScript `vendor-ai`. `apps/web` dibangun dengan Next.js 14 App Router menggunakan pendekatan UI-first. Layout global menggunakan pola tiga panel: sidebar navigasi, panel konten utama, dan panel AI chat yang selalu hadir.

Delapan halaman utama melayani dua role user: Procurement Staff yang membuat dan memantau evaluasi, serta Manager yang melakukan approval dan mengkonfigurasi sistem.

State management menggunakan dua lapisan yang terpisah tugasnya: TanStack Query untuk server state (caching, refetching, invalidasi) dan Zustand untuk global client state (sesi user, riwayat chat, notifikasi).

Komponen UI dibangun di atas shadcn/ui dengan Tailwind CSS. Visualisasi data scoring menggunakan Chart.js. Shared TypeScript types antara `apps/web` dan `apps/api` dikelola di `packages/types`.

**Dokumen detail:** FE-01, FE-02, FE-03, FE-04, FE-05, FE-06

---

### 4.2 AI Agent Service — FastAPI (vendor-ai-agent)

FastAPI service adalah inti kecerdasan sistem. Ia dibangun dengan Python untuk memanfaatkan ekosistem ML/AI yang kaya — LangGraph untuk orchestration, numpy/scipy untuk scoring engine, OpenAI SDK (dengan `base_url` override ke OpenRouter) untuk LLM calls via DeepSeek-V4-Flash, dan Google Generative AI SDK untuk embedding.

**Tujuh sub-agent dengan dependency graph:**

```
Data Collector ──────────────────────────────┐
Financial Analyzer ──────────────────────────┤ (paralel)
Risk Assessor ───────────────────────────────┘
        ↓ semua selesai
Performance Scorer
        ↓ selesai
        ├── Negotiation Assistant ───────────┐ (paralel)
        └── Qualitative Analyzer ────────────┘
                ↓ keduanya selesai
        Preference Matcher
                ↓ selesai
        Scoring Engine
```

`Data Collector` mengumpulkan informasi publik vendor menggunakan Tavily API — profil perusahaan, sertifikasi, berita terkini, dan indikasi risiko.

`Financial Analyzer` mengevaluasi aspek finansial penawaran — kewajaran harga dibanding pasar, estimasi TCO, dan posisi harga relatif antar vendor.

`Risk Assessor` menilai risiko legalitas dan stabilitas bisnis berdasarkan informasi publik yang ditemukan, dengan disclaimer eksplisit bahwa ini bukan verifikasi resmi.

`Performance Scorer` mengevaluasi kemampuan teknis dan delivery vendor — kesesuaian spesifikasi, track record, dan kualitas layanan purna jual.

`Negotiation Assistant` menghasilkan rekomendasi negosiasi konkret berdasarkan output empat agent sebelumnya.

`Qualitative Analyzer` mengidentifikasi nilai tambah unik tiap vendor di luar lima kriteria standar — unique offerings yang ditemukan dari dokumen penawaran via RAG context dan output agent lain. Outputnya murni naratif, bukan skor numerik.

`Preference Matcher` mencocokkan profil vendor (TOPSIS + kualitatif) dengan preferensi bisnis perusahaan yang diinput opsional. Beroperasi dalam dua mode: netral (tanpa preferensi — output objektif) atau opinionated (dengan preferensi — rekomendasi 1–3 vendor yang paling sesuai, dengan catatan konflik jika berbeda dari ranking TOPSIS).

**Scoring Engine** menerima output agregat dari semua agent dan menjalankan TOPSIS untuk menghasilkan ranking vendor beserta skor per kriteria. Reasoning naratif — yang mengintegrasikan analisis kualitatif dan rekomendasi preferensi — dihasilkan terpisah oleh LLM setelah skor numerik terbentuk.

**Pipeline RAG** berjalan dalam dua momen berbeda: saat upload dokumen (indexing — chunking hierarkis, embedding via Google Gemini `text-embedding-004`, penyimpanan ke pgvector sebagai vektor 768 dimensi) dan saat chat (retrieval — query expansion, hybrid search BM25 + vector, injeksi context ke LLM).

**Dokumen detail:** AI-01, AI-02, AI-03, BE-07, AI-04, AI-05, AI-06

---

### 4.3 Platform Data — Supabase

Supabase dipilih sebagai platform tunggal yang menyediakan semua kapabilitas yang dibutuhkan sistem:

**PostgreSQL + pgvector** menyimpan sepuluh tabel yang merepresentasikan domain bisnis: user, evaluasi, vendor, dokumen upload, chunk dokumen untuk RAG, progress agent, hasil evaluasi, skor per vendor, konfigurasi kriteria, dan log approval. Ekstensi pgvector mengubah PostgreSQL menjadi vector store terintegrasi — tabel `dokumen_chunk` menyimpan embedding dari chunk dokumen penawaran dan digunakan untuk similarity search saat retrieval RAG. Semua tabel menggunakan UUID sebagai primary key dan soft delete untuk menjaga audit trail.

**Storage** menyimpan file dokumen penawaran vendor yang diupload user. Akses file hanya melalui signed URL yang berlaku terbatas.

**Auth** mengelola autentikasi user menggunakan JWT dengan access token berumur 1 jam dan refresh token 7 hari.

**Realtime** mem-broadcast perubahan pada tabel `agent_progress` ke frontend secara otomatis — memungkinkan halaman processing menampilkan status tiap agent (kini tujuh agent) secara real-time tanpa polling.

**Dokumen detail:** DB-01, DB-02, DB-03, DB-04

---

### 4.4 Lapisan Keamanan

Keamanan diterapkan dalam tiga lapisan independen yang bekerja secara defense in depth:

**Middleware Next.js** memvalidasi JWT dan memblokir akses ke route yang tidak sesuai role sebelum request mencapai handler apapun.

**API handler** melakukan pengecekan otorisasi ulang secara eksplisit — tidak bergantung pada middleware saja.

**Row Level Security (RLS) Supabase** memvalidasi akses di level database — lapisan terakhir yang tidak bisa dilewati bahkan jika ada bug di lapisan aplikasi.

**Dokumen detail:** BE-06

---

## 5. Alur Data End-to-End

Ini adalah alur lengkap dari saat user membuat evaluasi hingga rekomendasi tersedia:

```
1. User mengisi form evaluasi
   (requirement + preferensi opsional + daftar vendor + upload dokumen)
        │
        ▼
2. Next.js menyimpan evaluasi ke Supabase (status: draft)
   Jika ada dokumen: FastAPI menjalankan dua pipeline paralel:
     A. Ekstraksi field terstruktur (LLM)
     B. RAG indexing: chunking → embedding (Google Gemini) → simpan ke pgvector
        │
        ▼
3. User submit → Next.js memanggil FastAPI untuk memulai proses
   Status evaluasi → processing
        │
        ▼
4. FastAPI Orchestrator menginisialisasi 7 agent progress rows
   di Supabase. Supabase Realtime broadcast ke frontend → UI update
        │
        ▼
5. Tiga agent berjalan paralel: Data Collector, Financial Analyzer,
   Risk Assessor. Setiap progress update → tulis ke Supabase → broadcast
        │
        ▼
6. Performance Scorer berjalan setelah Data Collector selesai
        │
        ▼
7. Negotiation Assistant dan Qualitative Analyzer berjalan paralel.
   Qualitative Analyzer menggunakan RAG context dari dokumen penawaran
   untuk mengidentifikasi unique offerings tiap vendor
        │
        ▼
8. Preference Matcher berjalan setelah keduanya selesai.
   Jika ada preferensi → mode opinionated: cocokkan vendor dengan preferensi
   Jika tidak ada → mode netral: siapkan framing objektif
        │
        ▼
9. Orchestrator agregasi semua output → memanggil Scoring Engine
   Scoring Engine: normalisasi → TOPSIS → skor per kriteria →
   LLM generate reasoning (mengintegrasikan kualitatif + preferensi)
        │
        ▼
10. Hasil lengkap ditulis ke tabel hasil_evaluasi dan hasil_vendor
    (termasuk profil kualitatif, output preferensi, conflict callout jika ada)
    Status evaluasi → selesai
        │
        ▼
11. Frontend otomatis diarahkan ke halaman hasil (P-05)
    User melihat: ranking TOPSIS, profil kualitatif per vendor,
    rekomendasi berbasis preferensi (jika ada), reasoning AI
    AI Chat Panel aktif dengan RAG context → bisa menjawab pertanyaan
    berbasis isi dokumen penawaran asli
        │
        ▼
12. User mengirim hasil ke Manager → status → menunggu_approval
    Manager review dan approve/reject → approval_log dicatat
```

---

## 6. Keputusan Arsitektur Kunci

Bagian ini merangkum keputusan terpenting yang membentuk arsitektur sistem. Detail lengkap dengan alternatif yang ditolak ada di **SH-01 (Decision Log)**.

### 6.1 UI-first design (ADR-001)

Seluruh perancangan dimulai dari UI — mendefinisikan apa yang dilihat dan dilakukan user sebelum mendefinisikan API dan database. Ini memastikan sistem dibangun dari perspektif user, bukan perspektif teknis.

### 6.2 Arsitektur hybrid Next.js + FastAPI (ADR-010, ADR-036)

Next.js menangani semua operasi web standar (auth, CRUD, file upload). FastAPI menangani semua operasi AI dan komputasi berat. Pemisahan ini mengikuti batas alami antara ekosistem JavaScript/TypeScript dan Python — masing-masing digunakan untuk apa yang paling dikuasainya. Sesuai ADR-036, pemisahan teknis ini mencerminkan dua track pengerjaan: track Fullstack mengerjakan seluruh repo `vendor-ai` (database, backend, frontend), AI Engineer mengerjakan repo `vendor-ai-agent` secara eksklusif.

### 6.3 TOPSIS sebagai algoritma scoring (ADR-016)

TOPSIS dipilih karena hasilnya dapat dijelaskan secara intuitif ("vendor ini paling mendekati kondisi ideal"), deterministik (input sama selalu menghasilkan output sama), dan familiar bagi tim dengan background statistika/ML.

### 6.4 Supabase sebagai platform tunggal termasuk vector store (ADR-011, ADR-029)

Satu platform untuk database, storage, auth, realtime, **dan vector store** — mengurangi kompleksitas operasional secara signifikan. Ekstensi pgvector memungkinkan Supabase mengelola embedding RAG tanpa infrastruktur vector database terpisah.

### 6.5 Reasoning dipisah dari kalkulasi (AI-03)

Skor numerik dihitung oleh algoritma deterministik (TOPSIS). Penjelasan naratif — yang mengintegrasikan analisis kualitatif dan rekomendasi preferensi — dihasilkan terpisah oleh LLM *setelah* skor terbentuk. Ini memastikan narasi tidak mempengaruhi ranking dan hasil dapat diaudit secara independen.

### 6.6 Resiliensi agent — kegagalan satu tidak menghentikan yang lain (AI-01)

Jika satu agent gagal, agent lain tetap berjalan. Evaluasi diselesaikan dengan data yang tersedia, disertai flag dan peringatan tentang dimensi mana yang tidak lengkap. Ini diprioritaskan di atas kesempurnaan data — evaluasi parsial lebih berguna dari tidak ada evaluasi sama sekali.

### 6.7 RAG berbasis pgvector untuk AI Chat Panel (ADR-029, ADR-034, AI-04)

Dokumen penawaran diindeks ke pgvector saat upload — bukan dikirim ulang ke LLM setiap kali ada pertanyaan. Embedding menggunakan Google Gemini `text-embedding-004` yang menghasilkan vektor 768 dimensi. Retrieval menggunakan hybrid search (vector similarity + BM25) untuk menemukan chunk yang paling relevan. Ini memungkinkan AI Chat menjawab pertanyaan berbasis isi dokumen asli dengan biaya yang terkontrol.

### 6.8 Output berlapis — TOPSIS + kualitatif + preferensi (AI-03, AI-05, AI-06)

Sistem menghasilkan tiga lapisan output yang independen dan tidak saling mempengaruhi kalkulasi: ranking TOPSIS (objektif, numerik), analisis kualitatif (naratif, berbasis dokumen), dan rekomendasi preferensi (kontekstual, opsional). Lapisan ini memberikan fleksibilitas bagi procurement staff untuk memilih frame yang paling relevan dengan situasinya.

### 6.9 Form preferensi sebagai textarea bebas, bukan field terstruktur (ADR-030)

Preferensi bisnis terlalu bervariasi untuk distandarisasi dalam dropdown atau checkbox. Teks bebas memungkinkan ekspresi konteks yang natural — LLM lebih baik menginterpretasikan teks natural daripada mengisi kotak-kotak kaku. Opsionalitas memastikan sistem tetap sepenuhnya fungsional tanpa preferensi.

---

## 7. Stack Teknologi Lengkap

### Frontend (vendor-ai — apps/web)

| Komponen | Teknologi |
|---|---|
| Framework | Next.js 14 (App Router) |
| Bahasa | TypeScript 5 |
| Styling | Tailwind CSS |
| UI Components | shadcn/ui |
| State — server | TanStack Query v5 |
| State — client | Zustand v4 |
| Form & validasi | React Hook Form + Zod |
| Chart | Chart.js + react-chartjs-2 |
| Realtime client | Supabase JS Client |
| Testing | Vitest + React Testing Library + Playwright |
| Deployment | Vercel |

### Backend BFF (vendor-ai — apps/api)

| Komponen | Teknologi |
|---|---|
| Framework | Next.js 14 API Routes |
| Bahasa | TypeScript 5 |
| Validasi | Zod |
| Auth | Supabase Auth (JWT) |
| Database client | Supabase JS Client |
| Testing | Vitest |
| Deployment | Vercel (bersama apps/web) |

### AI Service (vendor-ai-agent)

| Komponen | Teknologi |
|---|---|
| Framework | FastAPI (Python) |
| Agent framework | LangGraph |
| LLM | DeepSeek-V4-Flash via OpenRouter (OpenAI SDK + base_url override) |
| Embedding | Google Gemini text-embedding-004 (768 dimensi) |
| Web search | Tavily API |
| Scoring engine | numpy + scipy |
| PDF extraction | pdfminer.six / pdfplumber |
| Async | asyncio + uvicorn |
| Testing | pytest + pytest-asyncio |
| Deployment | Railway atau Fly.io |

### Platform Data

| Komponen | Teknologi |
|---|---|
| Database | Supabase (PostgreSQL) |
| Vector store | pgvector (ekstensi PostgreSQL di Supabase) |
| Storage | Supabase Storage |
| Auth | Supabase Auth (JWT) |
| Realtime | Supabase Realtime |
| Migration | Supabase CLI |
| Backup | Supabase PITR + off-platform storage |

### Shared / Infrastructure

| Komponen | Teknologi |
|---|---|
| Version control | Git (GitHub) |
| Repository | 2-repo: `vendor-ai` (TypeScript monorepo) + `vendor-ai-agent` (Python) |
| CI/CD | GitHub Actions |
| Branching `vendor-ai` | `develop` (Fullstack) |
| Branching `vendor-ai-agent` | `develop` (AI Engineer) |
| Secret management | Environment variables (Vercel + Railway dashboard) |

---

## 8. Batasan & Scope MVP

Sistem MVP ini sengaja membatasi scope untuk memfokuskan pengembangan pada nilai inti. Batasan berikut adalah keputusan yang disengaja, bukan kekurangan:

### 8.1 Batasan yang sudah terdefinisi

**Dua role saja (staff dan manager).** Tidak ada admin, supervisor, atau role lain. Konfigurasi sistem sepenuhnya di tangan manager.

**Maksimum 10 vendor per evaluasi.** Cukup untuk proses pengadaan yang kompetitif, dalam batas biaya API yang wajar.

**Tidak ada integrasi ERP.** Data historis vendor diinput manual atau melalui upload dokumen. Integrasi ERP adalah roadmap pasca-MVP.

**Verifikasi legalitas tidak resmi.** Risk Assessor menggunakan informasi dari web search, bukan API database pemerintah (OSS, AHU). Setiap output menyertakan disclaimer tentang keterbatasan ini.

**Tidak ada notifikasi email.** Notifikasi hanya in-app. Email adalah roadmap pasca-MVP.

**Riwayat chat tidak persisten.** Chat history hilang saat browser ditutup. RAG context dari dokumen tetap tersimpan di pgvector dan diambil ulang saat sesi baru dimulai — yang tidak persisten adalah riwayat percakapan, bukan kemampuan menjawab berbasis dokumen.

**Bahasa interface: Indonesia.** Output naratif AI selalu dalam Bahasa Indonesia. Bahasa lain tidak didukung di MVP.

**Preferensi per evaluasi, tidak ada konfigurasi global.** Preferensi bisnis harus diisi ulang setiap evaluasi baru — tidak ada template atau konfigurasi default yang berlaku otomatis.

### 8.2 Mengapa batasan ini tepat untuk MVP portofolio

Batasan-batasan ini memungkinkan sistem dibangun dengan biaya dan waktu yang terkontrol sambil tetap mendemonstrasikan nilai inti yang sesungguhnya: AI agent yang menganalisa vendor secara multi-dimensi, scoring engine yang transparan dan dapat dijelaskan, dan approval workflow yang lengkap.

---

## 9. Roadmap Pasca-MVP

Berdasarkan diskusi selama perancangan, berikut adalah prioritas pengembangan setelah MVP selesai:

### Prioritas tinggi

**Integrasi ERP/SAP** — Mengambil data historis transaksi vendor langsung dari sistem ERP perusahaan. Ini adalah sumber sinyal paling berharga yang belum dimanfaatkan di MVP. Interface mock sudah disiapkan di arsitektur MVP untuk memudahkan integrasi ini.

**Verifikasi legalitas resmi** — Koneksi ke API resmi pemerintah (OSS, AHU Online) untuk verifikasi NIB dan status perusahaan yang akurat.

### Prioritas menengah

**Notifikasi email** — Menggunakan Resend atau SendGrid untuk mengirim notifikasi approval ke manager dan feedback ke staff.

**Riwayat chat persisten** — Menyimpan riwayat percakapan AI di server sehingga context tidak hilang saat sesi berakhir.

**Re-evaluasi** — Kemampuan untuk mengevaluasi ulang vendor yang sama dengan konfigurasi atau data yang diperbarui, dan membandingkan hasilnya dengan evaluasi sebelumnya.

### Prioritas rendah (jangka panjang)

**Integrasi marketplace vendor** — Mengambil data vendor dari platform B2B (Tokopedia for Business, Ralali, e-Katalog LKPP).

**Multi-bahasa** — Dukungan bahasa Inggris dan bahasa lain untuk perusahaan multinasional.

**Role tambahan** — Admin sistem, auditor read-only, atau approval multi-level.

---

## 10. Peta Dokumen Spesifikasi

Seluruh sistem didokumentasikan dalam **30 dokumen** yang terbagi dalam lima namespace:

### Shared — lintas domain

| Kode | Dokumen | Isi Singkat |
|---|---|---|
| SH-01 | Decision Log | 36 keputusan teknis dan produk dengan alternatif yang ditolak |
| SH-02 | Deployment Runbook | Prosedur deployment, branching strategy 2 track, rollback |
| SH-03 | Testing Strategy | Strategi testing holistik semua lapisan termasuk RAG |
| SH-04 | Cost & Usage Guide | Estimasi biaya per evaluasi dan per bulan, 5 komponen biaya |

### BE — Backend Engineer

Dikerjakan oleh track Fullstack, subdomain Backend (Next.js API Routes, `vendor-ai/apps/api`):

| Kode | Dokumen | Isi Singkat |
|---|---|---|
| BE-01 | System Architecture | Dokumen ini — gambaran arsitektur keseluruhan |
| BE-02 | API Contract | Endpoint lengkap termasuk RAG query endpoint |
| BE-06 | Auth & Security | JWT, RBAC, RLS, audit trail, secret management |
| BE-07 | Integration Spec | Tavily, Supabase Storage, OpenRouter (LLM), Google Gemini (embedding) |

### FE — Frontend Engineer

Dikerjakan oleh track Fullstack, subdomain Frontend (Next.js, `vendor-ai/apps/web`):

| Kode | Dokumen | Isi Singkat |
|---|---|---|
| FE-01 | UI Architecture | Next.js App Router, monorepo TypeScript `vendor-ai`, Vercel deployment |
| FE-02 | Component Library | 23 komponen termasuk komponen kualitatif dan preferensi |
| FE-03 | Page & User Flow | 8 halaman, form preferensi, P-05 dengan 6 bagian hasil |
| FE-04 | State Management | TanStack Query + Zustand, tiga lapisan state |
| FE-05 | API Integration | HTTP client, token refresh, SSE, Supabase Realtime |
| FE-06 | Testing & QA Frontend | Vitest, Playwright, aksesibilitas, coverage target |

### DB — Database Engineer

Dikerjakan oleh track Fullstack, subdomain Database (Supabase, `vendor-ai/supabase/migrations`):

| Kode | Dokumen | Isi Singkat |
|---|---|---|
| DB-01 | Data Model & ERD | 10 tabel termasuk dokumen_chunk untuk pgvector |
| DB-02 | Migration Strategy | Supabase CLI, aktivasi pgvector, urutan 10 tabel |
| DB-03 | Query & Performance | Query pattern termasuk hybrid search RAG |
| DB-04 | Backup & Retention | PITR, jadwal backup, restore procedure, retensi data |

### AI — AI Engineer

Dikerjakan oleh track AI Engineer (`vendor-ai-agent`, FastAPI + Python):

| Kode | Dokumen | Isi Singkat |
|---|---|---|
| AI-01 | Agent Orchestration | Tujuh agent, dependency graph, pipeline RAG indexing |
| AI-02 | Prompt Library | Template prompt 7 agent + query expansion RAG |
| AI-03 | Scoring Engine | TOPSIS + output berlapis (kualitatif + preferensi) |
| AI-04 | RAG Specification | Pipeline indexing + retrieval, pgvector, hybrid search |
| AI-05 | Qualitative Analyzer Agent | Agent keenam — analisis nilai tambah unik vendor |
| AI-06 | Preference Matcher Agent | Agent ketujuh — pencocokan preferensi bisnis perusahaan |

---

*Dokumen ini adalah living document — akan diperbarui saat ada perubahan arsitektur yang signifikan. Perubahan arsitektur yang berdampak besar harus dicatat di SH-01 (Decision Log) terlebih dahulu sebelum dokumen ini diperbarui.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-08 | Versi awal — dokumen penutup dari 21 dokumen spesifikasi | — |
| 2.0.0 | 2026-06-11 | Perbarui arsitektur untuk 7 agent (tambah Qualitative Analyzer dan Preference Matcher); tambah pipeline RAG dan OpenAI Embedding API ke diagram dan komponen; perbarui alur data end-to-end (12 langkah); tambah keputusan arsitektur kunci 6.7–6.9; perbarui stack teknologi; perbarui batasan MVP; perbarui peta dokumen dari 21 ke 24 dokumen | — |
| 3.0.0 | 2026-06-12 | Adopsi 2-repo (ADR-031): perbarui diagram arsitektur section 3 (dari 3 service ke 2-repo dengan pemisahan apps/web dan apps/api), perbarui section 4.1 (nama dan deskripsi service), perbarui tabel Shared/Infrastructure section 7 (Repository dan Branching) | — |
| 4.0.0 | 2026-06-12 | Adopsi 4 role (ADR-032): perbarui section 6.2 (tambah referensi ADR-032 dan kalimat pemisahan role developer); perbarui section 7 (pisah tabel stack menjadi tiga: Frontend, Backend BFF, AI Service; perbaiki label header dari nama lama ke nama repo baru); perbarui tabel Branching Shared/Infrastructure (pisah baris branching per repo dengan pemilik eksplisit); perbarui section 10 peta dokumen (pisah namespace BE menjadi dua kelompok: Backend Engineer dan AI Engineer; perbarui SH-01 count ADR; perbarui deskripsi SH-02) | — |
| 5.0.0 | 2026-06-13 | Ganti LLM dari Claude Sonnet (Anthropic API) ke DeepSeek-V4-Flash (OpenRouter API) dan embedding dari OpenAI text-embedding-3-small ke Google Gemini text-embedding-004 (768 dimensi): perbarui diagram External APIs (section 3), deskripsi SDK AI Service (section 4.2), deskripsi pipeline RAG (section 4.2), alur data langkah 2B (section 5), referensi ADR section 6.7, tabel stack AI Service (section 7), roadmap pasca-MVP (hapus Anthropic Batch API, section 9), deskripsi BE-07 dan jumlah ADR SH-01 di peta dokumen (section 10) | — |
| 6.0.0 | 2026-06-13 | Adopsi namespace AI (ADR-035) dan 2 track solo developer (ADR-036): perbarui section 6.2 (ADR-032 → ADR-036, narasi 4 role → 2 track); perbarui section 6.6/6.7/6.8 (referensi BE-03/05/08/09/10 → AI-01/03/04/05/06); perbarui tabel branching section 7 (fe/develop+be/develop → satu develop); tulis ulang section 10 peta dokumen (dari 4 namespace/24 dokumen → 5 namespace/30 dokumen; tambah namespace AI dengan AI-01 s/d AI-06; pisahkan namespace BE menjadi BE dan FE dan DB yang berdiri sendiri; perbarui jumlah ADR SH-01) | — |
