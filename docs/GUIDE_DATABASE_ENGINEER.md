# Panduan Implementasi — Database Engineer
 
**Project:** AI Vendor Selection System  
**Role:** Database Engineer  
**Versi:** 2.0.0  
**Tanggal:** 2026-06-12  
**Referensi Utama:** DB-01, DB-02, DB-03, DB-04, MILESTONE_PLAN v4.0.0
 
---
 
## Tentang Dokumen Ini
 
Panduan ini adalah panduan kerja operasional untuk Database Engineer — bukan dokumen spesifikasi. Dokumen ini mengorganisir semua task database dari Milestone Plan ke dalam format yang lebih lengkap per fitur: **apa yang perlu dibuat**, **urutan pekerjaan**, **hal-hal kritis yang tidak boleh terlewat**, dan **definisi "selesai" yang jelas**.
 
Semua task di sini mengacu ke dokumen spec resmi (DB-01, DB-02, DB-03, DB-04). Jika ada konflik antara panduan ini dan dokumen spec, dokumen spec yang berlaku.
 
---
 
## Prasyarat Sebelum Memulai
 
Sebelum coding dimulai, pastikan hal-hal berikut sudah siap:
 
- Supabase CLI terinstall dan sudah login ke akun Supabase
- Dua Supabase project sudah dibuat: `vendor-ai-dev` dan `vendor-ai-staging`
- Monorepo `vendor-ai` sudah diinisialisasi (koordinasi dengan Backend Engineer di F-00) — Supabase CLI di-init di root `vendor-ai` sehingga folder `supabase/migrations/` tersedia di dalam repo
- Database Engineer bekerja langsung di `supabase/migrations/` pada repo `vendor-ai` — tidak ada repository terpisah untuk database
- File `FEATURE_STATUS.md` sudah ada di root `vendor-ai` (dibuat bersama Backend Engineer)
---
 
## Konvensi Migration
 
Semua migration mengikuti konvensi dari DB-02:
 
**Format nama file:** `YYYYMMDDHHMMSS_deskripsi_singkat.sql`
 
**Konvensi isi file:** Setiap migration file wajib menyertakan komentar rollback di header:
```sql
-- Migration: deskripsi singkat perubahan
-- Rollback: perintah SQL untuk membatalkan migration ini
```
 
**Aturan yang tidak boleh dilanggar:**
- Jangan pernah mengedit migration file yang sudah dijalankan — buat migration baru
- Setiap RLS policy dibuat dalam migration file yang sama dengan tabel yang dilindungi
- Index dengan `CONCURRENTLY` tidak bisa dijalankan dalam transaction — tambahkan komentar `-- noqa: transaction` jika diperlukan
- Jangan pernah memasukkan data sensitif (password, API key, PII) ke migration atau seed file
---
 
## F-00 — Environment Setup
 
**Tier:** 0 | **Estimasi:** 2–3 hari
 
### Yang Perlu Dibuat
 
#### 1. Aktivasi pgvector (HARUS JADI MIGRATION PERTAMA)
 
Migration ini adalah fondasi untuk semua migration berikutnya karena tabel `dokumen_chunk` membutuhkan tipe `vector(1536)`. Tanpa ekstensi ini aktif terlebih dahulu, migration tabel apapun yang memiliki kolom vector akan gagal.
 
```
File: 20260607090000_enable_pgvector.sql
```
 
Aktivasi ekstensi `vector` dengan `CREATE EXTENSION IF NOT EXISTS vector`. Klausa `IF NOT EXISTS` penting untuk mencegah error jika dijalankan di environment yang sudah memiliki ekstensi ini.
 
#### 2. Tabel `user`
 
```
File: 20260607100000_create_user_table.sql
```
 
Tabel ini berdiri sendiri — tidak ada foreign key ke tabel lain sehingga aman dibuat paling awal. Kolom yang perlu ada: `id` (UUID, primary key, sama dengan `auth.users.id`), `nama`, `email` (unik), `role` (enum: `staff` | `manager`), `avatar_url` (nullable), plus kolom standar `created_at`, `updated_at`, `deleted_at`.
 
**RLS yang wajib ada di migration yang sama:**
- `SELECT`: user hanya bisa membaca data dirinya sendiri (`id = auth.uid()`)
- `UPDATE`: user hanya bisa mengupdate data dirinya sendiri
- `INSERT`: dikelola melalui Supabase Auth trigger, bukan langsung dari aplikasi
#### 3. Tabel `konfigurasi_kriteria`
 
```
File: 20260607100500_create_konfigurasi_kriteria_table.sql
```
 
Tabel ini juga berdiri sendiri. Kolom: `id`, `kategori` (enum), `kriteria` (JSONB — array of object berisi `key`, `label`, `bobot`, `threshold_min`), `updated_by` (FK ke `user.id`), plus kolom standar.
 
Tambahkan index B-tree pada kolom `kategori` — ini adalah kolom yang selalu digunakan sebagai filter saat mengambil konfigurasi aktif.
 
**RLS yang wajib ada:**
- `SELECT`: semua user authenticated bisa membaca
- `UPDATE`: hanya role `manager` yang bisa mengubah
#### 4. Seed Data Konfigurasi Kriteria
 
```
File: supabase/seed.sql
```
 
Isi seed data untuk setiap kategori pengadaan (minimum seluruh kategori yang ada di enum `kategori`). Setiap kategori harus memiliki 5 kriteria dengan total bobot 100. Nilai default bobot: 30/25/20/15/10.
 
Contoh struktur data untuk satu kategori:
```json
{
  "key": "harga_tco",
  "label": "Harga & TCO",
  "bobot": 30,
  "threshold_min": 60
}
```
 
