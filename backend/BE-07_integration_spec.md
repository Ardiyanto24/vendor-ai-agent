# BE-07 — Integration Spec Specification

**Project:** AI Vendor Selection System  
**Dokumen:** BE-07 — Integration Spec  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-13  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Gambaran Integrasi Eksternal](#3-gambaran-integrasi-eksternal)
4. [Pendekatan MVP: Simulasi dengan Real Search](#4-pendekatan-mvp-simulasi-dengan-real-search)
5. [Integrasi Tavily API](#5-integrasi-tavily-api)
6. [Integrasi Supabase Storage](#6-integrasi-supabase-storage)
7. [Integrasi OpenRouter API (LLM)](#7-integrasi-openrouter-api-llm)
8. [Integrasi Google Gemini Embedding API](#8-integrasi-google-gemini-embedding-api)
9. [Pola Integrasi Umum](#9-pola-integrasi-umum)
10. [Mock Layer untuk Data Simulasi](#10-mock-layer-untuk-data-simulasi)
11. [Roadmap Integrasi Pasca-MVP](#11-roadmap-integrasi-pasca-mvp)
12. [Aturan & Larangan](#12-aturan--larangan)
13. [Catatan untuk Dokumen Lanjutan](#13-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **semua integrasi dengan layanan dan sistem eksternal** — apa yang diintegrasikan, mengapa, bagaimana data mengalir, dan bagaimana ketergantungan pada pihak ketiga dikelola dengan aman.

Dokumen ini juga mendokumentasikan **keputusan MVP** tentang integrasi mana yang berjalan secara nyata dan mana yang disimulasikan, beserta alasan di balik keputusan tersebut dan rencana untuk masa mendatang.

Dokumen ini **tidak** mendefinisikan implementasi kode — itu diserahkan ke engineer.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| BE-03 | Agent Orchestration | Data Collector Agent yang menggunakan web search; pipeline indexing RAG |
| BE-06 | Auth & Security | Pengelolaan API key dan secret eksternal |
| BE-08 | RAG Specification | Detail pipeline RAG yang menggunakan OpenAI Embedding API |
| DB-01 | Data Model & ERD | Tabel `dokumen_upload` dan `dokumen_chunk` |
| SH-04 | Cost & Usage Guide | Estimasi biaya penggunaan API eksternal termasuk embedding |

---

## 3. Gambaran Integrasi Eksternal

Sistem bergantung pada empat kategori layanan eksternal:

```
AI Vendor Selection System
        │
        ├── OpenRouter API ─────── LLM untuk semua agent dan chat (DeepSeek-V4-Flash)
        │
        ├── Google Gemini API ───── Embedding teks untuk RAG indexing & retrieval
        │
        ├── Tavily API ─────────── Web search untuk Data Collector Agent
        │
        ├── Supabase ───────────── Database (+ pgvector), Storage, Auth, Realtime
        │
        └── [Pasca-MVP]
            ├── ERP/SAP ────────── Data historis transaksi vendor
            ├── SIUP/OSS API ───── Verifikasi legalitas vendor
            └── Email/Notifikasi ─ Notifikasi approval ke manager
```

**Mengapa dependensi eksternal dibatasi untuk MVP:** Setiap integrasi eksternal menambah kompleksitas — potensi downtime, biaya, perubahan API yang tidak terduga, dan kebutuhan pengelolaan credential tambahan. MVP fokus pada integrasi yang benar-benar diperlukan untuk membuktikan nilai inti sistem.

---

## 4. Pendekatan MVP: Simulasi dengan Real Search

### 4.1 Keputusan desain

Untuk MVP portofolio ini, pendekatan integrasi dibagi menjadi dua:

**Real (berjalan sungguhan):**
- Tavily API untuk web search di Data Collector Agent
- Supabase untuk semua kebutuhan database, storage, auth, dan realtime
- OpenRouter API untuk semua LLM call (model DeepSeek-V4-Flash)
- Google Gemini Embedding API untuk indexing dokumen penawaran dan RAG retrieval

**Disimulasikan (mock):**
- Data historis vendor dari ERP/SAP internal perusahaan → digantikan input manual
- Verifikasi legalitas resmi dari database pemerintah → disimulasikan dengan data yang diinput atau ditemukan via web search
- Notifikasi email ke manager → digantikan dengan notifikasi in-app

### 4.2 Mengapa pendekatan ini

**Nilai inti sistem tetap terbukti:** Kemampuan AI untuk menganalisa vendor, menghasilkan skor, dan memberikan rekomendasi yang dapat dijelaskan tidak bergantung pada integrasi ERP. Nilai ini sudah dapat didemonstrasikan dengan input manual.

**Web search tetap real:** Data Collector Agent menggunakan Tavily API yang sungguhan — bukan data yang di-hardcode. Ini memastikan portofolio dapat menunjukkan kemampuan agent mengumpulkan informasi dari internet secara dinamis, yang merupakan salah satu keunggulan sistem.

**Biaya terkontrol:** Dengan free tier Tavily (1.000 request/bulan) dan Anthropic API yang di-charge per token, biaya operasional MVP tetap minimal dan terprediksi.

### 4.3 Mock layer yang transparan

Komponen yang disimulasikan menggunakan mock layer yang terdokumentasi — bukan data yang di-hardcode secara tersembunyi. Mock layer dapat diganti dengan integrasi nyata tanpa mengubah interface yang digunakan oleh komponen lain. Ini memastikan sistem dapat di-upgrade dari MVP ke production tanpa refactor besar.

---

## 5. Integrasi Tavily API

### 5.1 Apa dan mengapa

Tavily adalah search API yang dirancang khusus untuk AI agent — hasil pencariannya sudah terstruktur (judul, URL, konten ringkas) tanpa memerlukan parsing HTML tambahan. Ini berbeda dari Selenium-based scraping yang rapuh dan Google Search API yang tidak dirancang untuk konsumsi LLM.

**Mengapa Tavily dipilih untuk MVP:** Free tier 1.000 request/bulan cukup untuk development dan demonstrasi portofolio. Hasilnya sudah dalam format yang siap dikonsumsi LLM, mengurangi kompleksitas implementasi di Data Collector Agent.

### 5.2 Digunakan oleh

Data Collector Agent (BE-03) — untuk mencari informasi publik tentang setiap vendor kandidat.

### 5.3 Apa yang dicari

Untuk setiap vendor, Data Collector Agent melakukan pencarian dengan query yang mencakup:
- Profil umum perusahaan (nama + "profil perusahaan" atau "company profile")
- Sertifikasi yang dimiliki (nama + "ISO" atau "sertifikasi")
- Berita terkini dalam 6 bulan terakhir (nama + "berita" atau "news")
- Indikasi masalah jika ada (nama + "sengketa" atau "masalah" atau "kasus")

Jumlah query per vendor: maksimum 4 query. Dengan 10 vendor maksimum per evaluasi, satu evaluasi mengonsumsi maksimum 40 Tavily request.

### 5.4 Data yang dikembalikan

Tavily mengembalikan per query: judul halaman, URL sumber, ringkasan konten (snippet), dan skor relevansi. Data ini diteruskan ke LLM dalam Data Collector Agent sebagai konteks untuk dianalisa dan disusun menjadi output terstruktur (format JSON sesuai BE-04).

### 5.5 Pengelolaan API key

Tavily API key disimpan sebagai environment variable di FastAPI service — tidak pernah di frontend atau di repository. Nama variabel: `TAVILY_API_KEY`.

### 5.6 Penanganan rate limit dan error

Tavily free tier tidak memiliki rate limit per detik yang ketat, tetapi tetap perlu penanganan error untuk:
- Request timeout (> 10 detik): retry sekali, jika tetap gagal lanjutkan tanpa data dari sumber tersebut
- HTTP 429 (rate limit): tunggu 60 detik sebelum retry
- HTTP 5xx (server error Tavily): catat error, lanjutkan tanpa data pencarian

Kegagalan Tavily tidak menghentikan proses evaluasi — Data Collector Agent melaporkan bahwa data dari web search tidak tersedia untuk vendor tersebut dan scoring engine menanganinya sesuai BE-05 section 7.

### 5.7 Batasan yang perlu disadari

Tavily free tier membatasi 1.000 request per bulan. Jika sistem digunakan lebih intensif (lebih dari 25 evaluasi dengan 10 vendor per bulan), free tier akan habis. Solusinya adalah upgrade ke paid tier atau mengurangi jumlah query per vendor. Monitoring penggunaan Tavily API harus dikonfigurasi (lihat SH-04).

---

## 6. Integrasi Supabase Storage

### 6.1 Apa dan mengapa

Supabase Storage digunakan untuk menyimpan file dokumen penawaran vendor yang diupload user. Ini adalah extension dari Supabase yang sudah digunakan sebagai database — tidak memerlukan konfigurasi service tambahan.

### 6.2 Digunakan oleh

- Next.js API Routes: menerima upload file dari browser dan meneruskan ke Supabase Storage
- FastAPI: mengakses file dari Storage URL untuk proses ekstraksi dokumen

### 6.3 Struktur penyimpanan

File disimpan dalam bucket yang terorganisir berdasarkan evaluasi:

```
bucket: vendor-documents
└── evaluasi/
    └── {evaluasi_id}/
        └── {upload_id}_{nama_file_asli}
```

Struktur ini memudahkan pengelolaan file per evaluasi — jika evaluasi dihapus (soft delete), file terkait dapat diidentifikasi dan dibersihkan dengan mudah.

### 6.4 Akses kontrol bucket

Bucket `vendor-documents` dikonfigurasi sebagai **private** — tidak ada file yang dapat diakses secara publik. Akses hanya melalui signed URL yang di-generate oleh Next.js API Routes untuk user yang sudah diverifikasi memiliki akses ke evaluasi terkait.

Masa berlaku signed URL maksimum 1 jam — cukup untuk sesi kerja normal tanpa membiarkan URL aktif selamanya.

### 6.5 Batasan ukuran dan tipe file

Batasan yang diterapkan di level Next.js sebelum file diteruskan ke Storage:
- Ukuran maksimum: 10MB per file
- Tipe file yang diizinkan: PDF dan Excel (.xlsx, .xls)

File yang tidak memenuhi batasan ini ditolak di level API — tidak pernah mencapai Supabase Storage.

### 6.6 Lifecycle file

File dokumen penawaran disimpan selama evaluasi aktif. Ketika evaluasi di-soft delete, file tidak langsung dihapus — mengikuti prinsip soft delete yang sama. Penghapusan permanen file dari Storage dilakukan sebagai bagian dari proses cleanup data yang terjadwal (lihat DB-04).

---

## 7. Integrasi OpenRouter API (LLM)

### 7.1 Apa dan mengapa

OpenRouter adalah aggregator LLM API yang menyediakan akses ke ratusan model dari berbagai provider melalui satu endpoint yang kompatibel dengan OpenAI API format. Sistem menggunakan OpenRouter untuk mengakses **DeepSeek-V4-Flash** sebagai LLM utama — model yang menawarkan kemampuan instruction-following dan structured JSON output yang kompetitif dengan biaya yang lebih efisien dibanding model proprietary tier tinggi.

Semua LLM call dari tujuh agent, ekstraksi dokumen, scoring reasoning, dan AI chat panel menggunakan endpoint OpenRouter yang sama.

### 7.2 Model yang digunakan

**DeepSeek-V4-Flash** digunakan untuk semua agent evaluasi dan reasoning scoring. Model ini dipilih karena kemampuan reasoning dan instruction-following yang baik untuk pipeline agent yang menghasilkan structured JSON output.

Untuk AI chat panel, model yang sama digunakan secara default. Jika hasil testing menunjukkan bahwa model yang lebih ringan sudah cukup untuk kebutuhan chat, AI Engineer dapat mengkonfigurasi model berbeda untuk endpoint chat tanpa mengubah arsitektur — cukup mengubah model string di konfigurasi.

### 7.3 Digunakan oleh

- FastAPI: semua agent (Data Collector, Financial Analyzer, Risk Assessor, Performance Scorer, Negotiation Assistant, Qualitative Analyzer, Preference Matcher)
- FastAPI: ekstraksi dokumen penawaran
- FastAPI: generasi reasoning naratif (Scoring Engine)
- FastAPI: AI chat panel (SSE streaming)

### 7.4 Pengelolaan API key

OpenRouter API key disimpan sebagai environment variable di FastAPI service: `OPENROUTER_API_KEY`. Tidak pernah diekspos ke frontend atau Next.js.

Integrasi menggunakan **OpenAI SDK** dengan override `base_url` ke endpoint OpenRouter:

```
base_url = "https://openrouter.ai/api/v1"
api_key  = OPENROUTER_API_KEY
model    = "deepseek/deepseek-v4-flash"  (verifikasi model string di dashboard OpenRouter)
```

Tidak diperlukan SDK tambahan — OpenAI SDK yang sudah digunakan untuk embedding dapat dipakai ulang dengan konfigurasi yang berbeda.

### 7.5 Penanganan rate limit

OpenRouter menerapkan rate limit berbasis credit dan request per menit yang bergantung pada tier akun. Untuk MVP:

- Jika rate limit tercapai: FastAPI menerapkan exponential backoff — tunggu sebelum retry
- Jika tetap gagal setelah 3 retry: agent dinyatakan gagal dan Orchestrator menerapkan fallback sesuai BE-03 section 7

Monitoring penggunaan kredit OpenRouter penting untuk memastikan biaya terkontrol (lihat SH-04).

### 7.6 Streaming response

Untuk AI chat panel, OpenRouter dipanggil dengan mode streaming — token dikirim ke client saat dihasilkan, bukan menunggu seluruh response selesai. OpenRouter mendukung streaming menggunakan format yang sama dengan OpenAI API (`stream=True`). Ini sudah didefinisikan di BE-02 section 10 dan FE-05 section 10.

Untuk agent evaluasi, streaming tidak digunakan — response ditunggu sampai selesai karena agent perlu seluruh output JSON sebelum bisa memproses hasilnya.

---

## 8. Integrasi Google Gemini Embedding API

### 8.1 Apa dan mengapa

Google Gemini Embedding API digunakan untuk mengubah teks (chunk dokumen penawaran dan query pencarian user) menjadi vektor numerik berdimensi 768 — representasi matematis yang menangkap makna semantik teks. Vektor inilah yang memungkinkan sistem menemukan potongan dokumen yang paling relevan dengan pertanyaan user, bahkan jika pertanyaan menggunakan kata-kata yang berbeda dari dokumen aslinya.

**Model yang digunakan:** `text-embedding-004` — menghasilkan vektor **768 dimensi**. Model stabil dari Google yang terbukti baik untuk teks berbahasa Indonesia dan Inggris.

**Mengapa Google Gemini:** Setelah LLM dipindah ke OpenRouter (ADR-033), diputuskan untuk mengkonsolidasi provider. Google `text-embedding-004` menawarkan dimensi 768 yang lebih efisien dari OpenAI `text-embedding-3-small` (1.536) untuk storage vector dan kecepatan similarity search, dengan kualitas retrieval yang setara untuk dokumen pengadaan. Detail keputusan ini ada di ADR-034 (SH-01).

### 8.2 Digunakan oleh

Dua pipeline yang berbeda menggunakan API ini:

**Pipeline indexing** (BE-03 section 9, BE-08 section 6) — dipanggil saat user mengupload dokumen penawaran. Setiap child chunk dari dokumen di-embed secara batch. Ini adalah operasi satu kali per dokumen.

**Pipeline retrieval** (BE-08 section 8) — dipanggil setiap kali user mengirim pesan di AI Chat Panel. Query user (setelah query expansion) di-embed untuk kemudian dibandingkan dengan chunk yang tersimpan di pgvector. Ini adalah operasi ringan per pesan.

### 8.3 Pengelolaan API key

Google API key disimpan sebagai environment variable di FastAPI service — tidak pernah di frontend atau di repository. Nama variabel: `GOOGLE_API_KEY`.

Ini adalah API key yang berbeda dari `OPENROUTER_API_KEY` — keduanya harus dikelola secara terpisah dan tidak saling bergantung. Jika salah satu bermasalah (expired, rate limit), yang lain tetap berfungsi.

### 8.4 Strategi batching

Untuk efisiensi biaya dan menghindari rate limit, embedding tidak dilakukan satu per satu:

**Saat indexing:** Semua child chunk dari satu dokumen di-batch dalam satu atau beberapa API call. Batching mengikuti batas yang didokumentasikan di Google AI API — verifikasi batas terkini saat implementasi.

**Saat retrieval:** Hanya satu query per pesan user — tidak perlu batching.

### 8.5 Penanganan rate limit dan error

Google Gemini Embedding API memiliki rate limit berbasis request per menit (RPM) dan token per menit (TPM) yang bergantung pada tier akun. Untuk satu dokumen 50 halaman, proses embedding selesai jauh di bawah rate limit standar.

Penanganan error:
- HTTP 429 (rate limit): eksponensial backoff, retry setelah jeda
- HTTP 5xx: retry maksimum 3 kali, jika tetap gagal tandai `indexing_rag_status = failed` di tabel `dokumen_upload`
- Kegagalan embedding tidak menghentikan ekstraksi field terstruktur — keduanya berjalan di cabang pipeline yang independen (BE-03 section 9.2)

### 8.6 Timeout

| Operasi | Timeout |
|---|---|
| Embedding batch saat indexing | 30 detik |
| Embedding query saat retrieval | 5 detik |

Jika embedding query gagal (timeout atau error), pipeline retrieval menggunakan hanya full-text search (BM25) sebagai fallback — kualitas retrieval berkurang tetapi chat tetap bisa menjawab pertanyaan.

### 8.7 Estimasi biaya

Biaya embedding sangat kecil dibanding biaya LLM. Verifikasi harga terkini di halaman pricing Google AI sebelum kalkulasi final — pricing dapat berubah. Estimasi kasar:

| Skenario | Token | Biaya (estimasi) |
|---|---|---|
| Indexing dokumen 20 halaman | ~10.000 token | sangat kecil |
| Indexing dokumen 50 halaman | ~25.000 token | sangat kecil |
| Retrieval per pesan chat | ~200 token | dapat diabaikan |
| **Total per evaluasi (indexing + 20 chat)** | **~150.000 token** | **< $0.005** |

Biaya embedding kurang dari 1% dari total biaya LLM per evaluasi. Detail integrasi ke estimasi biaya total ada di SH-04.

---

## 9. Pola Integrasi Umum

Pola berikut diterapkan secara konsisten ke semua integrasi eksternal.

### 8.1 Circuit breaker

Jika suatu layanan eksternal gagal berulang kali dalam periode singkat, sistem berhenti mencoba dan langsung mengembalikan error — tidak terus mencoba dan memblokir resource. Circuit breaker terbuka (berhenti mencoba) setelah 5 kegagalan berturut-turut, dan dicoba kembali setelah 60 detik.

**Mengapa:** Tanpa circuit breaker, kegagalan satu layanan eksternal bisa menyebabkan seluruh proses evaluasi tersangkut menunggu timeout satu per satu.

## 9. Pola Integrasi Umum

### 9.1 Satu abstraction layer per integrasi

### 9.2 Timeout yang eksplisit

Setiap request ke layanan eksternal memiliki timeout yang terdefinisi:

| Layanan | Timeout |
|---|---|
| Tavily API (per query) | 10 detik |
| OpenRouter API (non-streaming) | 60 detik |
| OpenRouter API (streaming, first token) | 30 detik |
| Google Gemini Embedding API (batch indexing) | 30 detik |
| Google Gemini Embedding API (query retrieval) | 5 detik |
| Supabase Storage (upload) | 120 detik |
| Supabase Storage (download untuk ekstraksi) | 30 detik |

### 9.3 Retry dengan exponential backoff

Semua integrasi eksternal menerapkan retry dengan pola yang sama:
- Maksimum 3 percobaan total (1 attempt awal + 2 retry)
- Jeda antar retry: 2 detik, lalu 8 detik (exponential backoff dengan faktor 4)
- Retry hanya untuk error sementara: timeout, HTTP 429, HTTP 5xx
- Tidak retry untuk error permanen: HTTP 400, HTTP 401, HTTP 403

### 9.4 Logging setiap external call

Setiap request ke layanan eksternal dicatat di log dengan informasi:
- Layanan yang dipanggil
- Durasi request
- HTTP status response
- Apakah ada retry yang dilakukan
- ID evaluasi yang terkait (untuk tracing)

Konten request dan response tidak dicatat secara penuh — hanya metadata. Ini melindungi data vendor dari tersimpan di log dan menghindari log yang terlalu besar.

---

## 10. Mock Layer untuk Data Simulasi

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

Data mock tidak di-hardcode sebagai data vendor yang spesifik. Data mock mengembalikan nilai default yang konsisten (misalnya: tidak ada riwayat transaksi tersedia, status legalitas tidak dapat diverifikasi dari sistem internal) — sehingga scoring engine menanganinya sebagai data tidak lengkap sesuai BE-05 section 7.

---

## 11. Roadmap Integrasi Pasca-MVP

Bagian ini mendokumentasikan integrasi yang direncanakan untuk iterasi berikutnya setelah MVP. Tujuannya adalah memastikan arsitektur MVP sudah mempertimbangkan kebutuhan ini sehingga tidak ada refactor besar saat integrasi ditambahkan.

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

### 10.3 Notifikasi Email (Prioritas Rendah)

**Tujuan:** Mengirim email notifikasi ke manager saat ada evaluasi yang perlu di-approve, dan ke staff saat keputusan approval sudah diberikan.

**Kandidat integrasi:** Resend, SendGrid, atau AWS SES.

**Titik integrasi:** Next.js API Routes — dipicu saat status evaluasi berubah ke `menunggu_approval` atau saat approval diberikan.

**Mengapa prioritas rendah:** Notifikasi in-app sudah cukup untuk MVP. Email menambahkan kompleksitas (template, deliverability, unsubscribe) yang tidak esensial di tahap awal.

### 10.4 Integrasi Marketplace Vendor (Jangka Panjang)

**Tujuan:** Mengambil data vendor langsung dari marketplace B2B seperti Tokopedia for Business, Ralali, atau platform pengadaan pemerintah (e-Katalog LKPP).

**Titik integrasi:** Data Collector Agent — sebagai sumber data tambahan.

---

## 12. Aturan & Larangan

**Dilarang menyimpan API key eksternal di kode atau repository.** Semua API key (Tavily, OpenRouter, Google) disimpan sebagai environment variable sesuai BE-06 section 10.

**Dilarang memanggil layanan eksternal dari frontend.** Semua request ke Tavily, OpenRouter, dan Google Gemini hanya dari FastAPI — tidak pernah dari browser secara langsung.

**Dilarang mencampur `OPENROUTER_API_KEY` dan `GOOGLE_API_KEY`.** Keduanya adalah credential yang berbeda untuk layanan yang berbeda. Pengelolaan, rotasi, dan monitoring keduanya dilakukan secara terpisah.

**Dilarang menghilangkan mock layer tanpa menggantinya dengan integrasi nyata.** Menghapus mock tanpa pengganti akan menyebabkan komponen yang bergantung padanya error.

**Dilarang menyimpan konten response API eksternal ke log secara penuh.** Konten vendor yang dikembalikan Tavily, output LLM dari OpenRouter, maupun vektor dari Google Gemini tidak boleh masuk ke log — hanya metadata request (durasi, status, ID evaluasi).

**Dilarang menggunakan Tavily untuk mencari informasi personal user** — hanya untuk informasi perusahaan vendor yang relevan dengan evaluasi pengadaan.

**Dilarang bypass circuit breaker** dengan cara apapun. Jika circuit breaker terbuka, sistem harus menunggu recovery period selesai — tidak ada override manual selama evaluasi berlangsung.

---

## 13. Catatan untuk Dokumen Lanjutan

### Untuk SH-04 (Cost & Usage Guide)

Tiga layanan eksternal berbayar perlu dimonitoring penggunaannya:
- Tavily API: 1.000 request gratis per bulan
- OpenRouter API: biaya per input dan output token (model DeepSeek-V4-Flash)
- Google Gemini Embedding API: biaya per token (sangat kecil, < $0.005 per evaluasi)
- Supabase: storage dan bandwidth untuk file dokumen dan vector data

SH-04 perlu memperbarui estimasi biaya per evaluasi untuk mencerminkan pricing DeepSeek via OpenRouter dan Google Gemini embedding.

### Untuk SH-02 (Deployment Runbook)

Runbook perlu mencakup prosedur setup environment variable untuk `OPENROUTER_API_KEY` dan `GOOGLE_API_KEY` menggantikan `ANTHROPIC_API_KEY` dan `OPENAI_API_KEY`.

### Untuk SH-03 (Testing Strategy)

Testing integrasi eksternal perlu mencakup:
- Test pipeline embedding dengan Google Gemini API key nyata di staging
- Test fallback saat Google Gemini API tidak tersedia (retrieval fallback ke BM25 saja)
- Test bahwa kegagalan embedding tidak memblokir ekstraksi field terstruktur
- Test structured JSON output dari DeepSeek-V4-Flash via OpenRouter untuk setiap agent — validasi konsistensi format lebih ketat dibanding sebelumnya

### Untuk BE-03 (Agent Orchestration)

Pipeline ekstraksi dokumen sekarang bercabang dua (BE-03 section 9.2). Pastikan timeout agent secara keseluruhan mencakup waktu embedding yang bisa mencapai 30 detik untuk dokumen besar.

---

*Dokumen ini adalah living document — integrasi baru akan ditambahkan sesuai perkembangan roadmap.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal — tiga integrasi eksternal | — |
| 2.0.0 | 2026-06-11 | Tambah section 8 integrasi OpenAI Embedding API; perbarui gambaran integrasi, pendekatan MVP, timeout table, aturan, dan catatan dokumen lanjutan | — |
| 3.0.0 | 2026-06-13 | Ganti section 7 dari Anthropic API ke OpenRouter API (DeepSeek-V4-Flash); ganti section 8 dari OpenAI Embedding API ke Google Gemini Embedding API (text-embedding-004); perbarui diagram, pendekatan MVP, timeout table, aturan, dan catatan dokumen lanjutan | — |
