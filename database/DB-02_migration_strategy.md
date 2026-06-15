# DB-02 — Migration Strategy Specification

**Project:** AI Vendor Selection System  
**Dokumen:** DB-02 — Migration Strategy  
**Versi:** 2.0.0  
**Tanggal:** 2026-06-11  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip Migration](#3-prinsip-migration)
4. [Tooling](#4-tooling)
5. [Urutan Pembuatan Tabel](#5-urutan-pembuatan-tabel)
6. [Strategi Versioning Migration](#6-strategi-versioning-migration)
7. [Seed Data](#7-seed-data)
8. [Zero-downtime Migration](#8-zero-downtime-migration)
9. [Rollback Plan](#9-rollback-plan)
10. [Alur Kerja Migration per Environment](#10-alur-kerja-migration-per-environment)
11. [Aturan & Larangan](#11-aturan--larangan)
12. [Catatan untuk Dokumen Lanjutan](#12-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **bagaimana skema database dibuat, diubah, dan dikelola** sepanjang masa hidup project — dari pembuatan awal hingga perubahan di production yang sudah berjalan.

Dokumen ini menjawab pertanyaan: bagaimana urutan tabel dibuat, bagaimana perubahan skema dikelola secara aman, apa yang dilakukan jika migration gagal, dan bagaimana memastikan production tidak pernah down saat migration berjalan.

Dokumen ini **tidak** mendefinisikan struktur tabel secara detail — itu adalah tanggung jawab DB-01.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| DB-01 | Data Model & ERD | Definisi tabel dan relasi yang dimigrasikan |
| DB-03 | Query & Performance | Index yang dibuat sebagai bagian dari migration |
| DB-04 | Backup & Retention | Backup yang harus ada sebelum migration production |
| SH-02 | Deployment Runbook | Prosedur deployment yang menyertakan migration |

---

## 3. Prinsip Migration

### 3.1 Migration adalah kode, bukan aksi manual

Setiap perubahan skema database — membuat tabel, menambah kolom, mengubah constraint, membuat index — harus ditulis sebagai migration file yang masuk ke version control. Tidak ada perubahan yang dilakukan langsung ke database melalui SQL manual atau Supabase dashboard tanpa migration file yang menyertainya.

**Mengapa:** Perubahan manual tidak bisa direproduksi, tidak bisa di-review, dan tidak bisa di-rollback dengan cara yang terkontrol. Migration file memastikan semua environment (development, staging, production) bisa mencapai state yang sama secara deterministik.

### 3.2 Setiap migration harus reversible

Setiap migration file harus memiliki pasangan rollback — instruksi untuk membatalkan perubahan yang dilakukan. Rollback ditulis bersamaan dengan migration, bukan setelah masalah terjadi.

### 3.3 Migration tidak boleh membuang data

Migration yang menghapus kolom atau tabel secara langsung berisiko kehilangan data yang tidak bisa dikembalikan. Pendekatan yang aman adalah deprecate dulu (biarkan kolom tetap ada tapi tidak digunakan), baru hapus di migration terpisah setelah dipastikan tidak ada kode yang merujuknya.

### 3.4 Migration production harus sudah diuji di staging

Setiap migration yang akan dijalankan di production wajib sudah berhasil dijalankan di staging environment terlebih dahulu — termasuk rollback-nya.

---

## 4. Tooling

### 4.1 Supabase CLI

Migration dikelola menggunakan **Supabase CLI**. Supabase CLI menyediakan perintah untuk membuat migration file baru, menjalankan migration, dan melihat status migration yang sudah dijalankan.

**Mengapa Supabase CLI, bukan tool migration lain:** Supabase CLI terintegrasi langsung dengan Supabase project — ia tahu tentang fitur-fitur spesifik Supabase seperti Row Level Security, Realtime publications, dan Storage buckets. Menggunakan tool generik seperti Flyway atau Liquibase akan membutuhkan konfigurasi tambahan dan tidak menangani fitur-fitur Supabase secara native.

### 4.2 Lokasi migration files

Semua migration files disimpan di folder `supabase/migrations/` dalam repository `vendor-ai-backend`. Folder ini masuk ke version control dan harus selalu dalam kondisi sinkron antara semua branch aktif.

### 4.3 Format nama file

Setiap migration file menggunakan format: `YYYYMMDDHHMMSS_deskripsi_singkat.sql`

Contoh:
- `20260607100000_create_user_table.sql`
- `20260607100500_create_evaluasi_table.sql`
- `20260615143000_add_index_evaluasi_status.sql`

Timestamp di awal nama file memastikan urutan eksekusi yang deterministik dan mencegah konflik saat dua developer membuat migration secara bersamaan.

---

## 5. Urutan Pembuatan Tabel

Tabel harus dibuat dalam urutan yang menghormati foreign key dependency — tabel yang dirujuk harus ada sebelum tabel yang merujuknya dibuat.

**Prasyarat — Aktivasi ekstensi pgvector:**

Sebelum tabel apapun dibuat, ekstensi pgvector harus diaktifkan di database. Ini harus menjadi migration pertama:

```sql
-- Migration: 20260607090000_enable_pgvector.sql
-- Rollback: DROP EXTENSION IF EXISTS vector;
CREATE EXTENSION IF NOT EXISTS vector;
```

Tanpa ekstensi ini, tabel `dokumen_chunk` yang menggunakan tipe kolom `vector(1536)` tidak bisa dibuat.

Urutan yang benar berdasarkan dependency di DB-01:

```
Tahap 0 — Prasyarat ekstensi
  └── Aktivasi pgvector

Tahap 1 — Tabel tanpa foreign key (berdiri sendiri)
  ├── user
  └── konfigurasi_kriteria

Tahap 2 — Tabel yang bergantung pada tahap 1
  └── evaluasi  (foreign key ke user)

Tahap 3 — Tabel yang bergantung pada tahap 2
  ├── vendor            (foreign key ke evaluasi)
  └── agent_progress    (foreign key ke evaluasi)

Tahap 4 — Tabel yang bergantung pada tahap 3
  ├── dokumen_upload    (foreign key ke evaluasi, vendor)
  └── hasil_evaluasi    (foreign key ke evaluasi, vendor)

Tahap 5 — Tabel yang bergantung pada tahap 4
  ├── dokumen_chunk     (foreign key ke dokumen_upload, vendor, evaluasi;
  │                      self-referential FK parent_chunk_id)
  ├── hasil_vendor      (foreign key ke hasil_evaluasi, vendor)
  └── approval_log      (foreign key ke evaluasi, user)
```

Setiap tahap dapat dibuat dalam satu migration file atau beberapa file terpisah, selama urutannya mengikuti dependency di atas.

### 5.1 Mengapa urutan ini penting

PostgreSQL akan menolak pembuatan foreign key constraint jika tabel yang dirujuk belum ada. Jika migration dijalankan dalam urutan yang salah, migration akan gagal dengan error constraint violation.

**Catatan khusus untuk tabel `dokumen_chunk`:** Tabel ini memiliki self-referential foreign key (`parent_chunk_id` → `dokumen_chunk.id`) yang harus ditambahkan setelah tabel dibuat, bukan bersamaan dengan pembuatan tabel. Urutan yang benar dalam satu migration file: buat tabel → buat kolom `parent_chunk_id` sebagai nullable tanpa FK → tambahkan FK constraint sebagai ALTER TABLE terpisah.

**Catatan khusus untuk index HNSW pgvector:** Index vektor HNSW di kolom `embedding` tabel `dokumen_chunk` tidak bisa dibuat menggunakan `CREATE INDEX CONCURRENTLY` — pgvector HNSW index memiliki mekanismenya sendiri. Index ini dibuat dalam migration terpisah setelah tabel dan data awal tersedia. Untuk MVP di mana tabel mulai kosong, index HNSW bisa dibuat bersamaan dengan tabel karena tidak ada locking concern pada tabel kosong.

### 5.2 Setup Row Level Security

RLS (Row Level Security) diaktifkan sebagai bagian dari migration yang sama dengan pembuatan tabel — bukan sebagai langkah terpisah. Mengaktifkan RLS setelah tabel sudah berisi data memerlukan perhatian khusus agar tidak memblokir operasi yang sedang berjalan.

Policy RLS untuk setiap tabel dibuat segera setelah tabel dibuat, dalam migration file yang sama.

---

## 6. Strategi Versioning Migration

### 6.1 Satu migration file per perubahan logis

Setiap migration file berisi satu perubahan logis yang kohesif. Membuat tabel `evaluasi` adalah satu migration. Menambahkan kolom baru ke tabel `evaluasi` adalah migration terpisah. Membuat index adalah migration tersendiri.

**Mengapa tidak menggabungkan semua dalam satu file besar:** Migration yang kecil dan fokus lebih mudah di-review, lebih mudah di-rollback jika bermasalah, dan memberikan riwayat perubahan yang lebih informatif.

### 6.2 Tidak boleh mengubah migration yang sudah dijalankan

Migration file yang sudah dijalankan di environment manapun tidak boleh diubah. Jika ada kesalahan di migration yang sudah dijalankan, buatlah migration baru yang memperbaiki kesalahan tersebut — jangan edit file yang sudah ada.

**Mengapa:** Supabase CLI melacak migration berdasarkan nama file dan checksumnya. Mengubah file yang sudah dijalankan akan menyebabkan konflik state yang sulit dipulihkan.

### 6.3 Status tracking

Supabase CLI menyimpan daftar migration yang sudah dijalankan di tabel internal `supabase_migrations.schema_migrations`. Status ini harus selalu konsisten antar environment — jika ada perbedaan, environment tersebut dianggap dalam kondisi tidak valid dan perlu diselaraskan sebelum migration baru dijalankan.

---

## 7. Seed Data

Seed data adalah data awal yang dibutuhkan aplikasi agar bisa berfungsi — bukan data testing, melainkan data konfigurasi yang memang harus ada.

### 7.1 Data yang perlu di-seed

**Konfigurasi kriteria default** — setiap kategori pengadaan perlu memiliki konfigurasi bobot kriteria awal. Tanpa ini, form pembuatan evaluasi tidak bisa berfungsi karena tidak ada konfigurasi yang bisa dimuat. Ini adalah satu-satunya seed data yang wajib ada.

**User admin pertama** — satu akun manager awal perlu dibuat agar ada yang bisa mengkonfigurasi sistem dan melakukan approval. Akun ini dibuat melalui Supabase Auth, bukan melalui migration SQL, karena pembuatan user melibatkan hashing password yang tidak boleh dilakukan di migration file.

### 7.2 Seed data bukan fixture testing

Data untuk keperluan testing (contoh evaluasi, contoh vendor, dll.) bukan seed data dan tidak termasuk dalam migration. Data testing dikelola terpisah dan tidak pernah masuk ke production.

### 7.3 Kapan seed dijalankan

Seed data dijalankan sekali setelah semua migration selesai pada setup environment baru. Seed tidak dijalankan ulang di environment yang sudah berjalan karena dapat menyebabkan data duplikat.

---

## 8. Zero-downtime Migration

Aplikasi harus tetap bisa diakses user selama migration berjalan di production. Ini memerlukan pendekatan khusus untuk beberapa jenis perubahan skema.

### 8.1 Perubahan yang aman (tidak memerlukan downtime)

Perubahan berikut dapat dijalankan kapan saja tanpa risiko mempengaruhi aplikasi yang sedang berjalan:

- Menambah kolom baru yang nullable atau memiliki default value
- Membuat tabel baru
- Membuat index baru (dengan `CONCURRENTLY` — lihat section 8.3)
- Menambah constraint yang tidak memvalidasi data yang sudah ada
- Menambah atau mengubah policy RLS

### 8.2 Perubahan yang berisiko (memerlukan prosedur khusus)

Perubahan berikut berisiko mempengaruhi aplikasi yang sedang berjalan dan memerlukan strategi expand-and-contract:

**Mengganti nama kolom:** Tidak boleh dilakukan langsung. Prosedur yang aman: tambah kolom baru dengan nama baru → deploy kode yang menulis ke kedua kolom → migrasi data dari kolom lama ke baru → deploy kode yang hanya menggunakan kolom baru → hapus kolom lama.

**Mengubah tipe data kolom:** Serupa dengan rename — buat kolom baru dengan tipe yang benar, migrasikan data, hapus yang lama.

**Menghapus kolom atau tabel:** Pastikan tidak ada kode yang masih merujuk kolom/tabel tersebut sebelum migration dijalankan. Deploy kode yang tidak lagi menggunakan kolom tersebut terlebih dahulu, baru jalankan migration.

**Menambah constraint NOT NULL ke kolom yang sudah ada:** Pastikan semua data yang ada sudah memenuhi constraint, atau isi nilai default terlebih dahulu.

### 8.3 Index dengan CONCURRENTLY

Membuat index pada tabel besar tanpa `CONCURRENTLY` akan mengunci tabel dan memblokir semua write operation selama proses berlangsung. Semua migration yang membuat index pada tabel yang sudah berisi data harus menggunakan opsi `CONCURRENTLY`.

**Catatan penting:** `CREATE INDEX CONCURRENTLY` tidak bisa dijalankan di dalam transaction block. Migration yang membuat index dengan CONCURRENTLY harus memiliki opsi `-- noqa: transaction` atau equivalent untuk memberitahu migration runner agar tidak membungkus perintah ini dalam transaction.

---

## 9. Rollback Plan

### 9.1 Rollback otomatis dalam transaction

Setiap migration file dijalankan dalam satu database transaction. Jika ada perintah yang gagal di tengah migration, seluruh migration dibatalkan secara otomatis dan database kembali ke state sebelumnya.

**Pengecualian:** Migration yang menggunakan `CONCURRENTLY` tidak bisa dijalankan dalam transaction (lihat section 8.3). Migration jenis ini perlu rollback manual.

### 9.2 Rollback manual

Setiap migration file memiliki pasangan rollback yang didokumentasikan di header file migration. Format yang digunakan:

```
-- Migration: menambah kolom lampiran_url ke tabel evaluasi
-- Rollback: ALTER TABLE evaluasi DROP COLUMN lampiran_url;
```

Jika migration sudah berhasil dijalankan tetapi perlu dibatalkan karena masalah aplikasi, rollback dilakukan dengan menjalankan perintah rollback secara manual melalui Supabase CLI atau SQL editor, lalu membuat migration baru yang mencerminkan state yang diinginkan.

### 9.3 Kapan rollback dilakukan

Rollback diputuskan dalam waktu maksimal **15 menit** setelah migration dijalankan di production. Jika dalam 15 menit tidak ada anomali yang terdeteksi (error rate, response time, alert monitoring), migration dianggap berhasil dan monitoring dilanjutkan secara normal.

Jika ada anomali, rollback segera dijalankan tanpa menunggu investigasi root cause selesai — investigasi dilakukan setelah sistem kembali stabil.

---

## 10. Alur Kerja Migration per Environment

### 10.1 Development (lokal)

Developer membuat migration file baru menggunakan Supabase CLI, menulis perubahan skema, dan mengujinya di database lokal. Rollback juga diuji di lokal sebelum push ke repository.

Tidak ada approval yang dibutuhkan untuk menjalankan migration di environment lokal.

### 10.2 Staging

Migration dijalankan secara otomatis sebagai bagian dari CI/CD pipeline ketika perubahan di-merge ke branch `staging`. Jika migration gagal di staging, deployment ke staging dihentikan dan tim diberi notifikasi.

Staging menggunakan database yang strukturnya identik dengan production tetapi berisi data sintetis — bukan data production yang sebenarnya.

### 10.3 Production

Migration di production **tidak dijalankan secara otomatis**. Setiap migration production memerlukan langkah-langkah berikut:

1. Pastikan migration sudah berhasil di staging minimal 24 jam sebelumnya
2. Pastikan backup production terbaru sudah ada (lihat DB-04)
3. Jalankan migration pada jam dengan traffic rendah (biasanya malam hari atau akhir pekan)
4. Monitor error rate dan response time selama 15 menit setelah migration
5. Siapkan rollback command yang siap dijalankan jika dibutuhkan

Dua orang harus hadir saat migration production dijalankan: satu yang menjalankan migration dan satu yang memonitor.

### 10.4 Sinkronisasi antar environment

State database di semua environment harus selalu bisa dicapai dengan menjalankan semua migration dari awal secara berurutan. Jika ada environment yang "ketinggalan" beberapa migration, jalankan migration yang tertinggal — jangan copy database dari environment lain.

---

## 11. Aturan & Larangan

**Dilarang mengubah database production secara manual** — melalui SQL editor Supabase dashboard atau tool lain — tanpa migration file. Setiap perubahan harus terlacak di version control.

**Dilarang mengedit migration file yang sudah dijalankan** di environment manapun. Buat migration baru untuk memperbaiki kesalahan.

**Dilarang menjalankan migration production tanpa backup** yang sudah diverifikasi. Lihat DB-04 untuk prosedur verifikasi backup.

**Dilarang membuat index besar tanpa CONCURRENTLY** di tabel yang sudah berisi data. Ini akan mengunci tabel dan menyebabkan downtime.

**Dilarang memasukkan data sensitif** (password, API key, PII) ke dalam migration file atau seed file karena file ini masuk ke version control.

**Dilarang menjalankan migration production sendirian** — selalu ada dua orang yang hadir.

---

## 12. Catatan untuk Dokumen Lanjutan

### Untuk DB-03 (Query & Performance)

Index yang perlu dibuat sebagai bagian dari migration sudah didefinisikan di DB-01 section 9 — termasuk index baru untuk `dokumen_chunk`: HNSW untuk vector search dan GIN untuk full-text search. DB-03 perlu memvalidasi bahwa semua index tersebut sudah masuk ke migration file yang sesuai dan menggunakan opsi yang benar.

### Untuk DB-04 (Backup & Retention)

Migration production memerlukan backup yang sudah diverifikasi sebagai prasyarat. DB-04 perlu mendefinisikan prosedur verifikasi backup yang bisa diselesaikan dalam waktu yang wajar sebelum jendela maintenance migration.

### Untuk SH-02 (Deployment Runbook)

Runbook deployment perlu menyertakan langkah-langkah migration sebagai bagian dari prosedur deployment production, termasuk urutan yang benar antara deployment kode baru dan eksekusi migration. Aktivasi pgvector harus menjadi langkah paling awal sebelum migration tabel apapun.

---

*Dokumen ini adalah living document — akan diperbarui jika ada perubahan tooling atau prosedur migration.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal — 9 tabel | — |
| 2.0.0 | 2026-06-11 | Tambah prasyarat aktivasi ekstensi pgvector (Tahap 0); tambah tabel `dokumen_chunk` di Tahap 5; tambah catatan khusus self-referential FK dan index HNSW pgvector | — |