#### 5. Aktivasi Supabase Realtime
 
Aktifkan Realtime publication untuk tabel `agent_progress`. Ini dilakukan melalui Supabase CLI atau migration SQL dengan mengaktifkan `supabase_realtime.publication`. Tabel ini belum dibuat di F-00, tetapi aktivasi Realtime bisa disiapkan sekarang dan akan efektif setelah tabel dibuat di F-06.
 
**Catatan:** Tabel `agent_progress` baru dibuat di F-06, tetapi Realtime harus sudah dikonfigurasi sebelum F-10 agar broadcast berjalan saat agent mulai menulis progress.
 
### Kriteria Selesai F-00 [DB]
 
```
□ pgvector aktif di Supabase dev (verifikasi: SELECT * FROM pg_extension WHERE extname='vector')
□ Tabel 'user' terbuat dengan semua kolom yang benar dan RLS aktif
□ Tabel 'konfigurasi_kriteria' terbuat dengan index kategori dan RLS aktif
□ Seed data konfigurasi tersedia untuk semua kategori (minimum 5 kriteria per kategori)
□ Supabase Realtime dikonfigurasi untuk tabel agent_progress
□ Semua file migration tersimpan di supabase/migrations/ dalam repo vendor-ai
□ FEATURE_STATUS.md tersedia di root vendor-ai
□ Semua migration berjalan bersih dari awal di environment dev yang fresh
```
 
---
 
## F-01 — Auth & Login
 
**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 2–3 hari (DB task: ~0.5 hari)
 
### Yang Perlu Dibuat
 
#### 1. Verifikasi RLS Tabel `user`
 
Tidak ada migration baru. Task ini memverifikasi bahwa RLS yang dibuat di F-00 sudah benar sebelum backend menggunakannya.
 
Verifikasi dengan menjalankan query manual sebagai dua role berbeda (gunakan Supabase dashboard atau psql):
- Login sebagai user A → SELECT dari tabel `user` → hanya boleh melihat baris milik user A
- Login sebagai user B → SELECT dari tabel `user` → hanya boleh melihat baris milik user B
#### 2. Seed Data Dua Akun Test
 
Buat dua akun user test melalui Supabase Auth (bukan langsung ke tabel `user`). Setelah akun dibuat via Auth, tambahkan row yang sesuai ke tabel `user`:
 
- `test-staff@vendor-ai.dev` — role: `staff`
- `test-manager@vendor-ai.dev` — role: `manager`
**Penting:** Password akun test disimpan di secret management (1Password, Bitwarden, dll.) dan dikomunikasikan ke semua developer melalui saluran terenkripsi. Jangan masukkan ke version control.
 
### Kriteria Selesai F-01 [DB]
 
```
□ Dua akun test (staff + manager) tersedia di Supabase dev dengan role yang benar
□ RLS terverifikasi: user A tidak bisa SELECT data user B (diuji manual)
□ Tidak ada migration baru yang diperlukan — semua sudah dibuat di F-00
```
 
---
 
## F-02 — Layout & AppShell
 
**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** Tidak ada task
 
Database Engineer tidak memiliki task di fitur ini. Tandai F-02 sebagai `N/A` di bagian DB pada `FEATURE_STATUS.md`.
 
---
 
## F-03 — Konfigurasi Kriteria (Settings P-08)
 
**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** ~0.5 hari
 
### Yang Perlu Dibuat
 
#### 1. Verifikasi Index dan RLS Tabel `konfigurasi_kriteria`
 
Tidak ada migration baru. Verifikasi bahwa:
 
- Index B-tree pada kolom `kategori` sudah ada dan digunakan oleh query (`EXPLAIN ANALYZE SELECT * FROM konfigurasi_kriteria WHERE kategori = 'X' AND deleted_at IS NULL`)
- RLS memblokir UPDATE dari role `staff` (uji manual: login sebagai staff, coba UPDATE satu row → harus menghasilkan error)
- RLS mengizinkan SELECT untuk semua authenticated user
### Kriteria Selesai F-03 [DB]
 
```
□ EXPLAIN ANALYZE query konfigurasi menggunakan index 'kategori' (bukan Seq Scan)
□ Staff yang coba UPDATE konfigurasi mendapat error RLS (diuji manual di psql atau REST)
□ Manager bisa UPDATE konfigurasi (diuji manual)
□ Semua kategori pengadaan memiliki seed data konfigurasi yang valid
```
 
---
 
## F-04 — Dashboard (P-02)
 
**Tier:** 1 | **Prerequisite:** F-01, F-02 | **Estimasi:** ~1.5 hari
 
### Yang Perlu Dibuat
 
#### 1. Tabel `evaluasi`
 
```
File: 20260608090000_create_evaluasi_table.sql
```
 
Tabel ini bergantung pada `user`, jadi dibuat setelah F-01 selesai. Kolom lengkap sesuai DB-01 section 6.2: `id`, `judul`, `kategori` (enum sama dengan `konfigurasi_kriteria`), `deskripsi`, `status` (enum lifecycle), `budget_min` (nullable BigInt), `budget_max` (BigInt), `deadline` (Date), `prioritas_kriteria` (Text[], nullable), `lampiran_url` (nullable), `created_by` (FK ke `user.id`), `preferensi_perusahaan` (Text, nullable, max 1.000 karakter), plus kolom standar.
 
**Enum status yang harus dibuat:**
```
draft → processing → selesai → menunggu_approval → approved | butuh_revisi
```
 
Buat tipe enum PostgreSQL untuk `status` dan `kategori` sebelum membuat tabel.
 
