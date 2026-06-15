# Panduan Implementasi — Frontend Engineer
 
**Project:** AI Vendor Selection System  
**Role:** Frontend Engineer  
**Versi:** 2.0.0  
**Tanggal:** 2026-06-12  
**Referensi Utama:** FE-01, FE-02, FE-03, FE-04, FE-05, FE-06, MILESTONE_PLAN v4.0.0
 
---
 
## Tentang Dokumen Ini
 
Panduan ini adalah panduan kerja operasional untuk Frontend Engineer — bukan dokumen spesifikasi. Dokumen ini menerjemahkan semua task frontend dari Milestone Plan ke format yang lebih lengkap: **apa yang perlu dibangun**, **keterkaitan antar komponen**, **pola state dan data fetching yang benar untuk setiap konteks**, dan **definisi selesai yang terukur**.
 
Setiap fitur di sini mengacu ke spec resmi (FE-01 s/d FE-06). Jika ada konflik antara panduan ini dan dokumen spec, dokumen spec yang berlaku.
 
---
 
## Prasyarat Sebelum Memulai
 
Sebelum coding dimulai, semua hal berikut harus sudah beres:
 
- Monorepo `vendor-ai` sudah diinisialisasi dengan pnpm workspaces (setup dilakukan di F-00)
- `apps/web` sudah diinisialisasi dengan Next.js 14+ (App Router)
- TypeScript, Tailwind CSS, shadcn/ui sudah terkonfigurasi di `apps/web`
- Dependencies terinstall di `apps/web`: TanStack Query v5, Zustand v4, React Hook Form, Zod, Chart.js, react-chartjs-2, Lucide React, MSW
- `packages/types` dapat diimport dari `apps/web` tanpa error
- Konfigurasi design tokens di `apps/web/tailwind.config.ts` sesuai FE-02 section 5 (warna status, tipografi, lebar panel)
- Struktur folder dibuat sesuai FE-01 section 6 (di dalam `apps/web/`): `app/`, `components/atomic/`, `components/composite/`, `components/layout/`, `components/feature/`, `components/charts/`, `hooks/`, `stores/`, `lib/api/`, `lib/constants/`, `test/handlers/`
- MSW terkonfigurasi: `msw init public/`, setup service worker untuk browser dan server untuk Node test environment
- Tiga Zustand stores diinisialisasi: `authStore`, `chatStore`, `notificationStore` (struktur data sesuai FE-04 section 5)
- TanStack Query `QueryClient` dikonfigurasi secara global di layout root dengan stale time default dan retry config (FE-04 section 6.5: retry 2x untuk query, 0x untuk mutasi)
- `lib/api/client.ts` dibuat sebagai base fetch wrapper dengan auth header injection dari `authStore`
- File `FEATURE_STATUS.md` sudah ada di root `vendor-ai` (dibuat di F-00)
- Branch `develop` sudah dibuat dari `main` di repo `vendor-ai`
---
 
## Konvensi Penting
 
Sebelum coding fitur pertama, pahami konvensi-konvensi ini karena berlaku di seluruh codebase:
 
**Naming komponen:** PascalCase. Props handler diawali `on` (onSubmit, onApprove), props boolean diawali `is` atau `has` (isLoading, hasError), props collection selalu plural (vendors, agents).
 
**MSW dulu, API staging kemudian:** Setiap fitur dimulai dengan membuat MSW handler terlebih dahulu. Setelah endpoint staging siap, switch dari MSW ke API staging. Jangan biarkan MSW handler aktif setelah switch — nonaktifkan agar tidak bertabrakan.
 
**Komponen presentasional menerima data, tidak mengambilnya:** Komponen UI hanya menerima data via props. Data fetching adalah tanggung jawab page atau container, bukan komponen itu sendiri. Pengecualian harus eksplisit dan terdokumentasi (lihat FE-02 section 4.1).
 
**Server Component sebagai default:** Mulai dari Server Component, pindah ke `'use client'` hanya ketika dibutuhkan (interaktivitas, state, hooks, event listener). Boundary Client Component harus sesempit mungkin.
 
**Soft delete transparan:** Filter `deleted_at IS NULL` diterapkan di backend — frontend tidak perlu mengelolanya. Tapi frontend harus memastikan tidak ada sisa state dari item yang dihapus (invalidasi cache setelah delete).
 
---
 
## F-00 — Environment Setup
 
**Tier:** 0 | **Estimasi:** 2–3 hari
 
### Yang Perlu Dibuat
 
#### 1. Inisialisasi `apps/web` dan Dependencies
 
```
apps/web/
├── app/
│   ├── (auth)/
│   │   ├── dashboard/
│   │   ├── evaluasi/baru/
│   │   ├── evaluasi/[id]/proses/
│   │   ├── evaluasi/[id]/hasil/
│   │   ├── riwayat/
│   │   ├── approval/
│   │   └── settings/kriteria/
│   ├── login/
│   └── layout.tsx
├── components/
│   ├── atomic/
│   ├── composite/
│   ├── layout/
│   ├── feature/
│   └── charts/
├── hooks/
├── stores/
│   ├── authStore.ts
│   ├── chatStore.ts
│   └── notificationStore.ts
├── lib/
│   ├── api/
│   │   └── client.ts
│   └── constants/
│       └── errorMessages.ts
└── test/
    └── handlers/
```
 
#### 2. Design Tokens di `tailwind.config.ts`
 
Definisikan semua nilai dari FE-02 section 5 sebagai custom colors di Tailwind config. Ini penting dikerjakan di F-00 karena semua komponen berikutnya akan merujuk token ini.
 
Warna status yang wajib ada (gunakan sebagai custom color names):
- `status-draft` — abu-abu
- `status-processing` — biru
- `status-selesai` — hijau
- `status-menunggu-approval` — kuning/amber
- `status-approved` — hijau tua
- `status-butuh-revisi` — merah
Lebar panel sebagai custom values:
- `sidebar-width` — lebar tetap sidebar
- `ai-panel-width` — lebar tetap panel AI kanan
#### 3. Zustand Stores
 
Inisialisasi tiga store dengan struktur data yang benar sesuai FE-04 section 5:
 
**`authStore`** — menyimpan: `id`, `nama`, `email`, `role` (enum: `staff` | `manager`), `avatarUrl`, `isAuthenticated`, `accessToken`. Actions: `setUser()`, `clearUser()`.
 
**`chatStore`** — menyimpan: `messages` (array pesan dengan `role`, `content`, `timestamp`), `activeContext` (halaman aktif dan `evaluasiId`), `isStreaming`. Actions: `addMessage()`, `setStreamingBuffer()`, `commitStreamingMessage()`, `resetChat()`, `setContext()`.
 
**`notificationStore`** — menyimpan: `notifications` (array dengan `id`, `type`, `message`, `duration`). Actions: `addNotification()`, `removeNotification()`.
 
#### 4. TanStack Query Setup
 
Konfigurasi global di `app/providers.tsx` (Client Component yang membungkus semua halaman di root layout):
- Retry: 2 untuk query, 0 untuk mutasi
- Error 401: ditangani secara global untuk memicu token refresh
- Default stale time: 1 menit (nanti di-override per query sesuai FE-04 section 6.3)
#### 5. Base API Client `lib/api/client.ts`
 
Base fetch wrapper yang:
- Membaca token dari `authStore` dan menyisipkan ke header `Authorization: Bearer <token>`
- Di Server Components, membaca token dari cookie request
- Melempar error terstandarisasi agar TanStack Query bisa menanganinya konsisten
- Menangani race condition pada token refresh (hanya satu refresh request yang berjalan bersamaan)
- Membaca base URL dari environment variable
#### 6. MSW Setup
 
```
test/handlers/
├── auth.ts          ← Handler untuk login, logout, refresh, me
├── evaluasi.ts      ← Handler untuk CRUD evaluasi
├── vendor.ts        ← Handler untuk vendor operations
├── konfigurasi.ts   ← Handler untuk konfigurasi kriteria
└── hasil.ts         ← Handler untuk hasil evaluasi (dibuat nanti di F-11)
```
 
MSW diaktifkan di development mode, tidak diaktifkan di production build.
 
#### 7. `lib/constants/errorMessages.ts`
 
