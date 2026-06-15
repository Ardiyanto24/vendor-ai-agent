# SH-04 — Cost & Usage Guide

**Project:** AI Vendor Selection System  
**Dokumen:** SH-04 — Cost & Usage Guide  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-13  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Gambaran Komponen Biaya](#3-gambaran-komponen-biaya)
4. [Biaya OpenRouter API (LLM)](#4-biaya-openrouter-api-llm)
5. [Biaya Google Gemini Embedding API](#5-biaya-google-gemini-embedding-api)
6. [Biaya Tavily API](#6-biaya-tavily-api)
7. [Biaya Supabase](#7-biaya-supabase)
8. [Biaya Vercel](#8-biaya-vercel)
9. [Biaya Storage Backup](#9-biaya-storage-backup)
10. [Estimasi Biaya per Evaluasi](#10-estimasi-biaya-per-evaluasi)
11. [Estimasi Biaya Bulanan](#11-estimasi-biaya-bulanan)
12. [Monitoring Penggunaan](#12-monitoring-penggunaan)
13. [Strategi Optimasi Biaya](#13-strategi-optimasi-biaya)
14. [Proyeksi Skala](#14-proyeksi-skala)
15. [Aturan & Larangan](#15-aturan--larangan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **estimasi biaya operasional sistem**, bagaimana biaya terdistribusi per komponen, cara memonitor penggunaan agar tidak ada tagihan yang mengejutkan, dan strategi optimasi jika biaya melebihi target.

Dokumen ini menjawab pertanyaan: berapa biaya untuk menjalankan satu evaluasi, berapa estimasi tagihan bulanan untuk berbagai skenario penggunaan, dan komponen mana yang paling dominan dari sisi biaya.

Dokumen ini **tidak** mendefinisikan pricing ke klien — hanya biaya infrastruktur untuk menjalankan sistem.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| AI-01 | Agent Orchestration | Volume LLM call per evaluasi |
| AI-02 | Prompt Library | Estimasi ukuran prompt per agent |
| AI-04 | Integration Spec (AI Engineer) | Penggunaan Tavily, OpenRouter, dan Google Gemini API |
| DB-04 | Backup & Retention | Biaya storage backup |
| FE-01 | UI Architecture | Platform deployment Vercel |

---

## 3. Gambaran Komponen Biaya

Sistem memiliki lima komponen biaya utama dengan karakteristik yang berbeda:

```
┌─────────────────────────────────────────────────────────┐
│  Biaya Variabel (bergantung pada volume evaluasi)        │
│  ├── OpenRouter API    ← dominan, ~65–70% total biaya   │
│  ├── Google Gemini     ← sangat kecil, ~1% total biaya  │
│  └── Tavily API        ← kecil, ~5% total biaya         │
├─────────────────────────────────────────────────────────┤
│  Biaya Fixed (per bulan, tidak bergantung volume)        │
│  ├── Supabase Pro      ← ~15% total biaya               │
│  ├── Vercel            ← ~5% total biaya (free/pro)     │
│  └── Backup storage    ← ~5% total biaya                │
└─────────────────────────────────────────────────────────┘
```

**Implikasi penting:** Biaya embedding Google Gemini sangat kecil (< 1% total) dan bisa diabaikan dalam perencanaan anggaran kasar. OpenRouter API (LLM) tetap menjadi komponen biaya dominan.

---

## 4. Biaya OpenRouter API (LLM)

### 4.1 Model dan pricing (per Juni 2026)

Sistem menggunakan **DeepSeek-V4-Flash** via OpenRouter. Pricing OpenRouter berbasis kredit dan ditagih per token sesuai pricing model yang dipilih. **Verifikasi pricing terkini di dashboard OpenRouter sebelum kalkulasi final** — pricing dapat berubah dan DeepSeek-V4-Flash adalah model yang relatif baru.

Sebagai referensi perbandingan dengan model sebelumnya (Claude Sonnet ~$3/$15 per 1M token input/output), DeepSeek-V4-Flash umumnya ditawarkan dengan harga yang jauh lebih rendah — ini adalah salah satu alasan utama migrasi ke model ini (ADR-033).

### 4.2 Estimasi token per evaluasi

Volume token tidak berubah dari estimasi sebelumnya — yang berubah hanya harga per token. Estimasi per vendor (dengan asumsi vendor rata-rata):

**Per agent, per vendor (4 agent kuantitatif yang berjalan per vendor):**

| Agent | Input token (est.) | Output token (est.) |
|---|---|---|
| Data Collector | 2.000 | 500 |
| Financial Analyzer | 1.500 | 400 |
| Risk Assessor | 1.500 | 400 |
| Performance Scorer | 1.500 | 400 |

**Agent yang berjalan satu kali per evaluasi (bukan per vendor):**

| Agent | Input token (est.) | Output token (est.) |
|---|---|---|
| Negotiation Assistant | 6.000 | 1.000 |
| Qualitative Analyzer | 8.000 | 2.000 |
| Preference Matcher (mode opinionated) | 5.000 | 1.500 |
| Preference Matcher (mode netral) | 2.000 | 500 |
| Query expansion RAG (per pesan chat) | 200 | 100 |

**Per evaluasi (10 vendor, mode opinionated):**

| Komponen | Input token | Output token |
|---|---|---|
| 4 agent kuantitatif × 10 vendor | 65.000 | 17.000 |
| Negotiation Assistant (1x) | 6.000 | 1.000 |
| Qualitative Analyzer (1x) | 8.000 | 2.000 |
| Preference Matcher (1x) | 5.000 | 1.500 |
| Scoring reasoning (1x) | 3.000 | 800 |
| **Total per evaluasi** | **87.000** | **22.300** |

### 4.3 Kalkulasi biaya per evaluasi (OpenRouter)

Biaya aktual bergantung pada pricing DeepSeek-V4-Flash di OpenRouter yang perlu diverifikasi. Sebagai gambaran kasar dengan asumsi harga lebih rendah dari Claude Sonnet, total biaya LLM per evaluasi diperkirakan **signifikan lebih rendah dari estimasi sebelumnya (~$0.60)**. Perbarui tabel ini setelah pricing diverifikasi di dashboard OpenRouter.

**Catatan kurs:** Gunakan kurs IDR aktual saat kalkulasi final.

### 4.4 Biaya AI chat panel

Chat panel menggunakan model yang sama (DeepSeek-V4-Flash via OpenRouter) secara terpisah dari evaluasi. Estimasi per sesi chat user (30 menit aktif, ~10 pesan) akan lebih rendah dari estimasi berbasis Claude Haiku sebelumnya karena pricing DeepSeek umumnya lebih kompetitif. Perbarui estimasi ini setelah verifikasi pricing.

### 4.5 Faktor yang mempengaruhi biaya OpenRouter

Biaya bisa lebih tinggi dari estimasi jika:
- Dokumen spesifikasi yang dilampirkan panjang (menambah token input)
- Agent perlu retry karena output tidak sesuai format (menambah call)
- Deskripsi requirement atau catatan vendor sangat panjang

Biaya bisa lebih rendah dari estimasi jika:
- Jumlah vendor per evaluasi rata-rata kurang dari 10
- Data vendor minimal sehingga prompt lebih pendek

**Catatan khusus validasi JSON:** DeepSeek-V4-Flash perlu divalidasi konsistensi structured JSON output-nya selama testing awal. Jika tingkat retry lebih tinggi dari yang diperkirakan, estimasi biaya perlu disesuaikan ke atas.

---

## 5. Biaya Google Gemini Embedding API

### 5.1 Pricing Google Gemini Embedding

**Verifikasi pricing terkini di Google AI Studio atau Google Cloud Console sebelum kalkulasi final** — pricing dapat berubah. Model yang digunakan: `text-embedding-004` (768 dimensi).

Sebagai referensi, biaya embedding Google Gemini untuk volume yang relevan di sistem ini umumnya berada di rentang yang sangat kecil — sebanding atau lebih rendah dari OpenAI `text-embedding-3-small` yang sebelumnya digunakan ($0.02/1M token).

### 5.2 Estimasi penggunaan per evaluasi

**Saat indexing dokumen (satu kali per dokumen per vendor):**

| Skenario dokumen | Token per dokumen | Biaya per dokumen |
|---|---|---|
| Dokumen ringan (10 halaman) | ~5.000 token | sangat kecil |
| Dokumen sedang (20 halaman) | ~10.000 token | sangat kecil |
| Dokumen berat (50 halaman) | ~25.000 token | sangat kecil |

Untuk 10 vendor dengan dokumen sedang rata-rata: **< $0.005 per evaluasi**

**Saat retrieval (per pesan chat):**

Query expansion menghasilkan ~200 token per query. Biaya per pesan dapat diabaikan.
Untuk 20 pesan chat per evaluasi: **dapat diabaikan**

**Total biaya embedding per evaluasi: < $0.005** — kurang dari 1% total biaya.

### 5.3 Monitoring Google Gemini

Monitoring melalui Google AI Studio (aistudio.google.com) atau Google Cloud Console:
- Usage dashboard per model per hari
- Quota dan spending limit dapat dikonfigurasi
- Alert saat penggunaan mencapai threshold tertentu

### 5.4 Fallback jika Google Gemini tidak tersedia

Jika Google Gemini API tidak dapat dijangkau saat indexing: `indexing_rag_status` di tabel `dokumen_upload` diset ke `failed`. Evaluasi tetap berjalan; AI Chat Panel menggunakan data terstruktur tanpa RAG context dari dokumen.

Jika Google Gemini API tidak tersedia saat retrieval: sistem fallback ke BM25 full-text search saja — kualitas retrieval berkurang tetapi chat tetap bisa menjawab pertanyaan.

---

## 6. Biaya Tavily API

### 5.1 Pricing Tavily

| Tier | Harga | Request/bulan |
|---|---|---|
| Free | $0 | 1.000 |
| Starter | $19/bulan | 4.000 |
| Pro | $49/bulan | 16.000 |

### 5.2 Estimasi penggunaan per evaluasi

Data Collector Agent melakukan maksimum 4 query Tavily per vendor:
- 10 vendor × 4 query = **40 request per evaluasi**

### 5.3 Kapasitas free tier

Free tier 1.000 request/bulan cukup untuk:
- **25 evaluasi per bulan** dengan 10 vendor
- **50 evaluasi per bulan** dengan 5 vendor rata-rata

Untuk portofolio dan development: free tier sangat mencukupi.

Untuk production ringan (< 25 evaluasi/bulan dengan 10 vendor): masih dalam free tier.

Untuk production dengan volume lebih tinggi: upgrade ke Starter ($19/bulan) yang mendukung hingga 100 evaluasi/bulan.

### 5.4 Monitoring Tavily

Dashboard Tavily menampilkan penggunaan request secara real-time. Alert harus dikonfigurasi saat penggunaan mencapai 80% dari limit tier aktif.

---

## 7. Biaya Supabase

### 6.1 Tier yang digunakan

Sesuai keputusan di ADR-027: **Supabase Pro** adalah minimum untuk production.

| Tier | Harga | Kapasitas utama |
|---|---|---|
| Free | $0 | 500MB database, 1GB storage, tanpa PITR |
| Pro | $25/bulan | 8GB database, 100GB storage, PITR 7 hari |
| Team | $599/bulan | Unlimited, SOC 2, dedicated support |

### 6.2 Estimasi penggunaan database

Estimasi ukuran data per evaluasi (10 vendor, dengan hasil scoring):
- Row evaluasi + vendor + agent_progress + hasil: ~50KB
- Dokumen upload di Storage: rata-rata 2MB per evaluasi

Proyeksi pertumbuhan per bulan (50 evaluasi):
- Database: ~2.5MB data baru per bulan
- Storage: ~100MB file baru per bulan

Dengan Pro tier (8GB database, 100GB storage), kapasitas mencukupi untuk **ratusan hingga ribuan bulan operasional** sebelum perlu upgrade.

### 6.3 Biaya overage Supabase Pro

Jika melewati batas Pro tier:
- Database overage: $0.125/GB per bulan
- Storage overage: $0.021/GB per bulan
- Bandwidth overage: $0.09/GB

Untuk skala MVP, overage sangat tidak mungkin terjadi.

---

## 8. Biaya Vercel

### 7.1 Tier yang digunakan

| Tier | Harga | Kapasitas |
|---|---|---|
| Hobby | $0 | Personal projects, tidak untuk commercial |
| Pro | $20/bulan per member | Unlimited deployments, analytics |
| Enterprise | Custom | SLA, advanced security |

**Untuk portofolio:** Hobby tier cukup.

**Untuk production komersial:** Pro tier diperlukan ($20/bulan untuk satu developer, lebih untuk tim).

### 7.2 Limit yang perlu diperhatikan di Hobby tier

- Bandwidth: 100GB/bulan (sangat cukup untuk MVP)
- Serverless function execution: 100GB-hours/bulan
- Build time: 6.000 menit/bulan

Untuk aplikasi dengan traffic rendah-menengah, Hobby tier mencukupi bahkan untuk production awal.

---

## 9. Biaya Storage Backup

### 8.1 Backup off-platform

Backup database yang disimpan di luar Supabase (lihat DB-04 section 5.3) menggunakan cloud storage eksternal.

Estimasi ukuran backup per bulan (50 evaluasi/bulan, setelah 6 bulan operasional):
- Database dump: ~50MB per backup
- Total backup harian (30 backup): ~1.5GB
- Total backup mingguan (4 backup): ~200MB
- Total backup bulanan (1 backup): ~50MB

**Estimasi biaya storage (S3 Standard):**
- Storage aktif (harian + mingguan): ~1.7GB × $0.023/GB = **~$0.04/bulan**
- Cold storage bulanan (S3 Glacier): akumulasi 24 bulan × 50MB = 1.2GB × $0.004/GB = **~$0.005/bulan**

Biaya backup sangat kecil dan hampir diabaikan pada skala MVP.

---

## 10. Estimasi Biaya per Evaluasi

Merangkum semua komponen variabel per evaluasi:

| Komponen | Biaya per evaluasi (10 vendor) | Catatan |
|---|---|---|
| OpenRouter API (LLM) | TBD — verifikasi pricing DeepSeek-V4-Flash | Dominan, lebih rendah dari estimasi sebelumnya |
| Google Gemini Embedding | < $0.005 (Rp < 80) | Sangat kecil, < 1% |
| Tavily API | $0 dalam free tier | Gratis hingga 25 eval/bulan |
| Supabase (variabel) | ~$0.001 | Hampir diabaikan |
| **Total per evaluasi** | **TBD — perbarui setelah verifikasi pricing** | Estimasi 10 vendor |

**Catatan:** Total biaya per evaluasi diperkirakan lebih rendah dari estimasi sebelumnya (~$0.60 berbasis Claude Sonnet) karena DeepSeek-V4-Flash memiliki pricing yang lebih kompetitif. Perbarui tabel ini setelah pricing diverifikasi di dashboard OpenRouter.

---

## 11. Estimasi Biaya Bulanan

### 11.1 Skenario: Portofolio / Development

Target: < 25 evaluasi per bulan, tidak ada pengguna aktif di production.

| Komponen | Biaya |
|---|---|
| OpenRouter API (LLM) | < $15 (tergantung pricing DeepSeek, perkiraan lebih rendah) |
| Google Gemini Embedding | < $0.10 |
| Tavily API | $0 (free tier) |
| Supabase | $0 (free tier untuk dev) |
| Vercel | $0 (Hobby tier) |
| Backup | $0 (belum diperlukan) |
| **Total** | **< $15/bulan** |

### 11.2 Skenario: Production Ringan

Target: 50–100 evaluasi per bulan, tim kecil (1–5 user aktif).

| Komponen | Biaya |
|---|---|
| OpenRouter API (LLM) | TBD — diperkirakan lebih rendah dari $30–60 (Claude Sonnet) |
| Google Gemini Embedding | < $0.50 |
| Tavily API | $19 (Starter tier) |
| Supabase Pro | $25 |
| Vercel Pro | $20 |
| Backup storage | ~$1 |
| **Total** | **~$65–100/bulan (estimasi — perbarui setelah verifikasi pricing)** |

### 11.3 Skenario: Production Menengah

Target: 200–500 evaluasi per bulan, tim menengah (5–20 user aktif).

| Komponen | Biaya |
|---|---|
| OpenRouter API (LLM) | TBD — diperkirakan lebih rendah dari $120–300 (Claude Sonnet) |
| Google Gemini Embedding | < $1.50 |
| Tavily API | $49 (Pro tier) |
| Supabase Pro | $25 |
| Vercel Pro | $40 (2 member) |
| Backup storage | ~$2 |
| FastAPI hosting | $20–50 (Railway atau Fly.io) |
| **Total** | **TBD — diperkirakan lebih rendah dari estimasi sebelumnya** |

**Catatan:** Biaya embedding Google Gemini tidak signifikan di semua skenario. Estimasi biaya total akan diperbarui setelah pricing DeepSeek-V4-Flash via OpenRouter diverifikasi dari data aktual testing.

---

## 12. Monitoring Penggunaan

### 12.1 OpenRouter API

Monitoring dilakukan melalui OpenRouter Dashboard (openrouter.ai/dashboard):
- Usage dashboard menampilkan token per hari, per model
- Cost breakdown per bulan dalam kredit OpenRouter
- Alert dapat dikonfigurasi saat pengeluaran mencapai threshold tertentu

**Alert yang harus dikonfigurasi:**
- Saat pengeluaran bulanan mencapai 80% dari budget yang ditetapkan
- Saat penggunaan harian jauh di atas rata-rata (kemungkinan ada evaluasi yang loop atau error)

### 12.2 Google Gemini Embedding API

Monitoring melalui Google AI Studio (aistudio.google.com) atau Google Cloud Console:
- Usage dashboard per model
- Quota dan spending limit bisa dikonfigurasi untuk mencegah tagihan tidak terduga
- Meskipun biaya sangat kecil, tetap perlu dikonfigurasi spending limit sebagai safety net

### 12.3 Tavily API

Monitoring melalui Tavily dashboard:
- Request count real-time
- Alert saat penggunaan mencapai 80% dari limit tier aktif

### 12.4 Supabase

Monitoring melalui Supabase dashboard:
- Database size
- Storage usage
- API request count
- Realtime connection count

### 12.5 Logging biaya per evaluasi di aplikasi

FastAPI mencatat usage token untuk setiap evaluasi yang diproses dan menyimpannya ke database. Ini memungkinkan:
- Analisa biaya rata-rata per evaluasi secara aktual (bukan estimasi)
- Identifikasi evaluasi yang unusually expensive (mungkin ada bug atau data yang sangat besar)
- Tren biaya seiring pertumbuhan penggunaan

Field yang dicatat per evaluasi:
- Total input token per agent
- Total output token per agent
- Total biaya Tavily request
- Timestamp dan evaluasi ID

### 12.6 Dashboard biaya internal

Sebaiknya ada halaman admin sederhana (tidak perlu masuk ke UI utama) yang menampilkan:
- Biaya total bulan berjalan
- Biaya rata-rata per evaluasi (30 hari terakhir)
- Trend penggunaan token per minggu
- Evaluasi yang paling mahal (untuk investigasi)

---

## 13. Strategi Optimasi Biaya

### 12.1 Optimasi prompt (dampak besar)

Mengurangi panjang prompt adalah cara paling efektif untuk mengurangi biaya OpenRouter — biaya input token lebih kecil dari output, tetapi volume input token jauh lebih besar.

**Cara mengoptimasi:**
- Hapus instruksi redundan di system prompt yang tidak mempengaruhi kualitas output
- Truncate catatan vendor yang terlalu panjang sebelum dikirim ke LLM
- Batasi panjang deskripsi requirement yang masuk ke prompt (misalnya maks 500 kata)

Estimasi penghematan dari optimasi prompt yang baik: 20–30% dari biaya OpenRouter.

### 13.2 Gunakan model yang lebih ringan untuk komponen toleran terhadap kualitas lebih rendah

OpenRouter memudahkan pergantian model per endpoint tanpa mengubah arsitektur. Komponen yang bisa menggunakan model yang lebih ringan (jika ditemukan model lebih murah dengan kualitas memadai):
- Query expansion RAG (parafrase sederhana, bukan reasoning kompleks)
- Generasi pesan progress singkat dari agent

Komponen yang harus menggunakan model utama (DeepSeek-V4-Flash):
- Lima agent analisa utama (kualitas reasoning mempengaruhi kualitas rekomendasi)
- Qualitative Analyzer (analisis nuanced tentang unique offerings)
- Preference Matcher dalam mode opinionated (pencocokan preferensi kompleks)
- Generasi reasoning naratif (kualitas teks yang ditampilkan ke user)
- Negotiation Assistant (reasoning kompleks multi-dimensi)

### 12.3 Caching hasil Tavily

Jika vendor yang sama muncul di beberapa evaluasi berbeda dalam periode singkat (misalnya minggu yang sama), hasil Tavily search bisa di-cache. Ini menghindari query yang sama diulang dan menghemat penggunaan Tavily.

Cache Tavily disimpan di Redis atau Supabase dengan TTL 7 hari — informasi vendor umumnya tidak berubah dalam seminggu.

Estimasi penghematan: 20–40% dari penggunaan Tavily request jika banyak vendor yang sama dievaluasi berulang.

### 12.4 Batasi konteks chat panel

Chat panel mengirim riwayat percakapan sebelumnya sebagai konteks ke setiap request. Riwayat yang panjang menambah input token secara signifikan.

Batasi riwayat chat yang dikirim ke maksimum 10 pesan terakhir (atau ~2.000 token dari riwayat) — cukup untuk menjaga konteks percakapan tanpa biaya yang membengkak untuk sesi chat yang panjang.

---

## 14. Proyeksi Skala

### 13.1 Break-even analysis

Jika sistem dijual sebagai SaaS dengan harga per evaluasi atau subscription:

Biaya operasional per evaluasi (production menengah): ~$0.75 (termasuk alokasi biaya fixed)

Harga yang masuk akal untuk monetisasi: $5–15 per evaluasi atau $200–500/bulan subscription.

Margin yang sehat dimulai dari volume di mana biaya fixed (Supabase, Vercel) sudah ter-cover oleh biaya variabel per evaluasi.

### 13.2 Titik upgrade komponen

| Komponen | Trigger upgrade |
|---|---|
| Tavily Free → Starter | > 25 evaluasi/bulan rata-rata |
| Tavily Starter → Pro | > 100 evaluasi/bulan rata-rata |
| Vercel Hobby → Pro | Saat digunakan untuk klien komersial |
| Supabase Free → Pro | Sebelum deployment production pertama |
| Supabase Pro → Team | Saat butuh SLA atau audit compliance |

### 13.3 Komponen yang perlu ditambahkan saat skala besar

Pada volume > 500 evaluasi/bulan, perlu mempertimbangkan:
- **Redis** untuk caching Tavily results (~$15–30/bulan di Redis Cloud)
- **FastAPI di dedicated server** bukan shared hosting (lebih predictable performa)
- **Negosiasi volume discount** dengan OpenRouter jika tersedia untuk penggunaan tinggi

---

## 15. Aturan & Larangan

**Dilarang deploy ke production tanpa mengkonfigurasi spending alert** di OpenRouter Dashboard dan Google AI Console. Tanpa alert, lonjakan biaya tidak terduga bisa terjadi tanpa diketahui.

**Dilarang menggunakan model yang lebih mahal** untuk komponen yang bisa menggunakan model lebih ringan via OpenRouter tanpa justifikasi yang terdokumentasi.

**Dilarang membiarkan prompt yang tidak dioptimasi** di production jika ukurannya melebihi 3.000 token system prompt per agent. Prompt yang panjang tanpa justifikasi adalah pemborosan biaya.

**Dilarang mengabaikan alert penggunaan** yang dikonfigurasi. Alert harus direspons dalam 24 jam — investigasi apakah ada anomali penggunaan atau memang pertumbuhan yang wajar.

**Dilarang logging token usage di luar sistem monitoring yang terdefinisi** untuk menghindari data yang tidak konsisten antara catatan internal dan tagihan aktual.

---

*Dokumen ini adalah living document — estimasi biaya akan diperbarui berdasarkan data aktual dari production dan perubahan pricing layanan eksternal.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal — empat komponen biaya | — |
| 2.0.0 | 2026-06-11 | Tambah section 5 biaya OpenAI Embedding API; perbarui estimasi token Anthropic untuk 7 agent; perbarui tabel biaya per evaluasi dan bulanan; tambah monitoring OpenAI; perbarui daftar komponen Haiku vs Sonnet | — |
| 3.0.0 | 2026-06-13 | Ganti section 4 dari Biaya Anthropic API ke Biaya OpenRouter API (DeepSeek-V4-Flash); ganti section 5 dari Biaya OpenAI Embedding ke Biaya Google Gemini Embedding (text-embedding-004); perbarui diagram komponen biaya, tabel estimasi per evaluasi, tabel bulanan semua skenario, monitoring, strategi optimasi, proyeksi skala, dan aturan; estimasi biaya LLM ditandai TBD menunggu verifikasi pricing DeepSeek-V4-Flash | — |
| 4.0.0 | 2026-06-13 | Adopsi ADR-035 (namespace AI): perbarui tabel referensi (BE-03→AI-01, BE-04→AI-02, BE-07→AI-04; deskripsi BE-07 diperbarui dari Anthropic ke OpenRouter+Google Gemini) | — |