**Index yang wajib ada:**
- Composite B-tree: `(created_by, status, deleted_at)` — hot path untuk daftar evaluasi staff
- Partial index: `(deleted_at) WHERE deleted_at IS NULL` — semua query default memfilter soft delete
**RLS yang wajib ada:**
- `SELECT`: staff hanya bisa melihat evaluasi miliknya (`created_by = auth.uid()`), manager bisa melihat semua
- `INSERT`: user authenticated bisa membuat evaluasi baru (dengan `created_by` di-set ke `auth.uid()`)
- `UPDATE`: staff hanya bisa mengupdate evaluasi miliknya; manager bisa mengupdate status untuk approval
- `DELETE`: tidak diizinkan — semua "hapus" harus soft delete
#### 2. Tabel `vendor`
 
```
File: 20260608090500_create_vendor_table.sql
```
 
Bergantung pada `evaluasi`. Kolom sesuai DB-01 section 6.3: `id`, `evaluasi_id` (FK ke `evaluasi.id`), `nama_perusahaan`, `kontak_atau_website` (nullable), `harga_penawaran` (BigInt, dalam IDR), `catatan` (nullable), `sumber_input` (enum: `manual` | `extracted`), plus kolom standar.
 
**Index:**
- B-tree pada `evaluasi_id` — semua query vendor selalu difilter berdasarkan evaluasi
**RLS:** Akses mengikuti evaluasi induknya. Staff hanya bisa mengakses vendor dari evaluasi miliknya.
 
### Kriteria Selesai F-04 [DB]
 
```
□ Tabel 'evaluasi' terbuat dengan semua kolom, enum status lifecycle, dan RLS
□ Tabel 'vendor' terbuat dengan FK ke evaluasi dan RLS
□ Composite index (created_by, status, deleted_at) ada di tabel evaluasi
□ Partial index pada deleted_at IS NULL ada di tabel evaluasi
□ Index evaluasi_id ada di tabel vendor
□ RLS diuji: staff A tidak bisa SELECT evaluasi milik staff B
□ EXPLAIN ANALYZE query daftar evaluasi memenuhi target < 100ms (dari DB-03 section 10)
```
 
---
 
## F-05 — Riwayat Evaluasi (P-06)
 
**Tier:** 1 | **Prerequisite:** F-01, F-02, F-04 | **Estimasi:** Tidak ada task baru
 
Tidak ada migration baru. Tabel `evaluasi` sudah dibuat di F-04 dan mencakup semua kolom yang dibutuhkan halaman P-06, termasuk filter status dan kategori. Verifikasi bahwa query dengan kombinasi filter (status + kategori + search + tanggal) masih memenuhi target performa.
 
```
□ EXPLAIN ANALYZE query dengan filter status + kategori + search menggunakan index yang sesuai
□ Tidak ada Seq Scan pada tabel evaluasi untuk query daftar normal
```
 
---
 
## F-06 — Buat Evaluasi: Requirement & Vendor Manual
 
**Tier:** 1 | **Prerequisite:** F-01, F-02, F-04 | **Estimasi:** ~1.5 hari
 
### Yang Perlu Dibuat
 
#### 1. Tabel `agent_progress`
 
```
File: 20260609090000_create_agent_progress_table.sql
```
 
Tabel ini dibutuhkan saat evaluasi di-submit (status berubah ke `processing`) karena backend langsung membuat 7 row — satu per agent — dengan status `idle`. Kolom sesuai DB-01 section 6.6: `id`, `evaluasi_id` (FK ke `evaluasi.id`), `agent_key` (enum 7 nilai), `status` (enum: `idle` | `running` | `done` | `error`), `progress` (Integer 0–100), `pesan_terakhir` (nullable), `error_detail` (nullable), `started_at` (nullable), `finished_at` (nullable), plus kolom standar.
 
**Enum `agent_key` yang wajib ada:**
```
data_collector, financial_analyzer, risk_assessor, performance_scorer,
negotiation_assistant, qualitative_analyzer, preference_matcher
```
 
**Constraint unik:** Kombinasi `(evaluasi_id, agent_key)` harus unik — satu evaluasi tidak boleh memiliki dua row untuk agent yang sama.
 
**Index:**
- B-tree pada `evaluasi_id` — query agent selalu difilter berdasarkan evaluasi
- Supabase Realtime harus diaktifkan untuk tabel ini (ini yang mengirim update ke frontend P-04)
**RLS:** Akses mengikuti evaluasi induknya.
 
#### 2. Tabel `hasil_evaluasi`
 
```
File: 20260609090500_create_hasil_evaluasi_table.sql
```
 
Bergantung pada `evaluasi`. Kolom sesuai DB-01 section 6.7: `id`, `evaluasi_id` (FK, unik — satu evaluasi satu hasil), `metodologi` (Text, default: `TOPSIS`), `vendor_rekomendasi_id` (FK ke `vendor.id`), `reasoning_utama`, `kelemahan_utama`, `rekomendasi_negosiasi`, `summary_komparatif_kualitatif` (nullable), `preference_matching_result` (JSONB, nullable), `conflict_callout` (JSONB, nullable), `konfigurasi_snapshot` (JSONB), `ada_data_tidak_lengkap` (Boolean), `agent_gagal` (Text[], nullable), `calculated_at`, plus kolom standar.
 
**Constraint:** `evaluasi_id` harus `UNIQUE` — satu evaluasi hanya boleh memiliki satu hasil aktif.
 
**RLS:** Akses mengikuti evaluasi induknya.
 
#### 3. Tabel `hasil_vendor`
 
```
File: 20260609091000_create_hasil_vendor_table.sql
```
 
