# FE-01 — UI Architecture Specification

**Project:** AI Vendor Selection System  
**Dokumen:** FE-01 — UI Architecture  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-07  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Gambaran Arsitektur Frontend](#3-gambaran-arsitektur-frontend)
4. [Tech Stack & Keputusan Teknologi](#4-tech-stack--keputusan-teknologi)
5. [Struktur Repository](#5-struktur-repository)
6. [Struktur Folder](#6-struktur-folder)
7. [Routing & Navigasi](#7-routing--navigasi)
8. [Rendering Strategy](#8-rendering-strategy)
9. [State Management](#9-state-management)
10. [Design System](#10-design-system)
11. [Environment & Konfigurasi](#11-environment--konfigurasi)
12. [Deployment](#12-deployment)
13. [Catatan untuk Dokumen Lanjutan](#13-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **fondasi arsitektur teknis frontend** — keputusan teknologi apa yang digunakan, mengapa dipilih, bagaimana project diorganisir, dan prinsip-prinsip apa yang mengikat seluruh codebase frontend.

Dokumen ini menjadi referensi pertama bagi siapapun yang bergabung ke tim frontend. Setelah membaca dokumen ini, engineer harus memahami keseluruhan landscape teknis sebelum masuk ke detail implementasi di dokumen lain.

Dokumen ini **tidak** mendefinisikan implementasi komponen, endpoint API, atau logika bisnis — masing-masing dibahas di FE-02, BE-02, dan dokumen lainnya.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-02 | Component Library | Komponen yang dibangun di atas arsitektur ini |
| FE-03 | Page & User Flow | Halaman dan alur yang diimplementasikan |
| FE-04 | State Management | Detail pengelolaan state global |
| FE-05 | API Integration | Pola konsumsi API dari frontend |
| BE-02 | API Contract | Kontrak API yang dikonsumsi frontend |

---

## 3. Gambaran Arsitektur Frontend

Frontend aplikasi ini adalah **aplikasi Next.js yang berdiri sendiri** dalam repository terpisah. Ia berkomunikasi dengan dua backend: Next.js API Routes (untuk operasi standar) dan FastAPI (untuk SSE streaming AI chat). Seluruh autentikasi dikelola melalui Supabase Auth, dan koneksi real-time untuk progress agent menggunakan Supabase Realtime client langsung dari browser.

```
┌─────────────────────────────────────────┐
│  Frontend (Next.js — Vercel)            │
│                                         │
│  ┌─────────────┐   ┌─────────────────┐  │
│  │ Server      │   │ Client          │  │
│  │ Components  │   │ Components      │  │
│  │ (RSC)       │   │ ('use client')  │  │
│  └──────┬──────┘   └────────┬────────┘  │
│         │                   │           │
└─────────┼───────────────────┼───────────┘
          │                   │
          │ fetch (server)     │ HTTP / SSE / Realtime
          ▼                   ▼
   Next.js API Routes     FastAPI & Supabase
```

**Dua lapisan rendering yang bekerja bersama:** Server Components menangani pengambilan data awal dan rendering HTML di server. Client Components menangani interaktivitas, state lokal, dan koneksi real-time. Pemisahan ini bukan sekadar konvensi — ia menentukan di mana logika dijalankan dan bagaimana performa dioptimalkan.

---

## 4. Tech Stack & Keputusan Teknologi

### 4.1 Ringkasan stack

| Kebutuhan | Teknologi | Versi Minimum |
|---|---|---|
| Framework | Next.js (App Router) | 14 |
| Bahasa | TypeScript | 5 |
| Styling | Tailwind CSS | 3 |
| UI Components | shadcn/ui | Latest |
| State management | Zustand | 4 |
| Data fetching | TanStack Query (React Query) | 5 |
| Form & validasi | React Hook Form + Zod | Latest |
| Chart | Chart.js + react-chartjs-2 | Chart.js 4 |
| Icon | Lucide React | Latest |
| Realtime | Supabase JS Client | 2 |
| HTTP Client | Native fetch (Next.js built-in) | — |

### 4.2 Mengapa Next.js App Router

App Router dipilih dibanding Pages Router karena beberapa alasan yang relevan untuk project ini. Server Components memungkinkan pengambilan data di server tanpa mengirim logika fetch ke browser, mengurangi JavaScript yang dikirim ke client. Nested layouts memudahkan implementasi layout 3-panel yang konsisten tanpa duplikasi kode. Route handlers (pengganti API routes di App Router) lebih fleksibel untuk implementasi middleware autentikasi.

### 4.3 Mengapa Zustand untuk state management

Zustand dipilih karena skalanya tepat untuk project ini. Redux Toolkit terlalu verbose untuk kompleksitas state yang ada — sebagian besar state dapat dikelola oleh TanStack Query (server state) atau state lokal komponen. Zustand mengisi celah untuk state global yang benar-benar perlu disharing antar komponen jauh: sesi user, riwayat chat AI panel, dan notifikasi global.

### 4.4 Mengapa TanStack Query

TanStack Query menangani semua yang berkaitan dengan server state: caching response API, refetching otomatis, loading dan error state, dan invalidasi cache saat mutasi terjadi. Tanpa TanStack Query, logika ini harus ditulis manual di setiap komponen atau dimasukkan ke Zustand — mencampur server state dan client state dalam satu store.

**Prinsip pembagian:** TanStack Query untuk data yang berasal dari server. Zustand untuk state UI global yang tidak berasal dari server.

### 4.5 Mengapa polyrepo

Frontend dan backend (Next.js API Routes + FastAPI) berada di repository terpisah. Keputusan ini didasarkan pada perbedaan bahasa (TypeScript vs Python), perbedaan siklus deployment, dan perbedaan tim yang bertanggung jawab. Polyrepo membuat batas tanggung jawab lebih jelas dan mencegah perubahan di satu sisi tidak sengaja mempengaruhi sisi lain.

---

## 5. Struktur Repository

Frontend memiliki repository tersendiri dengan nama yang disepakati tim. Repository ini hanya berisi kode Next.js — tidak ada kode Python atau konfigurasi FastAPI di dalamnya.

**Tiga repository dalam project ini:**

| Repository | Isi | Bahasa |
|---|---|---|
| `vendor-ai-frontend` | Next.js application | TypeScript |
| `vendor-ai-backend` | Next.js API Routes (BFF layer) | TypeScript |
| `vendor-ai-agent` | FastAPI service (AI & scoring) | Python |

**Catatan:** Repository `vendor-ai-backend` dan `vendor-ai-frontend` dapat digabung menjadi satu project Next.js (API Routes dan frontend dalam satu codebase). Keputusan ini diserahkan ke tim, tetapi dokumen ini mengasumsikan keduanya terpisah untuk kejelasan batas tanggung jawab.

---

## 6. Struktur Folder

Struktur folder mengikuti konvensi App Router Next.js dengan penambahan folder khusus untuk komponen, hooks, dan utilities.

```
vendor-ai-frontend/
├── app/                          ← Semua route dan halaman (App Router)
│   ├── (auth)/                   ← Route group untuk halaman yang butuh auth
│   │   ├── dashboard/
│   │   ├── evaluasi/
│   │   │   ├── baru/
│   │   │   └── [id]/
│   │   │       ├── proses/
│   │   │       └── hasil/
│   │   ├── riwayat/
│   │   ├── approval/             ← Hanya Manager
│   │   └── settings/             ← Hanya Manager
│   ├── login/
│   └── layout.tsx                ← Root layout
│
├── components/                   ← Semua komponen UI (lihat FE-02)
│   ├── atomic/
│   ├── composite/
│   ├── layout/
│   ├── feature/
│   └── charts/
│
├── hooks/                        ← Custom React hooks
│   ├── useEvaluasi.ts
│   ├── useAgentProgress.ts
│   └── useAIChat.ts
│
├── stores/                       ← Zustand stores
│   ├── authStore.ts
│   ├── chatStore.ts
│   └── notificationStore.ts
│
├── lib/                          ← Utilities dan konfigurasi
│   ├── api/                      ← API client functions
│   ├── supabase/                 ← Supabase client setup
│   ├── validations/              ← Zod schemas
│   └── constants/                ← Konstanta aplikasi
│
├── types/                        ← TypeScript type definitions
│
├── public/                       ← Static assets
│
└── middleware.ts                 ← Auth guard dan redirect rules
```

### 6.1 Mengapa route groups dengan `(auth)`

Route group `(auth)` memisahkan halaman yang membutuhkan autentikasi dari halaman publik (login). Semua route di dalam `(auth)` secara otomatis dilindungi oleh middleware — tanpa perlu menambahkan pengecekan auth di tiap halaman secara manual.

### 6.2 Mengapa `hooks/` terpisah dari `components/`

Custom hooks berisi logika yang bisa dipakai oleh beberapa komponen. Memisahkannya dari komponen mencegah duplikasi logika dan membuat testing lebih mudah — logika dapat di-test secara independen tanpa perlu me-render komponen.

---

## 7. Routing & Navigasi

### 7.1 Strategi routing

Aplikasi menggunakan **file-based routing** bawaan Next.js App Router. Setiap folder dalam `app/` merepresentasikan satu segmen URL. Tidak ada routing library tambahan.

### 7.2 Tabel route

| URL Path | Folder di `app/` | Halaman (FE-03) |
|---|---|---|
| `/login` | `app/login/` | P-01 |
| `/dashboard` | `app/(auth)/dashboard/` | P-02 |
| `/evaluasi/baru` | `app/(auth)/evaluasi/baru/` | P-03 |
| `/evaluasi/:id/proses` | `app/(auth)/evaluasi/[id]/proses/` | P-04 |
| `/evaluasi/:id/hasil` | `app/(auth)/evaluasi/[id]/hasil/` | P-05 |
| `/riwayat` | `app/(auth)/riwayat/` | P-06 |
| `/approval` | `app/(auth)/approval/` | P-07 |
| `/settings/kriteria` | `app/(auth)/settings/kriteria/` | P-08 |

### 7.3 Middleware autentikasi

File `middleware.ts` di root project bertugas memeriksa keberadaan dan validitas token sebelum request sampai ke halaman. Middleware ini menjalankan dua pengecekan:

Pertama, jika user belum login dan mengakses route di dalam `(auth)`, user diarahkan ke `/login`. Kedua, jika user sudah login dan mengakses `/login`, user diarahkan ke `/dashboard`.

Pengecekan role (staff vs manager) untuk route seperti `/approval` dan `/settings/kriteria` dilakukan di level halaman — bukan di middleware — karena membutuhkan informasi role yang ada di token, dan middleware sebaiknya tetap ringan.

### 7.4 Navigasi programatik

Perpindahan halaman yang dipicu oleh aksi user (bukan klik link) menggunakan `useRouter` dari Next.js. Contoh: setelah submit evaluasi berhasil, user diarahkan otomatis ke halaman processing.

---

## 8. Rendering Strategy

Salah satu keputusan arsitektur paling penting di App Router adalah menentukan komponen mana yang dirender di server (Server Components) dan mana yang dirender di client (Client Components).

### 8.1 Prinsip dasar

**Default ke Server Component.** Komponen hanya dijadikan Client Component jika membutuhkan salah satu dari: interaktivitas (event handler), state lokal (useState, useReducer), hooks browser (useEffect, useRef), atau koneksi real-time.

**Mengapa Server Component sebagai default:** Server Components tidak mengirim JavaScript ke browser — hanya HTML yang dihasilkan. Ini mengurangi ukuran bundle secara signifikan dan mempercepat initial load, terutama penting untuk halaman yang datanya bisa diambil di server.

### 8.2 Pembagian per halaman

| Halaman | Bagian Server Component | Bagian Client Component |
|---|---|---|
| P-02 Dashboard | Layout, data fetching awal | Stat cards (auto-refresh), AI panel |
| P-03 Buat Evaluasi | Layout, daftar kategori | Stepper, form input, upload handler |
| P-04 Processing | Layout, data awal evaluasi | Progress panel (Realtime), AI panel |
| P-05 Hasil | Layout, data hasil evaluasi | Tabel interaktif, AI panel |
| P-07 Approval | Layout, daftar evaluasi pending | Form approve/reject, AI panel |
| P-08 Settings | Layout, konfigurasi aktif | Form bobot dengan validasi real-time |

### 8.3 Boundaries Client Component

Client Components ditandai dengan direktif `'use client'` di baris pertama file. Penting untuk menjaga boundaries ini sekecil mungkin — jika hanya satu bagian kecil dari halaman yang butuh interaktivitas, ekstrak bagian itu menjadi komponen terpisah daripada menjadikan seluruh halaman sebagai Client Component.

---

## 9. State Management

### 9.1 Tiga lapisan state

Aplikasi mengelola state dalam tiga lapisan yang berbeda tujuan dan scope-nya:

**Server state** — data yang berasal dari API dan perlu di-sync dengan server. Dikelola oleh TanStack Query. Contoh: daftar evaluasi, detail evaluasi, hasil rekomendasi.

**Global client state** — state UI yang perlu diakses oleh banyak komponen di berbagai bagian halaman, tidak berasal dari server. Dikelola oleh Zustand. Contoh: data sesi user, riwayat chat AI panel, antrian notifikasi.

**Local component state** — state yang hanya relevan untuk satu komponen. Dikelola oleh `useState` atau `useReducer`. Contoh: apakah dropdown sedang terbuka, nilai input yang belum disubmit.

### 9.2 Zustand stores

Tiga store yang didefinisikan untuk project ini:

**`authStore`** — menyimpan data user yang sedang login (id, nama, role, token). Diisi saat login berhasil, dikosongkan saat logout. Diakses oleh Sidebar untuk menampilkan nama user dan oleh middleware untuk pengecekan role.

**`chatStore`** — menyimpan riwayat percakapan dengan AI panel dalam sesi aktif. Menyimpan konteks halaman yang sedang aktif sehingga AI panel tahu harus merespons dalam konteks apa. Di-reset saat user berpindah ke evaluasi yang berbeda.

**`notificationStore`** — menyimpan antrian notifikasi toast yang perlu ditampilkan. Komponen manapun dapat menambahkan notifikasi ke antrian ini, dan komponen NotificationContainer di layout root yang menampilkannya.

### 9.3 Mengapa TanStack Query untuk server state

TanStack Query menyediakan caching otomatis — data yang sudah pernah diambil tidak perlu di-fetch ulang selama masih fresh. Ini mencegah request berulang saat user navigasi bolak-balik antar halaman. TanStack Query juga menangani invalidasi cache saat terjadi mutasi: setelah user menambah vendor baru, cache daftar vendor otomatis di-invalidate dan data terbaru di-fetch.

---

## 10. Design System

### 10.1 Fondasi: Tailwind CSS + shadcn/ui

Design system dibangun di atas Tailwind CSS sebagai styling engine dan shadcn/ui sebagai komponen base. shadcn/ui bukan dependency — komponen di-generate ke dalam project sehingga tim memiliki kendali penuh atas kode.

Seluruh detail design tokens (warna, tipografi, spacing) didefinisikan di FE-02 section 5. Dokumen ini hanya mendefinisikan prinsip dan struktur design system, bukan nilai tokennya.

### 10.2 Prinsip design system

**Satu sumber kebenaran untuk nilai visual.** Semua warna, ukuran font, dan spacing direferensikan dari Tailwind config — tidak ada nilai yang ditulis hardcoded di dalam komponen.

**Dark mode by default.** Semua komponen harus terlihat baik di light mode maupun dark mode. Tailwind menyediakan variant `dark:` untuk ini. Tidak boleh ada komponen yang hanya ditest di satu mode.

**Konsistensi melalui abstraksi.** Daripada menggunakan class Tailwind langsung di setiap tempat, nilai yang sering dipakai bersama dikelompokkan dalam komponen shadcn/ui atau custom components. Ini memastikan perubahan visual cukup dilakukan di satu tempat.

### 10.3 Font

Aplikasi menggunakan font sistem sebagai default untuk performa — tidak ada custom font yang perlu di-load dari external source. Jika desainer menentukan custom font di masa mendatang, keputusan ini dapat direvisi dengan mempertimbangkan dampak performa.

---

## 11. Environment & Konfigurasi

### 11.1 Environment variables

Aplikasi membutuhkan beberapa nilai konfigurasi yang berbeda per environment (development, staging, production). Nilai-nilai ini tidak boleh di-hardcode di dalam kode.

**Variabel yang dibutuhkan:**

| Variabel | Scope | Keterangan |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Public | URL project Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public | Anon key Supabase untuk client-side |
| `NEXT_PUBLIC_FASTAPI_URL` | Public | Base URL FastAPI untuk SSE chat |
| `BACKEND_API_URL` | Server only | URL Next.js API Routes (untuk server-to-server) |
| `SUPABASE_SERVICE_ROLE_KEY` | Server only | Service role key untuk operasi admin Supabase |

**Mengapa ada pemisahan Public dan Server only:** Variabel dengan prefix `NEXT_PUBLIC_` dikirim ke browser dan bisa dibaca oleh siapapun. Variabel tanpa prefix hanya tersedia di server. Service role key dan secret credentials tidak boleh pernah masuk ke browser.

### 11.2 Environment files

| File | Digunakan untuk | Masuk Git |
|---|---|---|
| `.env.local` | Development lokal | Tidak |
| `.env.staging` | Staging environment | Tidak |
| `.env.production` | Production | Tidak |
| `.env.example` | Template tanpa nilai sensitif | Ya |

`.env.example` wajib di-update setiap kali ada variabel baru ditambahkan, agar developer baru tahu variabel apa yang perlu dikonfigurasi.

---

## 12. Deployment

### 12.1 Platform: Vercel

Frontend di-deploy ke Vercel karena integrasinya yang native dengan Next.js: zero-configuration deployment, optimasi otomatis untuk Server Components, edge network global, dan preview deployment untuk setiap pull request.

### 12.2 Strategi branching & deployment

| Branch Git | Environment | URL |
|---|---|---|
| `main` | Production | Domain utama aplikasi |
| `staging` | Staging | Subdomain staging |
| Pull Request | Preview | URL unik per PR, auto-generated Vercel |

**Mengapa preview deployment per PR penting:** Setiap perubahan UI dapat direview secara visual oleh tim sebelum masuk ke staging atau production, tanpa perlu setup environment lokal.

### 12.3 Build & CI

Setiap push ke semua branch menjalankan pipeline CI secara otomatis dengan urutan:
1. Type checking — memastikan tidak ada TypeScript error
2. Linting — memastikan kode mengikuti aturan ESLint yang disepakati
3. Build — memastikan aplikasi berhasil di-build tanpa error
4. Deploy — jika semua tahap sebelumnya berhasil

Push ke `main` dan `staging` hanya boleh dilakukan melalui pull request yang sudah di-review — tidak boleh push langsung.

---

## 13. Catatan untuk Dokumen Lanjutan

### Untuk FE-04 (State Management)

Dokumen ini mendefinisikan tiga Zustand stores (`authStore`, `chatStore`, `notificationStore`) dan pembagian antara server state (TanStack Query) dan client state (Zustand). FE-04 perlu mendefinisikan lebih detail:
- Struktur data tiap store
- Kapan dan bagaimana tiap store di-reset
- Pola TanStack Query per domain data (evaluasi, vendor, hasil)
- Strategi invalidasi cache setelah mutasi

### Untuk FE-05 (API Integration)

Dokumen ini mendefinisikan bahwa HTTP client menggunakan native fetch bawaan Next.js. FE-05 perlu mendefinisikan:
- Wrapper function untuk setiap kelompok endpoint
- Penanganan token refresh otomatis
- Pola error handling global
- Pola polling untuk status ekstraksi dokumen
- Pola subscribe Supabase Realtime
- Pola baca SSE stream untuk AI chat

### Untuk BE-02 (API Contract)

Middleware autentikasi di `middleware.ts` membaca token dari cookie. BE-02 perlu memastikan endpoint login mengembalikan token dalam format yang dapat disimpan sebagai cookie HttpOnly oleh Next.js.

---

*Dokumen ini adalah living document — akan diperbarui jika ada perubahan keputusan arsitektur.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
