# DB-03 — Query & Performance Specification

**Project:** AI Vendor Selection System  
**Dokumen:** DB-03 — Query & Performance  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-07  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip Performa](#3-prinsip-performa)
4. [Query Patterns Utama](#4-query-patterns-utama)
5. [Indexing Strategy](#5-indexing-strategy)
6. [Caching Strategy](#6-caching-strategy)
7. [Pagination](#7-pagination)
8. [Query yang Perlu Diwaspadai](#8-query-yang-perlu-diwaspadai)
9. [Monitoring & Alerting](#9-monitoring--alerting)
10. [Target Performa](#10-target-performa)
11. [Catatan untuk Dokumen Lanjutan](#11-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **pola query yang digunakan**, **strategi indexing**, **strategi caching**, dan **target performa** yang harus dicapai aplikasi dari sisi database.

Dokumen ini menjawab pertanyaan: query apa yang paling sering dijalankan, index apa yang diperlukan untuk mengoptimalkannya, kapan caching digunakan, dan bagaimana performa dimonitor dan dijaga.

Dokumen ini **tidak** mendefinisikan cara penulisan kode query — itu diserahkan ke engineer. Dokumen ini mendefinisikan **apa** yang perlu dioptimalkan dan **mengapa**.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| DB-01 | Data Model & ERD | Struktur tabel dan relasi yang di-query |
| DB-02 | Migration Strategy | Index dibuat melalui migration file |
| BE-02 | API Contract | Endpoint yang memicu query ke database |
| AI-01 | Agent Orchestration | Pola write agent progress ke database |

---

## 3. Prinsip Performa

### 3.1 Optimasi berdasarkan data nyata, bukan asumsi

Index dan optimasi tidak ditambahkan secara spekulatif. Setiap keputusan optimasi harus didasarkan pada query yang benar-benar dijalankan aplikasi dengan frekuensi dan volume yang teridentifikasi. Index yang tidak digunakan menambah overhead write tanpa memberikan manfaat read.

### 3.2 Database bukan tempat untuk logika bisnis yang kompleks

Query ke database seharusnya untuk mengambil dan menyimpan data, bukan untuk menjalankan logika bisnis yang rumit. Kalkulasi seperti scoring TOPSIS, transformasi data kompleks, dan agregasi berat diselesaikan di level aplikasi (FastAPI) — bukan di stored procedure atau trigger.

**Pengecualian yang diizinkan:** Constraint validasi sederhana, trigger untuk `updated_at` otomatis, dan RLS policy yang menggunakan fungsi bawaan PostgreSQL.

### 3.3 Hindari N+1 query

N+1 query terjadi ketika aplikasi menjalankan satu query untuk mendapatkan daftar N item, lalu menjalankan satu query lagi untuk setiap item — total N+1 query. Pola ini harus dihindari dengan menggunakan JOIN atau mengambil data yang dibutuhkan dalam satu query.

### 3.4 Soft delete harus transparan

Semua query secara default harus menyertakan filter `WHERE deleted_at IS NULL` untuk mengecualikan data yang sudah dihapus. Ini harus diterapkan konsisten di semua query agar data yang dihapus tidak pernah muncul ke user.

---

## 4. Query Patterns Utama

Bagian ini mendokumentasikan query yang paling sering dijalankan, beserta tabel yang terlibat dan alasan mengapa query tersebut penting untuk dioptimalkan.

---

### 4.1 Query daftar evaluasi (Dashboard & Riwayat)

**Frekuensi:** Sangat tinggi — dijalankan setiap kali user membuka Dashboard atau Riwayat, dan di-refresh secara periodik.

**Tabel yang terlibat:** `evaluasi`, `user` (untuk nama pembuat)

**Karakteristik:**
- Selalu difilter berdasarkan `deleted_at IS NULL`
- Untuk staff: selalu difilter berdasarkan `created_by`
- Untuk manager: bisa tanpa filter `created_by`, atau dengan filter spesifik
- Filter opsional: `status`, `kategori`, rentang tanggal
- Hasil di-sort berdasarkan `updated_at DESC` sebagai default
- Hasil di-paginate (20 item per halaman)

**Mengapa penting dioptimalkan:** Ini adalah query yang paling sering dijalankan di seluruh aplikasi. Lambatnya query ini langsung terasa oleh semua user setiap kali mereka membuka aplikasi.

---

### 4.2 Query detail evaluasi + vendor (P-03, P-04, P-05)

**Frekuensi:** Tinggi — dijalankan setiap kali user membuka halaman detail evaluasi manapun.

**Tabel yang terlibat:** `evaluasi`, `vendor`

**Karakteristik:**
- Difilter berdasarkan `evaluasi.id` yang spesifik
- Menyertakan semua vendor yang terkait dengan evaluasi tersebut
- Vendor yang sudah soft-deleted tidak ditampilkan

**Mengapa penting:** Data ini ditampilkan di tiga halaman berbeda (P-03, P-04, P-05) dan menjadi fondasi untuk semua operasi terkait evaluasi.

---

### 4.3 Query hasil evaluasi lengkap (P-05)

**Frekuensi:** Sedang — dijalankan saat user membuka halaman hasil, biasanya setelah evaluasi selesai diproses.

**Tabel yang terlibat:** `hasil_evaluasi`, `hasil_vendor`, `vendor`

**Karakteristik:**
- Difilter berdasarkan `evaluasi_id`
- Menyertakan semua `hasil_vendor` untuk evaluasi tersebut
- Data ini relatif statis setelah scoring selesai — tidak berubah kecuali ada re-scoring

**Mengapa penting:** Halaman hasil adalah halaman terpenting di aplikasi. Lambatnya query ini akan merusak pengalaman di momen paling kritis.

---

### 4.4 Query status agent real-time (P-04)

**Frekuensi:** Sangat tinggi dalam periode burst — dijalankan setiap kali ada update dari Supabase Realtime, yang bisa terjadi setiap beberapa detik selama proses evaluasi berlangsung.

**Tabel yang terlibat:** `agent_progress`

**Karakteristik:**
- Difilter berdasarkan `evaluasi_id`
- Selalu mengambil state terbaru (bukan riwayat perubahan)
- Ditulis oleh FastAPI, dibaca oleh Supabase Realtime

**Mengapa penting:** Meskipun setiap query kecil, frekuensinya bisa sangat tinggi ketika banyak evaluasi sedang diproses bersamaan. Total beban query ini bisa signifikan.

---

### 4.5 Query daftar evaluasi pending approval (P-07)

**Frekuensi:** Sedang — dijalankan ketika manager membuka halaman Approval.

**Tabel yang terlibat:** `evaluasi`, `user`, `hasil_evaluasi`

**Karakteristik:**
- Selalu difilter berdasarkan `status = 'menunggu_approval'`
- Menyertakan nama staff pengaju
- Menyertakan ringkasan hasil evaluasi (nama vendor rekomendasi dan skornya)

**Mengapa ini bukan query sederhana:** Query ini membutuhkan join ke `hasil_evaluasi` untuk mendapatkan nama vendor rekomendasi dan skor, yang berarti tiga tabel terlibat.

---

### 4.6 Query konfigurasi kriteria (setiap evaluasi dimulai)

**Frekuensi:** Sedang — dijalankan setiap kali evaluasi baru disubmit untuk mendapatkan konfigurasi bobot yang aktif.

**Tabel yang terlibat:** `konfigurasi_kriteria`

**Karakteristik:**
- Difilter berdasarkan `kategori`
- Data ini sangat jarang berubah (hanya saat manager mengubah konfigurasi)
- Merupakan kandidat ideal untuk caching

---

### 4.7 Query write agent progress (FastAPI → Supabase)

**Frekuensi:** Sangat tinggi dalam periode burst — FastAPI menulis update status setiap kali ada progress dari agent.

**Tabel yang terlibat:** `agent_progress`

**Karakteristik:**
- Operasi UPDATE, bukan INSERT (satu row per agent per evaluasi, di-update terus)
- Harus cepat karena dilakukan di tengah proses agent yang sedang berjalan
- Kegagalan write tidak boleh menghentikan proses agent

**Mengapa penting:** Write yang lambat ke tabel ini akan memperlambat keseluruhan proses evaluasi karena agent menunggu konfirmasi write sebelum melanjutkan.

---

## 5. Indexing Strategy

Index yang didefinisikan di DB-01 section 9 dijabarkan lebih detail di sini dengan konteks query yang dilayaninya.

### 5.1 Index yang wajib ada sejak awal

Index berikut harus sudah ada saat aplikasi pertama kali di-deploy karena langsung dibutuhkan oleh query-query utama di section 4.

| Tabel | Kolom | Tipe | Melayani Query |
|---|---|---|---|
| `evaluasi` | `created_by` | B-tree | 4.1 — filter daftar evaluasi per staff |
| `evaluasi` | `status` | B-tree | 4.1, 4.5 — filter berdasarkan status |
| `evaluasi` | `deleted_at` | Partial (WHERE NULL) | 4.1 — semua query default |
| `evaluasi` | `updated_at` | B-tree | 4.1 — sorting default |
| `vendor` | `evaluasi_id` | B-tree | 4.2 — join vendor ke evaluasi |
| `agent_progress` | `evaluasi_id` | B-tree | 4.4, 4.7 — baca dan tulis progress |
| `hasil_evaluasi` | `evaluasi_id` | B-tree (unique) | 4.3, 4.5 — join hasil ke evaluasi |
| `hasil_vendor` | `hasil_evaluasi_id` | B-tree | 4.3 — ambil semua skor vendor |
| `konfigurasi_kriteria` | `kategori` | B-tree | 4.6 — lookup konfigurasi aktif |
| `approval_log` | `evaluasi_id` | B-tree | join riwayat approval |

### 5.2 Partial index untuk soft delete

Partial index pada `deleted_at IS NULL` di tabel `evaluasi` lebih efisien dari index biasa pada kolom `deleted_at` karena sebagian besar record tidak akan pernah di-soft-delete. Index partial hanya mengindeks row yang aktif — ukurannya jauh lebih kecil dan scan-nya lebih cepat.

Pola yang sama dapat diterapkan ke tabel lain yang sering di-query dengan filter `deleted_at IS NULL` jika diperlukan.

### 5.3 Composite index untuk filter gabungan

Query daftar evaluasi sering menggunakan filter gabungan antara `created_by` dan `status`. Composite index pada `(created_by, status)` lebih efisien dari dua index terpisah untuk query dengan kedua filter tersebut.

Composite index harus dibuat dengan urutan kolom yang paling selektif di depan. `created_by` (filter per user) lebih selektif dari `status` (hanya 6 nilai), sehingga urutannya adalah `(created_by, status, deleted_at)`.

### 5.4 Index yang tidak perlu di awal

Index berikut tidak perlu dibuat di awal karena query yang dilayaninya tidak cukup sering atau datanya tidak cukup banyak untuk membutuhkan index:

- Index pada kolom `kategori` di tabel `evaluasi` — filter ini jarang digunakan sendirian tanpa filter `created_by`
- Index pada `approval_log.manager_id` — tabel ini relatif kecil dan jarang di-query secara intensif

Index ini dapat ditambahkan kemudian berdasarkan data monitoring query aktual.

---

## 6. Caching Strategy

### 6.1 Apa yang di-cache dan di mana

Aplikasi menggunakan dua lapisan cache:

**TanStack Query cache di frontend** — dijelaskan di FE-04. Ini adalah cache di sisi client yang mengurangi jumlah request ke server.

**Cache di level aplikasi (Next.js)** — untuk data yang sangat jarang berubah dan dibaca sangat sering, Next.js dapat menyimpan cache di level server. Kandidat utamanya adalah konfigurasi kriteria dan daftar kategori pengadaan.

### 6.2 Data yang cocok untuk di-cache di server

| Data | TTL Rekomendasi | Alasan |
|---|---|---|
| Daftar kategori pengadaan | 24 jam | Hampir tidak pernah berubah |
| Konfigurasi bobot kriteria per kategori | 10 menit | Hanya berubah saat manager mengubahnya, tapi bisa berubah kapan saja |

### 6.3 Data yang tidak boleh di-cache di server

- Status evaluasi — berubah secara real-time, cache akan menyebabkan data stale yang terlihat oleh user
- Daftar evaluasi — berubah saat evaluasi baru dibuat atau status berubah
- Hasil evaluasi — meskipun relatif statis, ini adalah data yang sensitivitasnya tinggi dan harus selalu akurat

### 6.4 Cache invalidation

Konfigurasi kriteria yang di-cache harus di-invalidate segera setelah ada perubahan yang disimpan oleh manager. Mekanisme invalidasi dilakukan dari Next.js API Routes yang menangani endpoint `PUT /konfigurasi/kriteria` — setelah write ke database berhasil, cache di-invalidate.

---

## 7. Pagination

### 7.1 Mengapa pagination penting

Tanpa pagination, query daftar evaluasi akan mengembalikan semua data yang ada setiap kali halaman dibuka. Seiring waktu jumlah evaluasi bertambah, query ini akan semakin lambat dan response semakin besar.

### 7.2 Strategi pagination: offset-based

Untuk MVP, aplikasi menggunakan **offset-based pagination** — query menyertakan `LIMIT` dan `OFFSET` yang dihitung dari nomor halaman dan jumlah item per halaman.

**Kelebihan:** Sederhana, mudah diimplementasikan, mendukung navigasi langsung ke halaman tertentu.

**Kelemahan yang perlu disadari:** Jika data baru ditambahkan saat user sedang melihat halaman 2, beberapa item mungkin muncul dua kali atau terlewat karena offset bergeser. Untuk kasus penggunaan ini, kelemahan tersebut dianggap dapat ditoleransi.

### 7.3 Default dan batas pagination

- Default: 20 item per halaman
- Maksimum: 50 item per halaman
- Halaman pertama dimulai dari nomor 1 (bukan 0)

Response selalu menyertakan metadata pagination: nomor halaman saat ini, total item, dan total halaman — sehingga frontend bisa merender komponen pagination dengan benar.

---

## 8. Query yang Perlu Diwaspadai

Bagian ini mendokumentasikan query yang berpotensi bermasalah dan cara mengatasinya.

### 8.1 Query daftar evaluasi dengan banyak filter

Query daftar evaluasi mendukung filter gabungan (status + kategori + tanggal + created_by). Kombinasi filter yang berbeda bisa menghasilkan query plan yang sangat berbeda. Filter yang jarang digunakan mungkin tidak memiliki index yang sesuai.

**Cara mengatasi:** Monitor query plan untuk kombinasi filter yang paling sering digunakan menggunakan `EXPLAIN ANALYZE`. Tambahkan index composite jika ditemukan kombinasi yang sering digunakan tanpa index yang mendukung.

### 8.2 Query hasil evaluasi dengan banyak vendor

Jika satu evaluasi memiliki 10 vendor dan setiap vendor memiliki skor di 5 kriteria, query hasil evaluasi akan mengambil 10 row `hasil_vendor` dengan JSONB column yang cukup besar. Ini umumnya masih dalam batas yang aman, tetapi perlu dimonitor seiring bertambahnya data.

### 8.3 Write burst saat banyak evaluasi diproses bersamaan

Jika banyak evaluasi diproses bersamaan, tabel `agent_progress` akan menerima banyak UPDATE secara bersamaan dari FastAPI. PostgreSQL menangani concurrent write dengan baik, tetapi jika volume sangat tinggi, ini bisa menjadi bottleneck.

**Cara mengatasi untuk MVP:** Batasi jumlah evaluasi yang bisa diproses bersamaan di level aplikasi (misalnya maksimum 5 evaluasi aktif sekaligus per instance FastAPI). Batasan ini bisa dilonggarkan seiring dengan data performa aktual.

### 8.4 JSONB column yang membesar

Kolom `skor_per_kriteria` dan `catatan_per_kriteria` di tabel `hasil_vendor` adalah JSONB. Seiring waktu, jika struktur konfigurasi kriteria bertambah kompleks, ukuran JSONB ini bisa bertambah.

**Cara mengatasi:** Monitor ukuran rata-rata row di tabel `hasil_vendor` secara berkala. Jika ukuran JSONB mulai tidak wajar, pertimbangkan normalisasi ke tabel terpisah di iterasi berikutnya.

---

## 9. Monitoring & Alerting

### 9.1 Metric yang perlu dimonitor

**Query performance:**
- Durasi rata-rata query per endpoint (dari log aplikasi)
- Query dengan durasi di atas threshold (slow query log)
- Jumlah query per detik per tabel

**Database health:**
- Ukuran database total dan per tabel
- Ukuran dan penggunaan index
- Jumlah koneksi aktif vs maksimum

**Error:**
- Query yang gagal karena constraint violation
- Deadlock yang terdeteksi

### 9.2 Slow query threshold

Query yang membutuhkan waktu lebih dari **500ms** dianggap slow query dan harus diinvestigasi. Supabase menyediakan log query yang bisa diaktifkan untuk menangkap slow query secara otomatis.

**Mengapa 500ms:** Ini adalah threshold yang wajar untuk query database dalam konteks aplikasi web. User mulai merasakan keterlambatan pada 300-500ms. Query database seharusnya berkontribusi paling banyak 100-200ms dari total response time — threshold 500ms memberikan ruang untuk investigasi sebelum benar-benar mempengaruhi UX.

### 9.3 Alert yang perlu dikonfigurasi

| Kondisi | Aksi |
|---|---|
| Slow query > 500ms lebih dari 10x dalam 5 menit | Notifikasi ke tim database |
| Jumlah koneksi > 80% dari maksimum | Notifikasi ke tim infrastructure |
| Ukuran database tumbuh > 20% dalam sehari | Investigasi data anomali |
| Error rate query > 1% | Notifikasi segera ke tim on-call |

---

## 10. Target Performa

Target ini adalah baseline minimum yang harus dipenuhi — bukan aspirasi, melainkan kontrak performa yang harus dicapai sebelum release ke production.

| Query | Target Durasi (P95) | Kondisi |
|---|---|---|
| Daftar evaluasi (20 item, filter default) | < 100ms | Hingga 1.000 evaluasi total |
| Detail evaluasi + vendor | < 80ms | Hingga 10 vendor per evaluasi |
| Hasil evaluasi lengkap | < 150ms | Hingga 10 vendor dengan scoring |
| Status agent (read) | < 50ms | Per evaluasi |
| Write agent progress (update) | < 30ms | Per agent per update |
| Konfigurasi kriteria (dari cache) | < 10ms | Setelah cache warm |
| Konfigurasi kriteria (dari database) | < 50ms | Cache miss |

**P95 berarti:** 95% dari seluruh eksekusi query tersebut harus selesai dalam durasi yang ditargetkan. 5% sisanya boleh lebih lambat, tetapi tidak boleh melebihi 3x dari target.

**Kondisi pengujian:** Target ini diukur pada database yang sudah berisi data representatif — bukan database kosong. Engineer harus mengisi database dengan data sintetis yang merepresentasikan volume MVP sebelum mengukur performa.

---

## 11. Catatan untuk Dokumen Lanjutan

### Untuk DB-04 (Backup & Retention)

Backup yang efektif memerlukan pemahaman tentang tabel mana yang paling kritis dan berapa ukuran data yang diharapkan. Tabel `evaluasi`, `hasil_evaluasi`, dan `hasil_vendor` adalah tabel paling kritis dari sisi bisnis — kehilangannya tidak bisa dikembalikan dari sumber lain.

### Untuk AI-01 (Agent Orchestration)

Pola write ke `agent_progress` dari FastAPI perlu mempertimbangkan burst write yang terjadi saat banyak evaluasi diproses bersamaan. AI-01 perlu mendefinisikan batasan konkurensi untuk menghindari overload pada database.

### Untuk SH-02 (Deployment Runbook)

Sebelum release ke production, engineer perlu menjalankan pengujian performa dengan data sintetis untuk memvalidasi target di section 10 tercapai. Runbook perlu menyertakan langkah ini sebagai gate sebelum deployment production.

---

*Dokumen ini adalah living document — target performa dan strategi optimasi akan diperbarui berdasarkan data monitoring aktual dari production.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 2.0.0 | 2026-06-13 | Adopsi ADR-035 (namespace AI): perbarui tabel referensi dan catatan dokumen lanjutan (BE-03→AI-01) | — |