Bergantung pada `hasil_evaluasi` dan `vendor`. Kolom sesuai DB-01 section 6.8: `id`, `hasil_evaluasi_id` (FK ke `hasil_evaluasi.id`), `vendor_id` (FK ke `vendor.id`), `rank` (Integer), `skor_total` (Numeric), `skor_per_kriteria` (JSONB), `catatan_per_kriteria` (JSONB, nullable), `lolos_threshold` (Boolean), `unique_offerings` (JSONB, nullable), `profil_kualitatif` (Text, nullable), `tingkat_kesesuaian_preferensi` (enum: `tinggi` | `sedang` | `rendah` | `tidak_relevan`, nullable), plus kolom standar.
 
**Index:**
- B-tree pada `hasil_evaluasi_id` — query semua skor vendor dalam satu hasil evaluasi
**RLS:** Akses mengikuti evaluasi induknya via `hasil_evaluasi`.
 
### Kriteria Selesai F-06 [DB]
 
```
□ Tabel 'agent_progress' terbuat dengan enum agent_key (7 nilai) dan unique constraint (evaluasi_id, agent_key)
□ Tabel 'hasil_evaluasi' terbuat dengan UNIQUE constraint pada evaluasi_id
□ Tabel 'hasil_vendor' terbuat dengan kolom kualitatif dan preferensi
□ Supabase Realtime aktif untuk tabel agent_progress (verifikasi dari dashboard Supabase)
□ Semua tabel memiliki RLS yang sesuai
□ Semua migration berjalan bersih dari awal di dev
```
 
---
 
## F-07 — Upload Dokumen & Ekstraksi
 
**Tier:** 2 | **Prerequisite:** F-06 | **Estimasi:** ~2 hari
 
### Yang Perlu Dibuat
 
#### 1. Tabel `dokumen_upload`
 
```
File: 20260610090000_create_dokumen_upload_table.sql
```
 
Bergantung pada `evaluasi` dan `vendor`. Kolom sesuai DB-01 section 6.4: `id`, `evaluasi_id` (FK), `vendor_id` (FK, nullable — diisi setelah ekstraksi), `file_url`, `file_type` (enum: `pdf` | `excel`), `file_size_bytes` (Integer), `status_ekstraksi` (enum: `pending` | `processing` | `done` | `done_partial` | `failed`), `hasil_ekstraksi` (JSONB, nullable), `confidence_score` (Numeric 0.0–1.0, nullable), `nama_vendor_hint` (nullable), `indexing_rag_status` (enum: `pending` | `processing` | `done` | `failed` | `skipped_no_text`, nullable), `chunk_count` (Integer, nullable), plus kolom standar.
 
**Catatan desain penting:** `vendor_id` nullable di sini karena dokumen bisa diupload sebelum vendor dikonfirmasi dari hasil ekstraksi. Setelah ekstraksi selesai dan user mengkonfirmasi, vendor_id diisi.
 
**Index:**
- B-tree pada `evaluasi_id` — query semua dokumen dalam satu evaluasi
**RLS:** Akses mengikuti evaluasi induknya.
 
#### 2. Tabel `dokumen_chunk`
 
```
File: 20260610090500_create_dokumen_chunk_table.sql
```
 
Ini adalah tabel paling kompleks karena memiliki tipe kolom `vector(1536)`, full-text search column `tsvector`, dan self-referential foreign key. **Ikuti urutan pembuatan ini dengan teliti:**
 
**Langkah 1 — Buat tabel tanpa self-referential FK:**
 
Kolom sesuai DB-01 section 6.5: `id`, `evaluasi_id` (FK), `vendor_id` (FK), `dokumen_upload_id` (FK), `is_parent` (Boolean), `parent_chunk_id` (UUID, nullable — **tanpa FK constraint dulu**), `teks_chunk` (Text), `embedding` (vector(1536), nullable — null untuk parent chunk), `teks_search` (tsvector, nullable — null untuk parent chunk), `halaman` (Integer), `tipe_konten` (enum: `paragraf` | `tabel` | `list` | `header`), `posisi_section` (nullable), `chunk_index` (Integer), `token_count` (Integer), `created_at`, `deleted_at`.
 
**Langkah 2 — Tambahkan self-referential FK setelah tabel dibuat:**
```sql
ALTER TABLE dokumen_chunk 
  ADD CONSTRAINT fk_parent_chunk 
  FOREIGN KEY (parent_chunk_id) 
  REFERENCES dokumen_chunk(id);
```
 
**Langkah 3 — Index dasar (B-tree) dalam migration yang sama:**
- B-tree pada `evaluasi_id` — filter wajib di setiap query RAG
- B-tree pada `vendor_id` — filter per vendor saat retrieval
- B-tree pada `parent_chunk_id` — lookup parent setelah child ditemukan
#### 3. Index Vector dan Full-Text (Migration Terpisah)
 
```
File: 20260610091000_create_dokumen_chunk_indexes.sql
```
 
Index HNSW dan GIN dibuat dalam migration **terpisah** karena keduanya memiliki karakteristik khusus:
 
**Index HNSW untuk vector similarity:**
```sql
-- Gunakan parameter default yang sesuai untuk MVP
-- m=16, ef_construction=64 sudah cukup untuk skala awal
```
 
Karena tabel baru saja dibuat dan masih kosong saat ini, index HNSW bisa dibuat tanpa `CONCURRENTLY`. Namun jika di kemudian hari perlu dibuat ulang di tabel yang sudah berisi data, wajib gunakan mekanisme yang sesuai (pgvector HNSW tidak mendukung `CONCURRENTLY` standar).
 