File konstanta yang memetakan error code API ke pesan user-friendly dalam Bahasa Indonesia. Ini dibuat di F-00 agar tersedia sejak fitur auth pertama kali diimplementasikan.
 
### Kriteria Selesai F-00 [FE]
 
```
□ apps/web berjalan di lokal tanpa error console (pnpm dev dari root atau apps/web)
□ MSW terkonfigurasi dan tidak throw error saat startup
□ Zustand stores terinisialisasi tanpa error (verifikasi via React DevTools)
□ TanStack Query QueryClient tersedia di semua halaman
□ Design tokens warna status dan lebar panel tersedia di Tailwind config
□ Struktur folder sesuai FE-01 section 6 (di dalam apps/web/)
□ packages/types dapat diimport dari apps/web tanpa error TypeScript
□ FEATURE_STATUS.md tersedia di root vendor-ai
□ Branch develop ada di repo vendor-ai
```
 
---
 
## F-01 — Auth & Login
 
**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 2–3 hari
 
### Yang Perlu Dibuat
 
#### 1. MSW Handlers untuk Auth
 
Buat handler di `test/handlers/auth.ts` untuk semua endpoint auth yang akan dikonsumsi:
- `POST /api/v1/auth/login` → kembalikan JWT + user dengan field `role`
- `POST /api/v1/auth/logout` → kembalikan 200
- `POST /api/v1/auth/refresh` → kembalikan access token baru
- `GET /api/v1/users/me` → kembalikan data user
Format response harus mengikuti persis kontrak yang didefinisikan di BE-02 section 6 agar switch ke API real semudah mengganti base URL.
 
#### 2. Halaman P-01 Login (`app/login/page.tsx`)
 
Halaman ini adalah Server Component di layer luar, dengan Client Component untuk form di dalamnya. Komponen form dipisahkan karena butuh `useState` dan event handler.
 
Yang perlu ada:
- Logo dan nama aplikasi
- Form email + password menggunakan React Hook Form + Zod (validasi format email, password tidak boleh kosong)
- Error inline di bawah field yang bermasalah (bukan alert browser, bukan toast)
- Loading state pada tombol saat request sedang berjalan
- Setelah login berhasil: simpan user data ke `authStore`, redirect ke `/dashboard`
```
lib/api/auth.ts  ← fungsi loginUser(), logoutUser(), refreshToken(), getMe()
```
 
#### 3. Middleware Route Guard (`middleware.ts`)
 
Di root project (bukan di dalam `app/`), buat `middleware.ts` yang:
- Membaca token dari cookie di setiap request
- Jika tidak ada token dan route bukan `/login`: redirect ke `/login`
- Jika ada token dan route adalah `/login`: redirect ke `/dashboard`
- Jika role `staff` dan route adalah `/approval` atau `/settings/kriteria`: redirect ke `/dashboard`
#### 4. Token Refresh Otomatis
 
Implementasi di `lib/api/client.ts`:
- Saat response 401 diterima, coba POST ke `/auth/refresh`
- Jika berhasil: simpan token baru ke `authStore`, ulangi request asli
- Jika gagal: clear `authStore`, redirect ke `/login`
- Guard race condition: jika ada banyak request yang bersamaan gagal 401, hanya satu refresh yang berjalan; yang lain mengantri
#### 5. Switch ke API Staging
 
Setelah endpoint F-01 selesai dan staging siap:
- Nonaktifkan MSW handler untuk auth
- Verifikasi alur login dengan akun test yang sudah dibuat di F-01 (`test-staff@vendor-ai.dev` dan `test-manager@vendor-ai.dev`)
### Kriteria Selesai F-01 [FE]
 
```
□ P-01: login berhasil dengan kredensial valid → redirect ke /dashboard
□ P-01: login gagal → pesan error tampil di form (bukan alert/toast)
□ P-01: form tidak bisa disubmit saat loading
□ Route guard: akses /dashboard tanpa token → redirect ke /login
□ Route guard: staff akses /approval → redirect ke /dashboard
□ Token refresh: request dengan token expired → refresh otomatis dan request diulangi
□ Logout: clear authStore → redirect ke /login
□ Unit test P-01 form: validasi error tampil, callback onSubmit dipanggil dengan argumen benar
```
 
---
 
## F-02 — Layout & AppShell
 
**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 2–3 hari
 
### Yang Perlu Dibuat
 
Ini adalah fitur FE-only. Tidak ada endpoint yang dikonsumsi. Tidak perlu MSW handler.
 
#### 1. AppShell (`components/layout/AppShell.tsx`)
 
Client Component karena membutuhkan akses ke `authStore` untuk info user dan role. Layout 3-panel:
- Sidebar kiri: lebar tetap sesuai token `sidebar-width`
- Panel konten tengah: `flex-1`, mengisi sisa ruang
- Panel AI kanan: lebar tetap sesuai token `ai-panel-width`
Di-render di `app/(auth)/layout.tsx` — semua halaman dalam route group `(auth)` mendapat AppShell otomatis.
 
#### 2. Sidebar (`components/layout/Sidebar.tsx`)
 
Client Component. Membaca role dari `authStore` untuk menentukan menu yang ditampilkan.
 
Menu untuk semua role:
- Dashboard (`/dashboard`)
- Buat Evaluasi Baru (`/evaluasi/baru`)
- Riwayat Evaluasi (`/riwayat`)
Menu hanya untuk Manager:
- Approval (`/approval`)
- Settings — Konfigurasi Kriteria (`/settings/kriteria`)
Active state: highlight menu yang route-nya aktif (gunakan `usePathname()` dari Next.js).
 
Footer: nama user, role, dan tombol logout. Logout memanggil `logoutUser()` dari `lib/api/auth.ts`, kemudian clear `authStore`, kemudian redirect ke `/login`.
 
#### 3. AIPanel Placeholder (`components/layout/AIPanel.tsx`)
 
Client Component. Di F-02, ini hanya placeholder — koneksi SSE belum aktif. Yang perlu ada:
- Header dengan label "AI Assistant" dan indikator konteks aktif (kosong untuk sekarang)
- Area pesan (kosong, dengan empty state "Tanyakan sesuatu kepada AI...")
- Input text dengan tombol kirim
- Tombol kirim disabled dan input tidak bisa diketik (SSE belum aktif)
Koneksi SSE baru diaktifkan di F-14. Semua infrastruktur state (`chatStore`) sudah siap dari F-00, tapi belum dihubungkan.
 
#### 4. Atomic Components
 
Empat komponen berikut dibutuhkan mulai F-04 dan seterusnya. Buat sekarang agar tersedia:
 
**`StatusBadge`** (`components/atomic/StatusBadge.tsx`) — props: `status` (enum 6 nilai). Tampilkan label teks sesuai status dan background color sesuai token design. Enam variant harus ditest secara eksplisit dengan unit test.
 
**`ScoreBar`** (`components/atomic/ScoreBar.tsx`) — props: `value` (0–100), `label`, `weight` (opsional). Bar horizontal dengan warna yang berubah berdasarkan rentang: merah (<40), kuning (40–60), biru (60–80), hijau (>80). Nilai di luar 0–100 di-clamp, jangan throw error.
 
**`RankBadge`** (`components/atomic/RankBadge.tsx`) — props: `rank` (integer). Rank 1 mendapat styling menonjol (background amber), rank 2–3 lebih subtle, rank 4+ tampil sebagai teks polos dengan circle kecil.
 
**`AgentStatusIcon`** (`components/atomic/AgentStatusIcon.tsx`) — props: `status` (enum: `idle` | `waiting` | `running` | `done` | `error`). Lima status, masing-masing dengan ikon Lucide yang berbeda:
- `idle`: lingkaran abu-abu polos
- `waiting`: jam pasir kuning (menunggu dependency agent lain)
- `running`: spinner biru dengan animasi berputar
- `done`: centang hijau
- `error`: X merah
**Catatan penting `waiting` vs `idle`:** `idle` berarti belum ada dalam pipeline. `waiting` berarti sudah tahu ia akan berjalan tapi menunggu agent sebelumnya selesai. Di P-04, saat pipeline mulai, agent yang menunggu dependency harus ditampilkan sebagai `waiting`, bukan `idle`, agar user paham bahwa urutan eksekusi memang disengaja.
 
### Kriteria Selesai F-02 [FE]
 
