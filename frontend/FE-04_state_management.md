# FE-04 — State Management Specification

**Project:** AI Vendor Selection System  
**Dokumen:** FE-04 — State Management  
**Versi:** 1.0.0  
**Tanggal:** 2026-06-07  
**Status:** Draft  
**Author:** —  
**Direview oleh:** —

---

## Daftar Isi

1. [Tujuan Dokumen](#1-tujuan-dokumen)
2. [Referensi Dokumen](#2-referensi-dokumen)
3. [Prinsip State Management](#3-prinsip-state-management)
4. [Tiga Lapisan State](#4-tiga-lapisan-state)
5. [Zustand — Global Client State](#5-zustand--global-client-state)
6. [TanStack Query — Server State](#6-tanstack-query--server-state)
7. [Local Component State](#7-local-component-state)
8. [Kasus Khusus](#8-kasus-khusus)
9. [Aturan & Larangan](#9-aturan--larangan)
10. [Catatan untuk Dokumen Lanjutan](#10-catatan-untuk-dokumen-lanjutan)

---

## 1. Tujuan Dokumen

Dokumen ini mendefinisikan **bagaimana state dikelola** di seluruh aplikasi frontend — state apa yang hidup di mana, kapan setiap lapisan digunakan, dan aturan apa yang menjaga konsistensi pengelolaan state.

Dokumen ini menjawab pertanyaan yang sering membingungkan dalam project React: "Di mana sebaiknya saya menyimpan data ini?" Dengan panduan yang jelas, seluruh tim bekerja dengan pola yang konsisten dan codebase tetap mudah diprediksi.

Dokumen ini **tidak** mendefinisikan implementasi kode — engineer memutuskan detail implementasinya.

---

## 2. Referensi Dokumen

| Kode | Nama Dokumen | Keterangan |
|---|---|---|
| FE-01 | UI Architecture | Keputusan teknologi (Zustand, TanStack Query) |
| FE-02 | Component Library | Komponen yang mengonsumsi state |
| FE-03 | Page & User Flow | Halaman dan alur yang membutuhkan state |
| FE-05 | API Integration | Pola fetching data yang berintegrasi dengan TanStack Query |
| BE-02 | API Contract | Struktur data yang dikembalikan server |

---

## 3. Prinsip State Management

### 3.1 State hidup sedekat mungkin dengan yang membutuhkannya

State tidak perlu dinaikkan ke level yang lebih tinggi sebelum benar-benar dibutuhkan di sana. Jika hanya satu komponen yang membutuhkan suatu state, state tersebut cukup hidup di komponen itu sebagai local state. Hanya ketika state perlu dibagi antar komponen yang jauh secara hierarki, barulah dinaikkan ke Zustand.

### 3.2 Server state dan client state dikelola secara terpisah

Data yang berasal dari server (hasil API call) bukan "state" dalam arti tradisional — ia adalah cache dari data yang sesungguhnya hidup di server. TanStack Query mengelola cache ini dengan aturannya sendiri: kapan stale, kapan perlu di-refetch, kapan dibuang. Mencampur server state dengan client state di Zustand menciptakan dua sumber kebenaran yang bisa tidak sinkron.

### 3.3 Sumber kebenaran tunggal per domain data

Untuk setiap jenis data, hanya ada satu tempat yang menjadi sumber kebenarannya. Data evaluasi bersumber dari server (TanStack Query). Data sesi user bersumber dari authStore (Zustand). Tidak boleh ada situasi di mana data yang sama disimpan di dua tempat berbeda.

---

## 4. Tiga Lapisan State

Aplikasi mengelola state dalam tiga lapisan dengan tanggung jawab yang tidak tumpang tindih.

```
┌─────────────────────────────────────────┐
│  Server State (TanStack Query)          │
│  Data dari API — evaluasi, vendor,      │
│  hasil, konfigurasi                     │
├─────────────────────────────────────────┤
│  Global Client State (Zustand)          │
│  State UI global — sesi user,           │
│  riwayat chat AI, notifikasi            │
├─────────────────────────────────────────┤
│  Local Component State (useState)       │
│  State lokal — form input, toggle UI,   │
│  ekspansi baris tabel                   │
└─────────────────────────────────────────┘
```

**Cara memilih lapisan yang tepat:**

| Pertanyaan | Jawaban Ya |
|---|---|
| Apakah data ini berasal dari API? | → TanStack Query |
| Apakah state ini perlu diakses oleh komponen di bagian halaman yang berbeda? | → Zustand |
| Apakah state ini hanya relevan untuk satu komponen? | → Local state |

---

## 5. Zustand — Global Client State

Zustand mengelola state UI global yang perlu dibagi antar komponen jauh dalam hierarki React, tetapi tidak berasal dari server.

### 5.1 authStore

**Tujuan:** Menyimpan identitas dan sesi user yang sedang login. Ini adalah store yang paling sering diakses — hampir semua bagian aplikasi membutuhkan informasi siapa user yang login dan apa role-nya.

**Data yang disimpan:**
- Identitas user: id, nama, email, role, avatar URL
- Status autentikasi: apakah user sudah login atau belum
- Token akses JWT (untuk disisipkan ke header request)

**Kapan diisi:** Segera setelah login berhasil dan token diterima dari API.

**Kapan dikosongkan:** Saat user logout, saat token tidak bisa di-refresh, atau saat user menutup browser (bergantung pada keputusan persistensi — lihat section 5.4).

**Siapa yang mengakses:**
- Sidebar — untuk menampilkan nama dan role user
- Middleware — untuk memvalidasi akses ke route tertentu
- API client (FE-05) — untuk menyisipkan token ke header setiap request
- Semua halaman yang menampilkan konten berbeda berdasarkan role

**Mengapa token disimpan di store, bukan hanya di cookie:** Store memungkinkan akses sinkronus ke token dari dalam JavaScript tanpa perlu parsing cookie. Cookie HttpOnly tetap digunakan sebagai mekanisme keamanan untuk persistensi, tetapi store adalah sumber kebenaran saat runtime.

---

### 5.2 chatStore

**Tujuan:** Menyimpan state percakapan dengan AI panel — riwayat pesan dalam sesi aktif dan konteks halaman yang sedang aktif.

**Data yang disimpan:**
- Riwayat pesan dalam sesi: array pesan dengan role (user atau assistant), konten, dan timestamp
- Konteks aktif: halaman apa yang sedang dibuka dan ID evaluasi yang relevan (jika ada)
- Status loading: apakah AI sedang menghasilkan respons saat ini

**Kapan di-reset:**
- Saat user berpindah ke evaluasi yang berbeda — riwayat percakapan tentang evaluasi A tidak relevan saat user membuka evaluasi B
- Saat user logout

**Kapan tidak di-reset:**
- Saat user navigasi antar halaman dalam konteks evaluasi yang sama — riwayat percakapan tentang evaluasi X tetap ada saat user berpindah dari halaman processing ke halaman hasil evaluasi X

**Mengapa riwayat chat tidak disimpan di server (untuk MVP):** Menyimpan riwayat chat di server menambah kompleksitas endpoint dan skema database. Untuk MVP, riwayat chat bersifat ephemeral — hilang saat browser ditutup. Ini adalah trade-off yang disengaja untuk menyederhanakan implementasi awal.

**Siapa yang mengakses:**
- AIPanel component — untuk menampilkan riwayat dan status loading
- AppShell — untuk memperbarui konteks saat halaman aktif berganti

---

### 5.3 notificationStore

**Tujuan:** Mengelola antrian notifikasi toast yang perlu ditampilkan ke user — pesan sukses, pesan error, dan pesan informasi yang muncul sementara di pojok layar.

**Data yang disimpan:**
- Antrian notifikasi: array item dengan id unik, tipe (success/error/info/warning), pesan, dan durasi tampil

**Mengapa dibutuhkan store:** Notifikasi dapat dipicu oleh komponen manapun — form submission, respons API, error handler global — tetapi ditampilkan oleh satu komponen terpusat di layout root. Tanpa store, komponen yang memicu notifikasi harus punya referensi ke komponen yang menampilkannya, menciptakan coupling yang tidak perlu.

**Perilaku:**
- Notifikasi baru ditambahkan ke antrian
- Setelah durasi tertentu, notifikasi otomatis dihapus dari antrian
- User dapat menutup notifikasi secara manual sebelum durasinya habis

**Siapa yang mengakses:**
- Komponen manapun yang perlu menampilkan notifikasi (write)
- NotificationContainer di root layout (read)

---

### 5.4 Persistensi Zustand

Tidak semua store perlu dipersistensikan ke localStorage atau cookie.

| Store | Persistensi | Alasan |
|---|---|---|
| `authStore` | Ya — token di cookie HttpOnly | Token perlu bertahan saat browser di-refresh |
| `chatStore` | Tidak | Riwayat chat bersifat ephemeral untuk MVP |
| `notificationStore` | Tidak | Notifikasi tidak relevan setelah halaman di-refresh |

**Mengapa token di cookie HttpOnly, bukan localStorage:** Cookie HttpOnly tidak bisa diakses oleh JavaScript — hanya bisa dibaca dan dikirim oleh browser secara otomatis. Ini melindungi token dari serangan XSS. localStorage bisa dibaca oleh JavaScript sehingga rentan jika ada script berbahaya yang berjalan di halaman.

---

## 6. TanStack Query — Server State

TanStack Query mengelola semua data yang berasal dari server. Ia bertindak sebagai cache layer antara API dan komponen React.

### 6.1 Mengapa TanStack Query penting

Tanpa TanStack Query, setiap komponen yang membutuhkan data dari API harus mengelola sendiri: loading state, error state, kapan data stale, dan kapan perlu di-refetch. TanStack Query menyediakan semua ini secara otomatis dan konsisten.

### 6.2 Query keys

Query key adalah identifier unik untuk setiap query. TanStack Query menggunakan key ini untuk caching — query dengan key yang sama berbagi cache yang sama.

**Konvensi penamaan query key:**

```
[domain, identifier?, filter?]
```

| Data | Query Key |
|---|---|
| Daftar evaluasi | `['evaluasi']` |
| Daftar evaluasi dengan filter | `['evaluasi', { status, kategori }]` |
| Detail satu evaluasi | `['evaluasi', id]` |
| Hasil evaluasi | `['evaluasi', id, 'hasil']` |
| Status agent | `['evaluasi', id, 'agent-status']` |
| Ringkasan dashboard | `['evaluasi', 'summary']` |
| Konfigurasi kriteria | `['konfigurasi-kriteria', kategori]` |
| Daftar kategori | `['kategori-pengadaan']` |

**Mengapa key berbentuk array:** Key array memungkinkan invalidasi yang granular. Memanggil `invalidateQueries(['evaluasi'])` akan menginvalidasi semua query yang key-nya dimulai dengan `'evaluasi'` — termasuk detail, hasil, dan status agent. Ini berguna setelah mutasi yang mempengaruhi banyak query sekaligus.

### 6.3 Stale time per domain data

Stale time menentukan berapa lama data dianggap segar sebelum TanStack Query menganggapnya perlu di-refresh. Nilai yang tepat bergantung pada seberapa sering data berubah.

| Data | Stale Time | Alasan |
|---|---|---|
| Daftar kategori pengadaan | 24 jam | Data ini hampir tidak pernah berubah |
| Konfigurasi kriteria | 10 menit | Jarang berubah, hanya oleh manager |
| Daftar evaluasi | 1 menit | Bisa berubah oleh user lain (manager) |
| Detail evaluasi | 30 detik | Status bisa berubah saat processing |
| Hasil evaluasi | 5 menit | Data final, tidak berubah setelah selesai |
| Status agent | Real-time (Supabase Realtime) | Berubah setiap detik saat processing |

**Catatan untuk status agent:** Status agent tidak menggunakan TanStack Query polling — ia menggunakan Supabase Realtime subscription yang dijelaskan di section 8.1.

### 6.4 Invalidasi cache setelah mutasi

Saat user melakukan aksi yang mengubah data di server, cache terkait harus diinvalidasi agar data yang ditampilkan tetap akurat.

| Aksi User | Cache yang diinvalidasi |
|---|---|
| Buat evaluasi baru | `['evaluasi']`, `['evaluasi', 'summary']` |
| Tambah vendor ke evaluasi | `['evaluasi', id]` |
| Hapus vendor dari evaluasi | `['evaluasi', id]` |
| Submit evaluasi | `['evaluasi', id]`, `['evaluasi']`, `['evaluasi', 'summary']` |
| Kirim evaluasi ke approval | `['evaluasi', id]`, `['evaluasi']` |
| Manager approve/reject | `['evaluasi', id]`, `['evaluasi']`, `['evaluasi', 'summary']` |
| Simpan konfigurasi kriteria | `['konfigurasi-kriteria', kategori]` |

### 6.5 Error handling di TanStack Query

TanStack Query memiliki mekanisme retry bawaan — jika sebuah query gagal, ia akan mencoba ulang secara otomatis sebelum mengembalikan error ke komponen. Konfigurasi yang disepakati:

- **Retry count:** 2 kali untuk query biasa, 0 kali untuk mutasi (aksi yang mengubah data tidak boleh di-retry otomatis tanpa konfirmasi user)
- **Error global:** Error 401 (token expired) ditangani secara global — trigger refresh token otomatis, bukan langsung redirect ke login
- **Error 403 dan 404:** Ditangani di level komponen — menampilkan pesan yang sesuai konteks halaman

---

## 7. Local Component State

Local state adalah pilihan default untuk state yang hanya dibutuhkan dalam satu komponen. Jika state tidak perlu dibagi dengan komponen lain, tidak perlu dinaikkan ke Zustand.

### 7.1 Kapan menggunakan local state

- Status buka/tutup dialog, dropdown, atau panel yang dapat dikollaps
- Nilai input form yang belum disubmit
- Baris mana yang sedang di-expand di tabel
- Tab mana yang aktif di dalam satu komponen
- State animasi atau transisi visual

### 7.2 Kapan local state tidak cukup

Local state tidak cukup ketika komponen yang membutuhkan state tersebut berada di cabang hierarki yang berbeda dan tidak memiliki ancestor bersama yang dekat. Dalam situasi ini, pindahkan state ke Zustand — jangan lakukan prop drilling lebih dari dua level.

### 7.3 Form state

Form yang kompleks (seperti stepper di P-03) menggunakan React Hook Form untuk mengelola nilai input, validasi, dan error state. Ini bukan TanStack Query dan bukan Zustand — React Hook Form adalah library khusus form state yang lebih efisien dari `useState` untuk form dengan banyak field karena tidak menyebabkan re-render di setiap keystroke.

---

## 8. Kasus Khusus

### 8.1 State real-time progress agent (P-04)

Progress agent adalah kasus khusus karena datanya berubah sangat cepat dan didorong dari server (push), bukan ditarik oleh client (pull).

**Pendekatan:** Supabase Realtime subscription, bukan polling TanStack Query.

**Mengapa Supabase Realtime, bukan polling:** Polling setiap 3 detik mengirimkan request meskipun tidak ada perubahan. Supabase Realtime hanya mengirimkan data saat ada perubahan nyata di database — lebih efisien dan lebih responsif.

**Alur state:**
1. Komponen AgentProgressPanel subscribe ke channel Supabase Realtime untuk evaluasi ID tertentu saat komponen di-mount
2. Setiap update dari database langsung memperbarui local state komponen
3. Saat semua agent berstatus `done`, komponen memanggil callback yang memicu navigasi ke halaman hasil
4. Subscription di-unsubscribe saat komponen di-unmount untuk mencegah memory leak

**Di mana state ini hidup:** Local state di komponen AgentProgressPanel — tidak perlu di Zustand karena hanya dibutuhkan oleh satu komponen dan bersifat ephemeral.

---

### 8.2 State AI chat streaming (AIPanel)

AI chat streaming adalah kasus khusus karena respons AI datang sebagai stream token demi token melalui SSE, bukan sebagai satu response utuh.

**Pendekatan:** Local state di AIPanel untuk pesan yang sedang di-stream, chatStore untuk riwayat pesan yang sudah selesai.

**Alur state:**
1. User mengirim pesan → pesan user ditambahkan ke `chatStore`
2. Koneksi SSE dibuka ke FastAPI
3. Selama streaming berlangsung, token yang diterima di-append ke buffer local state — bukan ke chatStore — untuk mencegah re-render berlebihan
4. Saat streaming selesai (event `done` diterima), pesan lengkap AI dipindahkan dari buffer ke `chatStore`
5. Koneksi SSE ditutup

**Mengapa token streaming tidak langsung masuk chatStore:** Setiap token yang diterima akan memicu re-render seluruh komponen yang subscribe ke chatStore. Dengan buffer local state, hanya AIPanel yang re-render selama streaming berlangsung.

---

### 8.3 State form multi-langkah (P-03 EvaluasiStepper)

Form pembuatan evaluasi terdiri dari tiga langkah. User bisa navigasi bolak-balik antar langkah tanpa kehilangan data yang sudah diisi.

**Pendekatan:** React Hook Form dengan satu form instance yang mencakup ketiga langkah.

**Mengapa satu form instance:** Memudahkan validasi per langkah (validate hanya field yang relevan di langkah aktif) dan memudahkan pengiriman semua data sekaligus di langkah terakhir.

**Di mana state ini hidup:** Local state di komponen EvaluasiStepper melalui React Hook Form — tidak perlu naik ke Zustand karena stepper adalah satu komponen yang self-contained.

**Skenario refresh browser:** Jika user me-refresh browser di tengah pengisian form, data yang belum disubmit akan hilang. Ini adalah trade-off yang diterima untuk MVP — menambahkan persistensi form ke localStorage dapat dipertimbangkan di iterasi berikutnya.

---

## 9. Aturan & Larangan

Aturan-aturan berikut wajib diikuti untuk menjaga konsistensi pengelolaan state di seluruh codebase.

**Dilarang menyimpan data server di Zustand.** Data yang berasal dari API (evaluasi, vendor, hasil) harus dikelola oleh TanStack Query. Menyimpannya di Zustand menciptakan dua sumber kebenaran yang bisa tidak sinkron.

**Dilarang prop drilling lebih dari dua level.** Jika sebuah prop diteruskan melewati lebih dari dua komponen tanpa digunakan di tengah, state tersebut harus dipindahkan ke Zustand atau diakses langsung menggunakan custom hook.

**Dilarang melakukan fetch data di dalam Zustand store.** Store hanya menyimpan dan memanipulasi state — ia tidak melakukan side effects seperti API call. Fetching data adalah tanggung jawab TanStack Query atau custom hook.

**Dilarang menyimpan state derivatif.** Jika sebuah nilai bisa dihitung dari state lain, jangan simpan sebagai state terpisah — hitung saat dibutuhkan. Contoh: `isAllAgentsDone` bukan state tersendiri, melainkan dihitung dari array agents yang semua statusnya `done`.

**Dilarang mengakses Zustand store langsung dari Server Components.** Server Components berjalan di server dan tidak memiliki akses ke browser state. Zustand hanya diakses dari Client Components.

---

## 10. Catatan untuk Dokumen Lanjutan

### Untuk FE-05 (API Integration)

Dokumen ini mendefinisikan query keys dan stale time untuk TanStack Query, serta kapan cache diinvalidasi. FE-05 perlu mendefinisikan:
- Fungsi-fungsi fetcher yang dipanggil oleh setiap query
- Setup TanStack Query client (QueryClient) dengan konfigurasi global
- Pola error handling di query dan mutasi
- Pola optimistic update jika diperlukan

### Untuk FE-02 (Component Library)

Beberapa komponen memiliki kebutuhan state yang spesifik yang sudah terdefinisi di dokumen ini:
- `AgentProgressPanel` — menggunakan Supabase Realtime subscription sebagai local state
- `AIPanel` — menggunakan kombinasi local buffer state dan chatStore
- `EvaluasiStepper` — menggunakan satu React Hook Form instance untuk tiga langkah

---

*Dokumen ini adalah living document — akan diperbarui jika ada perubahan pola state management.*

---

**Riwayat Perubahan**

| Versi | Tanggal | Perubahan | Author |
|---|---|---|---|
| 1.0.0 | 2026-06-07 | Versi awal | — |
