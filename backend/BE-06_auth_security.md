# BE-06 — Auth & Security Specification

**Project:** AI Vendor Selection System  
**Dokumen:** BE-06 — Auth & Security  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-07  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip Keamanan](#3-prinsip-keamanan)
4. [Autentikasi](#4-autentikasi)
5. [Otorisasi & RBAC](#5-otorisasi--rbac)
6. [Keamanan API](#6-keamanan-api)
7. [Keamanan Data](#7-keamanan-data)
8. [Keamanan Komunikasi](#8-keamanan-komunikasi)
9. [Audit Trail](#9-audit-trail)
10. [Manajemen Kredensial & Secret](#10-manajemen-kredensial--secret)
11. [Aturan & Larangan](#11-aturan--larangan)
12. [Catatan untuk Dokumen Lanjutan](#12-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **seluruh aspek keamanan sistem** — bagaimana user diautentikasi, bagaimana akses dikontrol berdasarkan role, bagaimana data dilindungi, dan bagaimana jejak aktivitas dicatat untuk keperluan audit.

Dokumen ini menjawab pertanyaan: siapa yang boleh mengakses apa, bagaimana sistem memastikan identitas user, apa yang terjadi jika token dicuri, dan bagaimana keputusan penting dalam sistem dapat ditelusuri kembali.

Dokumen ini **tidak** mendefinisikan implementasi kode — itu diserahkan ke engineer. Dokumen ini mendefinisikan **apa** yang harus diamankan dan **mengapa**.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| BE-02 | API Contract | Endpoint yang dilindungi oleh mekanisme auth |
| DB-01 | Data Model & ERD | Tabel `user` dan RLS yang menjadi fondasi otorisasi |
| FE-01 | UI Architecture | Middleware Next.js yang menerapkan auth di sisi frontend |
| FE-05 | API Integration | Pola token refresh di sisi client |
| SH-02 | Deployment Runbook | Prosedur pengelolaan secret di production |

---

## 3. Prinsip Keamanan

### 3.1 Defense in depth

Keamanan tidak boleh bergantung pada satu lapisan saja. Sistem menerapkan beberapa lapisan perlindungan yang bekerja secara independen — jika satu lapisan berhasil ditembus, lapisan berikutnya tetap melindungi:

- Middleware Next.js memvalidasi token sebelum request mencapai handler
- Handler API memvalidasi ulang token dan role secara independen
- RLS di Supabase memvalidasi akses di level database
- FastAPI memvalidasi token secara terpisah dari Next.js

### 3.2 Principle of least privilege

Setiap komponen — user, service, dan API key — hanya diberi akses ke apa yang benar-benar dibutuhkannya. Staff tidak memiliki akses ke fitur manager. FastAPI tidak memiliki akses ke seluruh database — hanya ke tabel yang dibutuhkannya. Service role key Supabase tidak diekspos ke frontend.

### 3.3 Fail secure

Jika ada keraguan tentang apakah sebuah akses seharusnya diizinkan, sistem menolak akses tersebut. Lebih baik user yang sah sesekali mendapat error 403 daripada user yang tidak berhak mendapat akses.

### 3.4 Keamanan procurement adalah prioritas

Data evaluasi vendor dan keputusan pengadaan adalah informasi bisnis yang sensitif. Kebocoran data ini bisa merugikan perusahaan secara finansial (harga penawaran vendor bocor ke kompetitor) dan reputasional. Keamanan sistem ini harus diperlakukan setara dengan sistem keuangan.

---

## 4. Autentikasi

### 4.1 Provider: Supabase Auth

Autentikasi dikelola oleh Supabase Auth — sistem tidak membangun autentikasi dari nol. Supabase Auth menangani penyimpanan password (hashed dengan bcrypt), penerbitan JWT, dan refresh token.

**Mengapa tidak membangun sendiri:** Membangun sistem autentikasi yang aman dari nol adalah kompleks dan rentan kesalahan. Supabase Auth adalah solusi battle-tested yang menangani edge case keamanan yang sering terlewat — brute force protection, secure token storage, dan sebagainya.

### 4.2 JWT (JSON Web Token)

Setiap sesi user direpresentasikan oleh dua token:

**Access token:**
- Berisi: user ID, email, role, dan expiry time
- Masa berlaku: 1 jam
- Digunakan: di header `Authorization` setiap request ke API
- Disimpan: di memori (Zustand store) saat runtime, di cookie HttpOnly untuk persistensi

**Refresh token:**
- Tidak berisi informasi user — hanya identifier sesi
- Masa berlaku: 7 hari
- Digunakan: untuk memperbarui access token yang expired
- Disimpan: di cookie HttpOnly yang tidak bisa diakses JavaScript

**Mengapa access token berumur pendek (1 jam):** Jika access token dicuri, kerusakannya terbatas pada 1 jam. Setelah itu token tidak bisa digunakan. Refresh token yang berumur lebih panjang hanya digunakan untuk meminta token baru — tidak bisa langsung digunakan untuk mengakses resource.

**Mengapa refresh token di cookie HttpOnly:** Cookie HttpOnly tidak bisa dibaca oleh JavaScript — hanya oleh browser saat mengirim request. Ini melindungi refresh token dari serangan XSS di mana script berbahaya mencoba mencuri token dari localStorage atau memori JavaScript.

### 4.3 Alur autentikasi lengkap

```
User submit login form
        ↓
Next.js API Routes → Supabase Auth
        ↓
Supabase Auth verifikasi kredensial
        ↓
Berhasil: kembalikan access token + refresh token
        ↓
Next.js menyimpan refresh token di cookie HttpOnly
Next.js mengembalikan access token ke frontend
        ↓
Frontend menyimpan access token di Zustand store
        ↓
Setiap request API menyertakan access token di header
        ↓
Saat access token expired (1 jam):
Frontend mengirim refresh token → dapat access token baru
        ↓
Saat refresh token expired (7 hari):
User diminta login ulang
```

### 4.4 Logout

Logout melakukan dua hal secara bersamaan:
- Invalidasi refresh token di Supabase (sehingga tidak bisa digunakan untuk meminta access token baru)
- Hapus cookie HttpOnly yang menyimpan refresh token
- Kosongkan Zustand store

Access token yang sudah diterbitkan tidak bisa di-invalidasi sebelum expired — ini adalah trade-off yang diterima dengan access token berumur pendek. Dalam 1 jam setelah logout, access token yang sudah ada masih secara teknis valid, tetapi tidak bisa diperbarui.

### 4.5 Brute force protection

Supabase Auth membatasi percobaan login yang gagal secara otomatis. Konfigurasi yang digunakan:
- Maksimum 5 percobaan gagal dalam 5 menit dari satu IP address
- Setelah limit tercapai: delay progressif sebelum percobaan berikutnya diizinkan

Next.js API Routes juga menerapkan rate limiting di level aplikasi sebagai lapisan tambahan (lihat section 6.2).

---

## 5. Otorisasi & RBAC

### 5.1 Dua role dalam sistem

Seperti didefinisikan di DB-01 dan FE-03, sistem memiliki dua role:

| Role | Kemampuan utama |
|---|---|
| `staff` | Membuat dan mengelola evaluasi milik sendiri, melihat hasil |
| `manager` | Semua kemampuan staff + approve/reject evaluasi semua staff + konfigurasi sistem |

### 5.2 Tiga lapisan pengecekan role

Role user dikodekan dalam JWT payload. Pengecekan role dilakukan di tiga lapisan secara independen:

**Lapisan 1 — Middleware Next.js:**
Membaca role dari JWT dan memblokir akses ke route yang tidak sesuai (misalnya `/approval` dan `/settings/kriteria` hanya untuk manager) sebelum request mencapai handler apapun.

**Lapisan 2 — API handler:**
Setiap endpoint yang dibatasi role melakukan pengecekan ulang secara eksplisit di awal handler — tidak bergantung pada middleware saja. Ini adalah defense in depth: jika ada bug di middleware yang meloloskan request yang tidak seharusnya, handler tetap menolaknya.

**Lapisan 3 — Row Level Security (RLS) Supabase:**
Di level database, RLS memastikan staff hanya bisa membaca dan memodifikasi data yang menjadi haknya, terlepas dari apa yang diizinkan lapisan di atasnya.

**Mengapa tiga lapisan:** Setiap lapisan bisa saja memiliki bug. Tiga lapisan yang independen memastikan setidaknya satu lapisan akan menangkap akses yang tidak sah.

### 5.3 Resource-level authorization

Selain role-level authorization, sistem menerapkan resource-level authorization — staff hanya bisa mengakses evaluasi miliknya sendiri, meskipun ia tahu ID evaluasi milik staff lain.

Pengecekan ini dilakukan di level API handler: sebelum mengambil atau memodifikasi evaluasi, handler memverifikasi bahwa `evaluasi.created_by` sama dengan user ID dari token. Jika tidak sama, kembalikan 403 — bukan 404.

**Mengapa 403, bukan 404:** Mengembalikan 404 saat resource ada tapi tidak boleh diakses adalah praktik umum untuk menyembunyikan eksistensi resource. Namun untuk sistem internal perusahaan di mana semua user sudah diautentikasi, 403 lebih informatif dan tidak memberikan informasi yang berarti ke penyerang internal.

### 5.4 Komunikasi internal Next.js → FastAPI

FastAPI hanya menerima request dari Next.js API Routes — tidak dari browser langsung (kecuali SSE chat). Autentikasi komunikasi internal ini menggunakan **service-to-service token** yang berbeda dari JWT user.

Service token adalah API key statis yang disimpan sebagai environment variable di kedua service. FastAPI memvalidasi service token di setiap request internal — jika service token tidak valid atau tidak ada, request ditolak dengan 401 tanpa informasi lebih lanjut.

**Mengapa tidak meneruskan JWT user ke FastAPI:** JWT user berisi informasi sensitif (email, role) yang tidak perlu diketahui FastAPI. FastAPI hanya perlu tahu bahwa request berasal dari Next.js yang sudah memvalidasi user — bukan siapa usernya.

---

## 6. Keamanan API

### 6.1 HTTPS wajib di semua environment

Semua komunikasi antara client dan server harus menggunakan HTTPS — termasuk di staging. HTTP tidak diizinkan di environment apapun selain localhost development.

Vercel dan Supabase sudah menyediakan HTTPS secara otomatis. FastAPI di deployment perlu dikonfigurasi untuk berjalan di belakang reverse proxy yang menangani TLS termination.

### 6.2 Rate limiting

Rate limiting diterapkan di dua level:

**Level Next.js API Routes:**

| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 5 request per menit per IP |
| `POST /evaluasi/:id/submit` | 3 request per menit per user |
| Semua endpoint lain | 60 request per menit per user |

**Level FastAPI:**

| Endpoint | Limit |
|---|---|
| `POST /v1/chat/stream` | 20 request per menit per user |
| `POST /v1/agent/ekstrak-dokumen` | 5 request per menit per evaluasi |
| Semua endpoint internal | 100 request per menit per service token |

**Mengapa endpoint chat di-rate limit lebih ketat:** Chat streaming mengonsumsi LLM tokens yang memiliki biaya per request. Rate limit melindungi dari penggunaan berlebihan yang tidak disengaja maupun yang disengaja.

### 6.3 Input validation

Semua input dari user divalidasi sebelum diproses — di level API handler menggunakan Zod (Next.js) dan Pydantic (FastAPI).

Prinsip validasi:
- Tolak input yang tidak sesuai schema — jangan coba "perbaiki" input yang salah
- Batasi panjang string untuk semua field teks
- Validasi format field seperti UUID, date, dan email dengan regex atau parser khusus
- Sanitasi input yang akan ditampilkan kembali ke user untuk mencegah XSS

### 6.4 CORS

Next.js API Routes hanya menerima request dari origin yang terdaftar. FastAPI SSE endpoint hanya menerima request dari origin Next.js frontend yang terdaftar.

Origin yang tidak terdaftar menerima response CORS error — request tidak diproses sama sekali.

### 6.5 Security headers

Semua response dari Next.js menyertakan security headers berikut:

| Header | Nilai | Tujuan |
|---|---|---|
| `Content-Security-Policy` | Dibatasi ke origin yang diketahui | Mencegah XSS dan injection |
| `X-Frame-Options` | `DENY` | Mencegah clickjacking |
| `X-Content-Type-Options` | `nosniff` | Mencegah MIME type sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Membatasi informasi referrer |
| `Strict-Transport-Security` | `max-age=31536000` | Memaksa HTTPS |

---

## 7. Keamanan Data

### 7.1 Data sensitif dalam sistem

Data yang diklasifikasikan sebagai sensitif dan memerlukan perlindungan khusus:

| Data | Tingkat Sensitivitas | Alasan |
|---|---|---|
| Harga penawaran vendor | Tinggi | Informasi kompetitif yang bisa merugikan perusahaan jika bocor |
| Hasil evaluasi dan skor | Tinggi | Keputusan bisnis yang sensitif |
| Reasoning AI | Sedang | Mencerminkan analisa internal perusahaan |
| Data profil user | Sedang | Informasi pribadi karyawan |
| Konfigurasi bobot kriteria | Sedang | Strategi evaluasi perusahaan |

### 7.2 Enkripsi data at rest

Supabase mengenkripsi semua data di database secara otomatis menggunakan enkripsi AES-256. Tidak diperlukan enkripsi tambahan di level aplikasi untuk data yang disimpan di Supabase.

File yang diupload ke Supabase Storage (dokumen penawaran vendor) juga dienkripsi at rest secara otomatis.

### 7.3 Enkripsi data in transit

Semua data in transit dienkripsi menggunakan TLS 1.2 atau lebih baru. Ini dijamin oleh HTTPS yang diwajibkan di semua environment (section 6.1).

### 7.4 Akses file dokumen penawaran

File dokumen penawaran vendor yang diupload ke Supabase Storage tidak boleh dapat diakses secara publik. File hanya dapat diakses melalui signed URL yang:
- Di-generate saat request dan berlaku hanya untuk durasi terbatas (maksimum 1 jam)
- Hanya bisa di-generate oleh user yang memiliki akses ke evaluasi terkait
- Tidak bisa dibagikan ke pihak ketiga secara permanen

### 7.5 Data masking di log

Log aplikasi tidak boleh mencatat informasi sensitif seperti:
- Nilai harga penawaran vendor
- Konten hasil evaluasi
- Token atau credential
- Password dalam bentuk apapun

Jika informasi sensitif perlu di-debug, gunakan ID atau hash sebagai referensi — bukan nilai aslinya.

---

## 8. Keamanan Komunikasi

### 8.1 Komunikasi browser ↔ Next.js

Dilindungi oleh HTTPS dan security headers (section 6.1 dan 6.5). JWT dikirim di header `Authorization` — tidak di URL parameter atau cookie biasa.

### 8.2 Komunikasi Next.js ↔ FastAPI

Komunikasi internal antar service menggunakan service-to-service token (section 5.4) dan HTTPS. FastAPI tidak boleh dapat diakses langsung dari internet — hanya dari Next.js melalui jaringan internal atau VPC.

### 8.3 Komunikasi browser ↔ FastAPI (SSE)

SSE endpoint di FastAPI yang diakses langsung oleh browser harus memvalidasi JWT user (bukan service token) dan menerapkan CORS yang ketat. Ini adalah satu-satunya titik di mana FastAPI menerima koneksi dari browser.

### 8.4 Komunikasi Next.js ↔ Supabase

Menggunakan Supabase JS client dengan anon key untuk operasi yang melewati RLS, dan service role key untuk operasi admin. Service role key hanya digunakan di server — tidak pernah di client.

---

## 9. Audit Trail

### 9.1 Mengapa audit trail penting untuk sistem pengadaan

Keputusan pengadaan sering membutuhkan justifikasi — kepada auditor internal, manajemen, atau regulator. Audit trail memungkinkan penelusuran: siapa yang membuat evaluasi, kapan, vendor apa yang dievaluasi, siapa yang menyetujui, dan kapan.

### 9.2 Event yang dicatat

Event berikut dicatat secara otomatis oleh sistem:

| Event | Data yang dicatat |
|---|---|
| Login berhasil | User ID, timestamp, IP address |
| Login gagal | Email yang dicoba, timestamp, IP address |
| Evaluasi dibuat | User ID, evaluasi ID, timestamp |
| Evaluasi disubmit | User ID, evaluasi ID, jumlah vendor, timestamp |
| Vendor ditambahkan | User ID, evaluasi ID, vendor ID, timestamp |
| Hasil evaluasi dibuat | Evaluasi ID, metodologi, vendor rank 1, timestamp |
| Evaluasi dikirim ke approval | User ID, evaluasi ID, timestamp |
| Approval diberikan | Manager ID, evaluasi ID, keputusan, timestamp |
| Konfigurasi kriteria diubah | Manager ID, kategori, perubahan bobot, timestamp |

### 9.3 Di mana audit log disimpan

Audit log disimpan di dua tempat:

**Database Supabase:** Event yang terkait langsung dengan objek bisnis (evaluasi, vendor, approval) dicatat di tabel yang relevan melalui kolom `created_at`, `updated_at`, dan tabel `approval_log`. Ini sudah tercakup dalam model data yang ada di DB-01.

**Log aplikasi:** Event autentikasi dan event keamanan (login gagal, akses ditolak) dicatat di log aplikasi Next.js dan FastAPI yang dikirim ke layanan log terpusat.

### 9.4 Retensi audit log

Audit log disimpan minimal **2 tahun** — sesuai dengan kebutuhan audit procurement pada umumnya. Kebijakan retensi yang lebih detail ada di DB-04.

### 9.5 Akses ke audit log

Audit log hanya bisa diakses oleh:
- Admin sistem (melalui Supabase dashboard langsung)
- Manager melalui fitur riwayat evaluasi di aplikasi (hanya log yang berkaitan dengan evaluasi yang dapat mereka akses)

Tidak ada endpoint API publik yang mengekspos raw audit log — untuk melindungi privasi dan mencegah penyalahgunaan informasi.

---

## 10. Manajemen Kredensial & Secret

### 10.1 Jenis secret dalam sistem

| Secret | Digunakan oleh | Disimpan di |
|---|---|---|
| Supabase anon key | Next.js frontend & backend | Environment variable (NEXT_PUBLIC_) |
| Supabase service role key | Next.js backend (server only) | Environment variable (server only) |
| Anthropic API key | FastAPI | Environment variable |
| Service-to-service token | Next.js & FastAPI | Environment variable |
| JWT secret | Supabase (dikelola otomatis) | Supabase internal |

### 10.2 Aturan penyimpanan secret

- Semua secret disimpan sebagai environment variable — tidak pernah ditulis dalam kode atau file konfigurasi yang masuk ke version control
- File `.env` tidak pernah di-commit ke Git — hanya `.env.example` yang berisi placeholder tanpa nilai
- Di Vercel dan platform deployment lain, secret diinput melalui dashboard environment variables — tidak melalui file
- Setiap secret harus didokumentasikan di `.env.example` agar developer baru tahu variabel apa yang perlu dikonfigurasi

### 10.3 Rotasi secret

Secret perlu dirotasi secara berkala atau segera jika ada indikasi kebocoran:

| Secret | Frekuensi rotasi | Rotasi darurat |
|---|---|---|
| Supabase service role key | Setiap 6 bulan | Jika ada akses tidak sah |
| Anthropic API key | Setiap 6 bulan | Jika ada penggunaan tidak wajar |
| Service-to-service token | Setiap 3 bulan | Jika ada indikasi kebocoran |

**Prosedur rotasi:** Generate secret baru → deploy ke semua service yang membutuhkan → verifikasi sistem berjalan normal → nonaktifkan secret lama. Kedua secret (lama dan baru) harus aktif bersamaan selama periode transisi deployment.

### 10.4 Jika secret bocor

Jika ada indikasi bahwa secret telah bocor:
1. Nonaktifkan secret lama segera (tidak menunggu rotasi terjadwal)
2. Generate dan deploy secret baru
3. Investigasi bagaimana kebocoran terjadi
4. Catat insiden dan tindakan yang diambil
5. Review apakah ada akses tidak sah yang terjadi menggunakan secret tersebut

---

## 11. Aturan & Larangan

**Dilarang menyimpan password dalam bentuk apapun** — termasuk sebagai plaintext, base64, atau hash yang lemah. Password dikelola sepenuhnya oleh Supabase Auth.

**Dilarang mengekspos service role key ke frontend** atau ke environment variable yang di-prefix `NEXT_PUBLIC_`. Service role key memberikan akses penuh ke database tanpa RLS — kebocoran ini bersifat kritis.

**Dilarang bypass RLS** menggunakan service role key untuk operasi yang seharusnya melalui RLS. Service role key hanya untuk operasi admin yang memang tidak bisa melalui RLS (misalnya seed data dan operasi maintenance).

**Dilarang menyimpan token di localStorage.** Access token disimpan di Zustand store (memori), refresh token di cookie HttpOnly. localStorage rentan terhadap XSS.

**Dilarang mencatat informasi sensitif di log.** Nilai harga, konten evaluasi, dan credential tidak boleh muncul di log dalam bentuk apapun.

**Dilarang mengizinkan akses langsung dari internet ke FastAPI** — kecuali endpoint SSE yang memang dirancang untuk browser. Semua endpoint internal FastAPI hanya boleh dapat dijangkau dari jaringan internal.

**Dilarang hardcode secret di kode** dalam bentuk apapun — string literal, komentar, atau konfigurasi default. Semua secret melalui environment variable.

---

## 12. Catatan untuk Dokumen Lanjutan

### Untuk SH-02 (Deployment Runbook)

Runbook perlu mencakup prosedur setup environment variables di setiap environment baru, prosedur rotasi secret, dan checklist keamanan sebelum deployment production (HTTPS aktif, CORS terkonfigurasi, RLS enabled di semua tabel).

### Untuk SH-03 (Testing Strategy)

Testing keamanan perlu mencakup:
- Test bahwa staff tidak bisa mengakses evaluasi milik staff lain
- Test bahwa endpoint manager tidak bisa diakses oleh staff
- Test bahwa request tanpa token ditolak dengan benar
- Test rate limiting berfungsi sesuai konfigurasi

### Untuk DB-01 (Data Model)

RLS policy yang sudah didefinisikan di DB-01 section 10 perlu diverifikasi konsistensinya dengan aturan otorisasi di dokumen ini — khususnya bahwa semua tabel yang berisi data sensitif sudah memiliki RLS yang aktif.

---

*Dokumen ini adalah living document — kebijakan keamanan akan diperbarui sesuai perkembangan ancaman dan kebutuhan compliance.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