**Index GIN untuk full-text search:**
```sql
-- Index pada kolom teks_search (tsvector)
-- GIN cocok untuk tsvector karena mendukung query @@ dengan cepat
```
 
#### 4. Bucket Supabase Storage
 
Aktifkan bucket `vendor-documents` sebagai **private** melalui Supabase CLI atau SQL:
 
```sql
-- Buat bucket private untuk dokumen vendor
INSERT INTO storage.buckets (id, name, public)
VALUES ('vendor-documents', 'vendor-documents', false);
```
 
Tambahkan storage policy yang memastikan:
- User hanya bisa upload ke bucket ini jika mereka punya akses ke evaluasi terkait
- User hanya bisa download file yang terkait dengan evaluasi miliknya
- File tidak bisa diakses secara public
### Kriteria Selesai F-07 [DB]
 
```
□ Tabel 'dokumen_upload' terbuat dengan semua enum status yang benar
□ Tabel 'dokumen_chunk' terbuat dengan urutan yang benar (tabel → self-ref FK → index)
□ Index HNSW pada kolom 'embedding' ada dan aktif
□ Index GIN pada kolom 'teks_search' ada dan aktif
□ Index B-tree pada evaluasi_id, vendor_id, parent_chunk_id ada di dokumen_chunk
□ Bucket 'vendor-documents' terbuat sebagai private
□ Storage policy mencegah akses file lintas evaluasi
□ Verifikasi: pgvector similarity search berjalan tanpa error pada dokumen_chunk kosong
```
 
---
 
## F-08 — Form Preferensi Opsional
 
**Tier:** 2 | **Prerequisite:** F-06 | **Estimasi:** ~0.5 hari
 
### Yang Perlu Dibuat
 
#### Tambah Kolom `preferensi_perusahaan` ke Tabel `evaluasi`
 
```
File: 20260611090000_add_preferensi_perusahaan_to_evaluasi.sql
```
 
Tambahkan kolom `preferensi_perusahaan` (Text, nullable) ke tabel `evaluasi` yang sudah ada. Ini adalah perubahan additive yang aman — kolom nullable tidak membutuhkan default value dan tidak akan mempengaruhi data yang sudah ada.
 
```sql
-- Migration: tambah kolom preferensi_perusahaan ke tabel evaluasi
-- Rollback: ALTER TABLE evaluasi DROP COLUMN preferensi_perusahaan;
ALTER TABLE evaluasi ADD COLUMN preferensi_perusahaan TEXT;
```
 
**Tidak perlu menambahkan CHECK constraint untuk max 1.000 karakter di database** — validasi ini dilakukan di level aplikasi (BE-02). Constraint di database boleh ditambahkan sebagai safety net opsional di iterasi berikutnya.
 
### Kriteria Selesai F-08 [DB]
 
```
□ Kolom 'preferensi_perusahaan' ada di tabel evaluasi (TEXT, nullable)
□ Data yang sudah ada di tabel evaluasi tidak terpengaruh (semua row baru punya nilai NULL di kolom baru)
□ Migration berjalan bersih tanpa error
```
 
---
 
## F-09 — Submit, Status Flow & Approval
 
**Tier:** 2 | **Prerequisite:** F-06, F-04 | **Estimasi:** ~1 hari
 
### Yang Perlu Dibuat
 
#### 1. Tabel `approval_log`
 
```
File: 20260611090500_create_approval_log_table.sql
```
 
Bergantung pada `evaluasi` dan `user`. Kolom sesuai DB-01 section 6.10: `id`, `evaluasi_id` (FK ke `evaluasi.id`), `manager_id` (FK ke `user.id`), `keputusan` (enum: `approved` | `rejected`), `komentar` (nullable — tapi wajib diisi jika `keputusan = 'rejected'`, validasi ini di level aplikasi), plus `created_at`, `updated_at`, `deleted_at`.
 
**Catatan:** Tabel ini menyimpan riwayat semua keputusan (bukan hanya yang terakhir) — satu evaluasi bisa memiliki banyak row jika ada siklus reject-revise-resubmit.
 
**Index:**
- B-tree pada `evaluasi_id` — query riwayat approval satu evaluasi
**RLS:**
- Staff hanya bisa SELECT approval_log dari evaluasi miliknya
- Manager bisa SELECT semua dan INSERT keputusan baru
#### 2. Verifikasi Aturan Transisi Status
 
Pastikan transisi status di tabel `evaluasi` sesuai dengan lifecycle yang didefinisikan DB-01 section 8.1:
 
```
draft → processing → selesai → menunggu_approval → approved
                                                  → butuh_revisi
```
 
Aturan ini diimplementasikan di level aplikasi (bukan constraint database), tetapi perlu didokumentasikan dan diverifikasi bersama tim backend bahwa transisi yang tidak valid (misal dari `draft` langsung ke `approved`) tidak bisa dilakukan.
 
### Kriteria Selesai F-09 [DB]
 
```
□ Tabel 'approval_log' terbuat dengan FK, index, dan RLS
□ Transisi status evaluasi terverifikasi mengikuti lifecycle yang benar
□ RLS: staff tidak bisa INSERT ke approval_log (hanya manager)
□ RLS: staff bisa SELECT approval_log dari evaluasinya sendiri
```
 
---
 
## Checkpoint Integrasi Tier 1–2
 
Sebelum memulai Tier 3, lakukan verifikasi database menyeluruh:
 
### Verifikasi Skema
 
```sql
-- Verifikasi semua 10 tabel ada
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
 
-- Hasilnya harus mencakup:
-- agent_progress, approval_log, dokumen_chunk, dokumen_upload,
-- evaluasi, hasil_evaluasi, hasil_vendor, konfigurasi_kriteria, user, vendor
```
 
