# DB-04 — Backup & Data Retention Specification

**Project:** AI Vendor Selection System  
**Dokumen:** DB-04 — Backup & Data Retention  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-07  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip Backup & Retensi](#3-prinsip-backup--retensi)
4. [Klasifikasi Data](#4-klasifikasi-data)
5. [Strategi Backup Database](#5-strategi-backup-database)
6. [Strategi Backup File (Supabase Storage)](#6-strategi-backup-file-supabase-storage)
7. [Restore Procedure](#7-restore-procedure)
8. [Kebijakan Retensi Data](#8-kebijakan-retensi-data)
9. [Cleanup Data Terjadwal](#9-cleanup-data-terjadwal)
10. [Monitoring & Alerting](#10-monitoring--alerting)
11. [Aturan & Larangan](#11-aturan--larangan)
12. [Catatan untuk Dokumen Lanjutan](#12-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **bagaimana data dilindungi dari kehilangan** — jadwal backup, prosedur restore, dan kebijakan berapa lama data disimpan sebelum dihapus secara permanen.

Dokumen ini menjawab pertanyaan: apa yang terjadi jika database corrupt atau terhapus tidak sengaja, berapa lama data bisa dipulihkan, data apa yang boleh dihapus dan kapan, dan bagaimana memastikan backup benar-benar bisa digunakan saat dibutuhkan.

Dokumen ini **tidak** mendefinisikan implementasi teknis backup — itu diserahkan ke engineer dan tim infrastructure.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| DB-01 | Data Model & ERD | Tabel yang perlu di-backup dan klasifikasi kritisitasnya |
| DB-02 | Migration Strategy | Backup wajib ada sebelum migration production |
| DB-03 | Query & Performance | Tabel yang paling sering diakses dan paling kritis |
| BE-03 | Auth & Security | Audit trail yang perlu dipertahankan |
| SH-02 | Deployment Runbook | Prosedur verifikasi backup sebelum deployment |

---

## 3. Prinsip Backup & Retensi

### 3.1 Backup yang tidak pernah ditest adalah backup yang tidak ada

Backup hanya bernilai jika bisa direstore dengan sukses. Backup yang belum pernah ditest restore-nya tidak memberikan jaminan apapun. Oleh karena itu, restore test dilakukan secara terjadwal — bukan hanya saat terjadi masalah.

### 3.2 3-2-1 Rule

Sistem mengikuti aturan backup 3-2-1:
- **3** salinan data (production + 2 backup)
- **2** media penyimpanan berbeda
- **1** salinan di lokasi geografis berbeda (off-site)

Supabase secara otomatis memenuhi sebagian besar aturan ini melalui infrastruktur cloud mereka — backup disimpan di multiple availability zones secara default.

### 3.3 Retensi data mengikuti kebutuhan bisnis dan regulasi

Berapa lama data disimpan ditentukan oleh dua faktor: kebutuhan bisnis (kapan data masih berguna) dan kebutuhan kepatuhan (apakah ada regulasi yang mensyaratkan retensi minimum). Untuk sistem pengadaan, kebutuhan audit internal umumnya mensyaratkan data disimpan minimal 2 tahun.

### 3.4 Data yang dihapus user tidak langsung hilang

Soft delete (yang sudah diterapkan di semua tabel — lihat DB-01) memberikan buffer waktu sebelum data benar-benar tidak bisa dipulihkan. Data yang di-soft delete masih ada di database dan di backup, sehingga pemulihan masih dimungkinkan dalam periode tertentu.

---

## 4. Klasifikasi Data

Tidak semua data memiliki tingkat kritisitas yang sama. Klasifikasi ini menentukan prioritas backup dan perlindungan yang diperlukan.

### 4.1 Kritis — tidak bisa direkonstruksi

Data yang jika hilang tidak bisa dibuat ulang dari sumber lain. Kehilangan data ini berdampak langsung pada operasional bisnis.

| Tabel/Data | Mengapa kritis |
|---|---|
| `evaluasi` | Catatan proses pengadaan yang sudah berjalan |
| `vendor` | Data vendor yang sudah diinput dengan effort signifikan |
| `hasil_evaluasi` + `hasil_vendor` | Keputusan AI yang menjadi dasar kontrak — tidak bisa di-generate ulang dengan hasil identik |
| `approval_log` | Bukti keputusan approval untuk keperluan audit |
| `konfigurasi_kriteria` | Konfigurasi yang menentukan bagaimana evaluasi dilakukan |

### 4.2 Penting — bisa direkonstruksi dengan effort

Data yang jika hilang bisa dibuat ulang, tetapi membutuhkan waktu dan upaya signifikan.

| Tabel/Data | Cara rekonstruksi |
|---|---|
| `user` | Dibuat ulang melalui Supabase Auth + input manual profil |
| `agent_progress` | Tidak perlu direkonstruksi — hanya relevan saat evaluasi sedang berjalan |
| `dokumen_upload` | Diminta ulang ke vendor |

### 4.3 File dokumen (Supabase Storage)

File dokumen penawaran vendor yang diupload ke Supabase Storage dikategorikan sebagai **penting** — bisa diminta ulang ke vendor jika hilang, tetapi membutuhkan effort komunikasi. File ini di-backup mengikuti jadwal yang sama dengan database.

---

## 5. Strategi Backup Database

### 5.1 Backup otomatis Supabase

Supabase menyediakan backup otomatis yang berbeda berdasarkan tier:

**Supabase Pro tier (minimum yang direkomendasikan untuk production):**
- Point-in-time recovery (PITR) dengan granularitas hingga 1 menit
- Backup harian yang disimpan selama 7 hari
- Backup mingguan yang disimpan selama 4 minggu

**Mengapa minimal Pro tier:** Free tier Supabase tidak menyediakan PITR — hanya backup harian tanpa kemampuan restore ke titik waktu tertentu. Untuk sistem pengadaan yang datanya sensitif, kemampuan PITR sangat penting jika terjadi data corruption yang baru terdeteksi beberapa jam setelah kejadian.

### 5.2 Backup tambahan sebelum migration

Selain backup otomatis Supabase, backup manual wajib dilakukan sebelum setiap migration production. Prosedur ini sudah didefinisikan di DB-02 section 10.3.

Backup manual ini disimpan terpisah dari backup otomatis Supabase — di luar platform Supabase — sebagai lapisan keamanan tambahan jika ada masalah dengan infrastruktur Supabase itu sendiri.

### 5.3 Jadwal backup tambahan (off-platform)

Untuk memenuhi prinsip 3-2-1 (section 3.2) dan memiliki salinan di luar Supabase:

| Frekuensi | Jenis | Disimpan selama | Lokasi |
|---|---|---|---|
| Harian | Full database dump | 30 hari | Cloud storage eksternal (S3 atau GCS) |
| Mingguan | Full database dump | 6 bulan | Cloud storage eksternal |
| Bulanan | Full database dump | 2 tahun | Cloud storage eksternal (cold storage) |

Backup harian dan mingguan menggunakan storage kelas standar untuk akses cepat saat dibutuhkan. Backup bulanan menggunakan cold storage (lebih murah) karena jarang diakses.

### 5.4 Enkripsi backup

Semua backup di-enkripsi sebelum disimpan di lokasi eksternal. Kunci enkripsi disimpan terpisah dari backup itu sendiri — disimpan di secret management service (misalnya AWS Secrets Manager atau Vault) yang aksesnya terbatas.

---

## 6. Strategi Backup File (Supabase Storage)

### 6.1 File dokumen penawaran

File yang diupload ke Supabase Storage bucket `vendor-documents` di-backup mengikuti jadwal yang sama dengan database:
- Backup harian ke cloud storage eksternal
- Disimpan selama 30 hari untuk backup harian, 6 bulan untuk mingguan

### 6.2 Sinkronisasi antara database dan file

Backup database dan backup file harus konsisten secara temporal — backup database tanggal X harus dipasangkan dengan backup file tanggal X yang sama. Ini memastikan saat restore, referensi file di database (`lampiran_url`, `file_url`) masih valid dan file yang dimaksud memang ada di storage.

### 6.3 File yang sudah soft-deleted

File yang terkait dengan evaluasi atau vendor yang sudah di-soft-delete tetap di-backup sampai proses cleanup permanen berjalan (section 9). Ini konsisten dengan pendekatan soft delete di seluruh sistem.

---

## 7. Restore Procedure

### 7.1 Kapan restore diperlukan

Restore diperlukan dalam tiga skenario:

**Skenario 1 — Data corruption:** Data di database corrupt akibat bug aplikasi atau kegagalan hardware. PITR Supabase digunakan untuk restore ke titik sebelum corruption terjadi.

**Skenario 2 — Penghapusan tidak sengaja:** User atau engineer menghapus data yang tidak seharusnya dihapus. Jika masih dalam periode soft delete, recovery bisa dilakukan langsung di database tanpa restore backup. Jika sudah melewati periode cleanup, gunakan backup.

**Skenario 3 — Kegagalan migration:** Migration production gagal dan data dalam kondisi tidak konsisten. Gunakan backup yang dibuat sebelum migration (DB-02 section 10.3).

### 7.2 Recovery Time Objective (RTO)

RTO adalah waktu maksimum yang dibutuhkan untuk memulihkan sistem setelah kegagalan.

| Skenario | Target RTO |
|---|---|
| Restore dari PITR Supabase | < 1 jam |
| Restore dari backup harian | < 4 jam |
| Restore dari backup mingguan/bulanan | < 8 jam |

### 7.3 Recovery Point Objective (RPO)

RPO adalah jumlah data maksimum yang boleh hilang, diukur dalam waktu.

| Jenis backup | RPO |
|---|---|
| PITR (Point-in-time Recovery) | < 1 menit |
| Backup harian | < 24 jam |
| Backup mingguan | < 7 hari |

Untuk sistem pengadaan MVP, RPO 24 jam dari backup harian dianggap acceptable — evaluasi tidak berjalan 24/7 secara terus-menerus sehingga kehilangan data maksimal satu hari kerja masih dapat diterima.

### 7.4 Prosedur restore

Prosedur restore didokumentasikan secara detail di SH-02 (Deployment Runbook). Di sini hanya prinsip-prinsip utamanya:

**Sebelum restore:** Pastikan akar masalah sudah diidentifikasi sebelum melakukan restore — restore ke environment yang masih memiliki masalah yang sama tidak akan menyelesaikan apapun.

**Restore ke environment staging dulu:** Setiap restore production harus diuji di staging terlebih dahulu untuk memverifikasi bahwa backup valid dan proses restore berjalan dengan benar.

**Verifikasi setelah restore:** Setelah restore selesai, lakukan serangkaian smoke test untuk memverifikasi integritas data — bukan hanya bahwa aplikasi bisa berjalan.

**Minimal dua orang hadir:** Sama seperti migration production, restore production memerlukan minimal dua orang.

### 7.5 Restore test terjadwal

Setiap bulan, tim melakukan restore test di environment terpisah untuk memverifikasi bahwa backup dapat digunakan. Test ini mendokumentasikan:
- Backup mana yang digunakan (tanggal dan jenis)
- Waktu yang dibutuhkan untuk restore
- Hasil verifikasi integritas data
- Masalah yang ditemukan dan cara mengatasinya

Hasil restore test dicatat dan disimpan sebagai bukti bahwa sistem backup berfungsi.

---

## 8. Kebijakan Retensi Data

### 8.1 Retensi data aktif (di database production)

Data aktif adalah data yang masih dalam penggunaan normal — belum di-soft-delete.

| Data | Retensi di database | Alasan |
|---|---|---|
| Evaluasi dan semua data terkait | Tidak ada batas (selama perusahaan beroperasi) | Data historis pengadaan memiliki nilai referensi jangka panjang |
| Log autentikasi | 1 tahun | Kebutuhan audit keamanan |
| `agent_progress` | 90 hari setelah evaluasi selesai | Tidak diperlukan untuk referensi jangka panjang |

### 8.2 Retensi data soft-deleted

Data yang sudah di-soft-delete (ditandai dengan `deleted_at` terisi) masih ada di database dalam periode grace period sebelum dihapus permanen.

| Tipe data | Grace period sebelum hard delete |
|---|---|
| Evaluasi dan semua data terkait | 90 hari |
| Vendor individual dalam evaluasi | 90 hari |
| File dokumen di Storage | 90 hari setelah evaluasi di-soft-delete |
| User yang dinonaktifkan | 1 tahun |

Grace period 90 hari memberikan waktu yang cukup untuk recovery jika penghapusan tidak disengaja, sekaligus tidak membiarkan data tidak terpakai menumpuk selamanya.

### 8.3 Retensi backup

Kebijakan retensi backup sudah didefinisikan di section 5.3 (tabel jadwal backup). Ringkasan:
- Backup harian: 30 hari
- Backup mingguan: 6 bulan
- Backup bulanan: 2 tahun

Setelah periode retensi habis, backup dihapus secara otomatis. Tidak perlu intervensi manual untuk cleanup backup.

### 8.4 Pengecualian retensi

Data yang terkait dengan evaluasi yang sedang dalam proses hukum atau audit formal tidak boleh dihapus meskipun melewati periode retensi normal. Pengecualian ini harus didokumentasikan secara eksplisit dan disetujui oleh tim legal atau manajemen.

---

## 9. Cleanup Data Terjadwal

### 9.1 Mengapa cleanup diperlukan

Tanpa cleanup terjadwal, data soft-deleted akan terus menumpuk di database — memperlambat query, membesar ukuran database, dan meningkatkan biaya storage. Cleanup otomatis memastikan database hanya berisi data yang relevan.

### 9.2 Proses cleanup

Cleanup dijalankan sebagai scheduled job seminggu sekali, pada hari dan jam dengan traffic paling rendah. Cleanup menjalankan dua operasi:

**Hard delete data yang melewati grace period:**
Menghapus permanen semua row yang `deleted_at`-nya sudah melewati grace period yang berlaku untuk tabel tersebut. Operasi dilakukan dalam batch kecil (maksimum 1.000 row per batch) untuk menghindari lock yang terlalu lama pada tabel.

**Cleanup file di Supabase Storage:**
Menghapus file di Storage bucket yang terkait dengan evaluasi atau vendor yang sudah melewati grace period. File yang terkait dengan evaluasi aktif tidak boleh tersentuh.

### 9.3 Verifikasi sebelum cleanup

Sebelum setiap cleanup job berjalan, sistem melakukan verifikasi:
- Backup terbaru tidak lebih dari 24 jam yang lalu
- Tidak ada migration yang sedang berjalan
- Database dalam kondisi healthy (tidak ada replication lag atau error aktif)

Jika verifikasi gagal, cleanup job dibatalkan dan alert dikirimkan ke tim.

### 9.4 Logging cleanup

Setiap cleanup job mencatat:
- Jumlah row yang dihapus per tabel
- Jumlah file yang dihapus dari Storage
- Durasi cleanup
- Apakah ada error yang terjadi

Log ini penting untuk audit dan untuk mendeteksi jika cleanup berjalan tidak normal (misalnya tiba-tiba menghapus jauh lebih banyak row dari biasanya).

---

## 10. Monitoring & Alerting

### 10.1 Metric backup yang dimonitor

| Metric | Threshold Alert | Aksi |
|---|---|---|
| Usia backup terbaru | > 25 jam | Investigasi mengapa backup otomatis tidak berjalan |
| Ukuran backup | Turun > 20% dari baseline | Kemungkinan data terhapus tidak sengaja |
| Durasi backup | > 2x dari baseline | Kemungkinan masalah performa atau ukuran data yang tumbuh tidak wajar |
| Hasil restore test bulanan | Gagal | Investigasi segera — backup tidak bisa diandalkan |

### 10.2 Dashboard backup

Tim infrastructure harus memiliki akses ke dashboard yang menampilkan:
- Status backup terbaru (berhasil/gagal, ukuran, durasi)
- Daftar backup yang tersedia beserta tanggal dan ukurannya
- Riwayat restore test
- Estimasi biaya storage backup

### 10.3 Notifikasi kegagalan backup

Kegagalan backup harian harus menghasilkan notifikasi segera ke tim on-call — bukan hanya dicatat di log. Backup adalah lapisan keamanan terakhir; kegagalannya tidak boleh diabaikan.

---

## 11. Aturan & Larangan

**Dilarang menjalankan hard delete secara manual** di luar proses cleanup terjadwal — kecuali dalam kasus pengecualian yang didokumentasikan dan disetujui. Semua penghapusan melalui aplikasi harus soft delete.

**Dilarang restore production tanpa restore test di staging terlebih dahulu.** Restore langsung ke production tanpa verifikasi di staging adalah risiko yang tidak perlu.

**Dilarang menyimpan kunci enkripsi backup bersama dengan backup itu sendiri.** Kunci enkripsi harus disimpan di lokasi terpisah yang aksesnya terbatas.

**Dilarang menghapus backup secara manual** sebelum periode retensinya habis — kecuali ada alasan keamanan yang terdokumentasi (misalnya backup mengandung data yang seharusnya tidak ada).

**Dilarang melewatkan restore test bulanan.** Jika satu bulan terlewat, harus dijadwalkan ulang di minggu berikutnya — bukan diabaikan sampai bulan berikutnya.

**Dilarang menjalankan cleanup job saat migration sedang berlangsung.** Kedua operasi ini dapat saling interfere dan menyebabkan kondisi data yang tidak konsisten.

---

## 12. Catatan untuk Dokumen Lanjutan

### Untuk SH-02 (Deployment Runbook)

Runbook perlu mendokumentasikan prosedur restore yang detail — langkah demi langkah untuk setiap skenario (PITR, backup harian, backup mingguan). Termasuk: cara mengakses backup di platform Supabase, cara menjalankan restore ke staging, dan smoke test yang perlu dijalankan setelah restore.

### Untuk SH-03 (Testing Strategy)

Restore test bulanan (section 7.5) perlu dimasukkan ke dalam kalender testing keseluruhan sistem. SH-03 perlu mendefinisikan kriteria pass/fail untuk restore test dan siapa yang bertanggung jawab menjalankan dan mendokumentasikan hasilnya.

### Untuk SH-04 (Cost & Usage Guide)

Biaya storage backup adalah bagian dari total cost of ownership sistem. SH-04 perlu memperhitungkan:
- Biaya Supabase Pro tier (termasuk PITR)
- Biaya cloud storage eksternal untuk backup off-platform (harian + mingguan + bulanan)
- Biaya cold storage untuk backup bulanan jangka panjang (2 tahun)

---

*Dokumen ini adalah living document — kebijakan backup dan retensi akan diperbarui sesuai pertumbuhan data dan kebutuhan compliance.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 2.0.0 | 2026-06-13 | Adopsi ADR-035 (namespace AI): perbarui tabel referensi (BE-06→BE-03 sesuai renumber) | — |
