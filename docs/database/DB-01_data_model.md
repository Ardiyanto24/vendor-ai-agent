# DB-01 — Data Model & ERD Specification

**Project:** AI Vendor Selection System  
**Dokumen:** DB-01 — Data Model & ERD  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-13  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Keputusan Desain Database](#3-keputusan-desain-database)
4. [Konvensi Umum](#4-konvensi-umum)
5. [Gambaran Entitas & Relasi](#5-gambaran-entitas--relasi)
6. [Definisi Tabel](#6-definisi-tabel)
7. [Relasi Antar Tabel](#7-relasi-antar-tabel)
8. [Aturan Bisnis di Level Database](#8-aturan-bisnis-di-level-database)
9. [Strategi Indexing](#9-strategi-indexing)
10. [Row Level Security (RLS)](#10-row-level-security-rls)
11. [Catatan untuk Dokumen Lanjutan](#11-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **apa saja entitas data** yang dibutuhkan sistem, **bagaimana relasi antar entitas**, dan **mengapa struktur ini dirancang demikian**.

Dokumen ini menjadi acuan bagi database engineer dalam membuat skema, bagi backend engineer dalam memahami struktur data yang tersedia, dan bagi semua pihak dalam memastikan tidak ada data penting yang terlewat dimodelkan.

Dokumen ini **tidak** mendefinisikan sintaks SQL, migration script, atau detail implementasi teknis lainnya — itu diserahkan ke engineer.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| BE-02 | API Contract | Endpoint yang mengonsumsi dan memodifikasi data |
| AI-01 | Agent Orchestration | Proses yang menulis data progress agent |
| AI-03 | Scoring Engine | Proses yang menghasilkan data hasil evaluasi |
| AI-05 | RAG Specification | Tabel `dokumen_chunk` yang didefinisikan di sini |
| DB-02 | Migration Strategy | Strategi migrasi skema database |
| DB-03 | Query & Performance | Pola query dan strategi optimasi |
| DB-04 | Backup & Retention | Kebijakan backup dan retensi data |

---

## 3. Keputusan Desain Database

### 3.1 Platform: Supabase (PostgreSQL)

Supabase dipilih karena menyediakan tiga kapabilitas dalam satu platform yang semuanya dibutuhkan sistem ini: PostgreSQL sebagai database relasional yang handal, Storage untuk file dokumen penawaran vendor, dan Realtime untuk broadcast perubahan data ke frontend tanpa infrastruktur tambahan.

### 3.2 Pendekatan: Semi-relasional

Sebagian besar data disimpan dalam tabel relasional yang ternormalisasi. Pengecualian diberikan untuk data yang strukturnya dinamis dan bergantung pada konfigurasi — khususnya skor per kriteria dan data agregat vendor dari agent.

**Mengapa skor per kriteria disimpan sebagai JSON column:** Jumlah dan nama kriteria dapat berbeda per kategori pengadaan dan dapat berubah seiring waktu melalui konfigurasi manager. Menyimpan setiap kriteria sebagai kolom tersendiri akan membutuhkan perubahan skema setiap kali konfigurasi berubah. JSON column memberikan fleksibilitas ini tanpa mengorbankan kemampuan query PostgreSQL yang tetap bisa mengakses nilai di dalam JSON.

### 3.3 Primary key: UUID

Semua tabel menggunakan UUID sebagai primary key. UUID tidak bisa ditebak sehingga mencegah enumeration attack (user mencoba-coba ID lain), konsisten dengan standar Supabase Auth yang juga menggunakan UUID, dan aman untuk diekspos di URL publik.

### 3.4 Soft delete

Data yang "dihapus" user tidak benar-benar dihapus dari database, melainkan ditandai dengan mengisi kolom `deleted_at`. Data dengan `deleted_at` tidak null diperlakukan sebagai tidak ada oleh aplikasi.

**Mengapa soft delete:** Data evaluasi memiliki nilai audit — perusahaan mungkin perlu menelusuri kembali keputusan pengadaan di masa lalu untuk keperluan audit internal atau compliance. Hard delete akan menghilangkan jejak ini secara permanen.

---

## 4. Konvensi Umum

### 4.1 Penamaan

Semua nama tabel menggunakan **snake_case** dan **bentuk tunggal** (bukan plural). Contoh: `evaluasi`, `vendor`, bukan `evaluasis` atau `vendors`.

Semua nama kolom menggunakan **snake_case**. Contoh: `created_at`, `budget_max`, `vendor_id`.

### 4.2 Kolom standar di semua tabel

Setiap tabel memiliki empat kolom standar berikut:

| Kolom | Tipe | Keterangan |
|---|---|---|
| `id` | UUID | Primary key, di-generate otomatis |
| `created_at` | Timestamp with timezone | Waktu record dibuat, di-set otomatis |
| `updated_at` | Timestamp with timezone | Waktu record terakhir diperbarui, di-update otomatis |
| `deleted_at` | Timestamp with timezone | Null berarti aktif, terisi berarti sudah dihapus (soft delete) |

### 4.3 Timestamp

Semua timestamp disimpan dalam timezone UTC. Konversi ke timezone lokal adalah tanggung jawab frontend.

### 4.4 Nilai uang

Semua nilai uang disimpan sebagai integer dalam satuan rupiah (IDR) tanpa desimal, untuk menghindari masalah presisi floating-point.

---

## 5. Gambaran Entitas & Relasi

Sistem memiliki sepuluh entitas utama yang saling berelasi:

```
user
 │
 │ membuat (1 ke banyak)
 ▼
evaluasi ──────────────────── konfigurasi_kriteria
 │                               (per kategori pengadaan)
 │ memiliki (1 ke banyak)
 ▼
vendor
 │
 │ memiliki (1 ke banyak)
 ▼
dokumen_upload
 │
 │ menghasilkan chunk untuk RAG
 ▼
dokumen_chunk  (child & parent chunks untuk RAG)

evaluasi
 │
 │ menghasilkan (1 ke 1)
 ▼
hasil_evaluasi
 │
 │ berisi banyak
 ▼
hasil_vendor  (skor tiap vendor)

evaluasi
 │
 │ memiliki banyak
 ▼
agent_progress  (satu row per agent per evaluasi — 7 agent)

evaluasi
 │
 │ memiliki (1 ke 1, saat di-approve/reject)
 ▼
approval_log
```

**Sepuluh tabel:**

| Tabel | Merepresentasikan |
|---|---|
| `user` | Pengguna aplikasi (staff dan manager) |
| `evaluasi` | Satu proses evaluasi vendor |
| `vendor` | Satu vendor kandidat dalam satu evaluasi |
| `dokumen_upload` | Dokumen penawaran yang diupload per vendor |
| `dokumen_chunk` | Chunk teks terindeks untuk RAG dari dokumen penawaran |
| `agent_progress` | Status dan progress tiap sub-agent per evaluasi (7 agent) |
| `hasil_evaluasi` | Output scoring keseluruhan per evaluasi |
| `hasil_vendor` | Skor detail per vendor dalam satu evaluasi |
| `konfigurasi_kriteria` | Bobot dan threshold kriteria per kategori pengadaan |
| `approval_log` | Catatan keputusan approval per evaluasi |

---

## 6. Definisi Tabel

---

### 6.1 Tabel `user`

**Tujuan:** Menyimpan data pengguna aplikasi. Tabel ini bersanding dengan tabel `auth.users` milik Supabase Auth — tabel ini menyimpan data profil aplikasi, sementara Supabase Auth menangani kredensial dan session.

**Mengapa tabel terpisah dari Supabase Auth:** Supabase Auth dirancang untuk autentikasi, bukan untuk menyimpan data profil bisnis. Tabel `user` ini menyimpan data yang relevan untuk logika aplikasi seperti role, nama tampilan, dan preferensi.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key, sama dengan `auth.users.id` |
| `nama` | Text | Tidak | Nama lengkap untuk ditampilkan di UI |
| `email` | Text | Tidak | Email unik, sinkron dengan Supabase Auth |
| `role` | Enum | Tidak | Nilai: `staff` atau `manager` |
| `avatar_url` | Text | Ya | URL foto profil, opsional |
| `created_at` | Timestamptz | Tidak | — |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | — |

**Catatan:** `deleted_at` pada tabel ini berarti akun dinonaktifkan, bukan dihapus permanen. User yang dinonaktifkan tidak bisa login tetapi datanya tetap ada untuk keperluan audit evaluasi yang pernah mereka buat.

---

### 6.2 Tabel `evaluasi`

**Tujuan:** Menyimpan satu proses evaluasi vendor dari awal hingga selesai, termasuk semua requirement pengadaan yang diinput user.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `judul` | Text | Tidak | Nama singkat evaluasi |
| `kategori` | Enum | Tidak | Kategori pengadaan, menentukan konfigurasi kriteria yang dipakai |
| `deskripsi` | Text | Tidak | Penjelasan kebutuhan pengadaan |
| `status` | Enum | Tidak | Lifecycle status, lihat section 8.1 |
| `budget_min` | BigInt | Ya | Batas bawah anggaran dalam IDR |
| `budget_max` | BigInt | Tidak | Batas atas anggaran dalam IDR |
| `deadline` | Date | Tidak | Tanggal target pengiriman dari vendor |
| `prioritas_kriteria` | Text[] | Ya | Array nama kriteria, urutan mencerminkan prioritas user |
| `lampiran_url` | Text | Ya | URL dokumen spesifikasi teknis di Supabase Storage |
| `created_by` | UUID | Tidak | Foreign key ke `user.id` |
| `preferensi_perusahaan` | Text | Ya | Teks bebas preferensi bisnis yang diinput staff, maks 1.000 karakter. Digunakan oleh Preference Matcher Agent (AI-07) |
| `created_at` | Timestamptz | Tidak | — |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | Soft delete — evaluasi yang dihapus staff |

**Mengapa `prioritas_kriteria` disimpan sebagai array:** Prioritas ini adalah preferensi user saat membuat evaluasi dan bisa berbeda dari bobot numerik yang dikonfigurasi manager. Array sederhana cukup untuk menyimpan urutan preferensi tanpa membutuhkan tabel relasi tersendiri.

**Mengapa `preferensi_perusahaan` nullable:** Preferensi bersifat opsional — sistem bekerja sepenuhnya tanpa preferensi dalam mode netral. Nilai null berarti Preference Matcher Agent akan beroperasi dalam mode netral dan menghasilkan framing objektif tanpa rekomendasi berbasis preferensi.

---

### 6.3 Tabel `vendor`

**Tujuan:** Menyimpan data satu vendor kandidat yang akan dievaluasi dalam konteks satu evaluasi tertentu.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `evaluasi_id` | UUID | Tidak | Foreign key ke `evaluasi.id` |
| `nama_perusahaan` | Text | Tidak | Nama vendor |
| `kontak_atau_website` | Text | Ya | Informasi kontak atau URL website |
| `harga_penawaran` | BigInt | Tidak | Nilai penawaran dalam IDR |
| `catatan` | Text | Ya | Catatan tambahan dari staff |
| `sumber_input` | Enum | Tidak | Nilai: `manual` atau `extracted` |
| `created_at` | Timestamptz | Tidak | — |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | Soft delete — vendor yang dihapus dari evaluasi |

**Catatan penting:** Tabel ini merepresentasikan vendor dalam konteks satu evaluasi spesifik, bukan entitas vendor global. Dua evaluasi yang mengevaluasi vendor yang sama akan memiliki dua row terpisah di tabel ini. Ini disengaja — data vendor (harga, kontak) bisa berbeda per evaluasi dan per waktu.

---

### 6.4 Tabel `dokumen_upload`

**Tujuan:** Melacak dokumen penawaran yang diupload user beserta status dan hasil ekstraksi AI-nya.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `evaluasi_id` | UUID | Tidak | Foreign key ke `evaluasi.id` |
| `vendor_id` | UUID | Ya | Foreign key ke `vendor.id`, diisi setelah ekstraksi berhasil |
| `file_url` | Text | Tidak | URL file di Supabase Storage |
| `file_type` | Enum | Tidak | Nilai: `pdf` atau `excel` |
| `file_size_bytes` | Integer | Tidak | Ukuran file dalam bytes |
| `status_ekstraksi` | Enum | Tidak | Nilai: `pending`, `processing`, `done`, `done_partial`, `failed` |
| `hasil_ekstraksi` | JSONB | Ya | Data vendor hasil ekstraksi AI field terstruktur, null jika belum selesai |
| `confidence_score` | Numeric | Ya | Tingkat kepercayaan hasil ekstraksi AI (0.0–1.0) |
| `nama_vendor_hint` | Text | Ya | Nama vendor yang diinput user sebagai petunjuk untuk AI |
| `indexing_rag_status` | Enum | Ya | Status pipeline RAG indexing: `pending`, `processing`, `done`, `failed`, `skipped_no_text` |
| `chunk_count` | Integer | Ya | Jumlah chunk yang berhasil diindeks ke pgvector, null jika belum selesai |
| `created_at` | Timestamptz | Tidak | — |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | — |

**Mengapa `hasil_ekstraksi` disimpan sebagai JSONB:** Struktur data hasil ekstraksi bisa bervariasi tergantung isi dokumen. JSONB memungkinkan penyimpanan data semi-struktural tanpa memaksakan skema yang kaku, sekaligus tetap bisa di-query menggunakan operator JSON PostgreSQL.

**Mengapa ada `confidence_score`:** Nilai ini digunakan UI untuk memberi sinyal kepada user apakah hasil ekstraksi perlu diverifikasi secara manual. Ekstraksi dengan confidence rendah ditandai dengan indikator visual di VendorInputCard.

**Mengapa `status_ekstraksi` punya nilai `done_partial`:** Status ini mencerminkan kondisi di mana ekstraksi field terstruktur berhasil tetapi RAG indexing gagal (AI-01 section 9.3). Evaluasi tetap bisa disubmit, namun AI Chat Panel tidak bisa menjawab pertanyaan berbasis isi dokumen mentah untuk vendor ini.

**Mengapa `indexing_rag_status` terpisah dari `status_ekstraksi`:** Keduanya adalah proses yang berbeda dengan kemungkinan kegagalan yang berbeda pula. Memisahkannya memudahkan diagnosis — engineer bisa langsung tahu apakah masalah ada di ekstraksi LLM atau di pipeline embedding Google Gemini.

---

### 6.5 Tabel `dokumen_chunk`

**Tujuan:** Menyimpan semua chunk teks dari dokumen penawaran yang sudah diindeks untuk keperluan RAG (Retrieval-Augmented Generation). Setiap dokumen menghasilkan banyak chunk — baik parent chunk (untuk konteks LLM) maupun child chunk (untuk retrieval yang presisi).

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `evaluasi_id` | UUID | Tidak | Foreign key ke `evaluasi.id` — untuk isolasi data per evaluasi |
| `vendor_id` | UUID | Tidak | Foreign key ke `vendor.id` — untuk filter per vendor |
| `dokumen_upload_id` | UUID | Tidak | Foreign key ke `dokumen_upload.id` |
| `is_parent` | Boolean | Tidak | True = parent chunk (1.000–1.500 token), False = child chunk (300–500 token) |
| `parent_chunk_id` | UUID | Ya | Foreign key ke `dokumen_chunk.id` — null untuk parent chunk |
| `teks_chunk` | Text | Tidak | Isi teks chunk |
| `embedding` | vector(768) | Ya | Vektor embedding dari Google Gemini text-embedding-004. Null untuk parent chunk — parent tidak di-embed |
| `teks_search` | tsvector | Ya | Full-text search index untuk BM25 hybrid search. Null untuk parent chunk |
| `halaman` | Integer | Tidak | Nomor halaman dalam dokumen asli |
| `tipe_konten` | Enum | Tidak | Nilai: `paragraf`, `tabel`, `list`, `header` |
| `posisi_section` | Text | Ya | Judul section atau heading induk dari chunk ini |
| `chunk_index` | Integer | Tidak | Urutan chunk dalam dokumen (untuk ordering konteks) |
| `token_count` | Integer | Tidak | Perkiraan jumlah token — untuk monitoring batas context window |
| `created_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | Soft delete mengikuti lifecycle evaluasi induknya |

**Mengapa parent chunk tidak memiliki embedding:** Parent chunk tidak pernah dicari secara langsung — ia hanya diambil setelah child chunk ditemukan melalui similarity search. Tidak meng-embed parent chunk menghemat biaya embedding dan storage vector secara signifikan.

**Mengapa `evaluasi_id` disimpan langsung (redundan dengan relasi via `vendor_id`):** Filter `evaluasi_id` adalah syarat wajib di setiap query retrieval RAG untuk isolasi data. Menyimpannya langsung di tabel menghindari join ke tabel `vendor` yang menambah latensi di query hot path ini.

**Mengapa `tipe_konten` penting:** Tabel selalu diperlakukan sebagai unit atomic dalam chunking — tidak pernah dipotong di tengah. Field ini memungkinkan sistem memberi perlakuan khusus saat retrieval: tabel yang ditemukan selalu dikirim ke LLM sebagai satu unit lengkap.

Detail arsitektur RAG dan strategi chunking lengkap ada di AI-05.

---

### 6.6 Tabel `agent_progress`

**Tujuan:** Menyimpan status real-time tiap sub-agent selama proses evaluasi berlangsung. Tabel ini adalah sumber data untuk Supabase Realtime broadcast ke frontend.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `evaluasi_id` | UUID | Tidak | Foreign key ke `evaluasi.id` |
| `agent_key` | Enum | Tidak | Identifier agent: `data_collector`, `financial_analyzer`, `risk_assessor`, `performance_scorer`, `negotiation_assistant`, `qualitative_analyzer`, `preference_matcher` |
| `status` | Enum | Tidak | Nilai: `idle`, `running`, `done`, `error` |
| `progress` | Integer | Tidak | Persentase penyelesaian, 0–100 |
| `pesan_terakhir` | Text | Ya | Pesan singkat tentang apa yang sedang dikerjakan agent |
| `error_detail` | Text | Ya | Detail error jika status adalah `error` |
| `started_at` | Timestamptz | Ya | Waktu agent mulai berjalan |
| `finished_at` | Timestamptz | Ya | Waktu agent selesai atau berhenti karena error |
| `created_at` | Timestamptz | Tidak | — |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | — |

**Mengapa tujuh nilai enum `agent_key`:** Sistem kini menggunakan tujuh sub-agent (AI-01 section 4). Setiap evaluasi selalu memiliki tepat tujuh row di tabel ini — satu per agent — semua diinisialisasi dengan status `idle` sebelum proses dimulai.

**Mengapa ada `error_detail` terpisah dari `pesan_terakhir`:** `pesan_terakhir` adalah informasi positif untuk ditampilkan ke user. `error_detail` adalah informasi teknis untuk debugging — tidak perlu selalu ditampilkan ke user tetapi penting untuk logging dan monitoring.

---

### 6.7 Tabel `hasil_evaluasi`

**Tujuan:** Menyimpan output keseluruhan dari scoring engine untuk satu evaluasi — termasuk vendor yang direkomendasikan dan reasoning naratif AI.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `evaluasi_id` | UUID | Tidak | Foreign key ke `evaluasi.id`, unik (satu evaluasi satu hasil) |
| `metodologi` | Text | Tidak | Nama algoritma yang digunakan, contoh: `TOPSIS` |
| `vendor_rekomendasi_id` | UUID | Tidak | Foreign key ke `vendor.id` — vendor dengan rank 1 yang lolos threshold |
| `reasoning_utama` | Text | Tidak | Narasi mengapa vendor terpilih direkomendasikan (berbasis TOPSIS) |
| `kelemahan_utama` | Text | Tidak | Narasi tentang hal yang perlu diwaspadai dari vendor terpilih |
| `rekomendasi_negosiasi` | Text | Tidak | Saran langkah negosiasi selanjutnya |
| `summary_komparatif_kualitatif` | Text | Ya | Narasi perbandingan profil kualitatif semua vendor dari Qualitative Analyzer Agent |
| `preference_matching_result` | JSONB | Ya | Output lengkap dari Preference Matcher Agent — mencakup mode, rekomendasi, dan analisis kesesuaian. Null jika Preference Matcher gagal |
| `conflict_callout` | JSONB | Ya | Informasi konflik antara rekomendasi TOPSIS dan preferensi, jika ada. Null jika tidak ada konflik |
| `konfigurasi_snapshot` | JSONB | Tidak | Snapshot konfigurasi kriteria yang digunakan saat kalkulasi — untuk reproducibility |
| `ada_data_tidak_lengkap` | Boolean | Tidak | True jika ada agent yang gagal sehingga ada dimensi yang tidak dievaluasi penuh |
| `agent_gagal` | Text[] | Ya | Array nama agent yang gagal selama evaluasi, null jika semua agent berhasil |
| `calculated_at` | Timestamptz | Tidak | Waktu scoring engine selesai menghitung |
| `created_at` | Timestamptz | Tidak | — |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | — |

**Mengapa reasoning disimpan di database, bukan di-generate ulang setiap request:** Reasoning dari LLM bersifat non-deterministic — memanggil ulang LLM dengan input yang sama bisa menghasilkan teks yang berbeda. Menyimpannya di database memastikan konsistensi — apa yang dilihat staff sama dengan apa yang dilihat manager saat approval.

**Mengapa `preference_matching_result` sebagai JSONB:** Struktur output Preference Matcher cukup kompleks (analisis kesesuaian per vendor, rekomendasi, narasi) dan bervariasi tergantung mode (netral vs opinionated). JSONB adalah pilihan tepat untuk menyimpan struktur dinamis ini tanpa memaksa desain tabel yang kaku.

**Mengapa `conflict_callout` kolom tersendiri:** Callout konflik perlu diakses dengan cepat oleh UI untuk menentukan apakah perlu menampilkan warning prominan di P-05 — tanpa harus mem-parse seluruh JSONB `preference_matching_result`.

**Mengapa `konfigurasi_snapshot` ada di sini:** Konfigurasi bobot kriteria bisa berubah setelah evaluasi selesai. Menyimpan snapshot memastikan hasil evaluasi lama bisa diinterpretasikan dengan benar dalam konteks konfigurasi yang digunakan saat itu.

---

### 6.8 Tabel `hasil_vendor`

**Tujuan:** Menyimpan skor detail per vendor dalam satu evaluasi — termasuk rank, skor total, skor per kriteria, dan catatan AI per kriteria.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `hasil_evaluasi_id` | UUID | Tidak | Foreign key ke `hasil_evaluasi.id` |
| `vendor_id` | UUID | Tidak | Foreign key ke `vendor.id` |
| `rank` | Integer | Tidak | Posisi ranking TOPSIS, dimulai dari 1 |
| `skor_total` | Numeric | Tidak | Skor TOPSIS akhir hasil pembobotan, skala 0–100 |
| `skor_per_kriteria` | JSONB | Tidak | Skor tiap kriteria, contoh: `{"harga_tco": 88.0, "kualitas": 85.0}` |
| `catatan_per_kriteria` | JSONB | Ya | Narasi AI per kriteria, contoh: `{"harga_tco": "Harga 9% di bawah rata-rata pasar"}` |
| `lolos_threshold` | Boolean | Tidak | True jika vendor memenuhi semua threshold minimum |
| `unique_offerings` | JSONB | Ya | Array unique offerings dari Qualitative Analyzer — nilai tambah unik vendor ini di luar kriteria standar. Null jika agent gagal atau tidak ada unique offering teridentifikasi |
| `profil_kualitatif` | Text | Ya | Narasi profil kualitatif vendor dari Qualitative Analyzer. Null jika agent gagal |
| `tingkat_kesesuaian_preferensi` | Enum | Ya | Kesesuaian vendor dengan preferensi perusahaan: `tinggi`, `sedang`, `rendah`, `tidak_relevan`. Null jika tidak ada preferensi atau Preference Matcher gagal |
| `created_at` | Timestamptz | Tidak | — |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | — |

**Mengapa `skor_per_kriteria` dan `catatan_per_kriteria` disimpan sebagai JSONB:** Kriteria bersifat dinamis — jumlah dan namanya bergantung pada konfigurasi per kategori pengadaan. Menyimpannya sebagai JSONB menghindari kebutuhan membuat kolom baru setiap kali ada perubahan konfigurasi kriteria.

**Mengapa `unique_offerings` sebagai JSONB:** Struktur dan jumlah unique offerings per vendor tidak terprediksi — bisa nol, bisa banyak, dan setiap offering memiliki properti `deskripsi`, `relevansi`, dan `sumber`. JSONB adalah representasi alami untuk data semi-struktural ini.

**Mengapa `tingkat_kesesuaian_preferensi` sebagai Enum terpisah, bukan di dalam `preference_matching_result` di tabel induk:** Nilai ini dibutuhkan per vendor untuk ditampilkan di baris tabel VendorRankingTable — query per baris jauh lebih efisien dengan kolom Enum dibanding mem-parse JSONB induk untuk setiap baris.

---

### 6.9 Tabel `konfigurasi_kriteria`

**Tujuan:** Menyimpan bobot dan threshold minimum tiap kriteria per kategori pengadaan, yang dapat dikonfigurasi oleh manager.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `kategori` | Enum | Tidak | Kategori pengadaan yang dikonfigurasi |
| `kriteria` | JSONB | Tidak | Array konfigurasi tiap kriteria, lihat penjelasan di bawah |
| `updated_by` | UUID | Tidak | Foreign key ke `user.id` — manager yang terakhir mengubah |
| `created_at` | Timestamptz | Tidak | — |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | — |

**Struktur JSONB kolom `kriteria`:** Array of object, masing-masing berisi `key` (identifier unik kriteria), `label` (nama tampilan), `bobot` (integer, total semua harus 100), dan `threshold_min` (integer 0–100).

**Mengapa satu row per kategori:** Setiap kategori pengadaan memiliki satu set konfigurasi aktif. Pendekatan ini membuat query konfigurasi aktif sangat sederhana: cukup filter berdasarkan kategori dan ambil row yang tidak soft-deleted.

**Mengapa tidak ada versioning konfigurasi di tabel ini:** Konfigurasi yang digunakan saat evaluasi dibuat disimpan sebagai bagian dari proses scoring (lihat AI-03). Tabel ini hanya menyimpan konfigurasi aktif saat ini. Jika audit trail konfigurasi dibutuhkan di masa mendatang, dapat ditambahkan sebagai tabel `konfigurasi_kriteria_history`.

---

### 6.10 Tabel `approval_log`

**Tujuan:** Mencatat keputusan approval (approve atau reject) yang diberikan manager untuk satu evaluasi, beserta komentar dan timestamp.

| Kolom | Tipe | Nullable | Keterangan |
|---|---|---|---|
| `id` | UUID | Tidak | Primary key |
| `evaluasi_id` | UUID | Tidak | Foreign key ke `evaluasi.id` |
| `manager_id` | UUID | Tidak | Foreign key ke `user.id` — manager yang memberi keputusan |
| `keputusan` | Enum | Tidak | Nilai: `approved` atau `rejected` |
| `komentar` | Text | Ya | Komentar manager — wajib diisi jika keputusan `rejected` |
| `created_at` | Timestamptz | Tidak | Waktu keputusan dibuat |
| `updated_at` | Timestamptz | Tidak | — |
| `deleted_at` | Timestamptz | Ya | — |

**Mengapa tabel terpisah, bukan kolom di tabel `evaluasi`:** Satu evaluasi bisa melalui siklus approve/reject lebih dari sekali — staff bisa merevisi dan mengirim ulang. Tabel terpisah memungkinkan penyimpanan seluruh riwayat keputusan, bukan hanya keputusan terakhir. Ini penting untuk audit trail.

---

## 7. Relasi Antar Tabel

| Tabel Asal | Tabel Tujuan | Jenis Relasi | Keterangan |
|---|---|---|---|
| `evaluasi` | `user` | Many-to-one | Banyak evaluasi dibuat oleh satu user |
| `vendor` | `evaluasi` | Many-to-one | Banyak vendor ada dalam satu evaluasi |
| `dokumen_upload` | `evaluasi` | Many-to-one | Banyak dokumen diupload dalam satu evaluasi |
| `dokumen_upload` | `vendor` | Many-to-one | Satu dokumen terkait dengan satu vendor (setelah ekstraksi) |
| `dokumen_chunk` | `dokumen_upload` | Many-to-one | Banyak chunk dihasilkan dari satu dokumen |
| `dokumen_chunk` | `vendor` | Many-to-one | Chunk terikat ke vendor pemilik dokumen |
| `dokumen_chunk` | `evaluasi` | Many-to-one | Chunk terikat ke evaluasi (untuk isolasi RAG) |
| `dokumen_chunk` | `dokumen_chunk` | Self-referential | Child chunk merujuk ke parent chunk-nya |
| `agent_progress` | `evaluasi` | Many-to-one | Tujuh baris progress untuk satu evaluasi |
| `hasil_evaluasi` | `evaluasi` | One-to-one | Satu evaluasi menghasilkan satu set hasil |
| `hasil_evaluasi` | `vendor` | Many-to-one | Satu hasil evaluasi merekomendasikan satu vendor |
| `hasil_vendor` | `hasil_evaluasi` | Many-to-one | Banyak skor vendor dalam satu hasil evaluasi |
| `hasil_vendor` | `vendor` | Many-to-one | Satu skor vendor merupakan hasil penilaian satu vendor |
| `konfigurasi_kriteria` | — | Standalone | Tidak berelasi langsung, dirujuk berdasarkan nilai `kategori` |
| `approval_log` | `evaluasi` | Many-to-one | Banyak keputusan bisa ada untuk satu evaluasi (riwayat) |
| `approval_log` | `user` | Many-to-one | Banyak keputusan dibuat oleh satu manager |

---

## 8. Aturan Bisnis di Level Database

Beberapa aturan bisnis penting yang perlu diimplementasikan sebagai constraint di level database — bukan hanya di level aplikasi. Constraint di database memberikan lapisan keamanan terakhir yang tidak bisa dilewati apapun.

### 8.1 Enum status evaluasi

Kolom `status` di tabel `evaluasi` hanya boleh berisi nilai berikut, dalam urutan lifecycle yang valid:

`draft` → `processing` → `selesai` → `menunggu_approval` → `approved` atau `butuh_revisi`

### 8.2 Jumlah vendor per evaluasi

Satu evaluasi tidak boleh memiliki lebih dari 10 vendor aktif (yang belum soft-deleted) pada satu waktu.

### 8.3 Uniqueness agent per evaluasi

Kombinasi `evaluasi_id` dan `agent_key` di tabel `agent_progress` harus unik — tidak boleh ada dua row untuk agent yang sama dalam satu evaluasi. Nilai enum `agent_key` mencakup tujuh nilai: `data_collector`, `financial_analyzer`, `risk_assessor`, `performance_scorer`, `negotiation_assistant`, `qualitative_analyzer`, `preference_matcher`.

### 8.4 One hasil per evaluasi

Kolom `evaluasi_id` di tabel `hasil_evaluasi` harus unik — satu evaluasi hanya boleh memiliki satu set hasil aktif.

### 8.5 Validasi total bobot kriteria

Total semua nilai `bobot` dalam array JSONB di kolom `kriteria` tabel `konfigurasi_kriteria` harus sama dengan 100. Validasi ini sebaiknya dilakukan di level aplikasi terlebih dahulu, tetapi constraint PostgreSQL dapat ditambahkan sebagai safety net.

---

## 9. Strategi Indexing

Index dibuat untuk mengoptimalkan query yang paling sering dijalankan. Berikut adalah index yang diprioritaskan beserta alasannya.

| Tabel | Kolom | Jenis Index | Alasan |
|---|---|---|---|
| `evaluasi` | `created_by` | B-tree | Query daftar evaluasi milik user tertentu |
| `evaluasi` | `status` | B-tree | Filter evaluasi berdasarkan status |
| `evaluasi` | `kategori` | B-tree | Filter evaluasi berdasarkan kategori |
| `evaluasi` | `deleted_at` | Partial index (where null) | Query default hanya membaca data aktif |
| `vendor` | `evaluasi_id` | B-tree | Join vendor ke evaluasi |
| `dokumen_upload` | `evaluasi_id` | B-tree | Query dokumen dalam satu evaluasi |
| `dokumen_chunk` | `evaluasi_id` | B-tree | Filter wajib di setiap query RAG retrieval — hot path |
| `dokumen_chunk` | `vendor_id` | B-tree | Filter per vendor saat retrieval |
| `dokumen_chunk` | `embedding` | HNSW (pgvector) | Approximate nearest neighbor search untuk vector similarity |
| `dokumen_chunk` | `teks_search` | GIN | Full-text search PostgreSQL untuk BM25 hybrid search |
| `dokumen_chunk` | `parent_chunk_id` | B-tree | Lookup parent chunk setelah child ditemukan |
| `agent_progress` | `evaluasi_id` | B-tree | Query semua agent dalam satu evaluasi |
| `hasil_vendor` | `hasil_evaluasi_id` | B-tree | Query semua skor vendor dalam satu hasil evaluasi |
| `approval_log` | `evaluasi_id` | B-tree | Query riwayat approval satu evaluasi |
| `konfigurasi_kriteria` | `kategori` | B-tree | Lookup konfigurasi aktif berdasarkan kategori |

**Catatan khusus index HNSW:** pgvector mendukung dua jenis vector index — HNSW dan IVFFlat. HNSW dipilih karena query-time lebih cepat tanpa membutuhkan training data awal. Parameter default (`m=16, ef_construction=64`) sudah cukup untuk skala MVP.

---

## 10. Row Level Security (RLS)

Supabase mendukung Row Level Security (RLS) di level PostgreSQL — aturan akses data yang diterapkan langsung di database, bukan hanya di aplikasi. Ini memberikan lapisan keamanan tambahan yang tidak bisa dilewati bahkan jika ada bug di logika aplikasi.

### 10.1 Tabel `evaluasi`

- Staff hanya bisa membaca dan memodifikasi evaluasi miliknya sendiri (`created_by = auth.uid()`)
- Manager bisa membaca semua evaluasi
- Manager bisa memodifikasi status evaluasi untuk keperluan approval

### 10.2 Tabel `vendor`, `dokumen_upload`, `dokumen_chunk`, `agent_progress`, `hasil_evaluasi`, `hasil_vendor`

- Akses mengikuti evaluasi induknya — jika user punya akses ke evaluasi, user bisa mengakses semua data turunannya
- Staff hanya bisa mengakses data dari evaluasi miliknya
- **Khusus `dokumen_chunk`:** Setiap query ke tabel ini harus menyertakan filter `evaluasi_id` — ini ditegakkan di level aplikasi (AI-05) dan diperkuat oleh RLS. Tidak ada akses lintas evaluasi meskipun user adalah manager

### 10.3 Tabel `konfigurasi_kriteria`

- Semua user bisa membaca konfigurasi (dibutuhkan saat menampilkan form dan hasil evaluasi)
- Hanya manager yang bisa memodifikasi konfigurasi

### 10.4 Tabel `approval_log`

- Staff hanya bisa membaca approval log dari evaluasi miliknya
- Manager bisa membaca semua approval log dan membuat entri baru

### 10.5 Tabel `user`

- Setiap user hanya bisa membaca dan memodifikasi data profilnya sendiri
- Manager tidak bisa memodifikasi data user lain melalui aplikasi ini

---

## 11. Catatan untuk Dokumen Lanjutan

### Untuk DB-02 (Migration Strategy)

Urutan pembuatan tabel yang direkomendasikan berdasarkan dependency (diperbarui):
1. `user` — tidak bergantung pada tabel lain
2. `konfigurasi_kriteria` — tidak bergantung pada tabel lain
3. `evaluasi` — bergantung pada `user`
4. `vendor` — bergantung pada `evaluasi`
5. `dokumen_upload` — bergantung pada `evaluasi` dan `vendor`
6. `dokumen_chunk` — bergantung pada `dokumen_upload`, `vendor`, dan `evaluasi`
7. `agent_progress` — bergantung pada `evaluasi`
8. `hasil_evaluasi` — bergantung pada `evaluasi` dan `vendor`
9. `hasil_vendor` — bergantung pada `hasil_evaluasi` dan `vendor`
10. `approval_log` — bergantung pada `evaluasi` dan `user`

Aktivasi ekstensi pgvector (`CREATE EXTENSION IF NOT EXISTS vector`) harus menjadi migration pertama sebelum tabel apapun dibuat.

### Untuk DB-03 (Query & Performance)

Query yang diprediksi paling berat dan perlu dioptimasi (diperbarui):
- Query daftar evaluasi dengan filter gabungan — digunakan di P-06
- Query hasil evaluasi lengkap termasuk semua skor vendor dan data kualitatif — digunakan di P-05
- Query RAG retrieval: hybrid search (vector + full-text) dengan filter `evaluasi_id` — hot path saat AI Chat aktif
- Query real-time progress agent — digunakan di P-04, frekuensi tinggi

### Untuk AI-01 (Agent Orchestration)

Agent menulis ke tabel `agent_progress` setiap kali ada update status atau progress. Dengan tujuh agent, pola penulisan perlu lebih hati-hati terhadap write burst terutama saat tiga agent pertama berjalan paralel.

### Untuk AI-05 (RAG Specification)

Definisi tabel `dokumen_chunk` di section 6.5 adalah kontrak antara data model dan pipeline RAG. AI-05 mendefinisikan detail teknis chunking dan cara data diisi ke tabel ini.

---

*Dokumen ini adalah living document — akan diperbarui jika ada entitas baru yang diidentifikasi atau perubahan keputusan desain.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal — 9 tabel | — |
| 2.0.0 | 2026-06-11 | Tambah tabel `dokumen_chunk` (6.5) untuk RAG; tambah kolom `preferensi_perusahaan` di `evaluasi`; tambah kolom RAG indexing di `dokumen_upload`; update enum `agent_key` dari 5 menjadi 7 agent; tambah kolom kualitatif dan preferensi di `hasil_evaluasi` dan `hasil_vendor`; perbarui relasi, indexing, RLS, dan aturan bisnis | — |
| 3.0.0 | 2026-06-13 | Ubah kolom `embedding` di tabel `dokumen_chunk` dari `vector(1536)` (OpenAI text-embedding-3-small) menjadi `vector(768)` (Google Gemini text-embedding-004); perbarui keterangan kolom dan referensi provider embedding | — |
| 4.0.0 | 2026-06-13 | Adopsi ADR-035 (namespace AI): perbarui tabel referensi dan semua inline reference (BE-03→AI-01, BE-05→AI-03, BE-08→AI-05, BE-10→AI-07) | — |