### Verifikasi Index
 
```sql
-- Verifikasi semua index utama ada
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```
 
Index yang wajib ada: `idx_evaluasi_created_by_status_deleted_at`, `idx_vendor_evaluasi_id`, `idx_dokumen_chunk_evaluasi_id`, `idx_dokumen_chunk_embedding` (HNSW), `idx_dokumen_chunk_teks_search` (GIN), `idx_agent_progress_evaluasi_id`, `idx_hasil_vendor_hasil_evaluasi_id`, `idx_konfigurasi_kriteria_kategori`.
 
### Verifikasi RLS
 
```sql
-- Verifikasi RLS aktif di semua tabel
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
-- Semua tabel harus menunjukkan rowsecurity = true
```
 
### Verifikasi Performa Awal (dengan data sintetis)
 
Isi database dengan data sintetis minimal:
- 100 evaluasi (campuran semua status)
- 500 vendor (5 rata-rata per evaluasi)
- 200 dokumen_upload
- 1.000 dokumen_chunk dengan embedding dummy
Jalankan `EXPLAIN ANALYZE` untuk semua query utama dari DB-03 section 4 dan verifikasi tidak ada Seq Scan pada tabel besar.
 
```
□ Semua 10 tabel ada di public schema
□ Semua index dari DB-01 section 9 sudah terbuat
□ RLS aktif di semua tabel
□ EXPLAIN ANALYZE query daftar evaluasi menggunakan composite index (bukan Seq Scan)
□ EXPLAIN ANALYZE query hasil evaluasi lengkap < 150ms dengan data sintetis
□ pgvector similarity search berjalan tanpa error pada tabel dengan data
□ Tidak ada migration yang tertinggal antara dev dan staging
```
 
---
 
## F-10 — AI Processing & Progress Real-time
 
**Tier:** 3 | **Prerequisite:** F-06, F-07, Checkpoint Tier 1–2 | **Estimasi:** ~1 hari
 
### Yang Perlu Dibuat
 
#### 1. Verifikasi Enum `agent_key` di Tabel `agent_progress`
 
Verifikasi bahwa enum `agent_key` sudah mencakup semua 7 agent yang benar sesuai DB-01 section 8.3:
 
```
data_collector, financial_analyzer, risk_assessor, performance_scorer,
negotiation_assistant, qualitative_analyzer, preference_matcher
```
 
Jika ada agent yang belum masuk ke enum (misalnya jika tabel dibuat sebelum spec difinalisasi), tambahkan via migration:
 
```sql
-- Migration: tambah nilai ke enum agent_key jika belum ada
ALTER TYPE agent_key_enum ADD VALUE IF NOT EXISTS 'qualitative_analyzer';
ALTER TYPE agent_key_enum ADD VALUE IF NOT EXISTS 'preference_matcher';
```
 
**Catatan:** PostgreSQL mengizinkan menambah nilai ke enum (`ADD VALUE`) tetapi tidak mengizinkan menghapus nilai. Pastikan nama enum benar sebelum ditambahkan.
 
#### 2. Verifikasi Index `agent_progress`
 
Verifikasi index B-tree pada `evaluasi_id` ada dan digunakan:
 
```sql
EXPLAIN ANALYZE 
SELECT * FROM agent_progress 
WHERE evaluasi_id = '[uuid]' AND deleted_at IS NULL;
```
 
Query ini harus menggunakan index, bukan Seq Scan.
 
#### 3. Verifikasi Supabase Realtime
 
Konfirmasi Realtime aktif untuk tabel `agent_progress` dari Supabase dashboard:
- Masuk ke Supabase dashboard → Database → Replication
- Pastikan tabel `agent_progress` ada di daftar tables yang di-replicate
### Kriteria Selesai F-10 [DB]
 
```
□ Enum agent_key mencakup semua 7 agent dengan nama yang tepat
□ Index evaluasi_id di agent_progress digunakan oleh query (EXPLAIN ANALYZE)
□ Supabase Realtime aktif dan bisa menerima broadcast dari tabel agent_progress
□ Uji manual: update satu row agent_progress → perubahan terbroadcast ke subscriber Realtime
```
 
---
 
## F-11 — Hasil TOPSIS & Reasoning
 
**Tier:** 3 | **Prerequisite:** F-10 | **Estimasi:** ~0.5 hari
 
### Yang Perlu Dibuat
 
#### Verifikasi Schema `hasil_evaluasi` dan `hasil_vendor`
 
Tidak ada migration baru. Verifikasi bahwa schema sudah konsisten dengan output yang akan ditulis scoring engine:
 
**Verifikasi tabel `hasil_evaluasi`:**
- Kolom `preference_matching_result` (JSONB, nullable) ada
- Kolom `conflict_callout` (JSONB, nullable) ada
- Kolom `summary_komparatif_kualitatif` (Text, nullable) ada
- Kolom `konfigurasi_snapshot` (JSONB, NOT NULL) ada
- UNIQUE constraint pada `evaluasi_id` aktif
**Verifikasi tabel `hasil_vendor`:**
- Kolom `unique_offerings` (JSONB, nullable) ada
- Kolom `profil_kualitatif` (Text, nullable) ada
- Kolom `tingkat_kesesuaian_preferensi` (enum, nullable) ada
- Index B-tree pada `hasil_evaluasi_id` ada
Verifikasi ini penting karena scoring engine menulis ke kedua tabel ini dalam **satu transaksi atomik** — jika schema tidak sesuai, transaksi akan gagal dengan error yang sulit di-debug saat runtime.
 
