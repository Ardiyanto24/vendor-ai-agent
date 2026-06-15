# SH-03 — Testing Strategy Specification

**Project:** AI Vendor Selection System  
**Dokumen:** SH-03 — Testing Strategy  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-12  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip Testing Sistem](#3-prinsip-testing-sistem)
4. [Gambaran Lapisan Testing](#4-gambaran-lapisan-testing)
5. [Testing Frontend](#5-testing-frontend)
6. [Testing Backend — Next.js API Routes](#6-testing-backend--nextjs-api-routes)
7. [Testing Backend — FastAPI & Agent](#7-testing-backend--fastapi--agent)
8. [Testing Scoring Engine](#8-testing-scoring-engine)
9. [Testing Prompt & LLM Output](#9-testing-prompt--llm-output)
10. [Testing RAG](#10-testing-rag)
11. [Testing Integrasi Antar Service](#11-testing-integrasi-antar-service)
12. [Testing Keamanan](#12-testing-keamanan)
13. [Testing Performa Database](#13-testing-performa-database)
14. [Pipeline CI/CD Holistik](#14-pipeline-cicd-holistik)
15. [Restore Test Terjadwal](#15-restore-test-terjadwal)
16. [Aturan & Larangan](#16-aturan--larangan)
17. [Catatan untuk Dokumen Lanjutan](#17-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **strategi testing keseluruhan sistem** — mencakup semua lapisan dari frontend hingga database, termasuk komponen yang unik untuk sistem AI seperti testing prompt dan LLM output.

Dokumen ini menjadi panduan bagi seluruh tim tentang apa yang perlu diuji, di lapisan mana, dengan tools apa, dan bagaimana semua lapisan testing diintegrasikan dalam satu pipeline CI/CD yang kohesif.

Dokumen ini **tidak** menduplikasi detail yang sudah ada di FE-06 (Testing & QA Frontend) — ia merujuk dan mengintegrasikan dokumen tersebut ke dalam gambaran yang lebih besar.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-06 | Testing & QA Frontend | Detail testing frontend yang diintegrasikan di sini |
| AI-01 | Agent Orchestration | Skenario kegagalan agent yang perlu di-test (7 agent) |
| AI-02 | Prompt Library | Evaluasi prompt dan metric yang diukur |
| AI-03 | Scoring Engine | Validasi kalkulasi TOPSIS dan output kualitatif/preferensi |
| BE-06 | Auth & Security | Skenario security testing |
| AI-04 | RAG Specification | Strategi testing RAG: indexing, retrieval, isolasi data |
| AI-05 | Qualitative Analyzer Agent | Test cases agent kualitatif |
| AI-06 | Preference Matcher Agent | Test cases agent preferensi |
| DB-04 | Backup & Retention | Restore test terjadwal |
| SH-02 | Deployment Runbook | Pipeline CI/CD yang menjalankan semua test |

---

## 3. Prinsip Testing Sistem

### 3.1 Test di lapisan yang paling dekat dengan masalah

Setiap jenis bug paling efisien ditangkap di lapisan yang paling dekat dengan sumbernya. Bug logika kalkulasi TOPSIS paling tepat ditangkap oleh unit test scoring engine — bukan oleh E2E test yang memerlukan seluruh sistem berjalan. Sebaliknya, bug pada alur approval paling tepat ditangkap oleh E2E test yang melibatkan interaksi user nyata.

### 3.2 Sistem AI membutuhkan testing yang berbeda dari sistem konvensional

Komponen AI (agent, LLM output) bersifat probabilistik — output tidak selalu deterministik. Testing untuk komponen ini tidak bisa menggunakan pola assert exact equality yang lazim. Sebaliknya, evaluasi berbasis metric (format compliance, hallucination rate) dan sampling lebih sesuai.

### 3.3 Isolasi dependency eksternal dalam test

Test tidak boleh bergantung pada ketersediaan layanan eksternal (Anthropic API, Tavily API, Supabase production). Dependency ini di-mock atau di-stub untuk semua test otomatis — kecuali integration test yang memang dirancang untuk memverifikasi konektivitas eksternal.

### 3.4 Kegagalan test adalah informasi, bukan hambatan

Pipeline CI yang memblokir deployment saat test gagal adalah mekanisme keamanan yang disengaja. Ketika test gagal, tim mendapatkan informasi berharga tentang apa yang rusak — bukan hambatan yang harus disiasati.

---

## 4. Gambaran Lapisan Testing

```
┌──────────────────────────────────────────────────────────────┐
│  E2E Test (Playwright)                                        │
│  Critical path end-to-end: login → evaluasi → approval       │
├──────────────────────────────────────────────────────────────┤
│  Integration Test Antar Service                               │
│  Next.js ↔ FastAPI, FastAPI ↔ Supabase                       │
├──────────────────────────────────────────────────────────────┤
│  Integration Test per Service                                 │
│  FE: halaman + state | BE: endpoint + DB | Agent: alur       │
├──────────────────────────────────────────────────────────────┤
│  Unit Test                                                    │
│  FE: komponen | BE: handler | Scoring: kalkulasi | Prompt    │
├──────────────────────────────────────────────────────────────┤
│  Static Analysis                                              │
│  TypeScript, ESLint, Pylint, mypy                            │
└──────────────────────────────────────────────────────────────┘
```

Setiap lapisan memberikan coverage yang berbeda dan saling melengkapi. Tidak ada lapisan yang bisa menggantikan lapisan lain sepenuhnya.

---

## 5. Testing Frontend

Detail lengkap testing frontend sudah didefinisikan di **FE-06**. Bagian ini hanya merangkum aspek yang relevan untuk koordinasi lintas tim.

### 5.1 Ringkasan

- **Unit test:** Vitest + React Testing Library untuk komponen dengan logika kondisional
- **Integration test:** Vitest + MSW (Mock Service Worker) untuk alur per halaman
- **E2E test:** Playwright untuk critical path (happy path staff, approval flow manager)
- **Aksesibilitas:** axe-core via Playwright — zero violation WCAG 2.1 AA
- **Visual regression:** Playwright screenshot diff untuk komponen kritis

### 5.2 Koordinasi dengan backend

MSW handler yang digunakan untuk frontend integration test dan E2E test harus konsisten dengan API contract yang didefinisikan di BE-02. Jika ada perubahan endpoint atau response format di BE-02, MSW handler harus diupdate bersamaan.

---

## 6. Testing Backend — Next.js API Routes

### 6.1 Unit test handler

Setiap API handler di Next.js API Routes diuji secara terpisah dari database dan service eksternal menggunakan mock.

**Yang diuji per handler:**
- Response yang benar untuk input valid
- Response error yang tepat untuk berbagai kondisi gagal (validasi, resource tidak ditemukan, otorisasi gagal)
- Bahwa handler memanggil dependency yang benar (database, FastAPI) dengan argumen yang benar

**Tools:** Vitest, dengan mock untuk Supabase client dan fetch ke FastAPI.

### 6.2 Integration test endpoint

Integration test memverifikasi bahwa endpoint berfungsi end-to-end dari request HTTP hingga response — termasuk interaksi dengan database test (bukan production).

**Database test:** Supabase instance terpisah khusus untuk testing. Sebelum setiap test suite, database di-seed dengan data fixture yang terdefinisi. Setelah test selesai, data dibersihkan.

**Skenario yang diuji per domain:**

*Auth:*
- Login berhasil mengembalikan token yang valid
- Login dengan kredensial salah mengembalikan 401
- Akses endpoint protected tanpa token mengembalikan 401
- Refresh token yang expired mengembalikan 401

*Evaluasi:*
- Staff tidak bisa mengakses evaluasi milik staff lain (memastikan RLS berfungsi)
- Submit evaluasi dengan kurang dari 2 vendor ditolak
- Status evaluasi mengikuti lifecycle yang benar (tidak bisa lompat status)

*Approval:*
- Staff tidak bisa mengakses endpoint approval (403)
- Reject tanpa komentar ditolak dengan validasi error
- Approve mengubah status evaluasi dengan benar

*Konfigurasi:*
- Simpan bobot dengan total bukan 100 ditolak
- Hanya manager yang bisa mengubah konfigurasi

### 6.3 Rate limit testing

Test memverifikasi bahwa rate limiting berfungsi sesuai konfigurasi di BE-06 — endpoint login dibatasi 5 request per menit, endpoint lain mengikuti batasannya masing-masing.

---

## 7. Testing Backend — FastAPI & Agent (AI Engineer)

> Section ini mendefinisikan strategi testing untuk `vendor-ai-agent` — territory AI Engineer. Semua test di section ini ditulis dan dijalankan oleh AI Engineer menggunakan pytest.

### 7.1 Unit test per agent

Setiap sub-agent diuji secara terpisah dengan LLM di-mock. Mock LLM mengembalikan response fixture yang sudah terdefinisi — bukan memanggil Anthropic API sungguhan.

**Mengapa LLM di-mock untuk unit test:** LLM call mahal (biaya token), lambat (latensi jaringan), dan non-deterministik. Unit test yang bergantung pada LLM sungguhan tidak akan reliable dan biayanya tidak terkontrol.

**Yang diuji per agent:**
- Agent memproses payload input dengan benar
- Agent menangani output LLM yang valid sesuai format JSON yang diharapkan
- Agent menangani output LLM yang tidak sesuai format (retry logic)
- Agent menangani timeout LLM dengan benar
- Agent menulis progress ke database dengan benar di setiap tahap

### 7.2 Integration test orchestration

Test orchestration memverifikasi koordinasi antar agent — bahwa parallelism berjalan benar, dependency antar agent (Performance Scorer menunggu Data Collector) direspek, dan kegagalan satu agent tidak menghentikan yang lain.

**Skenario kegagalan yang wajib diuji:**

| Skenario | Yang diverifikasi |
|---|---|
| Data Collector timeout | Performance Scorer tetap berjalan dengan data minimal |
| Financial Analyzer error | Skor finansial menggunakan fallback, flag terset |
| Risk Assessor gagal setelah 3 retry | Level risiko default diterapkan, peringatan dicatat |
| Negotiation Assistant gagal | Evaluasi tetap selesai tanpa bagian negosiasi |
| Qualitative Analyzer gagal | Evaluasi selesai tanpa profil kualitatif; Preference Matcher berjalan dalam mode terdegradasi |
| Preference Matcher gagal | Evaluasi selesai tanpa rekomendasi berbasis preferensi; TOPSIS tetap ditampilkan |
| Semua agent gagal | Evaluasi ditandai tidak dapat diselesaikan |

### 7.3 Integration test ekstraksi dokumen dan RAG indexing

Test memverifikasi alur dari upload hingga dokumen siap digunakan oleh AI Chat Panel:
- Upload PDF valid → ekstraksi field terstruktur berhasil → confidence score tersedia
- Upload PDF valid → RAG indexing berhasil → `chunk_count` terisi → `indexing_rag_status: done`
- Upload file yang bukan PDF/Excel → ditolak sebelum sampai ke LLM
- Upload PDF scan tanpa teks → ekstraksi LLM via vision, RAG indexing di-skip → `indexing_rag_status: skipped_no_text`
- OpenAI Embedding API tidak tersedia → ekstraksi field terstruktur tetap berhasil → `status_ekstraksi: done_partial`, `indexing_rag_status: failed`
- Upload ulang dokumen → chunk lama di-soft delete → chunk baru menggantikan

---

## 8. Testing Scoring Engine (AI Engineer)

> Scoring Engine adalah bagian dari `vendor-ai-agent`. Test di section ini ditulis dan dijalankan oleh AI Engineer.

Scoring Engine adalah komponen yang paling mudah dan paling penting untuk diuji secara menyeluruh — ia sepenuhnya deterministik (tidak ada LLM), sehingga exact equality assertion bisa digunakan.

### 8.1 Unit test kalkulasi TOPSIS

Setiap tahap kalkulasi TOPSIS (lihat AI-03 section 5) diuji secara terpisah:

**Test per tahap:**
- Normalisasi vektor menghasilkan matriks yang benar (verifikasi matematis dengan nilai yang diketahui)
- Pembobotan menghasilkan weighted matrix yang benar
- Solusi ideal positif dan negatif diidentifikasi dengan benar
- Jarak Euclidean dihitung dengan benar
- Skor final dan ranking menghasilkan urutan yang benar

**Test fixture:** Minimal satu set data yang bisa dihitung secara manual untuk verifikasi. Ini memastikan implementasi sesuai dengan metodologi TOPSIS yang terdefinisi di AI-03.

### 8.2 Test normalisasi data agent

Test memverifikasi konversi field kategorikal ke skor numerik (AI-03 section 6.3):
- Setiap nilai enum menghasilkan skor yang tepat
- `tidak_dapat_dinilai` menghasilkan skor default yang benar dan flag `data_tidak_lengkap` terset
- Data null mengaktifkan logika fallback yang sesuai

### 8.3 Test threshold minimum

Test memverifikasi bahwa threshold diterapkan dengan benar:
- Vendor yang tidak lolos threshold diberi flag `lolos_threshold: false`
- Vendor yang tidak lolos threshold tidak bisa menjadi rekomendasi utama
- Jika semua vendor tidak lolos threshold, output mencerminkan kondisi ini

### 8.4 Test validasi output

Test memverifikasi semua validasi yang didefinisikan di AI-03 section 11:
- Skor total semua vendor dalam rentang 0–100
- Tidak ada dua vendor dengan skor identik hingga desimal keempat
- Jumlah row output sama dengan jumlah vendor input
- Jika validasi gagal, tidak ada penulisan ke database

### 8.5 Test dengan data tidak lengkap

Skenario data parsial (agent gagal) diuji secara eksplisit:

| Input | Expected Output |
|---|---|
| Financial Analyzer gagal total | Skor finansial dari harga nominal saja, flag terset |
| Risk Assessor gagal total | Skor risiko default 50, peringatan di output |
| Qualitative Analyzer gagal | Kolom `profil_kualitatif` dan `unique_offerings` null, TOPSIS tetap lengkap |
| Preference Matcher gagal | Kolom `preference_matching_result` null, TOPSIS dan kualitatif tetap ditampilkan |
| Qualitative Analyzer gagal + ada preferensi | Preference Matcher berjalan dalam mode terdegradasi, flag `kualitas_terdegradasi: true` |
| Tiga dari tujuh agent gagal | Output tetap dihasilkan dengan peringatan komprehensif |
| Semua agent gagal | Evaluasi ditandai `tidak_dapat_dihitung` |

---

## 9. Testing Prompt & LLM Output (AI Engineer)

> Test prompt disimpan bersama file prompt di `vendor-ai-agent/tests/` dan dijalankan oleh AI Engineer.

Ini adalah aspek testing yang paling berbeda dari sistem konvensional. LLM output tidak deterministik, sehingga pendekatan yang digunakan adalah evaluasi berbasis metric, bukan exact assertion.

### 9.1 Test suite per agent

Setiap agent memiliki test suite dengan minimal 10 test case yang mencakup empat kategori (seperti didefinisikan di AI-02 section 9.2):
- Kasus normal: data lengkap dan jelas
- Kasus edge: data sangat minim
- Kasus negatif: vendor dengan masalah yang perlu terdeteksi
- Kasus ambiguitas: data tidak jelas atau kontradiktif

**Test tambahan untuk Qualitative Analyzer Agent:**

Qualitative Analyzer menghasilkan narasi, bukan skor numerik — test-nya berbeda dari lima agent kuantitatif:
- Output tidak berisi klaim tanpa sumber yang bisa ditelusuri (tidak ada hallucination kualitatif)
- Vendor tanpa unique offering menghasilkan `unique_offerings: []` bukan mengarang
- Output `profil_kualitatif` panjangnya dalam rentang 100–150 kata
- `potensi_tie_breaker: true` hanya diset jika unique offerings benar-benar signifikan
- Kasus tidak ada RAG context tersedia: output tetap dihasilkan dari data agent lain saja

**Test tambahan untuk Preference Matcher Agent:**

- Mode netral (preferensi null): `rekomendasi_vendor` array kosong, `narasi_pengantar` tidak menyebut preferensi spesifik
- Mode opinionated dengan preferensi jelas: rekomendasi 1–3 vendor, `alasan_utama` berbasis data aktual
- Mode opinionated dengan preferensi ambigu: output mendekati mode netral, tidak memaksakan rekomendasi
- Konflik TOPSIS vs preferensi: `ada_konflik_topsis: true`, `catatan_konflik` terisi
- Preferensi bertentangan dengan requirement: kontradiksi disebutkan eksplisit di `interpretasi_preferensi`

### 9.2 Metric yang diukur

Empat metric yang didefinisikan di AI-02 section 9.3 diukur untuk setiap perubahan prompt:

| Metric | Target | Cara mengukur |
|---|---|---|
| Format compliance | > 95% | Validasi JSON schema otomatis |
| Null rate | < 10% | Hitung field null saat data tersedia |
| Hallucination rate | < 5% | Review manual sample output |
| Confidence calibration | > 0.7 | Korelasi confidence vs akurasi aktual |

### 9.3 Kapan test prompt dijalankan

Test prompt tidak dijalankan di setiap commit — terlalu mahal dari sisi biaya API dan waktu. Test prompt dijalankan:
- Sebelum setiap PR yang mengubah file prompt
- Setiap bulan sebagai regression check (mendeteksi degradasi akibat perubahan model LLM)
- Setelah pergantian versi model LLM

### 9.4 Test dengan LLM sungguhan vs mock

Test metric menggunakan **LLM sungguhan** (Anthropic API) untuk menghasilkan output yang nyata. Test unit dan integration agent menggunakan **LLM mock** untuk kecepatan dan kontrol biaya.

Kedua jenis test perlu ada dan tidak saling menggantikan.

---

## 10. Testing RAG

Testing RAG adalah kategori tersendiri karena melibatkan tiga komponen berbeda yang saling bergantung: pipeline indexing, pipeline retrieval, dan integrasi ke AI Chat Panel.

### 10.1 Test pipeline indexing

**Yang diverifikasi:**

Setelah dokumen PDF diupload dan pipeline indexing selesai, tabel `dokumen_chunk` harus berisi chunk yang benar:
- Jumlah chunk sesuai dengan estimasi berdasarkan panjang dokumen
- Setiap child chunk memiliki `embedding` (vektor, bukan null)
- Setiap child chunk memiliki `teks_search` (tsvector, bukan null)
- Setiap parent chunk memiliki `embedding: null` (parent tidak di-embed)
- Tabel tidak dipotong di tengah (tipe konten `tabel` selalu menjadi satu chunk utuh)
- Metadata chunk akurat: `halaman`, `tipe_konten`, `posisi_section`, `chunk_index`
- `parent_chunk_id` pada child chunk merujuk ke parent yang benar

**Test isolasi:**
- Chunk dari evaluasi A tidak muncul saat query dengan `evaluasi_id` evaluasi B
- Upload ulang dokumen menggantikan chunk lama (soft delete chunk lama, buat chunk baru)

**Test edge case:**
- PDF scan tanpa teks: `indexing_rag_status: skipped_no_text`, tidak ada chunk di database
- PDF dengan tabel besar (> 1.500 token): tabel tetap satu chunk, tidak dipotong
- OpenAI API gagal saat embedding: `indexing_rag_status: failed`, ekstraksi field terstruktur tidak terdampak

### 10.2 Test pipeline retrieval

**Yang diverifikasi:**

Pipeline retrieval harus mengembalikan chunk yang relevan dengan pertanyaan:
- Vector similarity search menemukan chunk yang secara semantik relevan
- Full-text search menemukan chunk yang mengandung kata kunci eksak (nama produk, angka, kode)
- Hybrid search (RRF) menggabungkan kedua hasil dengan benar
- Top-5 child chunk ditemukan → parent chunk-nya diambil dengan benar
- Deduplication: jika dua child berasal dari parent yang sama, parent hanya muncul sekali

**Test query expansion:**
- Query user pendek diperluas menjadi query yang lebih kaya
- Jika query expansion gagal (timeout), pertanyaan asli digunakan sebagai fallback
- Query expansion menggunakan model yang benar (Haiku, bukan Sonnet)

**Test filter isolasi:**
- Retrieval selalu menggunakan filter `evaluasi_id` — tidak ada chunk dari evaluasi lain yang ikut muncul
- Test dengan `evaluasi_id` palsu menghasilkan hasil kosong, bukan error

### 10.3 Test kualitas retrieval

Kualitas retrieval diukur secara kuantitatif menggunakan test case yang sudah diketahui jawabannya:

| Pertanyaan | Chunk yang seharusnya ditemukan |
|---|---|
| "Berapa harga penawaran vendor X?" | Chunk yang mengandung tabel harga vendor X |
| "Garansi apa yang ditawarkan vendor Y?" | Chunk dari section garansi dokumen vendor Y |
| "Vendor mana yang menawarkan training?" | Chunk dari semua vendor yang menyebut training |

**Target:** Minimal 80% dari pertanyaan test case menemukan chunk yang relevan di top-3 hasil (precision@3 ≥ 0.8).

Test ini dijalankan menggunakan dokumen penawaran sintetis yang dibuat khusus untuk testing — bukan dokumen vendor nyata.

### 10.4 Test integrasi RAG dengan AI Chat Panel

**Yang diverifikasi:**
- Chat panel di halaman P-05 mengirim query ke pipeline retrieval sebelum memanggil LLM
- RAG context diinjeksikan ke prompt sebelum riwayat percakapan
- LLM menyebutkan nama vendor dan nomor halaman saat merujuk isi dokumen (attribution)
- Jika tidak ada chunk relevan (RRF score < threshold), LLM mengakui keterbatasan tanpa mengarang
- Chat tetap berfungsi jika RAG index tidak tersedia (fallback ke data terstruktur saja)

### 10.5 Kapan test RAG dijalankan

Test pipeline indexing dan retrieval dijalankan di environment staging dengan OpenAI API key nyata — tidak bisa di-mock karena kualitas embedding bergantung pada model nyata.

Test kualitas retrieval (10.3) dijalankan:
- Setiap kali ada perubahan pada strategi chunking atau parameter retrieval
- Setiap bulan sebagai regression check
- Tidak di setiap commit — terlalu mahal

---

## 11. Testing Integrasi Antar Service

Integration test antar service memverifikasi bahwa komponen yang dikembangkan secara terpisah bekerja bersama dengan benar.

### 11.1 Next.js → FastAPI

**Yang diverifikasi:**
- Next.js meneruskan request ke FastAPI dengan format yang benar saat evaluasi disubmit
- Service-to-service token divalidasi dengan benar oleh FastAPI
- Next.js menangani response error dari FastAPI dengan benar (503 saat FastAPI down)
- Payload yang dikirim Next.js ke FastAPI konsisten dengan yang diharapkan AI-01

**Environment:** Staging environment dengan kedua service berjalan. FastAPI menggunakan LLM mock untuk menghindari biaya API.

### 11.2 FastAPI → Supabase

**Yang diverifikasi:**
- FastAPI berhasil menulis progress agent ke tabel `agent_progress` (7 agent)
- Penulisan progress bersifat idempotent (menulis status yang sama dua kali aman)
- Penulisan hasil evaluasi sebagai satu transaksi (rollback jika gagal sebagian)
- FastAPI berhasil menulis bulk insert chunk ke tabel `dokumen_chunk`
- RLS tidak memblokir operasi FastAPI yang menggunakan service role key
- Query retrieval RAG (hybrid search) di pgvector mengembalikan hasil dalam waktu yang wajar (< 500ms)

### 11.3 Supabase Realtime → Frontend

**Yang diverifikasi:**
- Perubahan pada tabel `agent_progress` ter-broadcast ke frontend dalam waktu yang wajar (< 2 detik)
- Frontend menerima dan memproses event Realtime dengan benar
- Koneksi Realtime di-unsubscribe dengan benar saat komponen unmount

### 11.4 SSE Frontend → FastAPI

**Yang diverifikasi:**
- Koneksi SSE berhasil dibuat dengan token yang valid
- Token yang tidak valid ditolak dengan benar (401)
- Stream token diterima dan dirender secara bertahap di UI
- Koneksi ditutup dengan benar saat event `done` diterima
- Koneksi ditutup dengan benar jika user meninggalkan halaman

---

## 12. Testing Keamanan

### 12.1 Otorisasi

**Skenario yang wajib diuji:**

| Skenario | Expected behavior |
|---|---|
| Staff akses evaluasi milik staff lain (dengan ID yang diketahui) | 403 |
| Staff akses endpoint `/approval` | 403 atau redirect |
| Staff akses endpoint `/settings/kriteria` | 403 atau redirect |
| Request tanpa Authorization header ke endpoint protected | 401 |
| Request dengan token expired | 401 |
| Request dengan token yang di-forge (signature salah) | 401 |
| Manager akses evaluasi staff lain | 200 (diizinkan) |

### 11.2 Input validation

**Skenario yang wajib diuji:**
- Budget min lebih besar dari budget max → validasi error yang jelas
- Deadline di masa lalu → validasi error yang jelas
- Total bobot kriteria bukan 100 → tolak dengan pesan yang jelas
- Upload file lebih dari 10MB → tolak sebelum sampai ke storage
- Upload file tipe yang tidak didukung → tolak dengan pesan yang jelas
- String yang sangat panjang di field teks → di-truncate atau ditolak

### 11.3 Rate limiting

**Skenario yang wajib diuji:**
- Lebih dari 5 request login dalam 1 menit dari IP yang sama → 429
- Lebih dari 20 request chat dalam 1 menit dari user yang sama → 429
- Response setelah rate limit habis kembali normal setelah periode reset

### 11.4 RLS (Row Level Security)

RLS adalah lapisan keamanan di database yang harus diverifikasi secara terpisah dari logika aplikasi — bahkan jika bug di aplikasi melewatkan pengecekan otorisasi, RLS harus tetap memblokir akses yang tidak sah.

**Yang diverifikasi:**
- Query langsung ke Supabase (tanpa melalui aplikasi) dengan credentials staff tidak bisa mengakses evaluasi staff lain
- Query dengan anon key tidak bisa membaca atau menulis data apapun ke tabel yang dilindungi

---

## 13. Testing Performa Database

### 13.1 Load test query utama

Sebelum release ke production, semua query utama yang didefinisikan di DB-03 section 4 diuji dengan data representatif untuk memverifikasi target performa di DB-03 section 10 tercapai.

**Data test yang diperlukan:**
- Minimal 1.000 evaluasi di database
- Distribusi status evaluasi yang realistis
- Rata-rata 5 vendor per evaluasi
- Minimal 500 dokumen yang sudah diindeks (untuk test RAG query)

**Target yang diverifikasi:**

| Query | Target P95 |
|---|---|
| Daftar evaluasi dengan filter default | < 100ms |
| Detail evaluasi + vendor | < 80ms |
| Hasil evaluasi lengkap (termasuk kualitatif) | < 150ms |
| Status agent (read) | < 50ms |
| Write agent progress | < 30ms |
| RAG hybrid search dengan filter evaluasi_id | < 500ms |

### 13.2 Test index effectiveness

Setiap index yang didefinisikan di DB-01 section 9 diverifikasi menggunakan `EXPLAIN ANALYZE` — memastikan query plan menggunakan index yang diharapkan, bukan sequential scan. Khusus untuk index HNSW pgvector, pastikan query similarity search menggunakan HNSW scan, bukan sequential scan pada tabel `dokumen_chunk`.

### 13.3 Test concurrent write

Simulasi write burst ke tabel `agent_progress` ketika 5 evaluasi diproses bersamaan — dengan 7 agent per evaluasi (35 concurrent writers) — memverifikasi tidak ada deadlock atau penurunan performa yang signifikan.

---

## 14. Pipeline CI/CD Holistik

### 14.1 Dua pipeline yang berbeda

Sistem menggunakan dua pipeline CI sesuai dua track pengerjaan (ADR-036):

**Pipeline `vendor-ai` — Track Fullstack (berjalan di setiap PR):**

Pipeline ini mencakup seluruh monorepo TypeScript — `apps/web` (frontend) dan `apps/api` (BFF) berjalan dalam satu PR karena dikerjakan oleh satu developer Fullstack.

```
apps/web:  Type check → Lint → Unit test → Integration test → Coverage → Build → E2E* → Deploy preview
apps/api:  Type check → Lint → Unit test → Integration test (dengan DB test) → Build
```
*E2E hanya di branch staging dan main

**Pipeline `vendor-ai-agent` — Track AI Engineer (berjalan di setiap PR):**
```
Lint (Pylint) → Type check (mypy) → Unit test (dengan LLM mock) → Integration test
```

### 13.2 Integration test lintas service

Integration test yang melibatkan lebih dari satu service dijalankan di **staging environment** — bukan di CI per-PR, karena membutuhkan semua service berjalan bersamaan.

Trigger: setiap merge ke branch `staging` di salah satu repository.

```
Deploy semua service ke staging
        ↓
Jalankan integration test Next.js → FastAPI
        ↓
Jalankan integration test FastAPI → Supabase
        ↓
Jalankan integration test Supabase Realtime → Frontend
        ↓
Jalankan E2E test full stack
        ↓
Jalankan security test (otorisasi, RLS)
        ↓
Jika semua lulus → staging dianggap siap untuk promotion ke production
```

### 13.3 Gate sebelum merge ke main (production)

Sebelum kode bisa di-merge ke main branch (yang trigger deployment production), semua kondisi berikut harus terpenuhi:
- Semua pipeline CI per-PR lulus
- Integration test di staging lulus
- Performa database dalam batas target (diverifikasi manual atau otomatis)
- Tidak ada security violation baru yang terdeteksi
- Untuk perubahan prompt: evaluasi prompt metric lulus

### 13.4 Notifikasi kegagalan

Kegagalan di pipeline manapun mengirimkan notifikasi segera ke seluruh tim melalui channel yang sudah dikonfigurasi. Tidak ada kegagalan yang diabaikan — setiap kegagalan harus diinvestigasi dan diselesaikan sebelum merge berikutnya.

---

## 15. Restore Test Terjadwal

Sesuai yang didefinisikan di DB-04 section 7.5, restore test dilakukan setiap bulan. Bagian ini mendefinisikan proses dan tanggung jawabnya.

### 14.1 Prosedur restore test

```
Pilih backup yang akan ditest (backup harian terbaru atau backup mingguan)
        ↓
Buat environment restore yang terisolasi (tidak mempengaruhi staging atau production)
        ↓
Jalankan restore dari backup yang dipilih
        ↓
Verifikasi integritas data:
  - Jumlah row per tabel sesuai ekspektasi
  - Relasi antar tabel konsisten (tidak ada foreign key yang broken)
  - RLS masih aktif setelah restore
  - Sample evaluasi dapat dibaca dengan benar
        ↓
Catat hasil dalam test report
        ↓
Hapus environment restore
```

### 14.2 Kriteria pass/fail

**Pass:** Restore selesai dalam RTO yang ditargetkan (< 4 jam untuk backup harian), semua verifikasi integritas data lulus, tidak ada error yang tidak terduga.

**Fail:** Restore tidak selesai dalam RTO, ada data yang hilang atau corrupt, RLS tidak aktif setelah restore, atau ada error yang membutuhkan investigasi.

### 14.3 Tindakan jika fail

Jika restore test gagal, deployment production diblokir sampai masalah diinvestigasi dan diselesaikan. Backup yang gagal di-restore tidak bisa diandalkan sebagai safety net.

### 14.4 Dokumentasi

Setiap restore test menghasilkan laporan yang mencatat: tanggal test, backup yang digunakan, durasi restore, hasil verifikasi, masalah yang ditemukan (jika ada), dan penanda pass/fail. Laporan ini disimpan dan dapat diakses oleh seluruh tim.

---

## 16. Aturan & Larangan

**Dilarang merge kode ke main jika ada test yang gagal** — tidak ada pengecualian. Jika ada test yang dianggap tidak relevan, hapus test tersebut melalui PR yang di-review, jangan skip.

**Dilarang menggunakan LLM sungguhan dalam unit test** — gunakan mock. Selain biaya, LLM call dalam unit test membuat test suite lambat dan tidak reliable.

**Dilarang menggunakan database production untuk test apapun** — selalu gunakan database test yang terisolasi.

**Dilarang membiarkan flaky test lebih dari satu sprint** tanpa investigasi dan perbaikan. Flaky test merusak kepercayaan terhadap seluruh test suite.

**Dilarang deploy ke production tanpa integration test di staging lulus** terlebih dahulu.

**Dilarang melewatkan restore test bulanan** tanpa penjadwalan ulang di minggu yang sama.

**Dilarang mengubah prompt tanpa menjalankan evaluasi prompt metric** sebelum merge ke main.

---

## 17. Catatan untuk Dokumen Lanjutan

### Untuk FE-06 (Testing & QA Frontend)

Komponen baru yang perlu ditambahkan ke test suite frontend: `QualitativeProfileCard`, `PreferenceRecommendationCard`, `ConflictCallout`, `PreferenceInput`. Komponen `AgentProgressPanel` perlu diperbarui untuk menampilkan 7 agent dengan state `waiting`.

### Untuk AI-01 (Agent Orchestration)

Skenario kegagalan rantai antara Qualitative Analyzer dan Preference Matcher (section 7.2) perlu didefinisikan secara eksplisit di AI-01 sebagai bagian dari fallback logic.

### Untuk AI-04 (RAG Specification)

Test kualitas retrieval di section 10.3 membutuhkan dokumen penawaran sintetis yang mencerminkan variasi format dokumen nyata — tabel harga, klausul garansi, section spesifikasi teknis. AI-04 perlu mendefinisikan karakteristik dokumen test yang representatif.

### Untuk SH-02 (Deployment Runbook)

Pipeline CI/CD untuk `vendor-ai-agent` perlu ditambahkan test RAG yang menggunakan Google Gemini API key staging. Ini berbeda dari test lain yang bisa di-mock — perlu konfigurasi khusus di environment CI. Runbook juga perlu mendefinisikan cara setup dan teardown tabel `dokumen_chunk` di environment test.

### Untuk AI-02 (Prompt Library)

Test suite per agent (section 9.1) — termasuk test tambahan untuk Qualitative Analyzer dan Preference Matcher — perlu dibuat dan disimpan bersama file prompt di repository `vendor-ai-agent`.

### Untuk DB-04 (Backup & Retention)

Restore test terjadwal (section 15) perlu dimasukkan ke kalender tim sebagai recurring task.

---

*Dokumen ini adalah living document — strategi testing akan berkembang seiring pertumbuhan sistem dan ditemukannya pola kegagalan baru.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 2.0.0 | 2026-06-11 | Tambah section 10 Testing RAG (indexing, retrieval, kualitas, integrasi chat); perbarui skenario kegagalan orchestration untuk 7 agent; tambah test cases Qualitative Analyzer dan Preference Matcher (9.1); perbarui test scoring untuk agent baru (8.5); perbarui testing ekstraksi dokumen untuk RAG indexing (7.3); perbarui target query performa database untuk RAG hybrid search | — |
| 3.0.0 | 2026-06-12 | Adopsi 4 role (ADR-032): tambah label kepemilikan AI Engineer di header section 7 (Testing FastAPI & Agent), section 8 (Testing Scoring Engine), section 9 (Testing Prompt); perbarui section 14.1 pipeline CI/CD (perbaiki nama pipeline dari nama repo lama ke nama repo baru; tambah label role FE/BE/AI Engineer per pipeline) | — |
| 4.0.0 | 2026-06-13 | Adopsi namespace AI (ADR-035): perbarui tabel referensi section 2 (BE-03/04/05/08/09/10 → AI-01/02/03/04/05/06); perbarui section 17 catatan dokumen lanjutan (referensi ke AI-01, AI-02, AI-04; ganti OpenAI API key → Google Gemini API key di catatan SH-02); adopsi 2 track solo developer (ADR-036): perbarui section 14.1 (dari tiga pipeline → dua pipeline, label FE/BE Engineer dihapus, digabung menjadi pipeline Track Fullstack) | — |