```
□ AppShell: layout 3-panel ter-render konsisten di semua halaman dalam route group (auth)
□ Sidebar: menu Manager tidak tampil untuk role staff (verifikasi dengan authStore yang di-mock)
□ Sidebar: active state benar sesuai route (gunakan usePathname)
□ AIPanel: placeholder ter-render, input ada tapi tidak bisa diketik
□ StatusBadge: 6 variant warna sesuai design tokens — unit test semua variant
□ ScoreBar: warna berubah sesuai rentang — unit test semua rentang
□ AgentStatusIcon: animasi berjalan saat status 'running', diam saat lainnya
□ Zero axe-core violation di AppShell dan Sidebar (jalankan axe secara manual atau via jest-axe)
```
 
---
 
## F-03 — Konfigurasi Kriteria (Settings P-08)
 
**Tier:** 0 | **Prerequisite:** F-00 | **Estimasi:** 2–3 hari
 
### Yang Perlu Dibuat
 
#### 1. MSW Handlers untuk Konfigurasi
 
Di `test/handlers/konfigurasi.ts`:
- `GET /api/v1/konfigurasi/kriteria?kategori=X` → kembalikan 5 kriteria dengan bobot 30/25/20/15/10
- `PUT /api/v1/konfigurasi/kriteria` → validasi total 100, kembalikan `INVALID_WEIGHT_TOTAL` jika tidak
- `GET /api/v1/kategori-pengadaan` → kembalikan daftar kategori enum
#### 2. API Client Functions
 
Di `lib/api/konfigurasi.ts`:
- `getKonfigurasiKriteria(kategori)` — query ke GET endpoint
- `updateKonfigurasiKriteria(kategori, kriteria[])` — mutasi ke PUT endpoint
- `getKategoriPengadaan()` — query ke GET kategori
#### 3. Komponen `CriteriaWeightInput` (`components/composite/CriteriaWeightInput.tsx`)
 
Props: `kriteria` (nama), `bobot` (nilai saat ini), `thresholdMin`, `isInvalid` (boolean, tampilkan border merah jika total semua bobot bukan 100), `onChange`.
 
Ini adalah komponen per-baris untuk satu kriteria. Di-compose oleh halaman P-08 untuk menampilkan 5 kriteria sekaligus.
 
#### 4. Halaman P-08 Settings Konfigurasi Kriteria
 
Route: `/settings/kriteria` — hanya Manager. Jika staff akses langsung, middleware sudah handle redirect.
 
Yang perlu ada:
- Dropdown untuk memilih kategori pengadaan (data dari `getKategoriPengadaan()`)
- Saat kategori dipilih: fetch konfigurasi kriteria untuk kategori itu dan tampilkan 5 `CriteriaWeightInput`
- Indikator total bobot yang diperbarui real-time saat user mengubah angka (tampilkan "Total: 95%" dengan warna merah jika bukan 100)
- Tombol simpan disabled selama total ≠ 100%
- Tombol reset ke nilai default
- Setelah simpan berhasil: invalidasi cache `['konfigurasi-kriteria', kategori]` dan tampilkan toast sukses
State form dikelola dengan React Hook Form. Indikator total adalah nilai derivatif yang dihitung live dari `watch()` React Hook Form — tidak perlu `useState` tersendiri.
 
#### 5. Switch ke API Staging
 
Setelah endpoint F-03 selesai.
 
### Kriteria Selesai F-03 [FE]
 
```
□ P-08: hanya bisa diakses Manager (middleware sudah handle, tapi verifikasi di integration test)
□ P-08: dropdown kategori berfungsi dan memuat konfigurasi yang benar
□ P-08: total bobot diperbarui real-time saat input berubah
□ P-08: tombol simpan disabled saat total ≠ 100%
□ P-08: simpan berhasil → toast sukses + data ter-refresh
□ Unit test CriteriaWeightInput: isInvalid = true menampilkan border merah, onChange dipanggil dengan nilai benar
```
 
---
 
## F-04 — Dashboard (P-02)
 
**Tier:** 1 | **Prerequisite:** F-01, F-02 | **Estimasi:** 2–3 hari
 
### Yang Perlu Dibuat
 
#### 1. MSW Handlers untuk Evaluasi
 
Di `test/handlers/evaluasi.ts` (mulai populasi handler yang akan terus berkembang):
- `GET /api/v1/evaluasi` dengan query params: `status`, `kategori`, `search`, `page`, `limit` → kembalikan daftar evaluasi dengan pagination
- `GET /api/v1/evaluasi/summary` → kembalikan `{ draft: 2, processing: 1, selesai: 3, menunggu_approval: 1 }`
Buat beberapa variasi data: evaluasi dengan status berbeda, tanggal berbeda, dan pembuat berbeda (untuk test role manager vs staff).
 
#### 2. API Client Functions
 
Di `lib/api/evaluasi.ts`:
- `getEvaluasiList(filters)` — query dengan semua filter yang didukung
- `getEvaluasiSummary()` — query ringkasan jumlah per status
#### 3. Komponen `EvaluasiRow` (`components/composite/EvaluasiRow.tsx`)
 
Props: `evaluasi` (object dengan id, judul, kategori, jumlahVendor, status, createdAt, vendorTerpilih). Tampilkan semua info dalam satu baris yang bisa di-klik.
 
Baris ini digunakan di P-02, P-06, dan P-07 — harus reusable tanpa perubahan.
 
#### 4. Halaman P-02 Dashboard
 
Route: `/dashboard` — Server Component di luar, Client Components untuk bagian interaktif.
 
Bagian yang butuh Client Component:
- **4 stat cards** — refresh data otomatis setiap 30 detik menggunakan TanStack Query `refetchInterval`
- **Daftar evaluasi terbaru** — klik baris → navigasi berdasarkan status:
  - `processing` → `/evaluasi/:id/proses`
  - `selesai` atau `menunggu_approval` atau `approved` atau `butuh_revisi` → `/evaluasi/:id/hasil`
  - `draft` → `/evaluasi/baru` (atau detail draft jika ada)
Untuk Manager: tampilkan badge/indikator khusus di stat card "Menunggu Approval" jika ada evaluasi pending.
 
Query key: `['evaluasi', 'list', filters]` untuk daftar, `['evaluasi', 'summary']` untuk stat cards.
Stale time: 1 menit untuk daftar, 1 menit untuk summary (auto-refresh sudah handle).
 
### Kriteria Selesai F-04 [FE]
 
```
□ P-02: 4 stat cards menampilkan angka yang benar dari mock data
□ P-02: klik evaluasi dengan status 'processing' → navigasi ke /evaluasi/:id/proses
□ P-02: klik evaluasi dengan status 'selesai' → navigasi ke /evaluasi/:id/hasil
□ P-02: data stat cards refresh otomatis tanpa reload halaman (verifikasi dengan mock yang di-update)
□ P-02: Manager melihat badge evaluasi pending approval
□ Integration test P-02: stat cards menampilkan angka sesuai mock API
□ Integration test P-02: klik baris evaluasi mengarah ke URL yang benar berdasarkan status
```
 
---
 
## F-05 — Riwayat Evaluasi (P-06)
 
**Tier:** 1 | **Prerequisite:** F-01, F-02, F-04 | **Estimasi:** 1–2 hari
 
### Yang Perlu Dibuat
 
Tidak ada handler atau API function baru. Semua sudah tersedia dari F-04.
 
#### Halaman P-06 Riwayat Evaluasi
 
Route: `/riwayat`
 
Perbedaan dengan Dashboard: filter lebih lengkap dan pagination full 20 item per halaman.
 
Yang perlu ada:
- Tabel daftar evaluasi reuse komponen `EvaluasiRow`
- Filter sidebar: status (multi-select), kategori (dropdown), rentang tanggal (date range picker)
- Search bar: search berdasarkan judul evaluasi (debounced 300ms sebelum trigger query)
- Pagination: 20 item per halaman, navigasi ke halaman sebelum/sesudah, total item ditampilkan
- Filter mengubah query key sehingga TanStack Query memperlakukan setiap kombinasi filter sebagai cache terpisah
Query key: `['evaluasi', 'list', { status, kategori, search, dateRange, page }]`
 
### Kriteria Selesai F-05 [FE]
 