### Kriteria Selesai F-11 [DB]
 
```
□ Schema hasil_evaluasi konsisten dengan output scoring engine (semua kolom ada dan tipe data benar)
□ Schema hasil_vendor konsisten (kolom kualitatif dan preferensi ada dengan tipe yang benar)
□ UNIQUE constraint pada hasil_evaluasi.evaluasi_id aktif dan diuji
□ Uji manual: INSERT dua row ke hasil_evaluasi dengan evaluasi_id yang sama → harus gagal dengan constraint violation
```
 
---
 
## F-12 — Profil Kualitatif
 
**Tier:** 3 | **Prerequisite:** F-10, F-11 | **Estimasi:** ~0.5 hari
 
### Yang Perlu Dibuat
 
#### Verifikasi Kolom Kualitatif di `hasil_vendor`
 
Verifikasi kolom `unique_offerings` dan `profil_kualitatif` ada di tabel `hasil_vendor` (sudah dibuat di F-06). Tidak ada migration baru kecuali ternyata ada yang terlewat.
 
```sql
-- Verifikasi kolom ada
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'hasil_vendor' 
  AND column_name IN ('unique_offerings', 'profil_kualitatif');
```
 
Jika kolom belum ada karena alasan apapun, tambahkan via migration additive.
 
### Kriteria Selesai F-12 [DB]
 
```
□ Kolom unique_offerings (JSONB, nullable) ada di hasil_vendor
□ Kolom profil_kualitatif (Text, nullable) ada di hasil_vendor
□ Backend bisa menulis ke kedua kolom ini (verifikasi dari output agent F-10)
```
 
---
 
## F-13 — Rekomendasi Preferensi & Conflict Callout
 
**Tier:** 3 | **Prerequisite:** F-08, F-12 | **Estimasi:** ~0.5 hari
 
### Yang Perlu Dibuat
 
#### Verifikasi Kolom Preferensi
 
Verifikasi semua kolom yang dibutuhkan Preference Matcher sudah ada:
 
**Di tabel `hasil_evaluasi`:**
- `preference_matching_result` (JSONB, nullable) — output lengkap PM
- `conflict_callout` (JSONB, nullable) — info konflik jika ada
**Di tabel `hasil_vendor`:**
- `tingkat_kesesuaian_preferensi` (enum, nullable) — nilai: `tinggi`, `sedang`, `rendah`, `tidak_relevan`
```sql
-- Verifikasi semua kolom preferensi ada
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('hasil_evaluasi', 'hasil_vendor')
  AND column_name IN ('preference_matching_result', 'conflict_callout', 'tingkat_kesesuaian_preferensi');
```
 
### Kriteria Selesai F-13 [DB]
 
```
□ Kolom preference_matching_result ada di hasil_evaluasi (JSONB, nullable)
□ Kolom conflict_callout ada di hasil_evaluasi (JSONB, nullable)
□ Kolom tingkat_kesesuaian_preferensi ada di hasil_vendor dengan enum yang benar
□ Backend bisa menulis ke semua kolom ini tanpa error
```
 
---
 
## F-14 — AI Chat Panel + RAG
 
**Tier:** 3 | **Prerequisite:** F-07, F-11 | **Estimasi:** ~0.5 hari
 
### Yang Perlu Dibuat
 
#### Verifikasi Index Vector dan Full-Text di `dokumen_chunk`
 
Ini adalah hot path sistem — setiap pertanyaan ke AI Chat Panel memicu hybrid search ke tabel ini. Verifikasi bahwa kedua index sudah ada dan digunakan:
 
```sql
-- Verifikasi index HNSW ada
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'dokumen_chunk' 
  AND indexname LIKE '%embedding%';
 
-- Verifikasi index GIN ada
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'dokumen_chunk' 
  AND indexname LIKE '%teks_search%';
```
 
Uji query hybrid search secara manual dengan dummy data:
 
```sql
-- Test vector similarity search
SELECT id, teks_chunk, 
       embedding <=> '[0.1, 0.2, ...]'::vector AS distance
FROM dokumen_chunk 
WHERE evaluasi_id = '[uuid]' 
  AND is_parent = false
  AND deleted_at IS NULL
ORDER BY distance
LIMIT 5;
```
 
```sql
-- Test full-text search
SELECT id, teks_chunk,
       ts_rank(teks_search, plainto_tsquery('indonesian', 'harga pengiriman')) AS rank
FROM dokumen_chunk
WHERE evaluasi_id = '[uuid]'
  AND teks_search @@ plainto_tsquery('indonesian', 'harga pengiriman')
  AND deleted_at IS NULL
ORDER BY rank DESC
LIMIT 5;
```
 
Kedua query harus menggunakan index (verifikasi dengan `EXPLAIN ANALYZE`) dan tidak menghasilkan error.
 
### Kriteria Selesai F-14 [DB]
 
```
□ Index HNSW pada dokumen_chunk.embedding ada dan digunakan untuk vector similarity search
□ Index GIN pada dokumen_chunk.teks_search ada dan digunakan untuk full-text search
□ Query hybrid search manual (vector + full-text) berjalan tanpa error
□ EXPLAIN ANALYZE hybrid search tidak menunjukkan Seq Scan pada tabel dengan data
```
 
---
 
## Checkpoint Final — Release Readiness
 
### Verifikasi Performa Final
 
Isi database dengan data representatif volume production (bukan data test):
- 500+ evaluasi dengan berbagai status
- 2.000+ vendor
- 1.000+ dokumen_upload
- 10.000+ dokumen_chunk dengan embedding nyata dari OpenAI
Jalankan semua query target dari DB-03 section 10 dan verifikasi P95 tercapai:
 
