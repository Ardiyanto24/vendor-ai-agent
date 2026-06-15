# BE-04 — Integration Spec (Fullstack)

**Project:** AI Vendor Selection System  
**Dokumen:** BE-04 — Integration Spec (Fullstack)  
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
3. [Integrasi Supabase Storage](#3-integrasi-supabase-storage)
4. [Aturan & Larangan](#4-aturan--larangan)
5. [Catatan untuk Dokumen Lanjutan](#5-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **integrasi dengan layanan eksternal yang dikerjakan oleh track Fullstack** di repo `vendor-ai` — spesifik untuk pengelolaan file dokumen penawaran vendor melalui Supabase Storage.

Integrasi Supabase Storage melibatkan dua sisi: Next.js API Routes (`apps/api`) menerima upload dari browser dan meneruskan file ke Storage, sementara FastAPI mengakses file dari Storage URL untuk proses ekstraksi. Koordinasi antara kedua service untuk alur ini dijelaskan di sini dari perspektif Fullstack.

Integrasi layanan AI eksternal (Tavily, OpenRouter, Google Gemini) yang sepenuhnya dikerjakan di `vendor-ai-agent` didefinisikan di **AI-04**.

Dokumen ini **tidak** mendefinisikan implementasi kode — itu diserahkan ke engineer.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| BE-02 | API Contract | Endpoint upload file yang menggunakan Supabase Storage |
| BE-03 | Auth & Security | Pengelolaan API key dan akses kontrol storage |
| AI-04 | Integration Spec (AI Engineer) | Integrasi AI service yang dikerjakan di vendor-ai-agent |
| DB-01 | Data Model & ERD | Tabel `dokumen_upload` yang menyimpan metadata file |
| SH-04 | Cost & Usage Guide | Estimasi biaya storage dan bandwidth Supabase |

---

## 3. Integrasi Supabase Storage

### 3.1 Apa dan mengapa

Supabase Storage digunakan untuk menyimpan file dokumen penawaran vendor yang diupload user. Ini adalah extension dari Supabase yang sudah digunakan sebagai database — tidak memerlukan konfigurasi service tambahan, tidak ada vendor baru yang perlu dikelola.

### 3.2 Digunakan oleh

- **Next.js API Routes** (`apps/api`): menerima upload file dari browser dan meneruskan ke Supabase Storage. Bertanggung jawab atas validasi tipe dan ukuran file sebelum diteruskan.
- **FastAPI** (`vendor-ai-agent`): mengakses file dari Storage URL untuk proses ekstraksi dokumen dan indexing RAG. FastAPI tidak pernah menerima file langsung dari browser.

### 3.3 Struktur penyimpanan

File disimpan dalam bucket yang terorganisir berdasarkan evaluasi:

```
bucket: vendor-documents
└── evaluasi/
    └── {evaluasi_id}/
        └── {upload_id}_{nama_file_asli}
```

Struktur ini memudahkan pengelolaan file per evaluasi — jika evaluasi dihapus (soft delete), file terkait dapat diidentifikasi dan dibersihkan dengan mudah.

### 3.4 Akses kontrol bucket

Bucket `vendor-documents` dikonfigurasi sebagai **private** — tidak ada file yang dapat diakses secara publik. Akses hanya melalui signed URL yang di-generate oleh Next.js API Routes untuk user yang sudah diverifikasi memiliki akses ke evaluasi terkait.

Masa berlaku signed URL maksimum 1 jam — cukup untuk sesi kerja normal tanpa membiarkan URL aktif selamanya.

### 3.5 Batasan ukuran dan tipe file

Batasan yang diterapkan di level Next.js API Routes sebelum file diteruskan ke Storage:
- Ukuran maksimum: 10MB per file
- Tipe file yang diizinkan: PDF dan Excel (.xlsx, .xls)

File yang tidak memenuhi batasan ini ditolak di level API — tidak pernah mencapai Supabase Storage.

### 3.6 Lifecycle file

File dokumen penawaran disimpan selama evaluasi aktif. Ketika evaluasi di-soft delete, file tidak langsung dihapus — mengikuti prinsip soft delete yang sama. Penghapusan permanen file dari Storage dilakukan sebagai bagian dari proses cleanup data yang terjadwal (lihat DB-04).

### 3.7 Alur upload end-to-end

```
Browser
  │  multipart/form-data
  ▼
Next.js API Routes (apps/api)
  │  1. Validasi tipe file dan ukuran
  │  2. Upload file ke Supabase Storage
  │  3. Simpan metadata ke tabel dokumen_upload (file_url, file_type, file_size_bytes)
  │  4. Trigger FastAPI untuk ekstraksi
  ▼
FastAPI (vendor-ai-agent)
  │  5. Akses file via Storage URL (signed URL dari apps/api)
  │  6. Ekstraksi field terstruktur + indexing RAG (paralel)
  ▼
Supabase Storage
  └── vendor-documents/evaluasi/{evaluasi_id}/{upload_id}_{nama_file}
```

---

## 4. Aturan & Larangan

**Dilarang mengekspos bucket sebagai public.** Semua akses file harus melalui signed URL yang di-generate server-side dengan masa berlaku terbatas.

**Dilarang menerima upload file langsung di FastAPI.** File hanya diterima di Next.js API Routes — FastAPI mengakses file via URL dari Storage, tidak pernah via multipart upload langsung dari browser.

**Dilarang menyimpan file di luar bucket `vendor-documents`.** Semua file dokumen penawaran harus tersimpan dalam struktur folder yang terdefinisi di section 3.3.

**Dilarang menghapus file dari Storage secara langsung saat evaluasi di-soft delete.** Penghapusan mengikuti proses cleanup yang terjadwal — bukan penghapusan segera saat soft delete terjadi.

**Dilarang menerima tipe file di luar PDF dan Excel.** Validasi tipe file harus dilakukan di level API sebelum file mencapai Storage.

---

## 5. Catatan untuk Dokumen Lanjutan

### Untuk BE-02 (API Contract)

Endpoint `POST /api/v1/evaluasi/{id}/dokumen` harus mencakup: validasi tipe dan ukuran file, upload ke Supabase Storage, dan pembuatan row di tabel `dokumen_upload`. Format response harus mencakup `file_url` dan `upload_id` yang dibutuhkan FastAPI untuk mengakses file.

### Untuk DB-01 (Data Model)

Tabel `dokumen_upload` menyimpan metadata file: `file_url` (path di Supabase Storage), `file_type`, `file_size_bytes`, dan status ekstraksi. Kolom `vendor_id` nullable karena file bisa diupload sebelum vendor dikonfirmasi dari hasil ekstraksi.

### Untuk AI-04 (Integration Spec AI Engineer)

FastAPI mengakses file via signed URL yang di-generate Next.js. Koordinasi format URL dan masa berlaku signed URL perlu dikonfirmasi antara kedua service saat implementasi.

### Untuk SH-04 (Cost & Usage Guide)

Biaya Supabase Storage bergantung pada total ukuran file yang disimpan dan bandwidth saat akses. Dengan maksimum 10MB per file dan 10 vendor per evaluasi, estimasi storage per evaluasi adalah maksimum 100MB.

---

*Dokumen ini adalah living document — akan diperbarui jika ada perubahan pada kebijakan storage atau alur upload.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-13 | Dibuat sebagai pecahan dari BE-07 v3.0.0 (ADR-035) — berisi integrasi yang dikerjakan track Fullstack: Supabase Storage; integrasi AI service (Tavily, OpenRouter, Google Gemini) dipindah ke AI-04 | — |
