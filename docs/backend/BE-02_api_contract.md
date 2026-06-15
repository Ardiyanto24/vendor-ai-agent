# BE-02 — API Contract Specification

**Project:** AI Vendor Selection System  
**Dokumen:** BE-02 — API Contract  
**Versi:** 3.0.0  
**Tanggal:** 2026-06-11  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Arsitektur Service](#3-arsitektur-service)
4. [Konvensi Umum](#4-konvensi-umum)
5. [Autentikasi & Otorisasi](#5-autentikasi--otorisasi)
6. [Kelompok 1 — Auth & User](#6-kelompok-1--auth--user)
7. [Kelompok 2 — Manajemen Evaluasi](#7-kelompok-2--manajemen-evaluasi)
8. [Kelompok 3 — AI Agent Orchestration](#8-kelompok-3--ai-agent-orchestration)
9. [Kelompok 4 — Scoring Engine](#9-kelompok-4--scoring-engine)
10. [Kelompok 5 — AI Chat](#10-kelompok-5--ai-chat)
11. [Real-time](#11-real-time)
12. [Error Handling](#12-error-handling)
13. [Daftar Lengkap Endpoint](#13-daftar-lengkap-endpoint)
14. [Catatan untuk Dokumen Lanjutan](#14-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **seluruh kontrak komunikasi** antara frontend dan backend — apa saja endpoint yang tersedia, data apa yang dikirim dan diterima, dan aturan apa yang berlaku.

Dokumen ini menjawab pertanyaan **what** (endpoint apa yang ada, data apa yang dipertukarkan) dan **why** (mengapa endpoint ini dibutuhkan, mengapa struktur data dirancang seperti ini). Cara implementasi diserahkan ke engineer.

Dokumen ini adalah **kontrak** — setiap perubahan endpoint yang berdampak pada frontend atau backend harus diperbarui di sini terlebih dahulu sebelum diimplementasi.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-03 | Page & User Flow | Halaman yang mengonsumsi endpoint ini |
| FE-02 | Component Library | Komponen yang membutuhkan data tertentu |
| FE-05 | API Integration | Pola konsumsi API di sisi frontend |
| DB-01 | Data Model & ERD | Struktur data yang dikembalikan endpoint |
| AI-01 | Agent Orchestration | Detail implementasi agent |
| AI-03 | Scoring Engine | Detail implementasi scoring |

---

## 3. Arsitektur Service

### 3.1 Dua service backend

Sistem menggunakan dua service backend dengan tanggung jawab yang berbeda.

**Next.js API Routes** menangani semua operasi yang bersifat standar dan ringan: autentikasi, CRUD data evaluasi, manajemen file, dan approval. Service ini adalah satu-satunya yang berbicara langsung dengan Supabase untuk operasi database standar.

**FastAPI (Python)** menangani semua yang berhubungan dengan kecerdasan buatan dan komputasi: orchestrasi agent, scoring engine, ekstraksi dokumen, dan chat AI. Python dipilih karena ekosistemnya yang unggul untuk ML/AI (LangChain, numpy, scipy, dll.).

**Mengapa dipisah:** Memisahkan beban komputasi AI dari operasi CRUD standar membuat keduanya bisa di-scale secara independen. Jika AI processing membutuhkan lebih banyak resource, hanya FastAPI yang perlu di-scale up tanpa mempengaruhi Next.js.

### 3.2 Siapa yang berbicara ke siapa

```
Browser → Next.js API Routes    (untuk semua operasi standar)
Browser → FastAPI               (hanya untuk SSE chat streaming)
Next.js → FastAPI               (untuk memicu proses AI secara internal)
Next.js → Supabase              (untuk semua operasi database)
FastAPI → Supabase              (untuk menulis progress agent real-time)
```

Frontend tidak perlu tahu alamat FastAPI kecuali untuk koneksi SSE. Semua komunikasi AI lainnya di-proxy melalui Next.js.

### 3.3 Database

Supabase dipilih sebagai database karena menyediakan tiga hal sekaligus yang dibutuhkan sistem ini: PostgreSQL sebagai database relasional yang handal, Storage untuk file dokumen penawaran vendor, dan Realtime untuk broadcast perubahan status agent ke frontend tanpa polling manual.

---

## 4. Konvensi Umum

### 4.1 Format data

Semua request dan response menggunakan format JSON. Upload file menggunakan multipart/form-data.

Semua response memiliki struktur seragam dengan field `success` (boolean), `data` (payload), dan `meta` (informasi tambahan seperti timestamp dan pagination). Response error memiliki field `error` berisi kode error dan pesan yang dapat ditampilkan ke user.

**Mengapa struktur seragam:** Frontend dapat menangani semua response dengan pola yang sama tanpa perlu logika khusus per endpoint.

### 4.2 Format waktu & angka

Semua tanggal dan waktu menggunakan format ISO 8601 UTC. Nilai uang disimpan dan dikirim sebagai integer dalam rupiah (tanpa desimal). Nilai skor dikirim sebagai desimal satu angka di belakang koma.

**Mengapa integer untuk uang:** Menghindari masalah presisi floating-point yang sering muncul saat mengolah nilai mata uang.

### 4.3 Versioning

Semua endpoint menggunakan prefix `/v1/`. Jika ada breaking change di masa depan, endpoint baru dibuat di `/v2/` tanpa menghapus `/v1/`. Ini memastikan frontend versi lama tidak rusak saat versi baru di-deploy.

---

## 5. Autentikasi & Otorisasi

### 5.1 Mekanisme autentikasi

Sistem menggunakan JWT (JSON Web Token) yang diterbitkan oleh Supabase Auth. Setiap request ke endpoint yang membutuhkan autentikasi wajib menyertakan token ini di header Authorization.

Token memiliki masa berlaku pendek (1 jam) untuk alasan keamanan. Refresh token dengan masa berlaku lebih panjang (7 hari) digunakan untuk memperbarui access token secara otomatis tanpa memaksa user login ulang.

### 5.2 Informasi role dalam token

Token JWT menyertakan informasi role user (staff atau manager). Ini memungkinkan setiap service memverifikasi hak akses tanpa perlu query database tambahan untuk setiap request.

### 5.3 Aturan akses berdasarkan role

Endpoint yang ditandai **Manager only** akan mengembalikan error 403 jika diakses oleh staff. Ini diberlakukan di level middleware, bukan di level logika bisnis.

---

## 6. Kelompok 1 — Auth & User

Endpoint autentikasi diproses oleh **Next.js API Routes** dan meneruskan ke Supabase Auth.

---

### Login

**Tujuan:** Memverifikasi identitas user dan mengembalikan token akses.

**Endpoint:** `POST /api/v1/auth/login`  
**Auth required:** Tidak  
**Digunakan di:** P-01

**Data yang dikirim:** Email dan password user.

**Data yang dikembalikan:** Access token, refresh token, dan informasi dasar user (id, nama, email, role, avatar).

**Mengapa role dikembalikan saat login:** Frontend membutuhkan role untuk menentukan menu mana yang ditampilkan di sidebar sejak halaman pertama setelah login, tanpa perlu request tambahan.

**Kondisi error:** Kredensial salah (401), terlalu banyak percobaan login dalam waktu singkat (429).

---

### Logout

**Tujuan:** Menginvalidasi sesi aktif user.

**Endpoint:** `POST /api/v1/auth/logout`  
**Auth required:** Ya  
**Digunakan di:** Sidebar (tombol Logout)

---

### Refresh Token

**Tujuan:** Memperbarui access token yang sudah atau akan segera expired tanpa memaksa user login ulang.

**Endpoint:** `POST /api/v1/auth/refresh`  
**Auth required:** Tidak (menggunakan refresh token)

**Mengapa endpoint ini perlu:** Access token sengaja dibuat berumur pendek (1 jam) untuk keamanan. Refresh token memungkinkan pengalaman user yang mulus tanpa harus login berulang.

---

### Profil User

**Tujuan:** Mengambil data lengkap user yang sedang login untuk ditampilkan di sidebar.

**Endpoint:** `GET /api/v1/users/me`  
**Auth required:** Ya  
**Digunakan di:** Sidebar

---

## 7. Kelompok 2 — Manajemen Evaluasi

Semua endpoint di kelompok ini diproses oleh **Next.js API Routes**.

---

### Daftar Evaluasi

**Tujuan:** Mengambil daftar evaluasi dengan kemampuan filter dan pagination.

**Endpoint:** `GET /api/v1/evaluasi`  
**Auth required:** Ya  
**Digunakan di:** P-02 (Dashboard), P-06 (Riwayat), P-07 (Approval)

**Filter yang tersedia:** Status, kategori pengadaan, kata kunci judul, tanggal pembuatan, dan filter berdasarkan pembuat (khusus Manager).

**Mengapa filter berdasarkan pembuat hanya untuk Manager:** Staff hanya boleh melihat evaluasi miliknya sendiri. Filter ini di-enforce di backend berdasarkan role, bukan hanya di frontend.

---

### Ringkasan Statistik

**Tujuan:** Mengambil jumlah evaluasi per status untuk ditampilkan di widget stat cards Dashboard.

**Endpoint:** `GET /api/v1/evaluasi/summary`  
**Auth required:** Ya  
**Digunakan di:** P-02

**Mengapa endpoint terpisah:** Data summary tidak membutuhkan detail evaluasi dan lebih efisien diambil terpisah daripada menghitung dari daftar lengkap.

---

### Detail Evaluasi

**Tujuan:** Mengambil semua informasi satu evaluasi beserta daftar vendor yang sudah ditambahkan.

**Endpoint:** `GET /api/v1/evaluasi/:id`  
**Auth required:** Ya  
**Digunakan di:** P-04, P-05

**Kondisi error:** Evaluasi tidak ditemukan (404), staff mencoba mengakses evaluasi milik orang lain (403).

---

### Buat Evaluasi

**Tujuan:** Membuat evaluasi baru dengan status draft dari data requirement yang diisi user di step 1.

**Endpoint:** `POST /api/v1/evaluasi`  
**Auth required:** Ya  
**Digunakan di:** P-03 Step 1

**Data yang dikirim:** Judul, kategori, deskripsi, batas anggaran, deadline, dan prioritas kriteria.

**Mengapa evaluasi dibuat di step 1 bukan step 3:** Membuat evaluasi lebih awal memungkinkan sistem menyimpan progress secara incremental. Jika user tiba-tiba menutup browser di step 2, data step 1 tidak hilang.

---

### Tambah Vendor

**Tujuan:** Menambahkan satu vendor kandidat ke evaluasi yang sedang dalam status draft.

**Endpoint:** `POST /api/v1/evaluasi/:id/vendor`  
**Auth required:** Ya  
**Digunakan di:** P-03 Step 2

**Data yang dikirim:** Nama perusahaan, kontak/website, harga penawaran, catatan tambahan, dan sumber input (manual atau hasil ekstraksi AI).

**Batasan:** Maksimum 10 vendor per evaluasi. Vendor tidak bisa ditambah jika evaluasi sudah berstatus processing atau lebih lanjut.

**Mengapa ada batasan 10 vendor:** Terlalu banyak vendor akan membuat proses AI lebih lama dan hasil rekomendasi lebih sulit dibaca. 10 vendor dipandang cukup komprehensif untuk proses procurement yang sehat.

---

### Hapus Vendor

**Tujuan:** Menghapus satu vendor dari evaluasi yang masih berstatus draft.

**Endpoint:** `DELETE /api/v1/evaluasi/:id/vendor/:vendorId`  
**Auth required:** Ya  
**Digunakan di:** P-03 Step 2

---

### Upload Dokumen Penawaran

**Tujuan:** Mengunggah dokumen penawaran vendor (PDF atau Excel) untuk diekstrak datanya oleh AI secara async.

**Endpoint:** `POST /api/v1/evaluasi/:id/dokumen`  
**Auth required:** Ya  
**Content-Type:** multipart/form-data  
**Digunakan di:** P-03 Step 2

**Mengapa prosesnya async:** Ekstraksi dokumen oleh LLM membutuhkan waktu beberapa detik hingga puluhan detik tergantung panjang dokumen. Membuatnya async mencegah request timeout dan memberi user pengalaman yang lebih responsif.

**Batasan file:** PDF atau Excel, maksimum 10MB.

---

### Status Ekstraksi Dokumen

**Tujuan:** Mengecek apakah proses ekstraksi data vendor dari dokumen sudah selesai dan mengambil hasilnya.

**Endpoint:** `GET /api/v1/evaluasi/:id/dokumen/:uploadId/status`  
**Auth required:** Ya  
**Digunakan di:** P-03 Step 2

**Status yang mungkin:** Sedang diproses, selesai (beserta data yang berhasil diekstrak), atau gagal.

---

### Submit Evaluasi

**Tujuan:** Memulai proses evaluasi AI — mengubah status evaluasi dari draft ke processing dan memicu agent orchestration di FastAPI.

**Endpoint:** `POST /api/v1/evaluasi/:id/submit`  
**Auth required:** Ya  
**Digunakan di:** P-03 Step 3

**Prasyarat:** Evaluasi harus berstatus draft dan memiliki minimal 2 vendor.

**Mengapa minimal 2 vendor:** Evaluasi yang bermakna membutuhkan perbandingan. Satu vendor tidak memberikan konteks untuk menilai apakah vendor tersebut kompetitif atau tidak.

---

### Update Status Evaluasi

**Tujuan:** Mengubah status evaluasi untuk tindakan spesifik seperti mengirim ke manager untuk approval.

**Endpoint:** `PATCH /api/v1/evaluasi/:id/status`  
**Auth required:** Ya  
**Digunakan di:** P-05 (tombol "Kirim ke Manager")

**Transisi yang diizinkan per role:**
- Staff: dari `selesai` ke `menunggu_approval`
- Manager: dikelola via endpoint approval terpisah

---

### Approval Evaluasi

**Tujuan:** Manager memberikan keputusan final (approve atau reject) atas evaluasi yang menunggu.

**Endpoint:** `POST /api/v1/evaluasi/:id/approval`  
**Auth required:** Ya — Manager only  
**Digunakan di:** P-07

**Data yang dikirim:** Keputusan (approve atau reject) dan komentar (wajib jika reject, opsional jika approve).

**Mengapa komentar wajib saat reject:** Staff perlu tahu secara spesifik apa yang perlu diperbaiki. Reject tanpa komentar tidak memberikan arahan yang jelas.

---

### Daftar Kategori Pengadaan

**Tujuan:** Menyediakan daftar kategori yang valid untuk dropdown di form pembuatan evaluasi.

**Endpoint:** `GET /api/v1/kategori-pengadaan`  
**Auth required:** Ya  
**Digunakan di:** P-03 Step 1

---

### Konfigurasi Bobot Kriteria

**Tujuan:** Mengambil konfigurasi bobot kriteria yang aktif untuk satu kategori pengadaan.

**Endpoint:** `GET /api/v1/konfigurasi/kriteria`  
**Auth required:** Ya  
**Digunakan di:** P-08

**Parameter:** Kategori pengadaan (wajib).

---

### Simpan Konfigurasi Bobot Kriteria

**Tujuan:** Menyimpan perubahan bobot dan threshold minimum per kriteria untuk satu kategori pengadaan.

**Endpoint:** `PUT /api/v1/konfigurasi/kriteria`  
**Auth required:** Ya — Manager only  
**Digunakan di:** P-08

**Aturan validasi:** Total seluruh bobot harus tepat 100. Perubahan hanya berlaku untuk evaluasi yang dibuat setelah perubahan disimpan — tidak retroaktif.

**Mengapa tidak retroaktif:** Mengubah bobot pada evaluasi yang sudah selesai akan mengubah hasil yang sudah dikomunikasikan ke stakeholder, yang dapat menyebabkan kebingungan dan ketidakpercayaan terhadap sistem.

---

## 8. Kelompok 3 — AI Agent Orchestration

Endpoint kelompok ini berada di **FastAPI** dan dipanggil secara internal oleh Next.js — tidak langsung dari browser.

---

### Mulai Proses Agent

**Tujuan:** Memulai proses evaluasi AI dengan menjalankan semua sub-agent secara paralel.

**Endpoint:** `POST /v1/agent/evaluasi/:id/start` (internal)  
**Dipanggil oleh:** Next.js saat memproses `POST /api/v1/evaluasi/:id/submit`

**Data yang dikirim:** Informasi lengkap evaluasi termasuk daftar vendor, requirement, dan konfigurasi kriteria yang aktif.

**Mengapa Next.js yang memanggil, bukan browser langsung:** Ini melindungi FastAPI dari akses publik langsung. Next.js berfungsi sebagai gateway yang memvalidasi autentikasi dan otorisasi sebelum meneruskan request ke FastAPI.

**Proses berjalan async:** Agent berjalan di background. Progress tiap agent ditulis ke Supabase secara real-time sehingga bisa di-broadcast ke frontend.

---

### Status Agent

**Tujuan:** Mengambil status terkini semua sub-agent untuk satu evaluasi.

**Endpoint:** `GET /v1/agent/evaluasi/:id/status` (internal)  
**Dipanggil oleh:** Next.js dan di-proxy ke frontend sebagai `/api/v1/evaluasi/:id/agent-status`

**Data yang dikembalikan:** Status dan progress (0–100%) tiap sub-agent, pesan terkini dari masing-masing agent, dan estimasi waktu selesai keseluruhan.

---

### Ekstraksi Dokumen

**Tujuan:** Mengekstrak informasi vendor dari dokumen penawaran menggunakan LLM.

**Endpoint:** `POST /v1/agent/ekstrak-dokumen` (internal)  
**Dipanggil oleh:** Next.js setelah dokumen berhasil diupload ke Supabase Storage

**Data yang dikembalikan:** Data vendor yang berhasil diekstrak beserta tingkat kepercayaan (confidence score). Jika ekstraksi tidak yakin, confidence score yang rendah memberi sinyal ke user untuk memverifikasi secara manual.

---

## 9. Kelompok 4 — Scoring Engine

Endpoint kelompok ini berada di **FastAPI** dan dipanggil secara internal.

---

### Hitung Skor

**Tujuan:** Menghitung skor final semua vendor menggunakan algoritma MCDM (TOPSIS) berdasarkan data yang dikumpulkan agent.

**Endpoint:** `POST /v1/scoring/hitung` (internal)  
**Dipanggil oleh:** Agent Orchestration setelah semua agent selesai

**Data yang dikembalikan:** Ranking vendor beserta skor total, skor per kriteria, status kelulusan threshold minimum, dan reasoning naratif dalam tiga bagian (alasan rekomendasi utama, kelemahan yang perlu diperhatikan, saran negosiasi).

**Mengapa TOPSIS:** Dijelaskan lebih detail di AI-03 (Scoring Engine). Singkatnya, TOPSIS menghasilkan skor yang dapat dijelaskan karena didasarkan pada jarak relatif vendor terhadap solusi ideal dan solusi terburuk — konsep yang intuitif untuk disampaikan ke stakeholder non-teknis.

---

### Hasil Scoring

**Tujuan:** Mengambil hasil scoring yang sudah tersimpan untuk ditampilkan di halaman hasil evaluasi.

**Endpoint:** `GET /v1/scoring/evaluasi/:id/hasil` (internal)  
**Dipanggil oleh:** Next.js dan di-proxy ke frontend sebagai `/api/v1/evaluasi/:id/hasil`  
**Digunakan di:** P-05

---

## 10. Kelompok 5 — AI Chat

---

### Chat Streaming

**Tujuan:** Melayani percakapan real-time antara user dan AI di panel kanan dengan respons yang di-stream token demi token.

**Endpoint:** `POST /v1/chat/stream`  
**Auth required:** Ya (JWT yang sama dengan Next.js)  
**Dipanggil oleh:** Browser langsung (satu-satunya endpoint FastAPI yang diakses langsung dari browser)  
**Digunakan di:** AIPanel di semua halaman

**Mengapa SSE bukan WebSocket:** Chat AI adalah komunikasi satu arah — user kirim pesan, AI merespons. SSE lebih sederhana dan efisien untuk pola ini dibanding WebSocket yang dirancang untuk komunikasi dua arah. SSE juga lebih mudah di-debug dan lebih banyak didukung oleh proxy/CDN.

**Konteks yang dikirim:** Pesan user, informasi halaman yang sedang aktif, ID evaluasi yang sedang dibuka (jika ada), dan riwayat percakapan dalam sesi ini.

**Mengapa konteks dikirim dari frontend:** AI perlu tahu sedang berada di konteks apa untuk memberikan jawaban yang relevan. Tanpa konteks ini, AI akan menjawab secara generik.

**Format respons:** Stream teks token demi token, diakhiri dengan sinyal selesai yang menyertakan informasi penggunaan token.

---

## 11. Real-time

### 11.1 Supabase Realtime untuk progress agent

Digunakan di **P-04** untuk menampilkan progress agent tanpa polling manual.

FastAPI menulis update progress ke tabel `agent_progress` di Supabase setiap kali ada perubahan berarti. Supabase Realtime otomatis mendeteksi perubahan pada tabel ini dan mengirimkan notifikasi ke semua client yang subscribe ke channel evaluasi tersebut.

**Mengapa Supabase Realtime dipilih dibanding polling:** Polling setiap 3 detik mengirimkan request meskipun tidak ada perubahan, membuang bandwidth dan beban server. Realtime hanya mengirimkan data saat ada perubahan nyata.

**Mengapa Supabase Realtime dipilih dibanding WebSocket custom:** Supabase sudah menyediakan infrastruktur Realtime yang terintegrasi dengan database. Tidak perlu membangun WebSocket server terpisah.

**Yang di-broadcast:** Status dan progress tiap sub-agent, pesan terkini dari agent.

### 11.2 SSE untuk AI chat streaming

Digunakan di **AIPanel** di semua halaman.

Frontend membuka koneksi SSE ke FastAPI saat user mengirim pesan. Koneksi tetap terbuka selama LLM menghasilkan token, lalu ditutup secara otomatis saat streaming selesai.

**Tiga jenis event yang mungkin diterima:** Token teks (konten respons AI), sinyal selesai (streaming berakhir normal), dan sinyal error (terjadi masalah).

---

## 12. Error Handling

### 12.1 Prinsip error handling

Setiap error yang dikembalikan API harus:
- Memiliki kode error yang spesifik (bukan sekadar status HTTP) sehingga frontend bisa menangani tiap kasus berbeda
- Memiliki pesan yang dapat ditampilkan ke user (bukan pesan teknis internal)
- Konsisten dalam format di seluruh endpoint

### 12.2 HTTP status codes

| Status | Makna | Kapan digunakan |
|---|---|---|
| 200 | OK | Request berhasil |
| 201 | Created | Resource baru berhasil dibuat |
| 202 | Accepted | Request diterima, proses berjalan async |
| 400 | Bad Request | Input tidak valid |
| 401 | Unauthorized | Token tidak ada, tidak valid, atau expired |
| 403 | Forbidden | Token valid tapi tidak punya hak akses |
| 404 | Not Found | Resource tidak ditemukan |
| 409 | Conflict | Operasi tidak valid untuk kondisi resource saat ini |
| 429 | Too Many Requests | Rate limit terlampaui |
| 500 | Internal Server Error | Error tidak terduga di server |
| 503 | Service Unavailable | FastAPI tidak bisa dijangkau dari Next.js |

### 12.3 Daftar error codes

| Code | HTTP | Kondisi |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Satu atau lebih field tidak memenuhi aturan validasi |
| `INVALID_CREDENTIALS` | 401 | Email atau password salah |
| `INVALID_TOKEN` | 401 | JWT tidak valid atau sudah expired |
| `INVALID_REFRESH_TOKEN` | 401 | Refresh token tidak valid |
| `FORBIDDEN` | 403 | Tidak punya hak akses ke resource atau operasi ini |
| `EVALUASI_NOT_FOUND` | 404 | Evaluasi dengan ID tersebut tidak ditemukan |
| `VENDOR_NOT_FOUND` | 404 | Vendor dengan ID tersebut tidak ditemukan |
| `VENDOR_LIMIT_EXCEEDED` | 400 | Evaluasi sudah mencapai batas maksimum 10 vendor |
| `INSUFFICIENT_VENDORS` | 400 | Evaluasi membutuhkan minimal 2 vendor untuk disubmit |
| `EVALUASI_NOT_EDITABLE` | 409 | Evaluasi tidak bisa diedit karena statusnya bukan draft |
| `ALREADY_SUBMITTED` | 409 | Evaluasi sudah pernah disubmit dan tidak bisa disubmit ulang |
| `NOT_PENDING_APPROVAL` | 409 | Evaluasi tidak dalam status menunggu approval |
| `INVALID_WEIGHT_TOTAL` | 400 | Total bobot kriteria tidak sama dengan 100 |
| `FILE_TOO_LARGE` | 400 | File yang diupload melebihi batas 10MB |
| `INVALID_FILE_TYPE` | 400 | Format file tidak didukung (harus PDF atau Excel) |
| `AGENT_SERVICE_ERROR` | 503 | FastAPI service tidak dapat dijangkau |
| `RATE_LIMIT_EXCEEDED` | 429 | Terlalu banyak request dalam waktu singkat |
| `PREFERENCE_TOO_LONG` | 400 | Teks preferensi melebihi batas 1.000 karakter |
| `RAG_INDEX_NOT_READY` | 409 | Dokumen belum selesai diindeks, chat berbasis dokumen belum tersedia |

---

## 13. Daftar Lengkap Endpoint

### Next.js API Routes

| Method | Path | Deskripsi | Role |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Login | Public |
| POST | `/api/v1/auth/logout` | Logout | Auth |
| POST | `/api/v1/auth/refresh` | Refresh token | Public |
| GET | `/api/v1/users/me` | Data user aktif | Auth |
| GET | `/api/v1/evaluasi` | Daftar evaluasi | Auth |
| GET | `/api/v1/evaluasi/summary` | Ringkasan stat per status | Auth |
| GET | `/api/v1/evaluasi/:id` | Detail evaluasi | Auth |
| POST | `/api/v1/evaluasi` | Buat evaluasi baru (termasuk `preferensi_perusahaan` opsional) | Auth |
| POST | `/api/v1/evaluasi/:id/vendor` | Tambah vendor | Auth |
| DELETE | `/api/v1/evaluasi/:id/vendor/:vendorId` | Hapus vendor | Auth |
| POST | `/api/v1/evaluasi/:id/dokumen` | Upload dokumen penawaran | Auth |
| GET | `/api/v1/evaluasi/:id/dokumen/:uploadId/status` | Status ekstraksi dokumen dan RAG indexing | Auth |
| POST | `/api/v1/evaluasi/:id/submit` | Mulai proses evaluasi AI | Auth |
| PATCH | `/api/v1/evaluasi/:id/status` | Update status evaluasi | Auth |
| POST | `/api/v1/evaluasi/:id/approval` | Approve atau reject | Manager |
| GET | `/api/v1/evaluasi/:id/hasil` | Hasil rekomendasi | Auth |
| GET | `/api/v1/evaluasi/:id/agent-status` | Status progress agent | Auth |
| GET | `/api/v1/kategori-pengadaan` | Daftar kategori | Auth |
| GET | `/api/v1/konfigurasi/kriteria` | Bobot kriteria per kategori | Auth |
| PUT | `/api/v1/konfigurasi/kriteria` | Simpan perubahan bobot | Manager |

### FastAPI

| Method | Path | Deskripsi | Dipanggil oleh |
|---|---|---|---|
| POST | `/v1/agent/evaluasi/:id/start` | Mulai agent orchestration (7 agent) | Next.js (internal) |
| GET | `/v1/agent/evaluasi/:id/status` | Status semua agent | Next.js (internal) |
| POST | `/v1/agent/ekstrak-dokumen` | Ekstraksi field terstruktur + RAG indexing | Next.js (internal) |
| POST | `/v1/scoring/hitung` | Hitung skor TOPSIS + integrasi kualitatif + preferensi | Agent (internal) |
| GET | `/v1/scoring/evaluasi/:id/hasil` | Ambil hasil scoring lengkap | Next.js (internal) |
| POST | `/v1/chat/stream` | AI chat SSE streaming (dengan RAG context) | Browser langsung |
| POST | `/v1/rag/query` | Retrieval chunks relevan untuk konteks chat | Next.js (internal) |

---

## 14. Catatan untuk Dokumen Lanjutan

### Untuk AI-01 (Agent Orchestration)

Endpoint `POST /v1/agent/evaluasi/:id/start` sekarang memicu 7 agent (bukan 5). Payload yang dikirim Next.js ke FastAPI perlu menyertakan `preferensi_perusahaan` dari tabel `evaluasi` agar Preference Matcher Agent dapat beroperasi dalam mode yang benar.

### Untuk AI-03 (Scoring Engine)

Endpoint `POST /v1/scoring/hitung` sekarang menerima dan menghasilkan data yang lebih kaya — termasuk output kualitatif dan preferensi. Response dari `GET /v1/scoring/evaluasi/:id/hasil` perlu mengembalikan semua field baru yang terdefinisi di DB-01 section 6.7.

### Untuk AI-05 (RAG Specification)

Endpoint `POST /v1/rag/query` adalah endpoint internal baru yang digunakan Next.js untuk mengambil RAG context sebelum membangun prompt chat. Endpoint ini menerima `evaluasi_id` dan `query` (pertanyaan user), lalu mengembalikan chunks relevan yang sudah diformat.

### Untuk DB-01 (Data Model)

Response `GET /api/v1/evaluasi/:id/hasil` perlu mengembalikan field-field baru: `summary_komparatif_kualitatif`, `preference_matching_result`, `conflict_callout` dari `hasil_evaluasi`, dan per vendor: `unique_offerings`, `profil_kualitatif`, `tingkat_kesesuaian_preferensi`.

### Untuk FE-05 (API Integration)

Pola konsumsi yang perlu didefinisikan:
- Setup HTTP client dengan base URL, interceptor token, dan error handling global
- Pola polling untuk status ekstraksi dokumen dan RAG indexing (dua status berbeda)
- Pola subscribe Supabase Realtime channel untuk 7 agent di komponen React
- Pola membaca SSE stream untuk AI chat

---

*Dokumen ini adalah living document — akan diperbarui seiring perkembangan implementasi dan ditemukannya kebutuhan baru.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 2.0.0 | 2026-06-07 | Revisi: fokus ke what & why, hapus semua JSON schema dan code snippet | — |
| 3.0.0 | 2026-06-11 | Tambah endpoint `/v1/rag/query`; update deskripsi endpoint start agent (7 agent), ekstraksi dokumen (+ RAG indexing), scoring (+ kualitatif + preferensi), dan chat (+ RAG context); tambah error codes `PREFERENCE_TOO_LONG` dan `RAG_INDEX_NOT_READY` | — |
| 4.0.0 | 2026-06-13 | Perbarui referensi dokumen: BE-03→AI-01, BE-05→AI-03 (ADR-035) | — |
