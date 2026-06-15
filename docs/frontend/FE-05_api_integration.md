# FE-05 — API Integration Specification

**Project:** AI Vendor Selection System  
**Dokumen:** FE-05 — API Integration  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-07  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Gambaran Integrasi](#3-gambaran-integrasi)
4. [HTTP Client](#4-http-client)
5. [Autentikasi di Setiap Request](#5-autentikasi-di-setiap-request)
6. [Pola Query (Read)](#6-pola-query-read)
7. [Pola Mutasi (Write)](#7-pola-mutasi-write)
8. [Pola Async — Upload & Polling](#8-pola-async--upload--polling)
9. [Pola Real-time — Supabase Realtime](#9-pola-real-time--supabase-realtime)
10. [Pola Streaming — SSE AI Chat](#10-pola-streaming--sse-ai-chat)
11. [Error Handling Global](#11-error-handling-global)
12. [Aturan & Larangan](#12-aturan--larangan)
13. [Catatan untuk Dokumen Lanjutan](#13-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **bagaimana frontend berkomunikasi dengan semua sumber data** — Next.js API Routes, FastAPI, dan Supabase Realtime — beserta pola-pola yang digunakan untuk setiap jenis komunikasi.

Dokumen ini menjawab pertanyaan: bagaimana request dikirim, bagaimana token disisipkan secara otomatis, bagaimana error ditangani secara konsisten, dan bagaimana pola khusus seperti polling, real-time subscription, dan SSE streaming dikelola.

Dokumen ini **tidak** mendefinisikan endpoint yang tersedia — itu adalah tanggung jawab BE-02. Dokumen ini mendefinisikan **cara** frontend mengonsumsi endpoint tersebut.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-01 | UI Architecture | Tech stack dan keputusan HTTP client |
| FE-04 | State Management | TanStack Query sebagai pengelola server state |
| BE-02 | API Contract | Endpoint yang dikonsumsi, format request/response |
| DB-01 | Data Model | Struktur data yang dikembalikan |

---

## 3. Gambaran Integrasi

Frontend berkomunikasi dengan tiga sumber data yang berbeda, masing-masing dengan pola komunikasi yang berbeda pula.

```
Frontend (Browser)
     │
     ├── REST (fetch) ──────────► Next.js API Routes
     │                            (Auth, CRUD evaluasi,
     │                             approval, konfigurasi)
     │
     ├── SSE (EventSource) ─────► FastAPI
     │                            (AI chat streaming)
     │
     └── WebSocket/Realtime ────► Supabase Realtime
                                  (Progress agent real-time)
```

**Mengapa tiga jalur komunikasi berbeda:** Setiap jalur dipilih karena paling sesuai dengan karakteristik datanya. REST untuk operasi request-response standar. SSE untuk streaming satu arah dari server ke client (respons AI). Supabase Realtime untuk perubahan database yang perlu dipush ke semua client yang terkoneksi.

---

## 4. HTTP Client

### 4.1 Mengapa native fetch

Aplikasi menggunakan native `fetch` bawaan browser dan Next.js — tidak ada HTTP client library tambahan seperti Axios. Next.js 14 memperluas `fetch` dengan kemampuan caching dan revalidasi di Server Components, yang tidak tersedia di library pihak ketiga.

Untuk client-side fetching, perbedaan antara native `fetch` dan Axios tidak signifikan untuk kebutuhan project ini. Mengurangi satu dependency adalah keuntungan yang nyata.

### 4.2 API client wrapper

Alih-alih memanggil `fetch` langsung di komponen atau TanStack Query fetchers, semua HTTP call dikapsulasi dalam fungsi-fungsi di folder `lib/api/`. Setiap domain data memiliki file API client-nya sendiri.

**Struktur folder API client:**

```
lib/api/
├── client.ts          ← Base fetch wrapper dengan auth header
├── evaluasi.ts        ← Semua fungsi terkait evaluasi
├── vendor.ts          ← Fungsi terkait vendor
├── auth.ts            ← Fungsi autentikasi
├── konfigurasi.ts     ← Fungsi konfigurasi kriteria
└── hasil.ts           ← Fungsi hasil evaluasi
```

**Mengapa dikapsulasi:** Jika URL base API berubah, format header berubah, atau ada logika tambahan yang perlu diterapkan ke semua request (seperti logging), cukup ubah di satu tempat — `client.ts` — tanpa menyentuh setiap komponen yang melakukan fetching.

### 4.3 Base URL per environment

API client membaca base URL dari environment variables:
- Next.js API Routes: dibaca dari `NEXT_PUBLIC_BACKEND_API_URL` untuk client-side calls
- FastAPI (SSE): dibaca dari `NEXT_PUBLIC_FASTAPI_URL`
- Di Server Components, Next.js API Routes dipanggil langsung tanpa base URL eksternal

---

## 5. Autentikasi di Setiap Request

### 5.1 Penyisipan token otomatis

Setiap request ke Next.js API Routes yang membutuhkan autentikasi wajib menyertakan header `Authorization: Bearer <token>`. Token dibaca dari `authStore` (Zustand) saat runtime.

Penyisipan token dilakukan di `client.ts` — base fetch wrapper — sehingga semua fungsi di `lib/api/` secara otomatis menyertakan token tanpa perlu menambahkannya secara manual di setiap fungsi.

### 5.2 Token refresh otomatis

Access token memiliki masa berlaku 1 jam. Ketika server mengembalikan error 401, client harus mencoba me-refresh token menggunakan refresh token sebelum menyerah dan mengarahkan user ke halaman login.

**Alur token refresh:**

```
Request gagal dengan 401
        ↓
Coba POST /auth/refresh dengan refresh token
        ↓
    Berhasil?
   ↙         ↘
  Ya           Tidak
  ↓             ↓
Simpan token   Kosongkan authStore
baru di store  Redirect ke /login
Ulangi request
asli
```

**Mengapa ini penting:** Tanpa mekanisme ini, user akan mendapatkan error atau diarahkan ke halaman login setiap jam meskipun mereka masih aktif menggunakan aplikasi — pengalaman yang sangat buruk.

**Perlindungan race condition:** Jika beberapa request gagal 401 secara bersamaan, hanya satu refresh request yang boleh dikirim. Request-request lain menunggu hasil refresh sebelum melanjutkan.

### 5.3 Server Components

Di Server Components, token dibaca dari cookie request — bukan dari Zustand (yang tidak tersedia di server). Cookie diteruskan secara otomatis oleh browser ke setiap request, termasuk request yang dilakukan di server saat rendering.

---

## 6. Pola Query (Read)

Semua operasi read menggunakan TanStack Query dengan fungsi fetcher dari `lib/api/`.

### 6.1 Struktur dasar sebuah query

Setiap query memiliki tiga elemen yang selalu didefinisikan bersama:
- **Query key** — identifier unik sesuai konvensi di FE-04 section 6.2
- **Query function** — fungsi yang melakukan fetch dan mengembalikan data
- **Opsi** — stale time, enabled condition, dan opsi lain yang relevan

### 6.2 Enabled condition

Beberapa query hanya boleh dijalankan ketika prasyarat tertentu terpenuhi. Query detail evaluasi hanya dijalankan jika `id` tersedia. Query hasil evaluasi hanya dijalankan jika evaluasi berstatus `selesai` atau lebih lanjut.

Kondisi ini mencegah request yang tidak perlu dikirim ke server dan mencegah error yang terjadi karena query berjalan sebelum data yang dibutuhkannya tersedia.

### 6.3 Query untuk daftar evaluasi (dengan filter)

Query ini digunakan di Dashboard (P-02), Riwayat (P-06), dan Approval (P-07). Filter yang diaplikasikan berbeda per halaman, tetapi pola query-nya sama.

Query key menyertakan objek filter sebagai bagian dari key sehingga TanStack Query memperlakukan setiap kombinasi filter sebagai cache tersendiri. Filter berbeda menghasilkan cache berbeda.

### 6.4 Prefetching

Untuk meningkatkan performa navigasi, beberapa data dapat di-prefetch sebelum user benar-benar membutuhkannya:
- Data detail evaluasi dapat di-prefetch saat user mengarahkan kursor ke baris evaluasi di tabel
- Data hasil evaluasi dapat di-prefetch saat processing hampir selesai (berdasarkan progress yang mendekati 100%)

Prefetching bersifat opsional dan dapat diimplementasikan setelah fitur dasar berjalan.

---

## 7. Pola Mutasi (Write)

Semua operasi write (POST, PATCH, PUT, DELETE) menggunakan TanStack Query mutations.

### 7.1 Struktur dasar sebuah mutasi

Setiap mutasi memiliki tiga callback yang selalu didefinisikan:
- **`onSuccess`** — invalidasi cache yang relevan dan tampilkan notifikasi sukses
- **`onError`** — tampilkan notifikasi error dengan pesan yang sesuai
- **`onSettled`** — aksi yang perlu dilakukan terlepas dari sukses atau gagal (jarang dibutuhkan)

### 7.2 Invalidasi cache setelah mutasi

Setelah mutasi berhasil, cache yang terdampak harus diinvalidasi agar data yang ditampilkan tetap akurat. Tabel invalidasi lengkap ada di FE-04 section 6.4.

Invalidasi dilakukan di callback `onSuccess` mutasi — bukan setelah mutasi selesai di komponen — agar logika ini terpusat di satu tempat dan konsisten.

### 7.3 Loading state selama mutasi

Selama mutasi berlangsung, komponen yang memicunya harus menampilkan indikator loading dan menonaktifkan tombol submit untuk mencegah double submission. TanStack Query menyediakan property `isPending` untuk ini.

### 7.4 Mengapa mutasi tidak di-retry otomatis

Tidak seperti query yang bisa di-retry tanpa efek samping, mutasi yang diulangi bisa menyebabkan data duplikat atau aksi yang terjadi dua kali (misalnya evaluasi tersubmit dua kali). Retry mutasi hanya dilakukan secara eksplisit oleh user, bukan secara otomatis oleh sistem.

---

## 8. Pola Async — Upload & Polling

Upload dokumen penawaran vendor adalah operasi dua tahap: upload file ke storage, lalu tunggu AI mengekstrak datanya. Proses ekstraksi berjalan async di server dan hasilnya tidak tersedia langsung.

### 8.1 Mengapa pendekatan ini diperlukan

AI mengekstrak data dari dokumen menggunakan LLM yang bisa membutuhkan waktu beberapa detik hingga puluhan detik. Membuat request HTTP menunggu selama itu akan menyebabkan timeout dan pengalaman user yang buruk. Pendekatan async memungkinkan user melihat progress tanpa browser terblokir.

### 8.2 Alur upload dan polling

```
User upload file
      ↓
POST /evaluasi/:id/dokumen
      ↓
Server mengembalikan uploadId (status: extracting)
      ↓
Frontend mulai polling setiap 3 detik:
GET /evaluasi/:id/dokumen/:uploadId/status
      ↓
    Status?
   ↙    ↘
done    failed
  ↓       ↓
Tampilkan  Tampilkan
hasil      error,
ekstraksi  fallback
           ke manual
```

### 8.3 Mengapa polling, bukan Supabase Realtime untuk kasus ini

Ekstraksi dokumen adalah proses yang terisolasi per upload — tidak ada kebutuhan untuk broadcast ke banyak client. Polling sederhana cukup dan tidak membutuhkan subscription management tambahan. Supabase Realtime lebih tepat untuk data yang berubah cepat dan perlu di-sync ke banyak client (seperti progress agent).

### 8.4 Batas polling

Polling tidak boleh berjalan selamanya. Jika setelah 2 menit status masih bukan `done` atau `failed`, polling dihentikan dan ditampilkan pesan timeout kepada user dengan opsi untuk mencoba upload ulang. Ini melindungi dari kasus di mana server mengalami masalah dan tidak pernah memperbarui status.

---

## 9. Pola Real-time — Supabase Realtime

Supabase Realtime digunakan untuk menerima update progress agent secara real-time di halaman P-04.

### 9.1 Kapan subscription dibuat dan dihancurkan

Subscription dibuat saat komponen `AgentProgressPanel` di-mount dan dihancurkan saat komponen di-unmount. Manajemen lifecycle subscription ini penting — subscription yang tidak dihancurkan akan terus berjalan di background dan menyebabkan memory leak.

### 9.2 Apa yang di-subscribe

Frontend subscribe ke perubahan pada tabel `agent_progress` yang terbatas pada `evaluasi_id` tertentu. Hanya perubahan yang relevan untuk evaluasi yang sedang ditampilkan yang diterima — bukan seluruh perubahan tabel.

### 9.3 Alur data real-time

```
FastAPI menulis progress ke tabel agent_progress di Supabase
                    ↓
Supabase mendeteksi perubahan pada tabel
                    ↓
Supabase mengirimkan payload perubahan ke semua client
yang subscribe ke channel evaluasi tersebut
                    ↓
Frontend menerima payload dan memperbarui local state
AgentProgressPanel
                    ↓
Komponen re-render dengan data progress terbaru
```

### 9.4 Hubungan dengan TanStack Query

Data progress agent dari Supabase Realtime **tidak** masuk ke TanStack Query cache. Ia langsung masuk ke local state komponen AgentProgressPanel. TanStack Query hanya digunakan untuk fetch data awal saat halaman pertama kali dibuka (untuk mendapatkan status agent yang mungkin sudah ada jika user me-refresh halaman di tengah proses).

---

## 10. Pola Streaming — SSE AI Chat

AI chat di panel kanan menggunakan Server-Sent Events (SSE) untuk menerima respons AI secara streaming — token demi token seiring LLM menghasilkannya.

### 10.1 Mengapa SSE untuk AI chat

SSE adalah standar industri untuk streaming respons LLM. Karakteristiknya cocok dengan kebutuhan ini: komunikasi satu arah dari server ke client, koneksi HTTP standar yang bekerja di semua proxy dan CDN, dan tidak membutuhkan handshake seperti WebSocket.

### 10.2 Alur streaming

```
User kirim pesan
      ↓
Buka koneksi SSE ke POST /v1/chat/stream (FastAPI)
dengan body: pesan + konteks halaman + riwayat chat
      ↓
Terima stream event demi event:
  - type: "token"  → append ke buffer display
  - type: "done"   → pindahkan buffer ke chatStore, tutup koneksi
  - type: "error"  → tampilkan error, tutup koneksi
      ↓
Koneksi tertutup
```

### 10.3 Buffer display vs chatStore

Selama streaming berlangsung, token yang masuk diakumulasi di buffer local state AIPanel — bukan langsung ke chatStore. Ini mencegah re-render berlebihan yang akan terjadi jika setiap token langsung memperbarui store.

Hanya setelah streaming selesai, pesan lengkap dipindahkan ke chatStore sebagai satu operasi tunggal.

### 10.4 Konteks yang dikirim ke setiap request

Setiap request chat menyertakan konteks halaman aktif sehingga AI dapat merespons secara relevan. Konteks ini dibaca dari `chatStore` (yang diperbarui oleh AppShell setiap kali halaman berganti) dan disertakan sebagai bagian dari request body.

### 10.5 Penanganan koneksi yang terputus

Jika koneksi SSE terputus di tengah streaming (misalnya karena masalah jaringan), ditampilkan indikator error dan user diberi opsi untuk mengirim ulang pesan. Reconnect otomatis tidak dilakukan — respons AI yang terpotong tidak bisa dilanjutkan dari tengah.

---

## 11. Error Handling Global

### 11.1 Dua level error handling

**Level global** — error yang terjadi di luar konteks satu komponen spesifik, atau error yang pola penanganannya sama di seluruh aplikasi. Contoh: 401 untuk token refresh, 503 untuk server tidak tersedia.

**Level lokal** — error yang penanganannya bergantung pada konteks. Contoh: error saat submit form evaluasi ditampilkan sebagai notifikasi dengan pesan yang menjelaskan apa yang gagal. Error saat mengambil detail evaluasi yang tidak ditemukan ditampilkan sebagai halaman empty state.

### 11.2 Penanganan berdasarkan HTTP status

| Status | Penanganan |
|---|---|
| 400 | Tampilkan pesan error dari field `error.details` di dekat field yang bermasalah (form error) |
| 401 | Coba refresh token otomatis. Jika gagal, redirect ke `/login` |
| 403 | Tampilkan pesan "Anda tidak memiliki akses ke halaman ini" dan redirect ke `/dashboard` |
| 404 | Tampilkan empty state di halaman dengan pesan kontekstual |
| 409 | Tampilkan notifikasi error dengan pesan dari `error.message` |
| 429 | Tampilkan notifikasi bahwa user perlu menunggu sebelum mencoba lagi |
| 500 | Tampilkan notifikasi error umum. Log detail error untuk debugging |
| 503 | Tampilkan notifikasi bahwa layanan AI sedang tidak tersedia, minta user coba lagi nanti |

### 11.3 Error boundary

Untuk error yang tidak tertangkap (unexpected JavaScript error di Client Components), Next.js menyediakan mekanisme `error.tsx` per route segment. Setiap route utama memiliki `error.tsx` yang menampilkan halaman error yang informatif dengan tombol "Coba lagi".

### 11.4 Pesan error untuk user

Pesan error yang ditampilkan ke user harus:
- Ditulis dalam bahasa yang dimengerti user non-teknis
- Menjelaskan apa yang terjadi dan (jika memungkinkan) apa yang bisa dilakukan user
- Tidak mengekspos detail teknis seperti stack trace atau nama kolom database

Terjemahan dari error code ke pesan user-friendly disimpan di `lib/constants/errorMessages.ts` — bukan ditulis langsung di komponen.

---

## 12. Aturan & Larangan

**Dilarang memanggil `fetch` langsung di komponen.** Semua HTTP call harus melalui fungsi di `lib/api/` yang dikonsumsi melalui TanStack Query atau custom hook. Ini memastikan autentikasi dan error handling diterapkan secara konsisten.

**Dilarang menyimpan response API langsung ke Zustand.** Server state dikelola oleh TanStack Query. Zustand hanya untuk client state yang tidak berasal dari server.

**Dilarang mengekspos service role key Supabase ke client.** `SUPABASE_SERVICE_ROLE_KEY` hanya boleh digunakan di server (Next.js API Routes atau Server Components) — tidak boleh ada di variabel `NEXT_PUBLIC_`.

**Dilarang mengirim request tanpa error handling.** Setiap fungsi di `lib/api/` harus menangani kasus error dan melemparkan error dengan format yang konsisten sehingga TanStack Query dapat menanganinya.

**Dilarang polling tanpa batas waktu.** Setiap polling interval harus memiliki kondisi berhenti: status target tercapai, timeout, atau komponen di-unmount.

**Dilarang membiarkan koneksi SSE atau Realtime subscription terbuka setelah komponen di-unmount.** Setiap koneksi yang dibuka harus ditutup di cleanup function.

---

## 13. Catatan untuk Dokumen Lanjutan

### Untuk BE-02 (API Contract)

Pola token refresh di section 5.2 mengasumsikan endpoint `POST /api/v1/auth/refresh` tersedia dan mengembalikan token baru. BE-02 perlu memastikan endpoint ini mengembalikan format yang konsisten dengan yang diharapkan client.

### Untuk AI-01 (Agent Orchestration)

Pola Supabase Realtime di section 9 mengasumsikan FastAPI menulis ke tabel `agent_progress` dengan struktur yang sudah didefinisikan di DB-01. AI-01 perlu memastikan penulisan ke tabel ini dilakukan dengan benar agar Realtime broadcast berjalan.

### Untuk FE-04 (State Management)

Dokumen ini mengasumsikan query keys dan stale time sudah didefinisikan di FE-04. Kedua dokumen harus konsisten — perubahan query key di FE-04 harus diikuti perubahan di fungsi-fungsi `lib/api/`.

---

*Dokumen ini adalah living document — akan diperbarui jika ada perubahan pola integrasi.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
| 3.0.0 | 2026-06-13 | Adopsi ADR-035 (namespace AI): perbarui catatan dokumen lanjutan (BE-03→AI-01) | — |