```
□ P-06: filter status mengubah daftar yang ditampilkan
□ P-06: search dengan debounce tidak trigger request setiap keystroke
□ P-06: pagination 20 item per halaman, navigasi berfungsi
□ P-06: klik baris mengarah ke halaman yang sesuai status (sama dengan P-02)
□ Staff: hanya melihat evaluasi miliknya (data dari API sudah difilter backend, frontend cukup tampilkan apa yang dikembalikan)
```
 
---
 
## F-06 — Buat Evaluasi: Requirement & Vendor Manual
 
**Tier:** 1 | **Prerequisite:** F-01, F-02, F-04 | **Estimasi:** 3–4 hari
 
### Yang Perlu Dibuat
 
#### 1. MSW Handlers Tambahan
 
Tambahkan ke `test/handlers/evaluasi.ts`:
- `POST /api/v1/evaluasi` → kembalikan evaluasi baru dengan status `draft`
- `GET /api/v1/evaluasi/:id` → detail evaluasi dengan daftar vendor
- `POST /api/v1/evaluasi/:id/vendor` → tambah vendor, kembalikan vendor baru
- `DELETE /api/v1/evaluasi/:id/vendor/:vendorId` → kembalikan 204
- `POST /api/v1/evaluasi/:id/submit` → kembalikan 202, ubah status ke `processing` di mock state
- Skenario error: `VENDOR_LIMIT_EXCEEDED` jika vendor sudah 10, `INSUFFICIENT_VENDORS` jika kurang dari 2
#### 2. API Client Functions
 
Di `lib/api/evaluasi.ts`, tambahkan:
- `createEvaluasi(data)` — mutasi POST
- `getEvaluasiDetail(id)` — query GET detail
- `addVendor(evaluasiId, vendorData)` — mutasi POST
- `removeVendor(evaluasiId, vendorId)` — mutasi DELETE
- `submitEvaluasi(evaluasiId)` — mutasi POST
Di `lib/api/vendor.ts`: fungsi terpisah untuk operasi vendor jika perlu dipisahkan dari `evaluasi.ts`.
 
#### 3. Komponen `VendorInputCard` Mode Manual (`components/composite/VendorInputCard.tsx`)
 
Props: `vendor` (nullable — null berarti form kosong), `mode` (`manual` | `extracted` | `loading` | `error`), `onRemove`, `onSave`.
 
Di F-06, hanya mode `manual` yang diimplementasikan. Mode `extracted`, `loading`, dan `error` untuk F-07.
 
Mode manual: form dengan field nama perusahaan, kontak/website, harga penawaran (input angka dengan format IDR), catatan. Tombol hapus memanggil `onRemove`.
 
#### 4. Feature Component `EvaluasiStepper` (`components/feature/EvaluasiStepper.tsx`)
 
Client Component. Menggunakan satu React Hook Form instance untuk semua 3 langkah.
 
**Langkah 1 — Requirement Pengadaan:**
Field: judul evaluasi (required), kategori pengadaan (dropdown, required), deskripsi kebutuhan (required), budget_min (opsional), budget_max (required), deadline (date picker, required), prioritas_kriteria (reorderable list opsional), lampiran_url (file upload opsional — di F-06 cukup sebagai text input dulu).
 
Field `preferensi_perusahaan` belum ada di langkah ini — itu akan ditambahkan di F-08.
 
Validasi sebelum lanjut ke langkah 2: semua field required harus terisi.
 
**Langkah 2 — Tambah Vendor:**
Menampilkan daftar `VendorInputCard` yang sudah ditambahkan. Tombol "Tambah Vendor Manual" menambahkan card kosong baru. Minimum 2 vendor sebelum bisa lanjut ke langkah 3.
 
State daftar vendor dikelola sebagai local state di EvaluasiStepper (array of vendor IDs yang sudah di-save ke server). Setiap vendor yang disimpan langsung di-POST ke server — bukan dikumpulkan di form lalu di-batch-submit.
 
**Langkah 3 — Konfirmasi:**
Summary read-only semua data yang diisi di langkah 1 dan 2. Estimasi waktu proses AI. Tombol "Mulai Evaluasi" yang memanggil `submitEvaluasi()`.
 
Setelah submit berhasil:
- Invalidasi cache `['evaluasi']` dan `['evaluasi', 'summary']`
- Redirect ke `/evaluasi/:id/proses`
**Navigasi antar langkah:**
Data dari langkah yang sudah diisi tetap ada saat user kembali (karena satu React Hook Form instance). Tombol "Kembali" tidak melakukan API call.
 
#### 5. Halaman P-03 Buat Evaluasi Baru
 
Route: `/evaluasi/baru`
 
Secara teknis hanya berisi `EvaluasiStepper` di dalam AppShell. Stepper yang memiliki semua logika.
 
#### 6. Invalidasi Cache yang Benar
 
Setelah create evaluasi: invalidasi `['evaluasi', 'list']` dan `['evaluasi', 'summary']`.
Setelah tambah vendor: invalidasi `['evaluasi', id]`.
Setelah delete vendor: invalidasi `['evaluasi', id]`.
Setelah submit: invalidasi `['evaluasi', id]`, `['evaluasi', 'list']`, `['evaluasi', 'summary']`.
 
### Kriteria Selesai F-06 [FE]
 
```
□ P-03: step 1 tidak bisa lanjut jika field wajib kosong — pesan validasi muncul di field
□ P-03: data step 1 tetap ada saat user kembali dari step 2
□ P-03: vendor bisa ditambah (POST ke API) dan dihapus (DELETE ke API) di step 2
□ P-03: step 3 menampilkan ringkasan yang benar
□ P-03: tombol submit disabled saat kurang dari 2 vendor
□ P-03: submit berhasil → redirect ke /evaluasi/:id/proses (loading state)
□ Unit test EvaluasiStepper: navigasi antar step, validasi step 1, step indicator
□ Unit test VendorInputCard mode manual: tombol remove memanggil callback, field dapat diedit
```
 
---
 
## F-07 — Upload Dokumen & Ekstraksi
 
**Tier:** 2 | **Prerequisite:** F-06 | **Estimasi:** 3–4 hari
 
### Yang Perlu Dibuat
 
#### 1. MSW Handlers untuk Upload
 
Tambahkan ke `test/handlers/evaluasi.ts` atau buat `test/handlers/dokumen.ts`:
- `POST /api/v1/evaluasi/:id/dokumen` → kembalikan 202 dengan `uploadId`
- `GET /api/v1/evaluasi/:id/dokumen/:uploadId/status` → simulasikan progression: pertama `processing`, setelah 2x polling `done` dengan `hasilEkstraksi` terisi
- Skenario error: `FILE_TOO_LARGE` untuk file >10MB, `INVALID_FILE_TYPE` untuk bukan PDF/Excel
#### 2. API Client Functions
 
Di `lib/api/evaluasi.ts`:
- `uploadDokumen(evaluasiId, file, namaVendorHint?)` → POST multipart, kembalikan `uploadId`
- `getDokumenStatus(evaluasiId, uploadId)` → GET status polling
#### 3. Update `VendorInputCard` — Mode Upload
 
Tambahkan mode `loading` dan `extracted` ke komponen yang sudah ada:
 
**Mode loading (saat AI sedang mengekstrak):**
- Skeleton/spinner menggantikan form
- Pesan: "AI sedang membaca dokumen..."
- Indikator progress ekstraksi jika tersedia
- Setelah ekstraksi selesai, tampilkan indikator RAG indexing terpisah ("Mengindeks dokumen untuk AI Chat...")
**Mode extracted:**
- Form pre-filled dengan hasil ekstraksi AI
- `confidence_score` yang rendah ditandai dengan indikator kuning "Harap verifikasi hasil ini"
- User bisa mengedit semua field sebelum menyimpan
- Tombol "Konfirmasi" untuk menyimpan vendor dengan data yang sudah di-verifikasi
**Mode error:**
- Pesan error yang jelas
- Tombol "Input Manual" sebagai fallback
#### 4. Integrasi Polling di Langkah 2 EvaluasiStepper
 