| Query | Target P95 |
|---|---|
| Daftar evaluasi (20 item) | < 100ms |
| Detail evaluasi + vendor | < 80ms |
| Hasil evaluasi lengkap | < 150ms |
| Status agent (read) | < 50ms |
| Write agent progress | < 30ms |
| Konfigurasi kriteria (dari cache) | < 10ms |
 
### Verifikasi Backup Production
 
Sebelum go-live:
- Aktifkan Supabase Pro tier (bukan Free tier) — wajib untuk PITR
- Verifikasi backup otomatis pertama sudah dibuat
- Lakukan restore test ke environment staging terpisah dan verifikasi integritas data
- Konfigurasi backup off-platform (harian ke S3/GCS) sesuai DB-04 section 5.3
### Setup Cleanup Job
 
Buat scheduled job untuk menjalankan cleanup data terjadwal sesuai DB-04 section 9:
- Frekuensi: seminggu sekali, traffic rendah
- Grace period sebelum hard delete: 90 hari untuk evaluasi dan data terkait
- Jalankan dalam batch kecil (maks 1.000 row per batch) untuk menghindari lock panjang
### Verifikasi Concurrent Write
 
Simulasikan 5 evaluasi diproses bersamaan:
- 5 × 7 agent = 35 write concurrent ke tabel `agent_progress`
- Verifikasi tidak ada deadlock
- Verifikasi semua 35 row ter-update dengan benar
### Checklist Final [DB]
 
```
□ Semua query memenuhi target P95 dari DB-03 section 10 (diukur dengan data representatif)
□ Tidak ada deadlock saat 5 evaluasi diproses bersamaan
□ Supabase Pro aktif di production, PITR dikonfirmasi berfungsi
□ Restore test berhasil: backup terbaru ter-restore dengan data integritas penuh
□ Cleanup job terkonfigurasi dan sudah diuji di staging
□ Monitoring slow query aktif (threshold 500ms dari DB-03 section 9.2)
□ Alert backup terkonfigurasi (usia backup > 25 jam → notifikasi)
□ Semua pipeline CI di repo vendor-ai hijau
```
 
---
 
## Referensi Cepat — Urutan Semua Migration
 
Urutan lengkap migration dari awal hingga akhir:
 
| Urutan | File Migration | Dibuat di Fitur |
|---|---|---|
| 1 | `enable_pgvector.sql` | F-00 |
| 2 | `create_user_table.sql` | F-00 |
| 3 | `create_konfigurasi_kriteria_table.sql` | F-00 |
| 4 | `create_evaluasi_table.sql` | F-04 |
| 5 | `create_vendor_table.sql` | F-04 |
| 6 | `create_agent_progress_table.sql` | F-06 |
| 7 | `create_hasil_evaluasi_table.sql` | F-06 |
| 8 | `create_hasil_vendor_table.sql` | F-06 |
| 9 | `create_dokumen_upload_table.sql` | F-07 |
| 10 | `create_dokumen_chunk_table.sql` | F-07 |
| 11 | `create_dokumen_chunk_indexes.sql` | F-07 (migration terpisah untuk HNSW + GIN) |
| 12 | `add_preferensi_perusahaan_to_evaluasi.sql` | F-08 |
| 13 | `create_approval_log_table.sql` | F-09 |
 
---
 
## Referensi Cepat — RLS per Tabel
 
| Tabel | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| `user` | Diri sendiri | Via Auth trigger | Diri sendiri | Tidak diizinkan |
| `evaluasi` | Staff: miliknya; Manager: semua | User authenticated | Staff: miliknya; Manager: status approval | Tidak diizinkan (soft delete) |
| `vendor` | Mengikuti evaluasi induk | Mengikuti evaluasi induk | Mengikuti evaluasi induk | Tidak diizinkan (soft delete) |
| `dokumen_upload` | Mengikuti evaluasi induk | Mengikuti evaluasi induk | Mengikuti evaluasi induk | Tidak diizinkan |
| `dokumen_chunk` | Mengikuti evaluasi induk (wajib filter evaluasi_id) | Backend only | Backend only | Tidak diizinkan |
| `agent_progress` | Mengikuti evaluasi induk | Backend only | Backend only | Tidak diizinkan |
| `hasil_evaluasi` | Mengikuti evaluasi induk | Backend only | Backend only | Tidak diizinkan |
| `hasil_vendor` | Mengikuti evaluasi induk | Backend only | Backend only | Tidak diizinkan |
| `konfigurasi_kriteria` | Semua authenticated | Tidak diizinkan | Manager only | Tidak diizinkan (soft delete) |
| `approval_log` | Staff: dari evalnya; Manager: semua | Manager only | Tidak diizinkan | Tidak diizinkan |
 
---
 
*Dokumen ini adalah panduan kerja operasional yang harus selalu sinkron dengan spesifikasi di DB-01, DB-02, DB-03, dan DB-04. Jika ada perubahan spec, panduan ini perlu diperbarui sebelum task implementasi dimulai.*
 
---
 
**Riwayat Perubahan**
 
| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-12 | Versi awal | — |
| 2.0.0 | 2026-06-12 | Adopsi 2-repo (ADR-031): perbarui section Prasyarat (vendor-ai-backend → supabase/migrations/ di dalam vendor-ai, hapus branch db/develop, klarifikasi tidak ada repo terpisah untuk DB), perbarui kriteria selesai F-00 (path migration dan FEATURE_STATUS.md), perbarui checklist final (repo vendor-ai), perbarui referensi MILESTONE_PLAN ke v4.0.0 | — |