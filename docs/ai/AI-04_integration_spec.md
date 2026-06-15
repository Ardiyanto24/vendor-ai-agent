# AI-04 — Integration Spec (AI Engineer)

**Project:** AI Vendor Selection System  
**Dokumen:** AI-04 — Integration Spec (AI Engineer)  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-13  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —  
**Dipecah dari:** BE-07 v3.0.0

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Gambaran Integrasi AI Service](#3-gambaran-integrasi-ai-service)
4. [Pendekatan MVP: Simulasi dengan Real Search](#4-pendekatan-mvp-simulasi-dengan-real-search)
5. [Integrasi Tavily API](#5-integrasi-tavily-api)
6. [Integrasi OpenRouter API (LLM)](#6-integrasi-openrouter-api-llm)
7. [Integrasi Google Gemini Embedding API](#7-integrasi-google-gemini-embedding-api)
8. [Pola Integrasi Umum](#8-pola-integrasi-umum)
9. [Mock Layer untuk Data Simulasi](#9-mock-layer-untuk-data-simulasi)
10. [Roadmap Integrasi Pasca-MVP](#10-roadmap-integrasi-pasca-mvp)
11. [Aturan & Larangan](#11-aturan--larangan)
12. [Catatan untuk Dokumen Lanjutan](#12-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **semua integrasi dengan layanan eksternal yang dikerjakan oleh AI Engineer** di repo `vendor-ai-agent` — apa yang diintegrasikan, mengapa, bagaimana data mengalir, dan bagaimana ketergantungan pada pihak ketiga dikelola dengan aman.

Tiga integrasi yang tercakup di sini adalah: **Tavily API** (web search untuk Data Collector Agent), **OpenRouter API** (LLM untuk semua agent dan chat panel), dan **Google Gemini Embedding API** (embedding untuk RAG indexing dan retrieval).

Integrasi Supabase Storage (upload file dokumen) yang dikerjakan oleh track Fullstack didefinisikan di **BE-04**.

Dokumen ini **tidak** mendefinisikan implementasi kode — itu diserahkan ke engineer.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| AI-01 | Agent Orchestration | Data Collector Agent yang menggunakan Tavily; pipeline indexing RAG |
| AI-05 | RAG Specification | Detail pipeline RAG yang menggunakan Google Gemini Embedding API |
| BE-03 | Auth & Security | Pengelolaan API key dan secret eksternal |
| BE-04 | Integration Spec (Fullstack) | Integrasi Supabase Storage yang dikerjakan track Fullstack |
| DB-01 | Data Model & ERD | Tabel `dokumen_upload` dan `dokumen_chunk` |
| SH-04 | Cost & Usage Guide | Estimasi biaya penggunaan API eksternal termasuk embedding |

---

## 3. Gambaran Integrasi AI Service

Repo `vendor-ai-agent` bergantung pada tiga layanan eksternal berbayar:

```
vendor-ai-agent (FastAPI)
        │
        ├── OpenRouter API ─────── LLM untuk semua agent dan chat (DeepSeek-V4-Flash)
        │                          Semua AI call: evaluasi, ekstraksi, reasoning, chat SSE
        │
        ├── Google Gemini API ───── Embedding teks untuk RAG indexing & retrieval
        │                          Pipeline indexing saat upload + retrieval saat chat
        │
        └── Tavily API ─────────── Web search untuk Data Collector Agent
                                   Mencari informasi publik tentang vendor kandidat
```

**Mengapa dependensi dibatasi tiga layanan:** Setiap integrasi eksternal menambah kompleksitas — potensi downtime, biaya, perubahan API yang tidak terduga, dan kebutuhan pengelolaan credential tambahan. Tiga layanan ini adalah minimum yang diperlukan untuk membuktikan nilai inti sistem AI.

**Dua API key yang harus dikelola AI Engineer:**
- `OPENROUTER_API_KEY` — untuk semua LLM call
- `GOOGLE_API_KEY` — untuk semua embedding call
- `TAVILY_API_KEY` — untuk web search

---

## 4. Pendekatan MVP: Simulasi dengan Real Search

### 4.1 Yang berjalan sungguhan

- Tavily API untuk web search di Data Collector Agent
- OpenRouter API untuk semua LLM call (model DeepSeek-V4-Flash)
- Google Gemini Embedding API untuk indexing dokumen penawaran dan RAG retrieval

### 4.2 Yang disimulasikan (mock)

- Data historis vendor dari ERP/SAP internal perusahaan → digantikan input manual user
- Verifikasi legalitas resmi dari database pemerintah → disimulasikan dengan informasi yang ditemukan via web search

### 4.3 Mock layer yang transparan

Komponen yang disimulasikan menggunakan mock layer yang terdokumentasi — bukan data yang di-hardcode secara tersembunyi. Mock layer dapat diganti dengan integrasi nyata tanpa mengubah interface yang digunakan oleh komponen lain.

---

## 5. Integrasi Tavily API

### 5.1 Apa dan mengapa

Tavily adalah search API yang dirancang khusus untuk AI agent — hasil pencariannya sudah terstruktur (judul, URL, konten ringkas) tanpa memerlukan parsing HTML tambahan. Ini berbeda dari Selenium-based scraping yang rapuh dan Google Search API yang tidak dirancang untuk konsumsi LLM.

**Mengapa Tavily dipilih untuk MVP:** Free tier 1.000 request/bulan cukup untuk development dan demonstrasi portofolio. Hasilnya sudah dalam format yang siap dikonsumsi LLM, mengurangi kompleksitas implementasi di Data Collector Agent.

### 5.2 Digunakan oleh

Data Collector Agent (AI-01) — untuk mencari informasi publik tentang setiap vendor kandidat.

### 5.3 Apa yang dicari

Untuk setiap vendor, Data Collector Agent melakukan pencarian dengan query yang mencakup:
- Profil umum perusahaan (nama + "profil perusahaan" atau "company profile")
- Sertifikasi yang dimiliki (nama + "ISO" atau "sertifikasi")
- Berita terkini dalam 6 bulan terakhir (nama + "berita" atau "news")
- Indikasi masalah jika ada (nama + "sengketa" atau "masalah" atau "kasus")

Jumlah query per vendor: maksimum 4 query. Dengan 10 vendor maksimum per evaluasi, satu evaluasi mengonsumsi maksimum 40 Tavily request.

### 5.4 Data yang dikembalikan

Tavily mengembalikan per query: judul halaman, URL sumber, ringkasan konten (snippet), dan skor relevansi. Data ini diteruskan ke LLM dalam Data Collector Agent sebagai konteks untuk dianalisa dan disusun menjadi output terstruktur (format JSON sesuai AI-02).

### 5.5 Pengelolaan API key

Tavily API key disimpan sebagai environment variable di FastAPI service — tidak pernah di frontend atau di repository. Nama variabel: `TAVILY_API_KEY`.

### 5.6 Penanganan rate limit dan error

Tavily free tier tidak memiliki rate limit per detik yang ketat, tetapi tetap perlu penanganan error untuk:
- Request timeout (> 10 detik): retry sekali, jika tetap gagal lanjutkan tanpa data dari sumber tersebut
- HTTP 429 (rate limit): tunggu 60 detik sebelum retry
- HTTP 5xx (server error Tavily): catat error, lanjutkan tanpa data pencarian

Kegagalan Tavily tidak menghentikan proses evaluasi — Data Collector Agent melaporkan bahwa data dari web search tidak tersedia untuk vendor tersebut dan scoring engine menanganinya sesuai AI-03 section 7.

### 5.7 Batasan yang perlu disadari

Tavily free tier membatasi 1.000 request per bulan. Jika sistem digunakan lebih intensif (lebih dari 25 evaluasi dengan 10 vendor per bulan), free tier akan habis. Solusinya adalah upgrade ke paid tier atau mengurangi jumlah query per vendor. Monitoring penggunaan Tavily API harus dikonfigurasi (lihat SH-04).

---

## 6. Integrasi OpenRouter API (LLM)

### 6.1 Apa dan mengapa

OpenRouter adalah aggregator LLM API yang menyediakan akses ke ratusan model dari berbagai provider melalui satu endpoint yang kompatibel dengan OpenAI API format. Sistem menggunakan OpenRouter untuk mengakses **DeepSeek-V4-Flash** sebagai LLM utama — model yang menawarkan kemampuan instruction-following dan structured JSON output yang kompetitif dengan biaya yang lebih efisien dibanding model proprietary tier tinggi.

Semua LLM call dari tujuh agent, ekstraksi dokumen, scoring reasoning, dan AI chat panel menggunakan endpoint OpenRouter yang sama.

### 6.2 Model yang digunakan

**DeepSeek-V4-Flash** digunakan untuk semua agent evaluasi dan reasoning scoring. Model ini dipilih karena kemampuan reasoning dan instruction-following yang baik untuk pipeline agent yang menghasilkan structured JSON output.

Untuk AI chat panel, model yang sama digunakan secara default. Jika hasil testing menunjukkan bahwa model yang lebih ringan sudah cukup untuk kebutuhan chat, AI Engineer dapat mengkonfigurasi model berbeda untuk endpoint chat tanpa mengubah arsitektur — cukup mengubah model string di konfigurasi.

### 6.3 Digunakan oleh

- FastAPI: semua agent (Data Collector, Financial Analyzer, Risk Assessor, Performance Scorer, Negotiation Assistant, Qualitative Analyzer, Preference Matcher)
- FastAPI: ekstraksi dokumen penawaran
- FastAPI: generasi reasoning naratif (Scoring Engine)
- FastAPI: AI chat panel (SSE streaming)

### 6.4 Pengelolaan API key

OpenRouter API key disimpan sebagai environment variable di FastAPI service: `OPENROUTER_API_KEY`. Tidak pernah diekspos ke frontend atau Next.js.

Integrasi menggunakan **OpenAI SDK** dengan override `base_url` ke endpoint OpenRouter:

```
base_url = "https://openrouter.ai/api/v1"
api_key  = OPENROUTER_API_KEY
model    = "deepseek/deepseek-v4-flash"  (verifikasi model string di dashboard OpenRouter)
```

Tidak diperlukan SDK tambahan — OpenAI SDK yang sudah digunakan untuk embedding dapat dipakai ulang dengan konfigurasi yang berbeda.

### 6.5 Penanganan rate limit

OpenRouter menerapkan rate limit berbasis credit dan request per menit yang bergantung pada tier akun. Untuk MVP:

- Jika rate limit tercapai: FastAPI menerapkan exponential backoff — tunggu sebelum retry
- Jika tetap gagal setelah 3 retry: agent dinyatakan gagal dan Orchestrator menerapkan fallback sesuai AI-01 section 7

Monitoring penggunaan kredit OpenRouter penting untuk memastikan biaya terkontrol (lihat SH-04).

### 6.6 Streaming response

Untuk AI chat panel, OpenRouter dipanggil dengan mode streaming — token dikirim ke client saat dihasilkan, bukan menunggu seluruh response selesai. OpenRouter mendukung streaming menggunakan format yang sama dengan OpenAI API (`stream=True`). Ini sudah didefinisikan di BE-02 section 10 dan FE-05 section 10.

Untuk agent evaluasi, streaming tidak digunakan — response ditunggu sampai selesai karena agent perlu seluruh output JSON sebelum bisa memproses hasilnya.

---

## 7. Integrasi Google Gemini Embedding API

### 7.1 Apa dan mengapa

Google Gemini Embedding API digunakan untuk mengubah teks (chunk dokumen penawaran dan query pencarian user) menjadi vektor numerik berdimensi 768 — representasi matematis yang menangkap makna semantik teks. Vektor inilah yang memungkinkan sistem menemukan potongan dokumen yang paling relevan dengan pertanyaan user, bahkan jika pertanyaan menggunakan kata-kata yang berbeda dari dokumen aslinya.

**Model yang digunakan:** `text-embedding-004` — menghasilkan vektor **768 dimensi**. Model stabil dari Google yang terbukti baik untuk teks berbahasa Indonesia dan Inggris.

**Mengapa Google Gemini:** Setelah LLM dipindah ke OpenRouter (ADR-033), diputuskan untuk mengkonsolidasi provider. Google `text-embedding-004` menawarkan dimensi 768 yang lebih efisien dari OpenAI `text-embedding-3-small` (1.536) untuk storage vector dan kecepatan similarity search, dengan kualitas retrieval yang setara untuk dokumen pengadaan. Detail keputusan ini ada di ADR-034 (SH-01).

### 7.2 Digunakan oleh

Dua pipeline yang berbeda menggunakan API ini:

**Pipeline indexing** (AI-01 section 9, AI-05 section 6) — dipanggil saat user mengupload dokumen penawaran. Setiap child chunk dari dokumen di-embed secara batch. Ini adalah operasi satu kali per dokumen.

**Pipeline retrieval** (AI-05 section 8) — dipanggil setiap kali user mengirim pesan di AI Chat Panel. Query user (setelah query expansion) di-embed untuk kemudian dibandingkan dengan chunk yang tersimpan di pgvector. Ini adalah operasi ringan per pesan.

### 7.3 Pengelolaan API key

Google API key disimpan sebagai environment variable di FastAPI service — tidak pernah di frontend atau di repository. Nama variabel: `GOOGLE_API_KEY`.

Ini adalah API key yang berbeda dari `OPENROUTER_API_KEY` — keduanya harus dikelola secara terpisah dan tidak saling bergantung. Jika salah satu bermasalah (expired, rate limit), yang lain tetap berfungsi.

### 7.4 Strategi batching

Untuk efisiensi biaya dan menghindari rate limit, embedding tidak dilakukan satu per satu:

**Saat indexing:** Semua child chunk dari satu dokumen di-batch dalam satu atau beberapa API call. Batching mengikuti batas yang didokumentasikan di Google AI API — verifikasi batas terkini saat implementasi.

**Saat retrieval:** Hanya satu query per pesan user — tidak perlu batching.

### 7.5 Penanganan rate limit dan error

Google Gemini Embedding API memiliki rate limit berbasis request per menit (RPM) dan token per menit (TPM) yang bergantung pada tier akun. Untuk satu dokumen 50 halaman, proses embedding selesai jauh di bawah rate limit standar.

Penanganan error:
- HTTP 429 (rate limit): eksponensial backoff, retry setelah jeda
- HTTP 5xx: retry maksimum 3 kali, jika tetap gagal tandai `indexing_rag_status = failed` di tabel `dokumen_upload`
- Kegagalan embedding tidak menghentikan ekstraksi field terstruktur — keduanya berjalan di cabang pipeline yang independen (AI-01 section 9.2)

### 7.6 Timeout

| Operasi | Timeout |
|---|---|
| Embedding batch saat indexing | 30 detik |
| Embedding query saat retrieval | 5 detik |

Jika embedding query gagal (timeout atau error), pipeline retrieval menggunakan hanya full-text search (BM25) sebagai fallback — kualitas retrieval berkurang tetapi chat tetap bisa menjawab pertanyaan.

### 7.7 Estimasi biaya

Biaya embedding sangat kecil dibanding biaya LLM. Verifikasi harga terkini di halaman pricing Google AI sebelum kalkulasi final — pricing dapat berubah. Estimasi kasar:

| Skenario | Token | Biaya (estimasi) |
|---|---|---|
| Indexing dokumen 20 halaman | ~10.000 token | sangat kecil |
| Indexing dokumen 50 halaman | ~25.000 token | sangat kecil |
| Retrieval per pesan chat | ~200 token | dapat diabaikan |
| **Total per evaluasi (indexing + 20 chat)** | **~150.000 token** | **< $0.005** |

Biaya embedding kurang dari 1% dari total biaya LLM per evaluasi. Detail integrasi ke estimasi biaya total ada di SH-04.

---

## 8. Pola Integrasi Umum

Pola berikut diterapkan secara konsisten ke semua integrasi eksternal di `vendor-ai-agent`.

### 8.1 Circuit breaker

Jika suatu layanan eksternal gagal berulang kali dalam periode singkat, sistem berhenti mencoba dan langsung mengembalikan error — tidak terus mencoba dan memblokir resource. Circuit breaker terbuka (berhenti mencoba) setelah 5 kegagalan berturut-turut, dan dicoba kembali setelah 60 detik.

**Mengapa:** Tanpa circuit breaker, kegagalan satu layanan eksternal bisa menyebabkan seluruh proses evaluasi tersangkut menunggu timeout satu per satu.

### 8.2 Timeout yang eksplisit

Setiap request ke layanan eksternal memiliki timeout yang terdefinisi:

| Layanan | Timeout |
|---|---|
| Tavily API (per query) | 10 detik |
| OpenRouter API (non-streaming) | 60 detik |
| OpenRouter API (streaming, first token) | 30 detik |
| Google Gemini Embedding API (batch indexing) | 30 detik |
| Google Gemini Embedding API (retrieval query) | 5 detik |

### 8.3 Logging request

Setiap request ke layanan eksternal dicatat dalam log dengan informasi:
- Layanan yang dipanggil
- Durasi request
- HTTP status response
- Apakah ada retry yang dilakukan
- ID evaluasi yang terkait (untuk tracing)

Konten request dan response tidak dicatat secara penuh — hanya metadata. Ini melindungi data vendor dari tersimpan di log dan menghindari log yang terlalu besar.

---

## 9. Mock Layer untuk Data Simulasi

### 9.1 Apa yang di-mock

Untuk MVP, dua sumber data eksternal yang di-mock:

**Data historis vendor internal (ERP/SAP):** Digantikan sepenuhnya oleh input manual user di form pembuatan evaluasi. Tidak ada koneksi ke sistem internal perusahaan.

**Verifikasi legalitas resmi:** Risk Assessor Agent menggunakan informasi yang ditemukan via Tavily web search (misalnya mencari nama perusahaan di sumber berita atau direktori bisnis) — bukan query ke database resmi pemerintah seperti OSS atau AHU online.

### 9.2 Interface mock yang konsisten

Mock layer mengimplementasikan interface yang sama dengan integrasi nyata yang akan menggantikannya. Artinya, ketika integrasi ERP nyata diimplementasikan di masa mendatang, hanya mock layer yang perlu diganti — komponen yang mengonsumsinya (agent, scoring engine) tidak perlu diubah.

**Prinsip:** Mock bukan workaround sementara yang dihapus nanti — ia adalah placeholder dengan interface yang sudah terdefinisi untuk integrasi masa depan.

### 9.3 Identifikasi mock di kode

Setiap fungsi yang merupakan mock harus:
- Diberi nama yang jelas mencerminkan bahwa ia adalah mock (misalnya `get_vendor_history_mock`)
- Disertai komentar yang menyebutkan integrasi nyata apa yang akan menggantikannya
- Dicatat di dokumen ini sebagai kandidat replacement di roadmap pasca-MVP

### 9.4 Data mock yang digunakan

Data mock tidak di-hardcode sebagai data vendor yang spesifik. Data mock mengembalikan nilai default yang konsisten (misalnya: tidak ada riwayat transaksi tersedia, status legalitas tidak dapat diverifikasi dari sistem internal) — sehingga scoring engine menanganinya sebagai data tidak lengkap sesuai AI-03 section 7.

---

## 10. Roadmap Integrasi Pasca-MVP

### 10.1 Integrasi ERP/SAP (Prioritas Tinggi)

**Tujuan:** Mengambil data historis transaksi vendor — riwayat pembelian, rating evaluasi sebelumnya, complaint record — langsung dari sistem ERP perusahaan.

**Mengapa prioritas tinggi:** Data historis internal adalah sinyal paling reliabel tentang performa vendor nyata di masa lalu. Ini adalah keunggulan kompetitif signifikan dibanding evaluasi hanya berdasarkan informasi publik.

**Kandidat integrasi:** SAP Business One API, Oracle ERP Cloud API, atau sistem ERP custom via REST API yang disediakan perusahaan klien.

**Titik integrasi:** Data Collector Agent — sebagai sumber data tambahan yang melengkapi web search.

**Dampak pada arsitektur MVP:** Interface mock di section 9.2 sudah mempersiapkan titik integrasi ini. Tidak ada perubahan pada scoring engine atau komponen lain.

### 10.2 Verifikasi Legalitas Resmi (Prioritas Menengah)

**Tujuan:** Memverifikasi status legalitas vendor secara resmi melalui database pemerintah Indonesia.

**Kandidat integrasi:**
- OSS (Online Single Submission) API — verifikasi NIB dan izin usaha
- AHU Online API — data perusahaan dari Kemenkumham
- SLIK OJK API — informasi kredit perusahaan (memerlukan izin khusus)

**Titik integrasi:** Risk Assessor Agent — menggantikan/melengkapi pencarian web untuk aspek legalitas.

### 10.3 Integrasi Marketplace Vendor (Jangka Panjang)

**Tujuan:** Mengambil data vendor langsung dari marketplace B2B seperti Tokopedia for Business, Ralali, atau platform pengadaan pemerintah (e-Katalog LKPP).

**Titik integrasi:** Data Collector Agent — sebagai sumber data tambahan.

---

## 11. Aturan & Larangan

**Dilarang menyimpan API key eksternal di kode atau repository.** Semua API key (Tavily, OpenRouter, Google) disimpan sebagai environment variable sesuai BE-03 section 10.

**Dilarang memanggil layanan eksternal dari frontend.** Semua request ke Tavily, OpenRouter, dan Google Gemini hanya dari FastAPI — tidak pernah dari browser secara langsung.

**Dilarang mencampur `OPENROUTER_API_KEY` dan `GOOGLE_API_KEY`.** Keduanya adalah credential yang berbeda untuk layanan yang berbeda. Pengelolaan, rotasi, dan monitoring keduanya dilakukan secara terpisah.

**Dilarang menghilangkan mock layer tanpa menggantinya dengan integrasi nyata.** Menghapus mock tanpa pengganti akan menyebabkan komponen yang bergantung padanya error.

**Dilarang menyimpan konten response API eksternal ke log secara penuh.** Konten vendor yang dikembalikan Tavily, output LLM dari OpenRouter, maupun vektor dari Google Gemini tidak boleh masuk ke log — hanya metadata request (durasi, status, ID evaluasi).

**Dilarang menggunakan Tavily untuk mencari informasi personal user** — hanya untuk informasi perusahaan vendor yang relevan dengan evaluasi pengadaan.

**Dilarang bypass circuit breaker** dengan cara apapun. Jika circuit breaker terbuka, sistem harus menunggu recovery period selesai — tidak ada override manual selama evaluasi berlangsung.

---

## 12. Catatan untuk Dokumen Lanjutan

### Untuk SH-04 (Cost & Usage Guide)

Tiga layanan eksternal berbayar perlu dimonitoring penggunaannya:
- Tavily API: 1.000 request gratis per bulan
- OpenRouter API: biaya per input dan output token (model DeepSeek-V4-Flash)
- Google Gemini Embedding API: biaya per token (sangat kecil, < $0.005 per evaluasi)

SH-04 perlu memperbarui estimasi biaya per evaluasi untuk mencerminkan pricing DeepSeek via OpenRouter dan Google Gemini embedding.

### Untuk SH-02 (Deployment Runbook)

Runbook perlu mencakup prosedur setup environment variable untuk `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, dan `TAVILY_API_KEY` di environment staging dan production.

### Untuk SH-03 (Testing Strategy)

Testing integrasi eksternal perlu mencakup:
- Test pipeline embedding dengan Google Gemini API key nyata di staging
- Test fallback saat Google Gemini API tidak tersedia (retrieval fallback ke BM25 saja)
- Test bahwa kegagalan embedding tidak memblokir ekstraksi field terstruktur
- Test structured JSON output dari DeepSeek-V4-Flash via OpenRouter untuk setiap agent — validasi konsistensi format lebih ketat dibanding sebelumnya

### Untuk AI-01 (Agent Orchestration)

Pipeline ekstraksi dokumen sekarang bercabang dua (AI-01 section 9.2). Pastikan timeout agent secara keseluruhan mencakup waktu embedding yang bisa mencapai 30 detik untuk dokumen besar.

---

*Dokumen ini adalah living document — integrasi baru akan ditambahkan sesuai perkembangan roadmap.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-13 | Dibuat sebagai pecahan dari BE-07 v3.0.0 (ADR-035) — berisi integrasi yang dikerjakan AI Engineer: Tavily, OpenRouter, Google Gemini; section Supabase Storage dipindah ke BE-04; semua referensi kode dokumen diperbarui ke namespace baru | — |