Saat user mengupload file di VendorInputCard, alur polling berjalan:
1. POST upload → dapat `uploadId`, ubah mode card ke `loading`
2. Poll `getDokumenStatus` setiap 3 detik selama status `processing`
3. Saat status `done`: ubah mode card ke `extracted`, pre-fill form dengan `hasilEkstraksi`
4. Saat status `failed`: ubah mode card ke `error`
5. Timeout: jika setelah 2 menit masih `processing`, hentikan polling dan tampilkan pesan timeout (FE-05 section 8.4)
Polling diimplementasikan sebagai custom hook `useDocumentExtraction(uploadId)` yang menggunakan TanStack Query dengan `refetchInterval`. Hook ini menghentikan polling otomatis saat status bukan `processing`.
 
### Kriteria Selesai F-07 [FE]
 
```
□ VendorInputCard: mode loading tampil setelah upload
□ VendorInputCard: mode extracted tampil dengan hasil ekstraksi yang bisa diedit
□ VendorInputCard: confidence score rendah ditandai dengan indikator kuning
□ VendorInputCard: mode error tampil jika ekstraksi gagal, ada fallback ke manual
□ Polling: berhenti otomatis saat status done atau failed
□ Polling: berhenti setelah 2 menit dan tampilkan pesan timeout
□ Indikator RAG indexing tampil setelah ekstraksi selesai (terpisah dari ekstraksi)
□ Unit test VendorInputCard: semua 4 mode ter-render dengan benar
```
 
---
 
## F-08 — Form Preferensi Opsional
 
**Tier:** 2 | **Prerequisite:** F-06 | **Estimasi:** 1 hari
 
### Yang Perlu Dibuat
 
#### 1. Komponen `PreferenceInput` (`components/composite/PreferenceInput.tsx`)
 
Props: `value`, `onChange`, `maxLength` (default: 1000).
 
Yang tampil:
- Label "Preferensi atau Prioritas Perusahaan (opsional)"
- Textarea dengan counter karakter real-time: "X/1000 karakter"
- Counter berubah warna menjadi oranye saat >800, merah saat mendekati 1000
- Placeholder contoh: "Contoh: Kami lebih memilih vendor lokal yang memiliki layanan purna jual di kota kami, dan diprioritaskan vendor yang sudah berpengalaman di sektor pemerintahan..."
- Tidak ada validasi required — field ini memang opsional
#### 2. Tambahkan ke EvaluasiStepper Langkah 1
 
Tambahkan `PreferenceInput` ke langkah 1 di bagian bawah form, setelah semua field requirement lain.
 
Update React Hook Form schema untuk menyertakan field `preferensi_perusahaan` sebagai optional string.
 
Update `createEvaluasi()` API function untuk menyertakan `preferensi_perusahaan` di request body (bisa null).
 
Pastikan: validasi langkah 1 tidak berubah — form masih bisa disubmit tanpa mengisi preferensi.
 
### Kriteria Selesai F-08 [FE]
 
```
□ P-03 Langkah 1: textarea preferensi tampil di bawah field requirement lain
□ P-03 Langkah 1: counter karakter diperbarui real-time
□ P-03 Langkah 1: form bisa disubmit tanpa mengisi preferensi (preferensi null)
□ P-03 Langkah 1: form dengan preferensi terisi: nilai preferensi dikirim ke API
□ Unit test PreferenceInput: counter akurat, tidak mempengaruhi validasi required form lain
```
 
---
 
## F-09 — Submit, Status Flow & Approval
 
**Tier:** 2 | **Prerequisite:** F-06, F-04 | **Estimasi:** 3–4 hari
 
### Yang Perlu Dibuat
 
#### 1. MSW Handlers untuk Approval
 
Di `test/handlers/evaluasi.ts`:
- `PATCH /api/v1/evaluasi/:id/status` → ubah status ke `menunggu_approval`
- `POST /api/v1/evaluasi/:id/approval` → kembalikan 200 untuk approve/reject; `VALIDATION_ERROR` jika reject tanpa komentar
#### 2. API Client Functions
 
Di `lib/api/evaluasi.ts`:
- `kirimKeApproval(evaluasiId)` → mutasi PATCH
- `submitApproval(evaluasiId, keputusan, komentar?)` → mutasi POST
#### 3. Tombol "Kirim ke Manager" di P-05 (Placeholder)
 
P-05 belum ada kontennya di F-09, tapi tombol ini perlu ada. Buat halaman P-05 minimal dengan:
- Konten placeholder "Hasil evaluasi akan muncul di sini"
- Tombol "Kirim ke Manager untuk Approval" yang memanggil `kirimKeApproval()`
- Setelah berhasil: tombol berubah menjadi status "Sudah dikirim — menunggu persetujuan" dan disabled
Konten P-05 yang sesungguhnya baru dibangun di F-11 dan seterusnya.
 
#### 4. Komponen `ApprovalCard` (`components/composite/ApprovalCard.tsx`)
 
Props: `evaluasi` (dengan field judul, namaStaff, tanggalPengajuan, rekomendasiVendor, skor, budgetMax), `isSubmitting`, `onApprove`, `onReject`.
 
Yang tampil:
- Judul evaluasi dan info pengaju
- Rekomendasi vendor terpilih dengan skor (data dari hasil_evaluasi)
- Budget
- Tombol "Lihat Detail Lengkap" → navigasi ke `/evaluasi/:id/hasil`
- Form komentar (textarea)
- Tombol "Tolak" — disabled jika komentar kosong
- Tombol "Setujui" — tidak perlu komentar
#### 5. Halaman P-07 Approval
 
Route: `/approval` — hanya Manager.
 
Yang perlu ada:
- Dua tab: "Menunggu Keputusan" dan "Sudah Diproses"
- Tab "Menunggu": daftar `ApprovalCard` dari evaluasi status `menunggu_approval`
- Setelah approve/reject: card hilang dari tab "Menunggu", muncul di "Sudah Diproses"
- Invalidasi cache setelah approval: `['evaluasi', id]`, `['evaluasi', 'list']`, `['evaluasi', 'summary']`
### Kriteria Selesai F-09 [FE]
 
```
□ P-05: tombol "Kirim ke Manager" memanggil API dan berubah menjadi status "sudah dikirim"
□ P-07: hanya bisa diakses Manager (middleware handle, verifikasi di test)
□ P-07: tab "Menunggu" menampilkan evaluasi dengan status menunggu_approval
□ P-07: tombol reject disabled jika komentar kosong
□ P-07: setelah approve, card hilang dari tab "Menunggu"
□ P-07: setelah approve, status evaluasi berubah (verifikasi dari invalidasi cache)
□ Unit test ApprovalCard: tombol reject disabled tanpa komentar, callbacks dipanggil dengan argumen benar
```
 
---
 
## Checkpoint Integrasi Tier 1–2
 
Sebelum memulai Tier 3, lakukan verifikasi frontend menyeluruh:
 
### Happy Path Manual
 
Jalankan happy path ini secara manual di browser (dengan backend staging atau MSW):
 
1. Login sebagai staff → P-02 tampil dengan stat cards
2. Buat evaluasi baru: isi semua field step 1 (dengan dan tanpa preferensi), tambah 2 vendor manual, konfirmasi, submit
3. Redirect ke P-04 → loading state tampil
4. Upload dokumen di step 2: verifikasi polling status ekstraksi
5. Login sebagai manager → P-07 tampil evaluasi yang dikirim staff
6. Approve evaluasi → card hilang dari tab "Menunggu"
7. Ubah bobot di P-08: verifikasi total real-time, simpan berhasil
### Verifikasi Teknis
 
```
□ TanStack Query cache invalidation bekerja setelah setiap mutasi (verifikasi dari Network tab)
□ Token refresh otomatis berjalan saat token expired (simulasikan dengan token yang sengaja diset expired)
□ Tidak ada console error saat menjalankan happy path
□ Zero axe-core violation di semua halaman Tier 0–2
□ Semua MSW handlers yang akan dinonaktifkan sudah diidentifikasi dan siap di-switch ke staging
```
 
---
 
## F-10 — AI Processing & Progress Real-time (P-04)
 
**Tier:** 3 | **Prerequisite:** F-06, F-07, Checkpoint Tier 1–2 | **Estimasi:** 2–3 hari (FE portion)
 
### Yang Perlu Dibuat
 
#### 1. Feature Component `AgentProgressPanel` (`components/feature/AgentProgressPanel.tsx`)
 
