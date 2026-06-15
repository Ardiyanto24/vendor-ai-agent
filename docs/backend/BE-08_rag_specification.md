# BE-08 — RAG Specification

**Project:** AI Vendor Selection System  
**Dokumen:** BE-08 — RAG (Retrieval-Augmented Generation) Specification  
**Versi:** 2.0.0  
**Tanggal:** 2026-06-13  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Mengapa RAG Diperlukan](#3-mengapa-rag-diperlukan)
4. [Gambaran Arsitektur RAG](#4-gambaran-arsitektur-rag)
5. [Keputusan Teknologi](#5-keputusan-teknologi)
6. [Pipeline Indexing — Saat Upload Dokumen](#6-pipeline-indexing--saat-upload-dokumen)
7. [Chunking Strategy](#7-chunking-strategy)
8. [Pipeline Retrieval — Saat Chat](#8-pipeline-retrieval--saat-chat)
9. [Integrasi dengan AI Chat Panel](#9-integrasi-dengan-ai-chat-panel)
10. [Isolasi Data & Keamanan](#10-isolasi-data--keamanan)
11. [Skema Data Vector Store](#11-skema-data-vector-store)
12. [Penanganan Error & Edge Case](#12-penanganan-error--edge-case)
13. [Aturan & Larangan](#13-aturan--larangan)
14. [Catatan untuk Dokumen Lanjutan](#14-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **arsitektur dan mekanisme RAG (Retrieval-Augmented Generation)** yang memungkinkan AI Chat Panel menjawab pertanyaan berbasis isi dokumen penawaran vendor secara akurat — tanpa harus mengirimkan seluruh dokumen ke LLM setiap kali user bertanya.

Dokumen ini menjawab pertanyaan: bagaimana dokumen penawaran diproses dan diindeks, bagaimana potongan relevan diambil saat user bertanya, dan bagaimana konteks yang diambil diintegrasikan ke dalam respons AI Chat Panel.

Dokumen ini **tidak** mendefinisikan implementasi kode — itu diserahkan ke engineer. Dokumen ini mendefinisikan **apa** yang dilakukan sistem dan **mengapa** demikian.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| BE-03 | Agent Orchestration | Pipeline ekstraksi dokumen yang diperluas untuk indexing |
| BE-04 | Prompt Library | Prompt AI Chat Panel yang mengonsumsi konteks RAG |
| BE-07 | Integration Spec | Integrasi OpenAI Embedding API dan pgvector |
| DB-01 | Data Model & ERD | Tabel vector store dan relasi ke dokumen_upload |
| FE-03 | Page & User Flow | AI Chat Panel di halaman Hasil (P-05) sebagai konsumen utama |

---

## 3. Mengapa RAG Diperlukan

### 3.1 Keterbatasan pendekatan sebelumnya

Tanpa RAG, AI Chat Panel hanya memiliki akses ke data terstruktur hasil ekstraksi — field-field yang sudah terdefinisi seperti harga, garansi, dan spesifikasi yang ditawarkan. Ini cukup untuk pertanyaan tingkat tinggi, tetapi tidak cukup untuk pertanyaan yang membutuhkan detail dari isi dokumen penawaran asli.

Contoh pertanyaan yang tidak bisa dijawab tanpa RAG:

- *"Vendor A menyebutkan penalti keterlambatan delivery berapa persen per hari?"*
- *"Bandingkan klausul force majeure antara vendor B dan vendor C."*
- *"Vendor mana yang menawarkan training on-site gratis?"*

Pertanyaan-pertanyaan seperti ini membutuhkan akses ke teks asli dokumen penawaran — informasi yang tidak selalu masuk ke field ekstraksi terstruktur.

### 3.2 Mengapa tidak kirim seluruh dokumen ke LLM

Mengirimkan seluruh dokumen penawaran ke LLM setiap kali ada pertanyaan adalah pendekatan yang tidak scalable:

**Biaya token membengkak.** Satu dokumen penawaran rata-rata 20–50 halaman, atau sekitar 10.000–25.000 token. Dengan 5 vendor dan pertanyaan yang sering, biaya bisa 10–50x lebih tinggi dari yang diestimasi.

**Context window terbatas.** Dengan 5–10 vendor, mengirim semua dokumen sekaligus bisa melebihi context window model bahkan untuk model dengan window yang besar.

**Kualitas respons menurun.** LLM bekerja lebih akurat dengan konteks yang relevan dan terfokus dibanding dengan "lautan teks" yang harus diproses sekaligus — fenomena yang dikenal sebagai "lost in the middle."

### 3.3 RAG sebagai solusi

RAG memungkinkan sistem mengambil hanya potongan teks yang paling relevan dengan pertanyaan user — biasanya 3–5 potongan dari ribuan — lalu menyertakannya sebagai konteks ke LLM. Hasilnya: biaya terkontrol, respons akurat, dan tidak ada batasan jumlah dokumen yang bisa diindeks.

---

## 4. Gambaran Arsitektur RAG

Sistem RAG terbagi menjadi dua pipeline yang berjalan di waktu yang berbeda:

```
═══════════════════════════════════════════════════════
PIPELINE INDEXING (saat user upload dokumen di P-03)
═══════════════════════════════════════════════════════

File PDF diupload ke Supabase Storage
        ↓
FastAPI mengunduh file & mengekstrak teks
(bersamaan dengan proses ekstraksi field terstruktur)
        ↓
Teks dibagi menjadi chunk hierarkis
(section → paragraph, tabel sebagai atomic unit)
        ↓
Setiap child chunk di-embed via Google Gemini Embedding API
→ menghasilkan vektor 768 dimensi
        ↓
Chunk + vektor + metadata disimpan ke pgvector
di Supabase (tabel dokumen_chunk)
        ↓
Status indexing diperbarui di tabel dokumen_upload


═══════════════════════════════════════════════════════
PIPELINE RETRIEVAL (saat user bertanya di AI Chat Panel)
═══════════════════════════════════════════════════════

Pertanyaan user diterima oleh FastAPI /v1/chat/stream
        ↓
Query expansion: LLM merewrite pertanyaan menjadi
query yang lebih optimal untuk retrieval
        ↓
Query di-embed via Google Gemini Embedding API
        ↓
Hybrid search di pgvector:
  - Vector similarity search (cosine distance)
  - Keyword search (BM25/full-text search PostgreSQL)
  → Hasil digabung dengan RRF (Reciprocal Rank Fusion)
        ↓
Top-5 child chunk teridentifikasi
→ Ambil parent chunk masing-masing untuk konteks lebih luas
        ↓
Parent chunks + metadata (nama vendor, nomor halaman)
diinjeksikan ke context LLM
        ↓
LLM menghasilkan respons dengan konteks dokumen nyata
```

---

## 5. Keputusan Teknologi

### 5.1 Vector store: pgvector di Supabase

pgvector adalah ekstensi PostgreSQL yang menambahkan tipe data `vector` dan operator similarity search. Dipilih karena terintegrasi langsung dengan Supabase yang sudah menjadi platform data terpadu sistem ini.

**Mengapa pgvector, bukan dedicated vector DB (Qdrant, Pinecone, Weaviate):**

Tidak ada infrastruktur baru yang perlu di-deploy, di-monitor, dan dibayar terpisah. RLS Supabase yang sudah dikonfigurasi untuk tabel lain bisa langsung diterapkan ke tabel vector — isolasi data per user dan per evaluasi otomatis terjaga. Query bisa menggabungkan similarity search dengan filter relasional dalam satu transaksi SQL tanpa network hop tambahan.

Untuk skala MVP dengan maksimum 10 vendor × 50 halaman per dokumen, pgvector lebih dari cukup secara performa.

### 5.2 Embedding model: Google Gemini `text-embedding-004`

Model embedding dari Google yang menghasilkan vektor **768 dimensi**.

**Mengapa `text-embedding-004`:**

Model stabil dari Google dengan kualitas retrieval yang baik untuk dokumen teks berbahasa Indonesia dan Inggris. Dimensi 768 lebih efisien dari alternatif berdimensi lebih tinggi (OpenAI `text-embedding-3-small` menghasilkan 1.536 dimensi) — menghemat storage vector dan mempercepat similarity search tanpa penurunan kualitas retrieval yang signifikan untuk skala MVP. Detail keputusan ada di ADR-034 (SH-01).

**API key:** Sistem menggunakan dua API key terpisah — `OPENROUTER_API_KEY` untuk LLM calls dan `GOOGLE_API_KEY` untuk embedding calls. Keduanya disimpan sebagai environment variable di FastAPI service dan tidak pernah diekspos ke frontend.

### 5.3 Hybrid search: vector + BM25

Retrieval menggunakan kombinasi dua metode pencarian:

**Vector similarity search** menemukan chunk yang secara semantik mirip dengan pertanyaan — cocok untuk pertanyaan konseptual dan parafrase.

**BM25 (full-text search)** menemukan chunk yang mengandung kata kunci yang sama persis — penting untuk dokumen procurement yang banyak mengandung istilah teknis spesifik, kode produk, angka, dan nama merek yang mungkin tidak tertangkap dengan baik oleh vector search.

Hasil kedua metode digabungkan menggunakan **Reciprocal Rank Fusion (RRF)** — algoritma sederhana yang menggabungkan ranking dari dua sumber tanpa membutuhkan kalibrasi bobot.

PostgreSQL sudah mendukung full-text search secara native via `tsvector` dan `tsquery` — tidak perlu library tambahan untuk BM25.

### 5.4 Query expansion

Sebelum query di-embed untuk retrieval, LLM diminta untuk merewrite pertanyaan user menjadi query yang lebih optimal.

**Contoh:**

User bertanya: *"vendor mana yang paling bagus garansinya?"*

LLM merewrite menjadi: *"garansi produk masa berlaku periode tahun bulan layanan purna jual warranty service level agreement SLA"*

Query yang diperluas ini mengandung sinonim dan istilah terkait yang meningkatkan kemungkinan menemukan chunk relevan meskipun dokumen menggunakan terminologi yang berbeda dari pertanyaan user.

Query expansion menggunakan LLM yang sama dengan chat — call terpisah yang cepat sebelum retrieval dimulai.

---

## 6. Pipeline Indexing — Saat Upload Dokumen

### 6.1 Trigger dan timing

Pipeline indexing dipicu **saat user mengupload dokumen penawaran** di P-03, bersamaan dengan proses ekstraksi field terstruktur yang sudah terdefinisi di BE-03 section 9.

Kedua proses — ekstraksi field terstruktur dan indexing RAG — berjalan dalam satu pipeline async yang sama. User melihat satu status `extracting` yang merepresentasikan keduanya. Status `done` baru diberikan setelah keduanya selesai.

### 6.2 Langkah-langkah pipeline indexing

```
1. Unduh file dari Supabase Storage URL

2. Ekstraksi teks dari PDF
   → Gunakan library pdfminer.six atau pdfplumber
   → Preserve struktur: deteksi heading, tabel, list, paragraf
   → Output: dokumen terstruktur dengan metadata per elemen
     (tipe elemen, nomor halaman, posisi dalam dokumen)

3. Chunking hierarkis (detail di section 7)
   → Hasilkan parent chunks dan child chunks

4. Embedding child chunks
   → Batch call ke OpenAI Embedding API
   → Maksimum 2048 token per chunk untuk batching efisien
   → Retry dengan exponential backoff jika rate limit tercapai

5. Simpan ke tabel dokumen_chunk di Supabase
   → Satu row per child chunk
   → Menyertakan: teks child, teks parent, vektor, metadata
   → Bulk insert untuk efisiensi

6. Buat full-text search index
   → Kolom tsvector di-populate dari teks child chunk
   → PostgreSQL mengelola index ini secara otomatis

7. Update status di tabel dokumen_upload
   → Field indexing_status: 'done' atau 'failed'
   → Field chunk_count: jumlah chunk yang berhasil diindeks
```

### 6.3 Estimasi waktu dan biaya indexing

Untuk dokumen 20 halaman (~10.000 token):
- Ekstraksi teks: ~2–5 detik
- Chunking: < 1 detik
- Embedding (batch): ~1–3 detik
- Database insert: ~1 detik
- **Total: ~5–10 detik** (berjalan paralel dengan ekstraksi field terstruktur)
- **Biaya embedding: < $0.001** per dokumen

---

## 7. Chunking Strategy

### 7.1 Prinsip hierarchical parent-child chunking

Sistem menggunakan pendekatan dua lapisan:

**Child chunk** — unit kecil untuk retrieval yang presisi. Ukuran target 300–500 token. Ini yang di-embed dan dicari saat retrieval.

**Parent chunk** — unit besar untuk konteks LLM. Ukuran target 1.000–1.500 token. Biasanya satu section penuh. Ini yang dikirim ke LLM setelah child chunk ditemukan.

**Mengapa dua lapisan:** Child chunk kecil memastikan retrieval presisi — vektor dari chunk kecil lebih "terfokus" secara semantik. Parent chunk besar memastikan LLM mendapat konteks yang cukup untuk menjawab dengan akurat — informasi yang dibutuhkan sering tersebar dalam beberapa paragraf.

### 7.2 Hierarki chunking

```
Dokumen PDF
└── Section (H1/H2) → menjadi Parent Chunk
    ├── Paragraf 1 → menjadi Child Chunk A
    ├── Paragraf 2 → menjadi Child Chunk B
    ├── Tabel → menjadi Child Chunk C (ATOMIC — tidak dipecah)
    └── Paragraf 3 → menjadi Child Chunk D
```

Setiap child chunk menyimpan referensi ke parent chunk-nya. Saat child chunk ditemukan saat retrieval, sistem mengambil parent-nya untuk dikirim ke LLM.

### 7.3 Aturan chunking per tipe konten

**Paragraf naratif:**
- Jika paragraf < 500 token: satu paragraf = satu child chunk
- Jika paragraf > 500 token: pecah di boundary kalimat, overlap 50 token antar child chunk untuk menjaga kontinuitas

**Tabel (harga, spesifikasi teknis, perbandingan):**
- Selalu diperlakukan sebagai satu unit atomic — tidak pernah dipotong di tengah
- Jika tabel > 1.500 token: pertahankan sebagai satu chunk (melebihi target adalah pengecualian yang diterima)
- Header tabel selalu disertakan dalam chunk agar konteks kolom tidak hilang
- Metadata ditambahkan: `tipe: "tabel"`, `judul_tabel` jika ada

**Daftar (list item, bullet points):**
- Daftar pendek (< 10 item): satu list = satu child chunk
- Daftar panjang (> 10 item): pecah per 10 item dengan header list diulang di setiap chunk

**Header dan metadata dokumen (halaman pertama):**
- Nama vendor, tanggal penawaran, nomor dokumen: disimpan sebagai metadata global, bukan chunk terpisah

### 7.4 Metadata per chunk

Setiap chunk (child maupun parent) menyimpan metadata yang memungkinkan attribution yang akurat dalam respons AI:

| Metadata | Tipe | Keterangan |
|---|---|---|
| `evaluasi_id` | UUID | Untuk isolasi data per evaluasi |
| `vendor_id` | UUID | Untuk filter per vendor |
| `dokumen_upload_id` | UUID | Referensi ke file asli |
| `halaman` | Integer | Nomor halaman dalam dokumen asli |
| `tipe_konten` | Enum | `paragraf`, `tabel`, `list`, `header` |
| `posisi_section` | Text | Judul section/heading induk |
| `chunk_index` | Integer | Urutan chunk dalam dokumen |
| `is_parent` | Boolean | True untuk parent chunk |
| `parent_chunk_id` | UUID | Referensi ke parent (hanya untuk child) |

---

## 8. Pipeline Retrieval — Saat Chat

### 8.1 Trigger retrieval

Retrieval dipicu **setiap kali user mengirim pesan di AI Chat Panel** saat berada di halaman yang memiliki konteks evaluasi aktif — yaitu P-04 (Processing) dan P-05 (Hasil Rekomendasi).

Di halaman lain (Dashboard, P-03, P-07, P-08), RAG tidak diperlukan karena tidak ada dokumen vendor spesifik yang relevan — AI Chat Panel menggunakan context injection berbasis data terstruktur seperti yang sudah terdefinisi di BE-04 section 6.3.

### 8.2 Langkah-langkah pipeline retrieval

```
1. Terima pesan user

2. Query expansion (Claude Haiku)
   → Prompt: "Rewrite pertanyaan berikut menjadi query
     pencarian yang optimal untuk menemukan informasi
     relevan dalam dokumen penawaran vendor. Sertakan
     sinonim dan istilah terkait. Pertanyaan: [pesan user]"
   → Output: query string yang diperluas
   → Timeout: 3 detik — jika gagal, gunakan pesan asli

3. Embed query yang sudah diperluas
   → OpenAI text-embedding-3-small
   → Output: vektor 1536 dimensi

4. Hybrid search di tabel dokumen_chunk
   Filter wajib: evaluasi_id = [evaluasi aktif user]

   4a. Vector similarity search:
       SELECT * FROM dokumen_chunk
       WHERE evaluasi_id = $1
       ORDER BY embedding <=> $2  -- cosine distance
       LIMIT 20

   4b. Full-text search:
       SELECT * FROM dokumen_chunk
       WHERE evaluasi_id = $1
       AND teks_chunk @@ plainto_tsquery('indonesian', $3)
       LIMIT 20

   4c. Gabungkan dengan RRF:
       Score RRF = Σ 1/(k + rank_i) untuk setiap sumber
       k = 60 (konstanta standar RRF)
       Ambil top-5 child chunk berdasarkan RRF score

5. Ambil parent chunk untuk setiap child chunk yang ditemukan
   → Jika beberapa child berasal dari parent yang sama,
     parent hanya disertakan sekali (deduplication)
   → Maksimum 5 parent chunk yang berbeda

6. Format context untuk LLM
   → Setiap parent chunk diformat dengan metadata:
     [Vendor: {nama_vendor} | Halaman: {halaman} | Section: {posisi_section}]
     {teks_parent_chunk}
   → Semua context digabung dengan separator yang jelas

7. Injeksikan context ke prompt LLM
   → Context ditempatkan sebelum riwayat percakapan
   → LLM diminta untuk menyebutkan sumber (nama vendor
     dan halaman) saat menjawab pertanyaan berbasis dokumen
```

### 8.3 Batas context yang diinjeksikan

Maksimum 5 parent chunk dengan total tidak lebih dari 6.000 token diinjeksikan sebagai context RAG. Ini menjaga context window LLM tetap efisien dan biaya per chat tetap terkontrol.

Jika 5 parent chunk melebihi 6.000 token, chunk dengan RRF score terendah dipotong hingga batas terpenuhi.

### 8.4 Fallback jika tidak ada chunk relevan

Jika hybrid search tidak menemukan chunk yang cukup relevan (semua RRF score di bawah threshold 0.3), retrieval dianggap tidak berhasil. Sistem tetap menjawab pertanyaan user menggunakan data terstruktur yang tersedia (skor TOPSIS, reasoning naratif), tanpa context dokumen mentah, dan AI mengakui keterbatasan ini dalam responnya.

---

## 9. Integrasi dengan AI Chat Panel

### 9.1 Modifikasi sistem prompt

Saat RAG context tersedia, system prompt AI Chat Panel (BE-04 section 6) diperluas dengan blok khusus:

```
[KONTEKS DOKUMEN PENAWARAN]
Berikut adalah kutipan relevan dari dokumen penawaran
vendor yang berkaitan dengan pertanyaan user. Gunakan
informasi ini untuk memberikan jawaban yang akurat dan
spesifik. Selalu sebutkan nama vendor dan nomor halaman
saat merujuk informasi dari dokumen.

{formatted_rag_context}

[AKHIR KONTEKS DOKUMEN]
```

Blok ini ditempatkan setelah context halaman (BE-04 section 6.3) dan sebelum riwayat percakapan.

### 9.2 Instruksi attribution dalam respons

LLM diminta untuk selalu menyebutkan sumber saat menjawab pertanyaan yang berbasis dokumen — misalnya: *"Menurut dokumen penawaran Vendor A halaman 8, masa garansi yang ditawarkan adalah 2 tahun termasuk spare part."*

Ini penting untuk audit trail — procurement staff harus bisa memverifikasi klaim AI dengan kembali ke dokumen asli.

### 9.3 Kapan RAG aktif vs tidak aktif

| Halaman | RAG aktif? | Alasan |
|---|---|---|
| P-04 (Processing) | Ya | Dokumen sudah diindeks, user mungkin bertanya tentang vendor |
| P-05 (Hasil) | Ya | Halaman utama untuk analisis mendalam per vendor |
| P-02 (Dashboard) | Tidak | Tidak ada evaluasi spesifik yang aktif |
| P-03 (Buat Evaluasi) | Tidak | Dokumen belum tentu sudah diindeks semua |
| P-07 (Approval) | Ya | Manager mungkin bertanya detail sebelum memutuskan |
| P-08 (Settings) | Tidak | Tidak relevan dengan dokumen vendor |

---

## 10. Isolasi Data & Keamanan

### 10.1 Isolasi per evaluasi

Setiap query retrieval **wajib** menyertakan filter `evaluasi_id` — tidak boleh ada retrieval lintas evaluasi. Ini memastikan:

- Staff A tidak bisa mendapatkan informasi dari dokumen evaluasi Staff B
- Pertanyaan tentang "vendor A" hanya mencari dalam evaluasi yang sedang aktif, bukan evaluasi lain yang kebetulan punya vendor dengan nama sama

Filter ini diterapkan di level query SQL, bukan hanya di level aplikasi.

### 10.2 Row Level Security (RLS)

Tabel `dokumen_chunk` menerapkan RLS yang sama dengan tabel `dokumen_upload` — akses mengikuti akses ke evaluasi induknya. Jika user tidak punya akses ke evaluasi tertentu, mereka tidak bisa mengakses chunk dari dokumen evaluasi tersebut meskipun tahu `evaluasi_id`-nya.

### 10.3 API key embedding tidak diekspos

`GOOGLE_API_KEY` untuk embedding hanya ada di FastAPI service — tidak pernah dikirim ke frontend, tidak pernah di-log, dan tidak pernah masuk ke respons API. Ini mengikuti prinsip yang sama dengan `OPENROUTER_API_KEY`.

---

## 11. Skema Data Vector Store

### 11.1 Tabel `dokumen_chunk`

Tabel ini menyimpan semua chunk dari semua dokumen penawaran yang sudah diindeks.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `evaluasi_id` | UUID | Tidak | Foreign key ke `evaluasi.id` — untuk isolasi |
| `vendor_id` | UUID | Tidak | Foreign key ke `vendor.id` |
| `dokumen_upload_id` | UUID | Tidak | Foreign key ke `dokumen_upload.id` |
| `is_parent` | Boolean | Tidak | True = parent chunk, False = child chunk |
| `parent_chunk_id` | UUID | Ya | Foreign key ke `dokumen_chunk.id` — null untuk parent |
| `teks_chunk` | Text | Tidak | Isi teks chunk |
| `embedding` | vector(768) | Ya | Vektor embedding dari Google Gemini text-embedding-004 (null untuk parent chunk) |
| `teks_search` | tsvector | Ya | Full-text search index (null untuk parent chunk) |
| `halaman` | Integer | Tidak | Nomor halaman dalam dokumen asli |
| `tipe_konten` | Enum | Tidak | `paragraf`, `tabel`, `list`, `header` |
| `posisi_section` | Text | Ya | Judul section/heading induk |
| `chunk_index` | Integer | Tidak | Urutan chunk dalam dokumen |
| `token_count` | Integer | Tidak | Jumlah token (untuk monitoring batas context) |
| `created_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | Soft delete mengikuti evaluasi induk |

**Mengapa parent chunk tidak memiliki embedding:** Parent chunk tidak pernah dicari secara langsung — ia hanya diambil setelah child chunk ditemukan. Tidak perlu embedding berarti menghemat biaya dan storage.

**Mengapa `teks_search` hanya di child chunk:** Full-text search juga hanya dilakukan pada child chunk, konsisten dengan vector search. Parent chunk hanya berperan sebagai "konteks pengiriman."

### 11.2 Index yang diperlukan

| Index | Tipe | Alasan |
|---|---|---|
| `dokumen_chunk(evaluasi_id)` | B-tree | Filter wajib di setiap query retrieval |
| `dokumen_chunk(vendor_id)` | B-tree | Filter opsional saat retrieval per vendor |
| `dokumen_chunk(embedding)` | HNSW (pgvector) | Approximate nearest neighbor search |
| `dokumen_chunk(teks_search)` | GIN | Full-text search PostgreSQL |
| `dokumen_chunk(parent_chunk_id)` | B-tree | Lookup parent setelah child ditemukan |

**HNSW vs IVFFlat untuk vector index:** HNSW (Hierarchical Navigable Small World) dipilih karena query-time-nya lebih cepat dan tidak membutuhkan training data awal seperti IVFFlat. Untuk skala MVP, HNSW dengan parameter default (`m=16, ef_construction=64`) sudah cukup.

---

## 12. Penanganan Error & Edge Case

### 12.1 Dokumen tidak bisa diekstrak teksnya

Beberapa PDF menggunakan text layer yang terenkripsi, atau isinya adalah scan gambar tanpa OCR. Dalam kasus ini:

- Ekstraksi field terstruktur menggunakan vision capability LLM (mengirim halaman sebagai gambar) — ini sudah terdefinisi di BE-03
- Indexing RAG **tidak dilakukan** karena tidak ada teks yang bisa di-chunk
- Field `indexing_status` diset ke `skipped_no_text`
- User diinformasikan bahwa AI Chat tidak bisa menjawab pertanyaan berbasis dokumen untuk vendor ini

### 12.2 Google Gemini Embedding API tidak tersedia

Jika Google Gemini API mengalami downtime saat proses indexing:

- Ekstraksi field terstruktur tetap berjalan (tidak bergantung Google Gemini)
- Indexing ditandai sebagai `failed` dan dapat di-retry secara manual
- Sistem tetap bisa berfungsi tanpa RAG — AI Chat Panel menggunakan data terstruktur
- Evaluasi tidak diblokir karena kegagalan indexing

### 12.3 Dokumen sangat panjang (> 100 halaman)

Jika jumlah token setelah chunking melebihi 100.000 token per dokumen:

- Indexing tetap dilakukan, tetapi dengan prioritas: halaman awal (profil perusahaan, ringkasan eksekutif) dan halaman dengan heading utama diindeks lebih dulu
- User diberi peringatan bahwa dokumen sangat panjang dan beberapa bagian mungkin tidak bisa dijawab oleh AI
- Batas 100 halaman direkomendasikan sebagai best practice dalam dokumentasi upload

### 12.4 Pertanyaan tidak relevan dengan dokumen

Jika user bertanya sesuatu yang tidak berkaitan dengan isi dokumen (misalnya pertanyaan umum tentang procurement), RAG retrieval kemungkinan menghasilkan chunk dengan RRF score rendah. Dalam kasus ini sistem tetap menjawab menggunakan pengetahuan LLM dan data terstruktur — tidak memaksakan referensi ke dokumen yang tidak relevan.

---

## 13. Aturan & Larangan

**Dilarang retrieval lintas evaluasi.** Setiap query ke tabel `dokumen_chunk` harus selalu menyertakan filter `evaluasi_id`. Tidak ada pengecualian — termasuk untuk admin atau testing.

**Dilarang embedding parent chunk.** Parent chunk tidak perlu di-embed — ini pemborosan biaya. Hanya child chunk yang di-embed.

**Dilarang memotong tabel di tengah.** Tabel harga, spesifikasi teknis, dan tabel apapun dalam dokumen penawaran harus selalu menjadi satu chunk atomic. Tabel yang terpotong menghasilkan informasi yang menyesatkan.

**Dilarang menggunakan RAG context sebagai satu-satunya sumber kebenaran.** AI Chat Panel harus selalu mengintegrasikan informasi dari RAG context dengan data terstruktur hasil evaluasi (skor TOPSIS, reasoning agent) — bukan menggantikannya.

**Dilarang menyimpan GOOGLE_API_KEY di kode atau log.** API key embedding diperlakukan sama seriusnya dengan API key LLM — disimpan di environment variable dan tidak pernah muncul di output apapun.

**Dilarang indexing ulang tanpa menghapus chunk lama.** Jika user mengupload ulang dokumen yang sama, chunk lama harus dihapus (soft delete) sebelum indexing baru dimulai untuk menghindari duplikasi dalam retrieval.

---

## 14. Catatan untuk Dokumen Lanjutan

### Untuk BE-03 (Agent Orchestration)

Pipeline ekstraksi dokumen di section 9 perlu diperluas untuk mencakup indexing RAG. Kedua proses — ekstraksi field terstruktur dan chunking/embedding — berjalan dalam pipeline yang sama dan statusnya dilaporkan bersama ke tabel `dokumen_upload`.

### Untuk BE-04 (Prompt Library)

System prompt AI Chat Panel perlu diperbarui untuk mengakomodasi blok context RAG yang dijelaskan di section 9.1. Prompt juga perlu menyertakan instruksi attribution — LLM harus selalu menyebutkan nama vendor dan nomor halaman saat merujuk informasi dari dokumen.

### Untuk BE-07 (Integration Spec)

Section integrasi Google Gemini Embedding API sudah ditambahkan di BE-07 v3.0.0 — mencakup API key management, rate limit handling, batching strategy, dan estimasi biaya per evaluasi.

### Untuk DB-01 (Data Model & ERD)

Tabel `dokumen_chunk` perlu ditambahkan ke data model dengan semua kolom, relasi, RLS policy, dan index yang terdefinisi di section 11. Urutan dependency dalam DB-02 juga perlu diperbarui — `dokumen_chunk` bergantung pada `dokumen_upload` dan `vendor`.

### Untuk SH-04 (Cost & Usage Guide)

Estimasi biaya perlu diperbarui untuk mencerminkan biaya embedding Google Gemini — meskipun sangat kecil (< $0.005 per evaluasi), perlu terdokumentasi untuk transparansi.

### Untuk SH-03 (Testing Strategy)

Testing RAG perlu mencakup: akurasi retrieval (apakah chunk yang diambil relevan dengan pertanyaan), isolasi data (chunk dari evaluasi lain tidak bocor), dan fallback behavior saat retrieval gagal.

---

*Dokumen ini adalah living document — parameter chunking dan retrieval dapat disesuaikan berdasarkan hasil evaluasi kualitas jawaban AI Chat Panel.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-11 | Versi awal | — |
| 2.0.0 | 2026-06-13 | Ganti embedding model dari OpenAI text-embedding-3-small ke Google Gemini text-embedding-004; ubah dimensi vektor dari 1536 ke 768 di diagram pipeline, section 5.2, skema tabel, dan semua referensi terkait; perbarui section 10.3, 12.2, 13, dan 14 | — |