Ini adalah Client Component dengan Supabase Realtime subscription. Logika yang cukup kompleks — baca FE-04 section 8.1 dan FE-05 section 9 sebelum implementasi.
 
**Alur lifecycle komponen:**
1. Mount: subscribe ke channel Supabase Realtime `evaluasi-progress-{evaluasiId}`
2. Fetch data awal progress semua agent via TanStack Query (untuk kasus halaman di-refresh)
3. Setiap event dari Realtime: update local state agent yang berubah
4. Saat semua 7 agent berstatus `done`: panggil callback `onAllAgentsDone()`
5. Unmount: **wajib** unsubscribe dari channel (jika tidak, memory leak di background)
**Yang ditampilkan untuk setiap agent:**
- Nama agent yang human-readable (bukan `data_collector`, tapi "Data Collector")
- `AgentStatusIcon` sesuai status (`idle`/`waiting`/`running`/`done`/`error`)
- Progress bar (0–100%) dari field `progress`
- `pesan_terakhir` — teks singkat apa yang sedang dikerjakan
- Jika status `error`: `error_detail` ditampilkan dengan warna merah (bukan sebagai modal/blocking)
**State `waiting` vs `idle`:**
Saat pipeline dimulai, inisialisasi state semua agent berdasarkan dependency graph dari FE-03 P-04:
- DC, FA, RA: `idle` → `running` (3 paralel pertama)
- PS: `waiting` saat DC belum selesai, baru `running` setelah DC `done`
- NA, QA: `waiting` saat PS belum selesai
- PM: `waiting` saat NA dan QA belum selesai
Frontend tidak perlu "mengatur" state ini — Realtime akan mengirimkan update dari database. Tapi untuk tampilan awal sebelum Realtime pertama kali mengirim update, gunakan state `waiting` berdasarkan logika dependency di atas.
 
#### 2. Custom Hook `useAgentProgress(evaluasiId)`
 
Pisahkan logika Realtime ke dalam custom hook di `hooks/useAgentProgress.ts`. Komponen AgentProgressPanel hanya mengonsumsi hook ini dan merender UI.
 
Hook mengembalikan: `{ agents, isAllDone, error }`.
 
#### 3. Halaman P-04 Processing
 
Route: `/evaluasi/:id/proses`
 
Yang perlu ada:
- Header: judul evaluasi dan info singkat (kategori, jumlah vendor)
- `AgentProgressPanel` — komponen utama halaman ini
- Estimasi waktu selesai keseluruhan di bagian bawah panel
- Auto-redirect ke `/evaluasi/:id/hasil` saat `isAllDone = true` (delay kecil agar user sempat melihat semua agent `done`)
- Pesan bahwa user boleh meninggalkan halaman — proses tetap berjalan
### Kriteria Selesai F-10 [FE]
 
```
□ P-04: status 7 agent update real-time tanpa reload halaman
□ P-04: agent yang menunggu dependency ditampilkan dengan state 'waiting' yang berbeda dari idle
□ P-04: agent yang error ditampilkan sebagai warning (bukan error fatal yang memblokir halaman)
□ P-04: auto-redirect ke P-05 saat semua agent done
□ P-04: Realtime unsubscribe saat navigasi ke halaman lain (verifikasi tidak ada memory leak)
□ Unit test AgentProgressPanel: 7 agent ter-render, state waiting berbeda dari idle
```
 
---
 
## F-11 — Hasil TOPSIS & Reasoning (P-05 Bagian 1–2–6)
 
**Tier:** 3 | **Prerequisite:** F-10 | **Estimasi:** 5–7 hari
 
### Yang Perlu Dibuat
 
#### 1. MSW Handlers untuk Hasil
 
Di `test/handlers/hasil.ts`:
- `GET /api/v1/evaluasi/:id/hasil` → kembalikan struktur lengkap hasil evaluasi dengan ranking vendor, skor per kriteria, reasoning, dan semua field yang ada di `hasil_evaluasi` + `hasil_vendor`
- Buat beberapa fixture: evaluasi dengan 3 vendor (ranking jelas), evaluasi dengan konflik preferensi
Format response harus mencerminkan persis apa yang dikembalikan backend (lihat BE-02 section 9).
 
#### 2. API Client Function
 
Di `lib/api/hasil.ts`:
- `getHasilEvaluasi(evaluasiId)` → query GET hasil
#### 3. Komponen `RecommendationCard` (`components/feature/RecommendationCard.tsx`)
 
Props: `vendorNama`, `rankBadge`, `skorTotal`, `reasoningSingkat` (2 kalimat), `isLoading`.
 
Ini adalah "hero card" — harus secara visual paling menonjol di halaman. Ukuran lebih besar, styling berbeda.
 
#### 4. Komponen `VendorRankingTable` (`components/feature/VendorRankingTable.tsx`)
 
Props: `vendors` (array dengan rank, nama, skor per kriteria, kesesuaian preferensi, unique offerings, profil kualitatif), `konfigurasi` (nama dan bobot per kriteria untuk label kolom).
 
Yang tampil di baris utama: `RankBadge`, nama vendor, skor total, skor per kriteria (satu kolom per kriteria), badge `tingkat_kesesuaian_preferensi` (jika ada).
 
Expand per baris (klik baris untuk toggle):
- `ScoreBar` per kriteria dengan label nama kriteria
- Catatan AI per kriteria (teks singkat)
- `CriteriaBarChart` — bar chart horizontal per vendor ini
- Profil kualitatif (untuk F-12, tapi struktur expand sudah siapkan sekarang)
Kolom sortable: klik header kolom untuk sort ascending/descending. Sorting adalah local state, tidak trigger API call.
 
Di F-11, kolom preferensi belum diisi (null) dan profil kualitatif kosong — itu datang di F-12 dan F-13.
 
#### 5. Komponen `AIReasoningPanel` (`components/feature/AIReasoningPanel.tsx`)
 
Props: `reasoningUtama`, `kelemahanUtama`, `rekomendasiNegosiasi`.
 
Tiga bagian yang jelas terpisah:
- Mengapa vendor terpilih direkomendasikan
- Kelemahan yang perlu diwaspadai
- Rekomendasi langkah negosiasi selanjutnya
#### 6. Chart `CriteriaBarChart` (`components/charts/CriteriaBarChart.tsx`)
 
Props: `vendorNama`, `scores` (array of `{ kriteria, skor, bobot }`).
 
Bar chart horizontal menggunakan Chart.js. Warna bar sesuai rentang nilai (sama dengan ScoreBar). Label kriteria di sumbu Y.
 
#### 7. Halaman P-05 Hasil Rekomendasi (Bagian 1, 2, dan 6)
 
Route: `/evaluasi/:id/hasil`
 
Di F-11, implementasikan Bagian 1, 2, 3 (tabel ranking), dan 6:
 
**Bagian 1 — Narasi pengantar:**
Teks dari `preference_matching_result` jika ada preferensi, atau teks generik "Hasil evaluasi berdasarkan metrik terukur TOPSIS" jika tidak ada. Di F-11, cukup tampilkan teks generik — narasi dari PM baru di F-13.
 
**Bagian 2 — RecommendationCard:**
Data dari `vendor_rekomendasi_id` dan `reasoning_utama` di `hasil_evaluasi`. Tombol "Kirim ke Manager" ada di sini (sudah dibuat di F-09 tapi sekarang dalam konteks yang benar).
 
**Bagian 3 — VendorRankingTable:**
Semua vendor dari `hasil_vendor` diurutkan berdasarkan `rank`.
 
**Bagian 6 — AIReasoningPanel:**
Data dari `reasoning_utama`, `kelemahan_utama`, `rekomendasi_negosiasi` di `hasil_evaluasi`.
 
Bagian 4 (profil kualitatif) dan Bagian 5 (rekomendasi preferensi) placeholder untuk F-12 dan F-13.
 
Query key: `['evaluasi', id, 'hasil']`, stale time: 5 menit.
 
### Kriteria Selesai F-11 [FE]
 
```
□ P-05 Bagian 2: RecommendationCard menampilkan vendor rank 1 dengan skor dan reasoning
□ P-05 Bagian 3: VendorRankingTable menampilkan semua vendor terurut dari skor tertinggi
□ P-05 Bagian 3: expand baris menampilkan ScoreBar, catatan per kriteria, dan CriteriaBarChart
□ P-05 Bagian 3: sort kolom berfungsi (local state, tidak trigger API)
□ P-05 Bagian 6: AIReasoningPanel menampilkan tiga bagian reasoning
□ P-05: halaman bersifat read-only (tidak ada input)
□ Visual regression baseline di-capture untuk halaman P-05
□ Unit test VendorRankingTable: expand/collapse baris, sort kolom
□ Unit test RecommendationCard: render semua props dengan benar
```
 
---
 
## F-12 — Profil Kualitatif (P-05 Bagian 3–4)
 
**Tier:** 3 | **Prerequisite:** F-10, F-11 | **Estimasi:** 3–4 hari
 
### Yang Perlu Dibuat
 
#### 1. Komponen `QualitativeProfileCard` (`components/feature/QualitativeProfileCard.tsx`)
 
Props: `vendorNama`, `profilKualitatif` (teks naratif), `uniqueOfferings` (array of `{ deskripsi, relevansi, sumber }`), `isLoading`.
 
Yang tampil:
- Judul: nama vendor
- Narasi `profil_kualitatif` dalam paragraf
- Daftar `unique_offerings` dengan badge relevansi per item (`sangat_relevan` / `relevan` / `netral` — gunakan warna berbeda)
Jika `profil_kualitatif` null (agent gagal): tampilkan empty state "Data kualitatif tidak tersedia untuk vendor ini".
 
#### 2. Komponen `QualitativeSummaryPanel` (`components/feature/QualitativeSummaryPanel.tsx`)
 
Props: `summaryKomparatif` (teks naratif dari `summary_komparatif_kualitatif`).
 
Panel sederhana dengan narasi komparatif. Jika null: tampilkan empty state.
 
#### 3. Update `VendorRankingTable` — Expand dengan Profil Kualitatif
 
Tambahkan ke bagian expand baris: `QualitativeProfileCard` per vendor. Data sudah ada di `hasil_vendor`, tinggal di-pass sebagai props.
 
#### 4. Update Halaman P-05 — Bagian 3 dan 4
 
**Bagian 3 (sudah ada dari F-11) — tambahkan:**
Profil kualitatif muncul di expand baris VendorRankingTable.
 
**Bagian 4 (baru):**
- `QualitativeSummaryPanel` — summary komparatif semua vendor
- Daftar `QualitativeProfileCard` untuk setiap vendor (di luar tabel, sebagai section terpisah)
### Kriteria Selesai F-12 [FE]
 
```
□ P-05 Bagian 4: QualitativeSummaryPanel tampil dengan narasi komparatif
□ P-05 Bagian 4: QualitativeProfileCard tampil untuk setiap vendor
□ P-05 Bagian 3: expand baris VendorRankingTable menyertakan profil kualitatif vendor
□ QualitativeProfileCard: badge relevansi per unique offering tampil dengan warna yang benar
□ QualitativeProfileCard: empty state tampil jika profil_kualitatif null
□ Unit test QualitativeProfileCard: render semua variant (dengan data, null, loading)
```
 
---
 
## F-13 — Rekomendasi Preferensi & Conflict Callout (P-05 Bagian 5)
 
**Tier:** 3 | **Prerequisite:** F-08, F-12 | **Estimasi:** 3–4 hari
 
### Yang Perlu Dibuat
 
#### 1. Komponen `PreferenceRecommendationCard` (`components/feature/PreferenceRecommendationCard.tsx`)
 
Props: `recommendations` (array 1–3 vendor dengan `urutan`, `vendorNama`, `alasanUtama`).
 
Yang tampil per vendor yang direkomendasikan: badge urutan, nama vendor, narasi alasan mengapa vendor ini sesuai preferensi.
 
#### 2. Komponen `ConflictCallout` (`components/feature/ConflictCallout.tsx`)
 
Props: `vendorToptsis` (nama vendor rank 1 TOPSIS), `vendorPreferensi` (nama vendor paling sesuai preferensi), `catatanKonflik` (narasi trade-off).
 
**Desain yang wajib dipenuhi:**
- Warna peringatan yang tidak bisa dilewatkan (amber atau oranye kuat)
- Posisi prominan (sebelum PreferenceRecommendationCard)
- **Tidak bisa di-dismiss** — tidak ada tombol tutup — tampil selama halaman terbuka
- Isi: penjelasan singkat bahwa vendor terbaik TOPSIS ≠ vendor paling sesuai preferensi, disertai `catatan_konflik`
#### 3. Update Halaman P-05 — Bagian 1 dan 5
 
**Bagian 1 — Update narasi pengantar:**
Ganti teks placeholder dari F-11 dengan narasi yang sebenarnya dari `preference_matching_result`. Jika evaluasi menggunakan preferensi: tampilkan narasi yang menyebutkan preferensi apa yang dipertimbangkan. Jika tidak: tampilkan narasi objektif.
 
**Bagian 5 (baru) — hanya tampil jika evaluasi menggunakan preferensi:**
Kondisi tampil: `evaluasi.preferensi_perusahaan !== null`.
 
Urutan dalam Bagian 5:
1. `ConflictCallout` — tampil hanya jika `conflict_callout.ada_konflik === true`
2. `PreferenceRecommendationCard` — rekomendasi 1–3 vendor berbasis preferensi
**Update `VendorRankingTable`:**
Tambahkan badge `tingkat_kesesuaian_preferensi` di kolom baris utama (badge kecil: `tinggi`/`sedang`/`rendah`). Badge hanya tampil jika evaluasi menggunakan preferensi.
 
### Kriteria Selesai F-13 [FE]
 
```
□ P-05: Bagian 5 hanya tampil jika preferensi_perusahaan tidak null
□ P-05: ConflictCallout tampil prominan jika ada konflik, tidak bisa di-dismiss
□ P-05: Bagian 1 narasi berbeda antara mode netral dan opinionated
□ P-05: PreferenceRecommendationCard menampilkan 1–3 vendor rekomendasi dengan reasoning
□ VendorRankingTable: badge kesesuaian preferensi tampil di baris utama (jika ada preferensi)
□ Unit test ConflictCallout: tidak ada tombol dismiss, konten tampil dengan benar
□ Unit test PreferenceRecommendationCard: semua vendor rekomendasi ter-render
```
 
---
 
## F-14 — AI Chat Panel + RAG
 
**Tier:** 3 | **Prerequisite:** F-07, F-11 | **Estimasi:** 3–4 hari
 
### Yang Perlu Dibuat
 
#### 1. Aktifkan AIPanel — Koneksi SSE
 
Update `components/layout/AIPanel.tsx` dari placeholder menjadi implementasi penuh.
 
**Alur per pesan user (FE-04 section 8.2 dan FE-05 section 10):**
 
1. User kirim pesan → tambahkan pesan user ke `chatStore`
2. Buka koneksi SSE ke `POST /v1/chat/stream` (FastAPI) dengan body: `{ pesan, konteksHalaman, evaluasiId?, riwayatChat }` — riwayat maks 10 pesan terakhir dari `chatStore`
3. Tampilkan typing indicator (animasi 3 titik bergerak) selama streaming
4. Event `type: token` diterima → append ke buffer local state (bukan ke chatStore — cegah re-render berlebihan)
5. Buffer di-render sebagai pesan AI yang sedang ditulis secara live
6. Event `type: done` → pindahkan buffer ke chatStore sebagai satu pesan utuh; tutup koneksi SSE
7. Event `type: error` → tampilkan pesan error di chat; tutup koneksi SSE
**Reset chat:**
- Saat `evaluasiId` berubah (user berpindah ke evaluasi lain): panggil `chatStore.resetChat()`
- Saat logout: clear `chatStore`
#### 2. Konteks Per Halaman
 
Update `AppShell` untuk memperbarui `chatStore.activeContext` saat halaman berganti:
- Dashboard: `{ halaman: 'dashboard', evaluasiId: null }`
- Processing: `{ halaman: 'processing', evaluasiId: currentId }`
- Hasil: `{ halaman: 'hasil', evaluasiId: currentId }` — ini yang akan mengaktifkan RAG di backend
`activeContext` disertakan di setiap request SSE sehingga AI tahu konteks apa yang relevan.
 
#### 3. Custom Hook `useAIChat()`
 
Pisahkan logika SSE ke `hooks/useAIChat.ts`. Hook mengelola lifecycle koneksi, buffer, dan interaksi dengan `chatStore`. AIPanel mengonsumsi hook ini dan hanya merender UI.
 
Cleanup wajib: tutup SSE connection saat hook di-unmount (`useEffect` cleanup function).
 
#### 4. Update AIPanel dari Placeholder ke Full
 
Yang perlu ditambahkan ke AIPanel dari versi F-02:
- Koneksi SSE aktif (via `useAIChat()`)
- Typing indicator selama streaming
- Pesan AI yang sudah selesai dari `chatStore`
- Handling error SSE dengan pesan user-friendly
- Reset saat evaluasi berganti
### Kriteria Selesai F-14 [FE]
 
```
□ AIPanel: pesan user dan respons AI tampil berurutan
□ AIPanel: typing indicator tampil selama streaming berlangsung
□ AIPanel: pesan tidak duplikat saat streaming selesai (buffer ke chatStore hanya sekali)
□ AIPanel: reset saat user berpindah ke evaluasi berbeda
□ AIPanel: koneksi SSE tertutup saat navigasi ke halaman lain (verifikasi tidak ada memory leak)
□ AIPanel (P-05): context halaman 'hasil' + evaluasiId dikirim ke setiap request
□ Unit test useAIChat: koneksi dibuka saat send, ditutup saat unmount
```
 
---
 
## Checkpoint Final — Release Readiness
 
### Happy Path End-to-End
 
Jalankan skenario lengkap ini di browser (connected ke staging backend):
 
```
Login sebagai Staff (test-staff@vendor-ai.dev)
  ↓
Buat evaluasi baru:
  - Isi semua field step 1 lengkap
  - Isi field preferensi: "Kami memilih vendor lokal dengan support 24 jam"
  - Tambah 2 vendor manual + upload 1 PDF penawaran nyata
  - Konfirmasi ekstraksi, edit jika perlu, konfirmasi dan submit
  ↓
P-04: pantau 7 agent real-time — verifikasi urutan eksekusi, state waiting, auto-redirect
  ↓
P-05: verifikasi semua 6 bagian tampil
  - Narasi pengantar mode opinionated (ada preferensi)
  - RecommendationCard rank 1 dengan reasoning
  - VendorRankingTable dengan expand dan sort berfungsi
  - Profil kualitatif per vendor
  - Rekomendasi preferensi + ConflictCallout (jika ada konflik)
  - AIReasoningPanel dengan 3 bagian
  ↓
Chat dengan AIPanel di P-05 — tanya tentang isi dokumen vendor
  ↓
Klik "Kirim ke Manager"
  ↓
Login sebagai Manager (test-manager@vendor-ai.dev)
  ↓
P-07: evaluasi muncul di tab "Menunggu" — baca detail, approve
  ↓
Verifikasi status berubah ke 'approved' di P-06
```
 
### Verifikasi Aksesibilitas
 
```
□ Zero axe-core violation di semua 8 halaman (P-01 s/d P-08)
□ Semua form dapat diisi dengan keyboard saja (Tab untuk navigasi, Enter untuk submit)
□ Semua tombol memiliki label yang bermakna untuk screen reader
```
 
### Verifikasi Visual Regression
 
```
□ Semua screenshot baseline sudah diambil di environment yang konsisten (Docker)
□ Tidak ada perbedaan visual yang tidak disengaja (diff clean)
```
 
### E2E Test (Playwright)
 
Pastikan 4 critical path E2E berikut lulus:
 
```
□ Happy path staff: login → buat evaluasi → submit → P-04 loading → redirect P-05
□ Happy path approval: P-05 kirim ke manager → login manager → P-07 approve
□ Role restriction: staff tidak bisa akses /approval dan /settings
□ Token refresh: request dengan expired token berhasil di-refresh otomatis
```
 
### Checklist Final [FE]
 
```
□ Semua 4 critical path E2E lulus di Playwright
□ Zero axe-core violation di semua 8 halaman
□ Semua form dapat diisi dengan keyboard saja
□ Visual regression: tidak ada perbedaan yang tidak disengaja
□ Unit test coverage > 80% untuk semua komponen dengan logika kondisional
□ Tidak ada console error di browser saat menjalankan happy path
□ Semua MSW handlers nonaktif (tidak aktif di production build)
□ Environment variables production terkonfigurasi di Vercel
□ Build production berhasil tanpa error atau warning TypeScript
□ Semua pipeline CI di repo vendor-ai hijau
```
 
---
 
## Referensi Cepat — Komponen per Fitur
 
| Fitur | Komponen Baru | Digunakan Di |
|---|---|---|
| F-00 | — | Fondasi semua fitur |
| F-01 | LoginForm (Client dalam P-01) | P-01 |
| F-02 | AppShell, Sidebar, AIPanel (placeholder), StatusBadge, ScoreBar, RankBadge, AgentStatusIcon | Semua halaman |
| F-03 | CriteriaWeightInput | P-08 |
| F-04 | EvaluasiRow | P-02, P-06, P-07 |
| F-05 | — (reuse EvaluasiRow) | P-06 |
| F-06 | VendorInputCard (manual), EvaluasiStepper | P-03 |
| F-07 | VendorInputCard (mode extracted/loading/error) | P-03 |
| F-08 | PreferenceInput | P-03 Langkah 1 |
| F-09 | ApprovalCard | P-07; Tombol "Kirim" di P-05 |
| F-10 | AgentProgressPanel | P-04 |
| F-11 | RecommendationCard, VendorRankingTable, AIReasoningPanel, CriteriaBarChart | P-05 |
| F-12 | QualitativeProfileCard, QualitativeSummaryPanel | P-05 Bagian 3–4 |
| F-13 | PreferenceRecommendationCard, ConflictCallout | P-05 Bagian 5 |
| F-14 | AIPanel (full SSE) | Semua halaman |
 
---
 
## Referensi Cepat — State Management per Fitur
 
| Data | Di Mana Disimpan | Kapan Di-reset/Invalidasi |
|---|---|---|
| Data user & token | `authStore` | Saat logout atau token gagal di-refresh |
| Riwayat chat AI | `chatStore` | Saat evaluasiId berganti, saat logout |
| Notifikasi toast | `notificationStore` | Otomatis setelah durasi habis |
| Daftar evaluasi | TanStack Query `['evaluasi', 'list', filters]` | Setelah create, submit, approval |
| Detail evaluasi | TanStack Query `['evaluasi', id]` | Setelah tambah/hapus vendor, submit |
| Hasil evaluasi | TanStack Query `['evaluasi', id, 'hasil']` | Tidak pernah (data final) |
| Konfigurasi kriteria | TanStack Query `['konfigurasi-kriteria', kategori]` | Setelah manager simpan perubahan |
| Progress agent | Local state AgentProgressPanel | Di-reset saat komponen unmount |
| Token streaming AI | Buffer local state AIPanel | Setelah event `done` (dipindah ke chatStore) |
| Form buat evaluasi | React Hook Form di EvaluasiStepper | Saat form berhasil disubmit |
 
---
 
*Dokumen ini adalah panduan kerja operasional yang harus selalu sinkron dengan spesifikasi di FE-01 s/d FE-06. Jika ada perubahan spec, panduan ini perlu diperbarui sebelum task implementasi dimulai.*
 
---
 
**Riwayat Perubahan**
 
| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-12 | Versi awal | — |
| 2.0.0 | 2026-06-12 | Adopsi 2-repo (ADR-031): perbarui section Prasyarat (vendor-ai-frontend → apps/web dalam monorepo vendor-ai, tambah catatan packages/types dan FEATURE_STATUS.md bersama), perbarui struktur folder F-00 (nama root folder), perbarui kriteria selesai F-00 (nama path, branch di vendor-ai), perbarui checklist final (repo vendor-ai), perbarui referensi MILESTONE_PLAN ke v4.0.0 | — |
| 3.0.0 | 2026-06-13 | Adopsi ADR-036 (2 track solo developer): ganti `fe/develop` → `develop` di prasyarat F-00 dan checklist; hapus referensi "Backend Engineer" di konvensi MSW; ganti "Keempat" → "Empat" di deskripsi atomic components | — |